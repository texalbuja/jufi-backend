import json
import os
import time
import unittest
from urllib import error, request


class AdminUserFlowIntegrationTest(unittest.TestCase):
    BASE_URL = os.getenv("INTEGRATION_BASE_URL", "http://127.0.0.1:8080")
    ADMIN_EMAIL = os.getenv("INTEGRATION_ADMIN_EMAIL", "admin@jufi.local")
    ADMIN_PASSWORD = os.getenv("INTEGRATION_ADMIN_PASSWORD", "Admin123ChangeMe")

    def _api_call(self, method: str, path: str, token: str | None = None, payload: dict | None = None):
        url = f"{self.BASE_URL}{path}"
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")

        req = request.Request(url=url, data=body, headers=headers, method=method)

        try:
            with request.urlopen(req, timeout=15) as response:
                raw = response.read().decode("utf-8")
                parsed = json.loads(raw) if raw else {}
                return response.status, parsed
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            return exc.code, parsed

    def test_admin_user_management_end_to_end_flow(self):
        # 1) Login with bootstrap admin
        status, body = self._api_call(
            "POST",
            "/auth/login",
            payload={"email": self.ADMIN_EMAIL, "password": self.ADMIN_PASSWORD},
        )
        self.assertEqual(status, 200, body)
        admin_token = body.get("access_token")
        self.assertTrue(admin_token, body)
        admin_id = body.get("user", {}).get("id")
        self.assertIsNotNone(admin_id, body)

        # 2) Admin can list users
        status, body = self._api_call("GET", "/users", token=admin_token)
        self.assertEqual(status, 200, body)
        self.assertIn("items", body)
        self.assertIsInstance(body["items"], list)

        # 3) Admin registers a non-admin test user
        test_email = f"integration.gestor.{int(time.time())}@jufi.local"
        test_password = "QaPass123"

        status, body = self._api_call(
            "POST",
            "/auth/register",
            token=admin_token,
            payload={
                "name": "Integration Gestor",
                "email": test_email,
                "password": test_password,
                "roles": ["gestor"],
            },
        )
        self.assertEqual(status, 201, body)
        test_user_id = body.get("id")
        self.assertIsNotNone(test_user_id, body)

        # 4) New non-admin can login
        status, body = self._api_call(
            "POST",
            "/auth/login",
            payload={"email": test_email, "password": test_password},
        )
        self.assertEqual(status, 200, body)
        non_admin_token = body.get("access_token")
        self.assertTrue(non_admin_token, body)

        # 5) Non-admin cannot deactivate users
        status, body = self._api_call(
            "DELETE",
            f"/users/{test_user_id}",
            token=non_admin_token,
        )
        self.assertEqual(status, 403, body)

        # 6) Admin can deactivate user
        status, body = self._api_call(
            "DELETE",
            f"/users/{test_user_id}",
            token=admin_token,
        )
        self.assertEqual(status, 200, body)
        self.assertEqual(body.get("id"), test_user_id)

        # 7) Deactivating again is idempotent
        status, body = self._api_call(
            "DELETE",
            f"/users/{test_user_id}",
            token=admin_token,
        )
        self.assertEqual(status, 200, body)
        self.assertEqual(body.get("message"), "User already inactive")

        # 8) Inactive user can no longer login
        status, body = self._api_call(
            "POST",
            "/auth/login",
            payload={"email": test_email, "password": test_password},
        )
        self.assertEqual(status, 401, body)

        # 9) Missing user returns 404
        status, body = self._api_call(
            "DELETE",
            "/users/999999",
            token=admin_token,
        )
        self.assertEqual(status, 404, body)

        # 10) Admin cannot deactivate itself
        status, body = self._api_call(
            "DELETE",
            f"/users/{admin_id}",
            token=admin_token,
        )
        self.assertEqual(status, 403, body)


if __name__ == "__main__":
    unittest.main()
