import base64
import binascii
from typing import Callable

from flask import Blueprint, jsonify, request
from psycopg2.extras import DictCursor

MAX_ARCHIVO_BYTES = 2 * 1024 * 1024
ALLOWED_EXTRACTO_ESTADOS = {"Cargado", "Validado", "Consolidado", "Identificado"}


def _decode_archivo_blob(raw_value: object):
    if not isinstance(raw_value, str) or not raw_value.strip():
        return None, "archivo is required and must be a base64 string"

    try:
        decoded = base64.b64decode(raw_value, validate=True)
    except (binascii.Error, ValueError):
        return None, "archivo must be valid base64"

    if len(decoded) > MAX_ARCHIVO_BYTES:
        return None, "archivo exceeds 2MB limit"

    return decoded, None


def create_bank_accounts_blueprint(
    get_db_connection: Callable,
    token_required: Callable,
) -> Blueprint:
    bank_accounts_bp = Blueprint("bank_accounts", __name__)

    @bank_accounts_bp.route("/cuentas", methods=["GET"])
    @token_required()
    def list_cuentas():
        query = """
            SELECT id, nombre_cuenta, numero_cuenta, entidad_bancaria, estado
            FROM cuentas
            ORDER BY id ASC;
        """

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(query)
                rows = cur.fetchall()

        return jsonify(
            {
                "items": [
                    {
                        "id": row["id"],
                        "nombre_cuenta": row["nombre_cuenta"],
                        "numero_cuenta": row["numero_cuenta"],
                        "entidad_bancaria": row["entidad_bancaria"],
                        "estado": row["estado"],
                    }
                    for row in rows
                ]
            }
        )

    @bank_accounts_bp.route("/cuentas/<int:cuenta_id>/", methods=["GET"])
    @token_required()
    def get_cuenta_with_extractos(cuenta_id: int):
        cuenta_query = """
            SELECT id, nombre_cuenta, numero_cuenta, entidad_bancaria, estado
            FROM cuentas
            WHERE id = %s;
        """

        extractos_query = """
            SELECT id, nombre_del_archivo, fecha, tipo, fecha_carga, estado
            FROM extracto_bancario
            WHERE cuenta_id = %s
            ORDER BY fecha_carga DESC, id DESC;
        """

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(cuenta_query, (cuenta_id,))
                cuenta = cur.fetchone()
                if cuenta is None:
                    return jsonify({"error": "Cuenta not found"}), 404

                cur.execute(extractos_query, (cuenta_id,))
                extractos = cur.fetchall()

        return jsonify(
            {
                "cuenta": {
                    "id": cuenta["id"],
                    "nombre_cuenta": cuenta["nombre_cuenta"],
                    "numero_cuenta": cuenta["numero_cuenta"],
                    "entidad_bancaria": cuenta["entidad_bancaria"],
                    "estado": cuenta["estado"],
                },
                "extractos_bancarios": [
                    {
                        "id": row["id"],
                        "nombre_del_archivo": row["nombre_del_archivo"],
                        "fecha": row["fecha"],
                        "tipo": row["tipo"],
                        "fecha_carga": row["fecha_carga"].isoformat() if row["fecha_carga"] else None,
                        "estado": row["estado"],
                    }
                    for row in extractos
                ],
            }
        )

    @bank_accounts_bp.route("/cuentas/<int:cuenta_id>/extracto-bancario", methods=["POST"])
    @token_required()
    def create_extracto_bancario(cuenta_id: int):
        payload = request.get_json(silent=True) or {}
        nombre_del_archivo = (payload.get("nombre_del_archivo") or "").strip()
        fecha = (payload.get("fecha") or "").strip()
        tipo = (payload.get("tipo") or "XLSX").strip().upper()
        estado = (payload.get("estado") or "Cargado").strip()

        if not nombre_del_archivo:
            return jsonify({"error": "nombre_del_archivo is required"}), 400
        if not fecha:
            return jsonify({"error": "fecha is required"}), 400
        if len(fecha) > 16:
            return jsonify({"error": "fecha must have at most 16 characters"}), 400
        if tipo != "XLSX":
            return jsonify({"error": "tipo must be XLSX"}), 400
        if estado not in ALLOWED_EXTRACTO_ESTADOS:
            return jsonify({"error": "estado is invalid"}), 400

        archivo, decode_error = _decode_archivo_blob(payload.get("archivo"))
        if decode_error:
            return jsonify({"error": decode_error}), 400

        cuenta_exists_query = "SELECT id FROM cuentas WHERE id = %s;"
        insert_extracto_query = """
            INSERT INTO extracto_bancario (
                cuenta_id,
                nombre_del_archivo,
                archivo,
                fecha,
                tipo,
                estado
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, fecha_carga;
        """

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(cuenta_exists_query, (cuenta_id,))
                cuenta = cur.fetchone()
                if cuenta is None:
                    return jsonify({"error": "Cuenta not found"}), 404

                cur.execute(
                    insert_extracto_query,
                    (cuenta_id, nombre_del_archivo, archivo, fecha, tipo, estado),
                )
                created = cur.fetchone()
                conn.commit()

        return (
            jsonify(
                {
                    "id": created["id"],
                    "cuenta_id": cuenta_id,
                    "nombre_del_archivo": nombre_del_archivo,
                    "fecha": fecha,
                    "tipo": tipo,
                    "estado": estado,
                    "fecha_carga": created["fecha_carga"].isoformat() if created["fecha_carga"] else None,
                }
            ),
            201,
        )

    @bank_accounts_bp.route("/cuentas/<int:cuenta_id>/extracto-bancario/<int:extracto_id>", methods=["GET"])
    @token_required()
    def get_movimientos_bancarios(cuenta_id: int, extracto_id: int):
        extracto_query = """
            SELECT id, cuenta_id, nombre_del_archivo, fecha, tipo, fecha_carga, estado
            FROM extracto_bancario
            WHERE id = %s AND cuenta_id = %s;
        """

        movimientos_query = """
            SELECT
                id,
                extracto_bancario_id,
                fecha,
                oficina,
                numero_de_documento,
                descripcion,
                debito,
                credito,
                saldo
            FROM movimientos_bancarios
            WHERE extracto_bancario_id = %s
            ORDER BY id ASC;
        """

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(extracto_query, (extracto_id, cuenta_id))
                extracto = cur.fetchone()
                if extracto is None:
                    return jsonify({"error": "Extracto bancario not found"}), 404

                cur.execute(movimientos_query, (extracto_id,))
                movimientos = cur.fetchall()

        return jsonify(
            {
                "cuenta_id": cuenta_id,
                "extracto_bancario": {
                    "id": extracto["id"],
                    "nombre_del_archivo": extracto["nombre_del_archivo"],
                    "fecha": extracto["fecha"],
                    "tipo": extracto["tipo"],
                    "fecha_carga": extracto["fecha_carga"].isoformat() if extracto["fecha_carga"] else None,
                    "estado": extracto["estado"],
                },
                "movimientos": [
                    {
                        "id": row["id"],
                        "extracto_bancario_id": row["extracto_bancario_id"],
                        "fecha": row["fecha"],
                        "oficina": row["oficina"],
                        "numero_de_documento": row["numero_de_documento"],
                        "descripcion": row["descripcion"],
                        "debito": float(row["debito"]) if row["debito"] is not None else None,
                        "credito": float(row["credito"]) if row["credito"] is not None else None,
                        "saldo": float(row["saldo"]) if row["saldo"] is not None else None,
                    }
                    for row in movimientos
                ],
            }
        )

    return bank_accounts_bp
