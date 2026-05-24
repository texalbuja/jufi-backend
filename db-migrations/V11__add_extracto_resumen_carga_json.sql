-- Store Base Consolidada load summary per extract in JSON format.

ALTER TABLE extracto_bancario
ADD COLUMN IF NOT EXISTS resumen_carga JSONB;
