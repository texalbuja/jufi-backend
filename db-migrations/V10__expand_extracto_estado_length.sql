-- Increase extracto_bancario.estado length to support 'Parcialmente Consolidado'.

ALTER TABLE extracto_bancario
ALTER COLUMN estado TYPE VARCHAR(30);
