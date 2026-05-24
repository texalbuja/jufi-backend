ALTER TABLE movimientos_bancarios
ADD COLUMN IF NOT EXISTS fila_excel INTEGER,
ADD COLUMN IF NOT EXISTS estado_validacion VARCHAR(20),
ADD COLUMN IF NOT EXISTS error_validacion TEXT;
