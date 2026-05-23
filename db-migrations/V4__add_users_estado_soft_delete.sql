-- Add logical deletion status column for users management.
-- Estado values are limited to Activo/Inactivo.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS estado VARCHAR(10);

-- Backfill estado from existing is_active flag.
UPDATE users
SET estado = CASE
    WHEN COALESCE(is_active, TRUE) THEN 'Activo'
    ELSE 'Inactivo'
END
WHERE estado IS NULL;

ALTER TABLE users
    ALTER COLUMN estado SET DEFAULT 'Activo';

ALTER TABLE users
    ALTER COLUMN estado SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_users_estado'
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT chk_users_estado
            CHECK (estado IN ('Activo', 'Inactivo'));
    END IF;
END $$;
