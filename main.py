import os
from datetime import UTC, datetime, timedelta
from functools import wraps

import jwt
from flask import Flask, g, jsonify, request
from psycopg2 import IntegrityError
from psycopg2.extras import DictCursor
import psycopg2
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)

app.config["DATABASE_URL"] = os.getenv(
    "DATABASE_URL", "postgresql://localhost:5432/jufi"
)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-this-secret")
app.config["JWT_EXP_MINUTES"] = int(os.getenv("JWT_EXP_MINUTES", "60"))


def get_db_connection():
    return psycopg2.connect(app.config["DATABASE_URL"])


def create_access_token(user_id: int, email: str, roles: list[str]) -> str:
    issued_at = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "email": email,
        "roles": roles,
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + timedelta(minutes=app.config["JWT_EXP_MINUTES"])).timestamp()),
    }
    return jwt.encode(payload, app.config["JWT_SECRET_KEY"], algorithm="HS256")


def token_required(required_roles: set[str] | None = None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing Bearer token"}), 401

            token = auth_header.split(" ", 1)[1].strip()
            try:
                payload = jwt.decode(
                    token,
                    app.config["JWT_SECRET_KEY"],
                    algorithms=["HS256"],
                )
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401

            roles = set(payload.get("roles", []))
            if required_roles and not (roles & required_roles):
                return jsonify({"error": "Insufficient role permissions"}), 403

            g.user = {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "roles": list(roles),
            }
            return f(*args, **kwargs)

        return wrapper

    return decorator


def get_user_with_roles_by_email(email: str):
    query = """
        SELECT
            u.id,
            u.name,
            u.email,
            u.password_hash,
            u.is_active,
            COALESCE(ARRAY_AGG(r.name) FILTER (WHERE r.name IS NOT NULL), ARRAY[]::TEXT[]) AS roles
        FROM users u
        LEFT JOIN user_roles ur ON ur.user_id = u.id
        LEFT JOIN roles r ON r.id = ur.role_id
        WHERE lower(u.email) = lower(%s)
        GROUP BY u.id;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(query, (email,))
            return cur.fetchone()


@app.route("/api/hello", methods=["GET"])
def hello():
    return jsonify({"message": "Hello, World!"})


@app.route("/api/auth/register", methods=["POST"])
@token_required(required_roles={"admin"})
def register_user():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    role_names = data.get("roles") or ["gestor"]

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "password must have at least 8 characters"}), 400
    if not isinstance(role_names, list) or not all(isinstance(role, str) for role in role_names):
        return jsonify({"error": "roles must be a list of strings"}), 400

    normalized_roles = sorted({role.strip().lower() for role in role_names if role.strip()})
    if not normalized_roles:
        normalized_roles = ["gestor"]
    if "admin" in normalized_roles:
        return jsonify({"error": "admin role cannot be assigned from public register"}), 403

    password_hash = generate_password_hash(password)

    create_user_sql = """
        INSERT INTO users (name, email, password_hash, is_active)
        VALUES (%s, %s, %s, TRUE)
        RETURNING id, name, email;
    """

    assign_role_sql = """
        INSERT INTO user_roles (user_id, role_id)
        SELECT %s, r.id
        FROM roles r
        WHERE r.name = ANY(%s)
        ON CONFLICT (user_id, role_id) DO NOTHING;
    """

    fetch_assigned_roles_sql = """
        SELECT r.name
        FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = %s
        ORDER BY r.name;
    """

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            try:
                cur.execute(create_user_sql, (name, email, password_hash))
                created = cur.fetchone()
                if created is None:
                    conn.rollback()
                    return jsonify({"error": "User creation failed"}), 500
                cur.execute(assign_role_sql, (created["id"], normalized_roles))
                cur.execute(fetch_assigned_roles_sql, (created["id"],))
                assigned_roles = [row["name"] for row in cur.fetchall()]
                if not assigned_roles:
                    conn.rollback()
                    return jsonify({"error": "No valid roles provided"}), 400
                conn.commit()
            except IntegrityError:
                conn.rollback()
                return jsonify({"error": "Email already exists"}), 409

    return (
        jsonify(
            {
                "id": created["id"],
                "name": created["name"],
                "email": created["email"],
                "roles": assigned_roles,
            }
        ),
        201,
    )


@app.route("/api/auth/login", methods=["POST"])
def login_user():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = get_user_with_roles_by_email(email)
    if not user or not user["is_active"] or not user["password_hash"]:
        return jsonify({"error": "Invalid credentials"}), 401

    if not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(user["id"], user["email"], list(user["roles"]))
    return jsonify(
        {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in_minutes": app.config["JWT_EXP_MINUTES"],
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "roles": list(user["roles"]),
            },
        }
    )


@app.route("/api/auth/me", methods=["GET"])
@token_required()
def auth_me():
    return jsonify({"user": g.user})


@app.route("/api/admin/ping", methods=["GET"])
@token_required(required_roles={"admin"})
def admin_ping():
    return jsonify({"message": "Admin access granted"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
