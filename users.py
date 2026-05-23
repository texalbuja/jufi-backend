from typing import Callable

import psycopg2
from flask import Blueprint, g, jsonify
from psycopg2.extras import DictCursor


def create_users_blueprint(
    get_db_connection: Callable,
    token_required: Callable,
) -> Blueprint:
    users_bp = Blueprint("users", __name__)

    @users_bp.route("/users", methods=["GET"])
    @token_required(required_roles={"admin"})
    def list_users():
        query = """
            SELECT
                u.id,
                u.name,
                u.email,
                u.estado,
                u.is_active,
                u.created_at,
                u.updated_at,
                COALESCE(ARRAY_AGG(r.name) FILTER (WHERE r.name IS NOT NULL), ARRAY[]::TEXT[]) AS roles
            FROM users u
            LEFT JOIN user_roles ur ON ur.user_id = u.id
            LEFT JOIN roles r ON r.id = ur.role_id
            GROUP BY u.id
            ORDER BY u.created_at DESC, u.id DESC;
        """

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(query)
                rows = cur.fetchall()

        items = [
            {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "estado": row["estado"],
                "is_active": row["is_active"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                "roles": list(row["roles"] or []),
            }
            for row in rows
        ]

        return jsonify({"items": items})

    @users_bp.route("/users/<int:user_id>", methods=["DELETE"])
    @token_required(required_roles={"admin"})
    def deactivate_user(user_id: int):
        requester_id = str(g.user.get("id"))
        if requester_id == str(user_id):
            return jsonify({"error": "You cannot deactivate your own user"}), 403

        fetch_user_sql = """
            SELECT id, email, estado
            FROM users
            WHERE id = %s;
        """

        deactivate_sql = """
            UPDATE users
            SET
                estado = 'Inactivo',
                is_active = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id;
        """

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(fetch_user_sql, (user_id,))
                existing = cur.fetchone()
                if existing is None:
                    return jsonify({"error": "User not found"}), 404

                if (existing["email"] or "").lower() == "admin@jufi.local":
                    return jsonify({"error": "Bootstrap admin cannot be deactivated"}), 403

                if existing["estado"] == "Inactivo":
                    return jsonify({"message": "User already inactive", "id": user_id})

                try:
                    cur.execute(deactivate_sql, (user_id,))
                    conn.commit()
                except psycopg2.Error:
                    conn.rollback()
                    return jsonify({"error": "Could not deactivate user"}), 500

        return jsonify({"message": "User deactivated", "id": user_id})

    return users_bp
