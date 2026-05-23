-- Authentication and authorization schema
-- Adds role support and password hashes for JWT login flow.

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Seed common roles.
INSERT INTO roles (name, description)
VALUES
    ('admin', 'Rol de administrador con permisos elevados'),
    ('gestor', 'Rol para realizar operaciones diarias'),
    ('supervisor', 'Rol para supervisión y revisión'),
    ('aprobador', 'Rol para la aprobación de acciones importantes'),
    ('gestor_cuenta_bancaria', 'Rol para gestionar la carga y conciliación de movimientos bancarios')
ON CONFLICT (name) DO NOTHING;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS password_hash TEXT,
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- Normalize e-mail length and enforce case-insensitive uniqueness.
ALTER TABLE users
    ALTER COLUMN email TYPE VARCHAR(255);

CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email_lower
    ON users (LOWER(email));

CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX IF NOT EXISTS ix_user_roles_role_id ON user_roles(role_id);
