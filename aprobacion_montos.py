from decimal import Decimal
from typing import Callable

from flask import Blueprint, g, jsonify, request
from psycopg2.extras import DictCursor

ALLOWED_ESTADOS = {"Solicitado", "Aprobado", "Rechazado"}


def _to_positive_decimal(raw_value: object):
    if raw_value is None:
        return None

    try:
        value = Decimal(str(raw_value))
    except Exception:
        return None

    if value <= 0:
        return None

    return value


def _serialize_row(row):
    return {
        "id": row["id"],
        "obligacion_id": row["obligacion_id"],
        "monto_solicitado": str(row["monto_solicitado"]),
        "monto_aprobado": str(row["monto_aprobado"]) if row["monto_aprobado"] is not None else None,
        "gestor_id": row["gestor_id"],
        "aprobador_id": row["aprobador_id"],
        "motivo": row["motivo"],
        "comentario_aprobador": row["comentario_aprobador"],
        "estado": row["estado"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        "obligacion": {
            "nombre_cliente": row["nombre_cliente"],
            "identificacion": row["identificacion"],
            "monto_adeudado": str(row["monto_adeudado"]) if row["monto_adeudado"] is not None else None,
            "operaciones": list(row["operaciones"] or []),
            "tipo": row["tipo"],
        },
        "gestor": {
            "id": row["gestor_user_id"],
            "name": row["gestor_name"],
            "email": row["gestor_email"],
        },
        "aprobador": {
            "id": row["aprobador_user_id"],
            "name": row["aprobador_name"],
            "email": row["aprobador_email"],
        }
        if row["aprobador_user_id"] is not None
        else None,
    }


def create_aprobacion_montos_blueprint(
    get_db_connection: Callable,
    token_required: Callable,
) -> Blueprint:
    aprobacion_montos_bp = Blueprint("aprobacion_montos", __name__)

    def _is_gestor_assigned_to_obligacion(cur, gestor_user_id: int, obligacion_id: int) -> bool:
        cur.execute(
            """
            SELECT 1
            FROM cuenta_consolidada cc
            WHERE cc.gestor_user_id = %s
              AND cc.obligacion_id = %s
            LIMIT 1;
            """,
            (gestor_user_id, obligacion_id),
        )
        return cur.fetchone() is not None

    @aprobacion_montos_bp.route("/aprobacion-montos", methods=["GET"])
    @token_required(required_roles={"aprobador", "gestor"})
    def list_aprobacion_montos():
        estado = (request.args.get("estado") or "").strip()
        obligacion_id = (request.args.get("obligacion_id") or "").strip()
        user_roles = {role.lower() for role in (g.user.get("roles") or [])}
        current_user_id = int(g.user["id"])

        where_clauses = []
        params = []

        if estado:
            if estado not in ALLOWED_ESTADOS:
                return jsonify({"error": "estado is invalid"}), 400
            where_clauses.append("am.estado = %s")
            params.append(estado)

        if obligacion_id:
            if not obligacion_id.isdigit():
                return jsonify({"error": "obligacion_id must be numeric"}), 400
            where_clauses.append("am.obligacion_id = %s")
            params.append(int(obligacion_id))

        if "aprobador" not in user_roles:
            where_clauses.append(
                """
                EXISTS (
                    SELECT 1
                    FROM cuenta_consolidada cc
                    WHERE cc.obligacion_id = am.obligacion_id
                      AND cc.gestor_user_id = %s
                )
                """
            )
            params.append(current_user_id)

        where_sql = ""
        if where_clauses:
            where_sql = f"WHERE {' AND '.join(where_clauses)}"

        query = f"""
            SELECT
                am.id,
                am.obligacion_id,
                am.monto_solicitado,
                am.monto_aprobado,
                am.gestor_id,
                am.aprobador_id,
                am.motivo,
                am.comentario_aprobador,
                am.estado,
                am.created_at,
                am.updated_at,
                o.nombre_cliente,
                o.identificacion,
                o.monto_adeudado,
                o.operaciones,
                o.tipo,
                ug.id AS gestor_user_id,
                ug.name AS gestor_name,
                ug.email AS gestor_email,
                ua.id AS aprobador_user_id,
                ua.name AS aprobador_name,
                ua.email AS aprobador_email
            FROM aprobacion_montos am
            JOIN obligaciones o ON o.id = am.obligacion_id
            JOIN users ug ON ug.id = am.gestor_id
            LEFT JOIN users ua ON ua.id = am.aprobador_id
            {where_sql}
            ORDER BY am.created_at DESC, am.id DESC;
        """

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(query, tuple(params))
                rows = cur.fetchall()

        return jsonify({"items": [_serialize_row(row) for row in rows]})

    @aprobacion_montos_bp.route("/aprobacion-montos", methods=["POST"])
    @token_required(required_roles={"gestor"})
    def create_aprobacion_monto():
        payload = request.get_json(silent=True) or {}
        obligacion_id = payload.get("obligacion_id")
        monto_solicitado = _to_positive_decimal(payload.get("monto_solicitado"))
        motivo = (payload.get("motivo") or "").strip()
        gestor_id = int(g.user["id"])

        if not isinstance(obligacion_id, int):
            return jsonify({"error": "obligacion_id is required and must be an integer"}), 400
        if monto_solicitado is None:
            return jsonify({"error": "monto_solicitado must be a positive number"}), 400
        if not motivo:
            return jsonify({"error": "motivo is required"}), 400

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT id FROM obligaciones WHERE id = %s", (obligacion_id,))
                obligacion = cur.fetchone()
                if obligacion is None:
                    return jsonify({"error": "Obligacion not found"}), 404

                if not _is_gestor_assigned_to_obligacion(cur, gestor_id, obligacion_id):
                    return jsonify({"error": "Gestor is not assigned to this obligacion"}), 403

                cur.execute(
                    """
                    INSERT INTO aprobacion_montos (
                        obligacion_id,
                        monto_solicitado,
                        gestor_id,
                        motivo,
                        estado
                    )
                    VALUES (%s, %s, %s, %s, 'Solicitado')
                    RETURNING id;
                    """,
                    (obligacion_id, monto_solicitado, gestor_id, motivo),
                )
                created = cur.fetchone()
                conn.commit()

        return jsonify({"id": created["id"], "estado": "Solicitado"}), 201

    @aprobacion_montos_bp.route("/aprobacion-montos/<int:aprobacion_id>/aprobar", methods=["POST"])
    @token_required(required_roles={"aprobador"})
    def aprobar_aprobacion_monto(aprobacion_id: int):
        payload = request.get_json(silent=True) or {}
        monto_aprobado = _to_positive_decimal(payload.get("monto_aprobado"))
        comentario = (payload.get("comentario_aprobador") or "").strip() or None
        aprobador_id = int(g.user["id"])

        if monto_aprobado is None:
            return jsonify({"error": "monto_aprobado must be a positive number"}), 400

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(
                    """
                    SELECT am.id, am.estado, am.obligacion_id, o.monto_adeudado
                    FROM aprobacion_montos am
                    JOIN obligaciones o ON o.id = am.obligacion_id
                    WHERE am.id = %s
                    FOR UPDATE;
                    """,
                    (aprobacion_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return jsonify({"error": "Aprobacion not found"}), 404

                if row["estado"] != "Solicitado":
                    return jsonify({"error": "Only Solicitado records can be approved"}), 409

                if monto_aprobado > row["monto_adeudado"]:
                    return jsonify({"error": "monto_aprobado cannot exceed monto_adeudado"}), 400

                cur.execute(
                    """
                    UPDATE aprobacion_montos
                    SET
                        monto_aprobado = %s,
                        aprobador_id = %s,
                        comentario_aprobador = %s,
                        estado = 'Aprobado',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING id, estado, monto_aprobado;
                    """,
                    (monto_aprobado, aprobador_id, comentario, aprobacion_id),
                )
                updated = cur.fetchone()
                conn.commit()

        return jsonify(
            {
                "id": updated["id"],
                "estado": updated["estado"],
                "monto_aprobado": str(updated["monto_aprobado"]),
            }
        )

    @aprobacion_montos_bp.route("/aprobacion-montos/<int:aprobacion_id>/rechazar", methods=["POST"])
    @token_required(required_roles={"aprobador"})
    def rechazar_aprobacion_monto(aprobacion_id: int):
        payload = request.get_json(silent=True) or {}
        comentario = (payload.get("comentario_aprobador") or "").strip() or None
        aprobador_id = int(g.user["id"])

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, estado
                    FROM aprobacion_montos
                    WHERE id = %s
                    FOR UPDATE;
                    """,
                    (aprobacion_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return jsonify({"error": "Aprobacion not found"}), 404

                if row["estado"] != "Solicitado":
                    return jsonify({"error": "Only Solicitado records can be rejected"}), 409

                cur.execute(
                    """
                    UPDATE aprobacion_montos
                    SET
                        aprobador_id = %s,
                        comentario_aprobador = %s,
                        estado = 'Rechazado',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING id, estado;
                    """,
                    (aprobador_id, comentario, aprobacion_id),
                )
                updated = cur.fetchone()
                conn.commit()

        return jsonify({"id": updated["id"], "estado": updated["estado"]})

    @aprobacion_montos_bp.route("/aprobacion-montos/obligacion/<int:obligacion_id>", methods=["GET"])
    @token_required(required_roles={"aprobador", "gestor"})
    def list_aprobacion_montos_by_obligacion(obligacion_id: int):
        user_roles = {role.lower() for role in (g.user.get("roles") or [])}
        current_user_id = int(g.user["id"])

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT id FROM obligaciones WHERE id = %s", (obligacion_id,))
                if cur.fetchone() is None:
                    return jsonify({"error": "Obligacion not found"}), 404

                if "aprobador" not in user_roles:
                    if not _is_gestor_assigned_to_obligacion(cur, current_user_id, obligacion_id):
                        return jsonify({"error": "Gestor is not assigned to this obligacion"}), 403

                query = """
            SELECT
                am.id,
                am.obligacion_id,
                am.monto_solicitado,
                am.monto_aprobado,
                am.gestor_id,
                am.aprobador_id,
                am.motivo,
                am.comentario_aprobador,
                am.estado,
                am.created_at,
                am.updated_at,
                o.nombre_cliente,
                o.identificacion,
                o.monto_adeudado,
                o.operaciones,
                o.tipo,
                ug.id AS gestor_user_id,
                ug.name AS gestor_name,
                ug.email AS gestor_email,
                ua.id AS aprobador_user_id,
                ua.name AS aprobador_name,
                ua.email AS aprobador_email
            FROM aprobacion_montos am
            JOIN obligaciones o ON o.id = am.obligacion_id
            JOIN users ug ON ug.id = am.gestor_id
            LEFT JOIN users ua ON ua.id = am.aprobador_id
            WHERE am.obligacion_id = %s
            ORDER BY am.created_at DESC, am.id DESC;
        """
                cur.execute(query, (obligacion_id,))
                rows = cur.fetchall()

        return jsonify({"items": [_serialize_row(row) for row in rows]})

    return aprobacion_montos_bp