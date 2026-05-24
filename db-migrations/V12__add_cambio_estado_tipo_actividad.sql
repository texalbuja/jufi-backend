-- Add new actividad tipo for estado transitions in Base Consolidada.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'cuenta_consolidada_actividad'
    ) THEN
        ALTER TABLE cuenta_consolidada_actividad
            DROP CONSTRAINT IF EXISTS chk_cuenta_consolidada_actividad_tipo;

        ALTER TABLE cuenta_consolidada_actividad
            ADD CONSTRAINT chk_cuenta_consolidada_actividad_tipo
            CHECK (
                tipo IN (
                    'Asignacion de Gestor',
                    'Agregar Adjuntos',
                    'Observaciones',
                    'Confirmacion',
                    'Cambio de Estado'
                )
            );
    END IF;
END
$$;
