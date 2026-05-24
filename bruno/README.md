# Bruno collection - Auth, Users y Cuentas

Collection path: `jufi-backend/bruno`

## Recommended execution order
1. `01 Auth - Health`
2. `07 Auth - Login Admin JWT`
3. Copiar `access_token` al environment activo en la variable `adminToken`
4. `02 Auth - Registrar Usuario`
5. `08 Users - Listar Usuarios (admin)`
6. `09 Users - Desactivar Usuario (admin)`
7. `11 Cuentas - Listar Cuentas`
8. `12 Cuentas - Obtener Cuenta y Extractos`
9. `13 Cuentas - Cargar Extracto Bancario`
10. `14 Cuentas - Obtener Movimientos por Extracto`
11. Obtener/pegar token de usuario con rol `gestor_cuenta_bancaria` en `gestorCuentaToken`
12. `15 Cuentas - Cargar a Base Consolidada`
13. `16 Base Consolidada - Listar`
14. `17 Base Consolidada - Actualizar Registro`
15. `18 Base Consolidada - Agregar Adjunto`
16. `19 Base Consolidada - Listar Adjuntos`
17. `20 Base Consolidada - Registrar Actividad`
18. `21 Base Consolidada - Listar Actividad`

## Auth
- `02 Auth - Registrar Usuario`
- `03 Auth - Login Usuario JWT`
- `04 Auth - Me`
- `05 Auth - Admin Ping (403 token usuario)`
- `06 Auth - Admin Ping (token admin)`
- `07 Auth - Login Admin JWT`

## Users
- `08 Users - Listar Usuarios (admin)`
- `09 Users - Desactivar Usuario (admin)`
- `10 Users - Desactivar Usuario (403 token usuario)`

## Cuentas
- `11 Cuentas - Listar Cuentas`
- `12 Cuentas - Obtener Cuenta y Extractos`
- `13 Cuentas - Cargar Extracto Bancario`
- `14 Cuentas - Obtener Movimientos por Extracto`

## Base Consolidada
- `15 Cuentas - Cargar a Base Consolidada`
- `16 Base Consolidada - Listar`
- `17 Base Consolidada - Actualizar Registro`
- `18 Base Consolidada - Agregar Adjunto`
- `19 Base Consolidada - Listar Adjuntos`
- `20 Base Consolidada - Registrar Actividad`
- `21 Base Consolidada - Listar Actividad`

## Negative validation (non-admin)
- Obtener un JWT de usuario no admin y pegarlo en `token`.
- Ejecutar `10 Users - Desactivar Usuario (403 token usuario)` y esperar `403`.

## Environments included
- `localhost.bru`
- `docker.bru`

Variables nuevas para Base Consolidada:
- `gestorCuentaToken` (JWT con rol `gestor_cuenta_bancaria`)
- `consolidadaId` (id de registro en `cuenta_consolidada`)
- `actividadUsuarioId` (id de usuario para actividad)

## Notes for deactivation endpoint
- `DELETE /users/<id>` performs logical deletion (`estado = Inactivo`).
- You cannot deactivate your own user.
- You cannot deactivate bootstrap admin (`admin@jufi.local`).

## Notes for bank extracts endpoint
- `POST /cuentas/<id>/extracto-bancario` recibe `archivo` como base64 en JSON.
- Tamano maximo esperado para `archivo`: 2MB.
