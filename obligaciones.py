from typing import Callable

from flask import Blueprint, jsonify
from psycopg2.extras import DictCursor


def create_obligaciones_blueprint(
    get_db_connection: Callable,
    token_required: Callable,
) -> Blueprint:
    obligaciones_bp = Blueprint("obligaciones", __name__)

    @obligaciones_bp.route("/obligaciones/", methods=["GET"])
    @token_required()
    def list_obligaciones():
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
            ORDER BY id DESC;
        """

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(query)
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