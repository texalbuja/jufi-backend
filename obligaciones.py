from typing import Callable

from flask import Blueprint, jsonify, request
from psycopg2.extras import DictCursor


def create_obligaciones_blueprint(
    get_db_connection: Callable,
    token_required: Callable,
) -> Blueprint:
    obligaciones_bp = Blueprint("obligaciones", __name__)

    @obligaciones_bp.route("/obligaciones/", methods=["GET"])
    @token_required()
    def list_obligaciones():
        search = (request.args.get("q") or "").strip()

        query = """
            SELECT
                id,
                nombre_cliente,
                identificacion,
                telefonos,
                direcciones,
                emails,
                monto_adeudado,
                tipo,
                operaciones,
                created_at,
                updated_at
            FROM obligaciones
            {where_sql}
            ORDER BY id DESC;
        """

        where_sql = ""
        params = []
        if search:
            like_term = f"%{search}%"
            where_sql = """
            WHERE (
                nombre_cliente ILIKE %s
                OR identificacion ILIKE %s
                OR COALESCE(tipo, '') ILIKE %s
                OR EXISTS (
                    SELECT 1
                    FROM unnest(operaciones) AS op
                    WHERE op ILIKE %s
                )
            )
            """
            params = [like_term, like_term, like_term, like_term]

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(query.format(where_sql=where_sql), tuple(params))
                rows = cur.fetchall()

        items = [
            {
                "id": row["id"],
                "nombre_cliente": row["nombre_cliente"],
                "identificacion": row["identificacion"],
                "telefonos": list(row["telefonos"] or []),
                "direcciones": list(row["direcciones"] or []),
                "emails": list(row["emails"] or []),
                "monto_adeudado": str(row["monto_adeudado"]),
                "tipo": row["tipo"],
                "operaciones": list(row["operaciones"] or []),
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            }
            for row in rows
        ]

        return jsonify({"items": items})

    return obligaciones_bp