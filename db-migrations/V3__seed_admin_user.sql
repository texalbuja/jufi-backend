-- Seed a bootstrap admin user for local environments.
-- Initial credentials:
--   email: admin@jufi.local
--   password: Admin123ChangeMe
-- Change this password after first login.

WITH upsert_admin AS (
    INSERT INTO users (name, email, password_hash, is_active)
    VALUES (
        'Administrador',
        'admin@jufi.local',
        'scrypt:32768:8:1$yifLfayDmCjYdbwo$364ab47cc9828e487c15c5c91a8bfa5ce3eff00cf547dd1d4092d2173423954afea2147a2df9ff5e44c61318c70afcb1d6a4324cd6631aaf8c1627bb7e1cb39f',
        TRUE
    )
    ON CONFLICT (email)
    DO UPDATE SET
        name = EXCLUDED.name,
        password_hash = EXCLUDED.password_hash,
        is_active = TRUE,
        updated_at = CURRENT_TIMESTAMP
    RETURNING id
),
admin_user AS (
    SELECT id FROM upsert_admin
),
admin_role AS (
    SELECT id FROM roles WHERE name = 'admin'
)
INSERT INTO user_roles (user_id, role_id)
SELECT au.id, ar.id
FROM admin_user au
CROSS JOIN admin_role ar
ON CONFLICT (user_id, role_id) DO NOTHING;
