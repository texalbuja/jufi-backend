from typing import Callable

from flask import Blueprint, g, jsonify
from psycopg2.extras import DictCursor


def _table_exists(cur, table_name: str) -> bool:
    cur.execute("SELECT to_regclass(%s) IS NOT NULL AS exists", (f"public.{table_name}",))
    row = cur.fetchone()
    return bool(row and row["exists"])


def create_dashboard_blueprint(
    get_db_connection: Callable,
    token_required: Callable,
) -> Blueprint:
    dashboard_bp = Blueprint("dashboard", __name__)

    @dashboard_bp.route("/dashboard", methods=["GET"])
    @token_required(required_roles={"admin", "gestor", "aprobador", "gestor_cuenta_bancaria"})
    def get_dashboard_metrics():
        roles = {str(role).lower() for role in (g.user.get("roles") or [])}
        user_id = int(g.user["id"])

        is_admin = "admin" in roles
        has_gestor = "gestor" in roles
        has_aprobador = "aprobador" in roles
        has_gestor_cuenta = "gestor_cuenta_bancaria" in roles

        primary_role = "general"
        if is_admin:
            primary_role = "admin"
        elif has_gestor_cuenta:
            primary_role = "gestor_cuenta_bancaria"
        elif has_aprobador:
            primary_role = "aprobador"
        elif has_gestor:
            primary_role = "gestor"

        metrics = {
            "depositos_sin_identificar": None,
            "aprobaciones_montos_pendientes": None,
            "fecha_ultimo_extracto_subido": None,
        }

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                if (is_admin or has_gestor or has_gestor_cuenta) and _table_exists(cur, "cuenta_consolidada"):
                    cur.execute(
                        """
                        SELECT COUNT(*) AS total
                        FROM cuenta_consolidada cc
                        WHERE cc.obligacion_id IS NULL
                            AND cc.gestor_user_id IS NULL;
                        """
                    )
                    row = cur.fetchone()
                    metrics["depositos_sin_identificar"] = row["total"] if row and row["total"] is not None else None

                if (is_admin or has_aprobador or has_gestor) and _table_exists(cur, "aprobacion_montos"):
                    if is_admin or has_aprobador:
                        cur.execute(
                            """
                            SELECT COUNT(*) AS total
                            FROM aprobacion_montos am
                            WHERE am.estado = 'Solicitado';
                            """
                        )
                    else:
                        cur.execute(
                            """
                            SELECT COUNT(*) AS total
                            FROM aprobacion_montos am
                            WHERE am.estado = 'Solicitado'
                              AND am.gestor_id = %s;
                            """,
                            (user_id,),
                        )
                    metrics["aprobaciones_montos_pendientes"] = int(
                        (cur.fetchone() or {}).get("total", 0)
                    )

                if (is_admin or has_gestor_cuenta) and _table_exists(cur, "extracto_bancario"):
                    cur.execute(
                        """
                        SELECT MAX(eb.fecha_carga) AS fecha_ultimo_extracto_subido
                        FROM extracto_bancario eb;
                        """
                    )
                    last_extract = (cur.fetchone() or {}).get("fecha_ultimo_extracto_subido")
                    metrics["fecha_ultimo_extracto_subido"] = (
                        last_extract.isoformat() if last_extract else None
                    )

        return jsonify(
            {
                "roles": sorted(roles),
                "primary_role": primary_role,
                "metrics": metrics,
            }
        )

    return dashboard_bp
