# Bruno collection - JWT auth flow

Collection path: `jufi-backend/bruno`

## Recommended execution order
1. `01 Health`
2. `02 Register User`
3. `03 Login User JWT`
4. Copy `access_token` from login response into the active environment var `token`
5. `04 Auth Me`
6. `05 Admin Ping (Expected 403 with user token)`

## Admin validation (optional)
- Obtain an admin JWT and paste it into env var `adminToken`.
- Run `06 Admin Ping (with admin token)` and expect `200`.
- Run `08 Get Users (admin token)` and expect `200` with users list.
- Set env var `userIdToDeactivate` and run `09 Deactivate User (admin token)`.

## Negative validation (non-admin)
- Obtain a non-admin JWT and paste it into env var `token`.
- Run `10 Deactivate User (expected 403 with user token)` and expect `403`.

## Environments included
- `localhost.bru`
- `docker.bru`

## Notes for deactivation endpoint
- `DELETE /users/<id>` performs logical deletion (`estado = Inactivo`).
- You cannot deactivate your own user.
- You cannot deactivate bootstrap admin (`admin@jufi.local`).
