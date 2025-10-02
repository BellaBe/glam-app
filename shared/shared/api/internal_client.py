# shared/http/service_client.py
import os
import time
from collections.abc import Mapping
from typing import Any

import httpx
import jwt

# Usage example

# from shared.http.internal_api_client import InternalApiClient

# client = InternalApiClient("billing-svc")
# token = await client.fetch_service_token(
#     token_service_url=os.getenv("TOKEN_SVC_URL"),
#     correlation_id=ctx.correlation_id,
#     shop=shop,
# )


class InternalApiClientError(Exception):
    def __init__(self, status: int, msg: str, body: Any | None = None):
        super().__init__(f"{status} {msg}")
        self.status = status
        self.body = body


class InternalApiClient:
    def __init__(self, service_name: str, *, client: httpx.AsyncClient | None = None):
        self.service_name = service_name
        self.secret = os.getenv("INTERNAL_JWT_SECRET")
        if not self.secret:
            raise RuntimeError("INTERNAL_JWT_SECRET not configured")
        self.alg = os.getenv("JWT_ALGORITHM", "HS256")
        self.client = client or httpx.AsyncClient(timeout=5.0)

    def _make_jwt(self, ttl: int = 60) -> str:
        now = int(time.time())
        payload = {"sub": self.service_name, "iat": now, "exp": now + ttl}
        return jwt.encode(payload, self.secret, algorithm=self.alg)

    async def request(
        self,
        *,
        method: str,
        url: str,
        correlation_id: str,
        json: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        ttl: int = 60,
    ) -> Any:
        if not correlation_id:
            raise ValueError("correlation_id is required")

        token = self._make_jwt(ttl)
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Correlation-ID": correlation_id,
        }
        if json is not None:
            headers["Content-Type"] = "application/json"

        try:
            r = await self.client.request(method.upper(), url, headers=headers, json=json, params=params)
        except httpx.HTTPError as e:
            raise InternalApiClientError(599, f"upstream error: {e}") from e

        if 200 <= r.status_code < 300:
            try:
                return r.json()
            except ValueError:
                return r.text

        # non-2xx
        try:
            body = r.json()
            msg = body.get("detail") or body.get("message") or str(body)
        except ValueError:
            body, msg = r.text, (r.text or f"HTTP {r.status_code}")
        raise InternalApiClientError(r.status_code, msg, body=body)

    async def fetch_service_token(self, *, token_service_url: str, correlation_id: str, shop: str) -> str:
        """Call the token service to fetch an access token for a shop."""
        url = f"{token_service_url.rstrip('/')}/api/v1/internal/token"
        data = await self.request(
            method="GET",
            url=url,
            correlation_id=correlation_id,
            params={"shop": shop},
        )
        if "token" not in data:
            raise InternalApiClientError(500, "No token field in response", body=data)
        return data["token"]
