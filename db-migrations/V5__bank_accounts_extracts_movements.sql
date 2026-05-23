-- Banking accounts, extract uploads, and extracted movements schema.

CREATE TABLE IF NOT EXISTS cuentas (
    id SERIAL PRIMARY KEY,
    nombre_cuenta VARCHAR(150) NOT NULL,
    numero_cuenta VARCHAR(50) NOT NULL UNIQUE,
    entidad_bancaria VARCHAR(120) NOT NULL,
    estado VARCHAR(10) NOT NULL DEFAULT 'Activo',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_cuentas_estado CHECK (estado IN ('Activo', 'Inactivo'))
);

INSERT INTO cuentas (nombre_cuenta, numero_cuenta, entidad_bancaria, estado)
VALUES ('Automotriz', '2208512334', 'Banco Pichincha', 'Activo')
ON CONFLICT (numero_cuenta) DO NOTHING;

CREATE TABLE IF NOT EXISTS extracto_bancario (
    id SERIAL PRIMARY KEY,
    cuenta_id INTEGER NOT NULL REFERENCES cuentas(id) ON DELETE CASCADE,
    nombre_del_archivo TEXT NOT NULL,
    archivo BYTEA NOT NULL,
    fecha VARCHAR(16) NOT NULL,
    tipo VARCHAR(10) NOT NULL DEFAULT 'XLSX',
    fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(20) NOT NULL DEFAULT 'Cargado',
    CONSTRAINT chk_extracto_tipo CHECK (tipo IN ('XLSX')),
    CONSTRAINT chk_extracto_estado CHECK (estado IN ('Cargado', 'Validado', 'Consolidado', 'Identificado'))
);

CREATE INDEX IF NOT EXISTS ix_extracto_bancario_cuenta_id
    ON extracto_bancario(cuenta_id);

CREATE TABLE IF NOT EXISTS movimientos_bancarios (
    id SERIAL PRIMARY KEY,
    extracto_bancario_id INTEGER NOT NULL REFERENCES extracto_bancario(id) ON DELETE CASCADE,
    fecha VARCHAR(16) NOT NULL,
    oficina TEXT,
    numero_de_documento TEXT,
    descripcion TEXT,
    debito NUMERIC(14, 2),
    credito NUMERIC(14, 2),
    saldo NUMERIC(14, 2)
);

CREATE INDEX IF NOT EXISTS ix_movimientos_bancarios_extracto_id
    ON movimientos_bancarios(extracto_bancario_id);
