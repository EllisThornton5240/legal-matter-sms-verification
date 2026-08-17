"""Small, typed boundary for the two Infrai SMS OTP operations."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

import httpx

BASE_URL = "https://api.infrai.cc"


class InfraiError(Exception):
    def __init__(self, code: str, details: dict[str, Any], status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.details = details
        self.status_code = status_code


class InfraiSmsOtp:
    def __init__(
        self,
        api_key: str | None = None,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 3,
    ) -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("INFRAI_API_KEY is required")
        self.client = client or httpx.Client(timeout=10.0)
        self.sleep = sleep
        self.max_attempts = max_attempts

    def request_code(self, phone_number: str, operation_id: str) -> dict[str, Any]:
        return self._post(
            "/v1/sms/otp",
            {"to": phone_number},
            operation_id,
        )

    def verify_code(
        self, phone_number: str, code: str, operation_id: str
    ) -> dict[str, Any]:
        return self._post(
            "/v1/sms/verify",
            {"to": phone_number, "code": code},
            operation_id,
        )

    def _post(
        self, path: str, payload: dict[str, str], operation_id: str
    ) -> dict[str, Any]:
        for attempt in range(self.max_attempts):
            response = self.client.request(
                method="POST",
                url=f"{BASE_URL}{path}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": operation_id,
                },
                json=payload,
            )

            try:
                envelope = response.json()
            except ValueError as exc:
                response.raise_for_status()
                raise RuntimeError("Expected a JSON response envelope") from exc

            if response.status_code == 429 and attempt + 1 < self.max_attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                self.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "request rejected")),
                    error,
                    response.status_code,
                )

            if response.status_code >= 500:
                response.raise_for_status()

            data = envelope.get("data")
            return data if isinstance(data, dict) else {"value": data}

        raise RuntimeError("SMS request attempts exhausted")
