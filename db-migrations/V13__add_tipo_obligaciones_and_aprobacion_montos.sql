-- Add obligation type and amount-approval workflow table.

ALTER TABLE obligaciones
ADD COLUMN IF NOT EXISTS tipo VARCHAR(120);

CREATE TABLE IF NOT EXISTS aprobacion_montos (
    id BIGSERIAL PRIMARY KEY,
    obligacion_id BIGINT NOT NULL REFERENCES obligaciones(id) ON DELETE CASCADE,
    monto_solicitado NUMERIC(12, 2) NOT NULL,
    monto_aprobado NUMERIC(12, 2),
    gestor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    aprobador_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    motivo TEXT NOT NULL,
    comentario_aprobador TEXT,
    estado VARCHAR(20) NOT NULL DEFAULT 'Solicitado',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_aprobacion_montos_estado
        CHECK (estado IN ('Aprobado', 'Solicitado', 'Rechazado')),
    CONSTRAINT chk_aprobacion_montos_monto_solicitado
        CHECK (monto_solicitado > 0),
    CONSTRAINT chk_aprobacion_montos_monto_aprobado
        CHECK (monto_aprobado IS NULL OR monto_aprobado > 0),
    CONSTRAINT chk_aprobacion_montos_estado_aprobado_requires_monto
        CHECK (estado <> 'Aprobado' OR monto_aprobado IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_aprobacion_montos_obligacion_id
    ON aprobacion_montos(obligacion_id);

CREATE INDEX IF NOT EXISTS idx_aprobacion_montos_estado
    ON aprobacion_montos(estado);

CREATE INDEX IF NOT EXISTS idx_aprobacion_montos_gestor_id
    ON aprobacion_montos(gestor_id);

CREATE INDEX IF NOT EXISTS idx_aprobacion_montos_aprobador_id
    ON aprobacion_montos(aprobador_id);

CREATE INDEX IF NOT EXISTS idx_aprobacion_montos_created_at
    ON aprobacion_montos(created_at DESC);