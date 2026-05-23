# JF Portal Backend

A Flask REST API for the JF Portal.

This backend now includes:
- JWT authentication flow
- role-based authorization
- password hashing using Werkzeug (`generate_password_hash` / `check_password_hash`)
- PostgreSQL integration

## Setup

1. Install uv if not already installed:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Configure environment variables (example):
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/jf_portal"
   export JWT_SECRET_KEY="replace-with-a-strong-secret"
   export JWT_EXP_MINUTES="60"
   export CORS_ALLOWED_ORIGINS="http://localhost:5003,http://127.0.0.1:5003"
   ```

   Generate a strong JWT secret key (recommended, macOS):
   ```bash
   openssl rand -base64 48
   ```

   Alternative using Python:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

   Then export it:
   ```bash
   export JWT_SECRET_KEY="paste-generated-value"
   ```

   Notes:
   - Use a different key per environment.
   - Do not commit secrets to git.
   - Rotating this key invalidates existing JWTs.

4. Run the application:
   ```bash
   uv run python main.py
   ```

The API will be available at http://localhost:8080

## Database Migrations (Flyway, local without Docker)

If you are running PostgreSQL locally and not using Docker, you can run Flyway directly from your machine.

1. Install Flyway (macOS):
   ```bash
   brew install flyway
   flyway -v
   ```

2. From the repository root (one level above this folder), run migrations:
   ```bash
   cd /Users/texalbuja/Jufi

   flyway \
     -url=jdbc:postgresql://localhost:5432/jufi \
     -user=postgres \
     -password=password \
     -locations=filesystem:db-migrations \
     migrate
   ```

3. Check migration status:
   ```bash
   flyway \
     -url=jdbc:postgresql://localhost:5432/jufi \
     -user=postgres \
     -password=password \
     -locations=filesystem:db-migrations \
     info
   ```

Optional commands:
```bash
flyway -url=jdbc:postgresql://localhost:5432/jufi -user=postgres -password=password -locations=filesystem:db-migrations validate
flyway -url=jdbc:postgresql://localhost:5432/jufi -user=postgres -password=password -locations=filesystem:db-migrations repair
```

Optional config file (to avoid repeating flags):

Create a `flyway.conf` at repository root (`/Users/texalbuja/Jufi`) with:

```properties
flyway.url=jdbc:postgresql://localhost:5432/jufi
flyway.user=postgres
flyway.password=password
flyway.locations=filesystem:db-migrations
```

Then run:
```bash
flyway migrate
flyway info
```

## API Endpoints

- GET /hello: Returns a hello message in JSON format.
- POST /auth/register: Creates a user with hashed password and one or more roles.
- POST /auth/login: Validates credentials and returns a JWT token.
- GET /auth/me: Returns authenticated user claims from JWT.
- POST /auth/logout: Authenticated logout acknowledgement (JWT remains stateless).
- GET /admin/ping: Protected endpoint, requires `admin` role.

## Technical Documentation

- Admin auth and user registration flow: [ADMIN_AUTH_FLOW.md](ADMIN_AUTH_FLOW.md)