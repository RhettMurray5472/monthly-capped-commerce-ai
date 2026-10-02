from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail.get('message', 'request rejected')}"


class InfraiControl:
    def __init__(self, api_key: str, base_url: str, max_attempts: int = 3) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )
        self._max_attempts = max_attempts

    def set_monthly_budget(
        self, hard_cap_usd: float, alert_threshold_usd: float | None = None
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "hard_cap_usd": hard_cap_usd,
            "period": "monthly",
        }
        if alert_threshold_usd is not None:
            payload["alert_threshold_usd"] = alert_threshold_usd
        return self._request("PUT", "account/budget/set", payload)

    def _request(
        self, method: str, path: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        for attempt in range(self._max_attempts):
            response = self._client.request(method=method, url=path, json=payload)
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if response.status_code == 429 and attempt + 1 < self._max_attempts:
                delay = float(response.headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            if response.status_code >= 500:
                response.raise_for_status()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            return envelope.get("data") or {}
        raise RuntimeError("request attempts exhausted")
