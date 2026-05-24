-- Base consolidada schema for bank movement consolidation workflow.

ALTER TABLE movimientos_bancarios
ADD COLUMN IF NOT EXISTS error_carga TEXT;

ALTER TABLE extracto_bancario
DROP CONSTRAINT IF EXISTS chk_extracto_estado;

ALTER TABLE extracto_bancario
ADD CONSTRAINT chk_extracto_estado
CHECK (estado IN ('Cargado', 'Validado', 'Parcialmente Consolidado', 'Consolidado', 'Identificado'));

CREATE TABLE IF NOT EXISTS cuenta_consolidada (
    id SERIAL PRIMARY KEY,
    cuenta_id INTEGER NOT NULL REFERENCES cuentas(id) ON DELETE CASCADE,
    extracto_bancario_id INTEGER NOT NULL REFERENCES extracto_bancario(id) ON DELETE CASCADE,
    movimiento_bancario_id INTEGER NOT NULL REFERENCES movimientos_bancarios(id) ON DELETE CASCADE,
    fecha_movimiento VARCHAR(10) NOT NULL,
    numero_de_documento TEXT NOT NULL,
    descripcion TEXT,
    monto_pago NUMERIC(14, 2) NOT NULL,
    saldo NUMERIC(14, 2),
    cliente_id INTEGER,
    obligacion_id INTEGER,
    gestor_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    observaciones TEXT,
    estado VARCHAR(20) NOT NULL DEFAULT 'Pendiente',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_cuenta_consolidada_monto_pago CHECK (monto_pago > 0),
    CONSTRAINT chk_cuenta_consolidada_estado CHECK (estado IN ('Pendiente', 'En Progreso', 'Concluido')),
    CONSTRAINT uq_cuenta_consolidada_idempotencia UNIQUE (cuenta_id, numero_de_documento, fecha_movimiento)
);

CREATE INDEX IF NOT EXISTS ix_cuenta_consolidada_extracto_id
    ON cuenta_consolidada(extracto_bancario_id);

CREATE INDEX IF NOT EXISTS ix_cuenta_consolidada_estado
    ON cuenta_consolidada(estado);

CREATE INDEX IF NOT EXISTS ix_cuenta_consolidada_gestor_user_id
    ON cuenta_consolidada(gestor_user_id);

CREATE INDEX IF NOT EXISTS ix_cuenta_consolidada_cliente_id
    ON cuenta_consolidada(cliente_id);

CREATE INDEX IF NOT EXISTS ix_cuenta_consolidada_obligacion_id
    ON cuenta_consolidada(obligacion_id);

CREATE TABLE IF NOT EXISTS cuenta_consolidada_adjuntos (
    id SERIAL PRIMARY KEY,
    cuenta_consolidada_id INTEGER NOT NULL REFERENCES cuenta_consolidada(id) ON DELETE CASCADE,
    nombre_archivo TEXT NOT NULL,
    mime_type VARCHAR(120) NOT NULL,
    archivo BYTEA NOT NULL,
    uploaded_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_cuenta_consolidada_adjuntos_consolidada_id
    ON cuenta_consolidada_adjuntos(cuenta_consolidada_id);

CREATE TABLE IF NOT EXISTS cuenta_consolidada_actividad (
    id SERIAL PRIMARY KEY,
    cuenta_consolidada_id INTEGER NOT NULL REFERENCES cuenta_consolidada(id) ON DELETE CASCADE,
    tipo VARCHAR(40) NOT NULL,
    fecha TIMESTAMP NOT NULL,
    comentario TEXT NOT NULL DEFAULT '',
    usuario_id INTEGER NOT NULL REFERENCES users(id),
    CONSTRAINT chk_cuenta_consolidada_actividad_tipo
        CHECK (tipo IN ('Asignacion de Gestor', 'Agregar Adjuntos', 'Observaciones', 'Confirmacion'))
);

CREATE INDEX IF NOT EXISTS ix_cuenta_consolidada_actividad_consolidada_id
    ON cuenta_consolidada_actividad(cuenta_consolidada_id);
