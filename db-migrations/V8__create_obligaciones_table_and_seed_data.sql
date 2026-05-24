CREATE TABLE IF NOT EXISTS obligaciones (
    id BIGSERIAL PRIMARY KEY,
    nombre_cliente VARCHAR(180) NOT NULL,
    identificacion CHAR(10) NOT NULL,
    telefonos TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    direcciones TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    emails TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    monto_adeudado NUMERIC(12, 2) NOT NULL,
    operaciones TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT obligaciones_identificacion_format_chk
        CHECK (identificacion ~ '^(0[1-9]|1[0-9]|2[0-4])[0-9]{8}$')
);

CREATE INDEX IF NOT EXISTS idx_obligaciones_identificacion ON obligaciones (identificacion);
CREATE INDEX IF NOT EXISTS idx_obligaciones_nombre_cliente ON obligaciones (nombre_cliente);

INSERT INTO obligaciones (
    nombre_cliente,
    identificacion,
    telefonos,
    direcciones,
    emails,
    monto_adeudado,
    operaciones
)
SELECT
    UPPER(
        first_names[(RANDOM() * (ARRAY_LENGTH(first_names, 1) - 1))::INT + 1] || ' ' ||
        first_names[(RANDOM() * (ARRAY_LENGTH(first_names, 1) - 1))::INT + 1] || ' ' ||
        last_names[(RANDOM() * (ARRAY_LENGTH(last_names, 1) - 1))::INT + 1] || ' ' ||
        last_names[(RANDOM() * (ARRAY_LENGTH(last_names, 1) - 1))::INT + 1]
    ) AS nombre_cliente,
    LPAD(((RANDOM() * 23)::INT + 1)::TEXT, 2, '0') || LPAD((RANDOM() * 99999999)::BIGINT::TEXT, 8, '0') AS identificacion,
    ARRAY[
        CASE
            WHEN RANDOM() < 0.50 THEN '09' || LPAD((RANDOM() * 99999999)::BIGINT::TEXT, 8, '0')
            ELSE landline_prefixes[(RANDOM() * (ARRAY_LENGTH(landline_prefixes, 1) - 1))::INT + 1] || LPAD((RANDOM() * 9999999)::BIGINT::TEXT, 7, '0')
        END,
        CASE
            WHEN RANDOM() < 0.50 THEN '09' || LPAD((RANDOM() * 99999999)::BIGINT::TEXT, 8, '0')
            ELSE landline_prefixes[(RANDOM() * (ARRAY_LENGTH(landline_prefixes, 1) - 1))::INT + 1] || LPAD((RANDOM() * 9999999)::BIGINT::TEXT, 7, '0')
        END
    ] AS telefonos,
    ARRAY[
        streets[(RANDOM() * (ARRAY_LENGTH(streets, 1) - 1))::INT + 1] || ' S/N Y ' ||
        streets[(RANDOM() * (ARRAY_LENGTH(streets, 1) - 1))::INT + 1] ||
        ' ED: ' || building_codes[(RANDOM() * (ARRAY_LENGTH(building_codes, 1) - 1))::INT + 1],
        neighborhoods[(RANDOM() * (ARRAY_LENGTH(neighborhoods, 1) - 1))::INT + 1] ||
        ' MZ ' || ((RANDOM() * 40)::INT + 1)::TEXT ||
        ' SOLAR ' || ((RANDOM() * 25)::INT + 1)::TEXT
    ] AS direcciones,
    ARRAY[
        LOWER(
            REPLACE(
                first_names[(RANDOM() * (ARRAY_LENGTH(first_names, 1) - 1))::INT + 1] ||
                last_names[(RANDOM() * (ARRAY_LENGTH(last_names, 1) - 1))::INT + 1] ||
                ((RANDOM() * 999)::INT)::TEXT,
                ' ',
                ''
            )
        ) || '@gmail.com',
        LOWER(
            REPLACE(
                first_names[(RANDOM() * (ARRAY_LENGTH(first_names, 1) - 1))::INT + 1] || '.' ||
                last_names[(RANDOM() * (ARRAY_LENGTH(last_names, 1) - 1))::INT + 1],
                ' ',
                ''
            )
        ) || '@outlook.com'
    ] AS emails,
    ROUND((RANDOM() * 12000 + 120)::NUMERIC, 2) AS monto_adeudado,
    ARRAY[
        LPAD((RANDOM() * 9999999999)::BIGINT::TEXT, 10, '0'),
        LPAD((RANDOM() * 9999999999)::BIGINT::TEXT, 10, '0')
    ] AS operaciones
FROM GENERATE_SERIES(1, 500) AS gs
CROSS JOIN (
    SELECT
        ARRAY[
            'CARLOS', 'MARIA', 'LUIS', 'ANA', 'JOSE', 'CARMEN', 'DANIEL', 'PAOLA', 'ANDRES', 'SOFIA',
            'MATEO', 'VALENTINA', 'JUAN', 'GABRIELA', 'MIGUEL', 'NATALIA', 'DAVID', 'ISABEL', 'JORGE', 'LUCIA',
            'ESTEBAN', 'MARIANA', 'FERNANDO', 'ALEJANDRA', 'PABLO', 'DIANA', 'RODRIGO', 'MONICA', 'ANGEL', 'JIMENA',
            'FABIAN', 'CAROLINA', 'SEBASTIAN', 'MELISSA', 'ALFONSO', 'YADIRA', 'EDUARDO', 'ROSA'
        ]::TEXT[] AS first_names,
        ARRAY[
            'PEREZ', 'GONZALEZ', 'RODRIGUEZ', 'LOPEZ', 'MARTINEZ', 'SANCHEZ', 'RAMIREZ', 'TORRES', 'FLORES', 'RIVERA',
            'CASTRO', 'MORALES', 'ORTIZ', 'HERRERA', 'MENDOZA', 'ALVAREZ', 'SALAZAR', 'VARGAS', 'ROJAS', 'ACOSTA',
            'VEGA', 'VILLARREAL', 'PALACIOS', 'SANTOS', 'BENITEZ', 'PAREDES', 'CEVALLOS', 'CHAVEZ', 'ZAMBRANO', 'NAVARRETE',
            'AGUILAR', 'CALDERON', 'MEJIA', 'PENAFIEL', 'GUERRERO', 'SUAREZ', 'ALARCON', 'GALLEGOS'
        ]::TEXT[] AS last_names,
        ARRAY['02', '04', '07', '03', '05', '06']::TEXT[] AS landline_prefixes,
        ARRAY[
            'ANTONIO CLAVIJO', 'AV 9 DE OCTUBRE', 'ELOY ALFARO', 'SIMON BOLIVAR', 'ANTONIO JOSE DE SUCRE',
            'GARCIA MORENO', 'MALDONADO', 'LOS LAURELES', 'LAS PALMAS', 'COLON', 'PICHINCHA', 'RIOBAMBA'
        ]::TEXT[] AS streets,
        ARRAY['CA', 'TORRE A', 'BLOQUE 2', 'EDIFICIO DEL SOL', 'CONDOMINIO LUNA', 'PORTAL NORTE']::TEXT[] AS building_codes,
        ARRAY['KENNEDY', 'URDESA', 'CARCELEN', 'LA FLORESTA', 'LOS CEIBOS', 'SAMBORONDON', 'LA ARMENIA']::TEXT[] AS neighborhoods
) AS seeds
ON CONFLICT DO NOTHING;