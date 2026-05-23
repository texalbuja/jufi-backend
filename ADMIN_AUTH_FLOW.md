# Flujo tecnico de administracion y registro de usuarios

Este documento describe como funciona la autenticacion/autorizacion con JWT y el flujo para registrar usuarios desde una cuenta administradora.

## 1) Resumen funcional

- El backend usa Flask + PostgreSQL.
- Los usuarios se autentican con email y password.
- Al autenticarse, el backend emite un JWT con claims de identidad y roles.
- La creacion de usuarios en `POST /auth/register` esta restringida a usuarios con rol `admin`.

## 2) Modelo de roles

Roles actualmente sembrados en BD:

- admin
- gestor
- supervisor
- aprobador
- gestor_cuenta_bancaria

Tablas principales:

- `users`
- `roles`
- `user_roles`

Migraciones relevantes:

- `db-migrations/V1__create_initial_schema.sql`
- `db-migrations/V2__auth_roles_jwt_schema.sql`
- `db-migrations/V3__seed_admin_user.sql`

## 3) Usuario admin bootstrap

La migracion V3 crea (si no existe) un admin inicial:

- email: admin@jufi.local
- password inicial: Admin123ChangeMe
- rol asignado: admin

Recomendacion: cambiar la password inmediatamente despues del primer acceso.

## 4) Flujo JWT

### 4.1 Login

Endpoint:

- `POST /auth/login`

Entrada:

- `email`
- `password`

Salida:

- `access_token`
- `token_type`
- `expires_in_minutes`
- `user` (incluye roles)

### 4.2 Validacion de token

Los endpoints protegidos esperan:

- Header `Authorization: Bearer <token>`

Si falta, esta vencido o es invalido, retorna `401`.
Si el rol no alcanza para el endpoint, retorna `403`.

### 4.3 Claims del token

Claims emitidos:

- `sub` (id de usuario en formato string)
- `email`
- `roles`
- `iat`
- `exp`

Nota tecnica: `sub` se emite como string para cumplir el estandar JWT y evitar errores de validacion.

## 5) Restriccion de registro de usuarios

Endpoint:

- `POST /auth/register`

Regla actual:

- Requiere JWT valido de un usuario con rol `admin`.

Comportamiento:

- Si no hay token: `401 Missing Bearer token`
- Si token invalido: `401 Invalid token`
- Si rol insuficiente: `403 Insufficient role permissions`

Validaciones del payload:

- `name`, `email`, `password` obligatorios
- `password` minimo 8 caracteres
- `roles` debe ser lista de strings
- No permite asignar `admin` desde este endpoint publico

## 6) Ejemplo end-to-end con curl

1. Obtener token admin:

```bash
curl -X POST http://127.0.0.1:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@jufi.local",
    "password": "Admin123ChangeMe"
  }'
```

2. Registrar usuario con token admin:

```bash
curl -X POST http://127.0.0.1:8080/auth/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN_ADMIN>" \
  -d '{
    "name": "Operador Demo",
    "email": "operador.demo@jufi.local",
    "password": "DemoPass123",
    "roles": ["gestor"]
  }'
```

3. Verificar token actual:

```bash
curl http://127.0.0.1:8080/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## 7) Flujo recomendado en Bruno

Coleccion:

- `jufi-backend/bruno`

Requests utiles:

1. `07 Login Admin JWT`
2. Copiar `access_token` a variable `adminToken` en environment activo
3. Ejecutar request de registro (si aplica) usando token admin
4. `06 Admin Ping (with admin token)` para validar permisos admin
5. `04 Auth Me` para inspeccionar claims del token

## 8) Troubleshooting rapido

### Error: Invalid token

Revisar:

- Que el token sea reciente (no expirado).
- Que el token no tenga espacios/saltos de linea al copiar.
- Que el backend activo use el mismo `JWT_SECRET_KEY` con el que se emitio el token.
- Que se este enviando exactamente `Authorization: Bearer <token>`.

### Error: Insufficient role permissions

- El usuario autenticado no tiene rol `admin` para endpoints administrativos.

### Error: Email already exists

- El email ya esta registrado en `users`.

## 9) Seguridad minima recomendada

- Definir `JWT_SECRET_KEY` fuerte y distinto por ambiente.
- No commitear secretos al repositorio.
- Rotar password bootstrap del admin tras el primer uso.
- Reducir vida util de tokens si el riesgo del entorno lo requiere.
