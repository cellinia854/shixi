from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import requests

from src.config import Settings


class SeedanceError(RuntimeError):
    pass


@dataclass
class SeedanceTask:
    task_id: str
    raw: dict[str, Any]


@dataclass
class SeedanceStatus:
    task_id: str
    status: str
    result_urls: list[str]
    raw: dict[str, Any]


class SeedanceClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def create_video_task(self, input_payload: dict[str, Any]) -> SeedanceTask:
        if not self.settings.api_key:
            raise SeedanceError("Missing SEEDANCE_API_KEY.")

        url = f"{self.settings.api_base}/v1/videos/generations"
        payload = {
            "model": self.settings.model,
            "input": input_payload,
        }
        data = self._request("POST", url, json=payload)
        task_id = data.get("taskId") or data.get("id")
        if not task_id:
            raise SeedanceError(f"Seedance response did not include a task id: {data}")
        return SeedanceTask(task_id=task_id, raw=data)

    def get_task(self, task_id: str) -> SeedanceStatus:
        if not self.settings.api_key:
            raise SeedanceError("Missing SEEDANCE_API_KEY.")

        url = f"{self.settings.api_base}/v1/tasks/{task_id}"
        data = self._request("GET", url)
        result_urls = _extract_result_urls(data)
        return SeedanceStatus(
            task_id=task_id,
            status=str(data.get("status", "unknown")),
            result_urls=result_urls,
            raw=data,
        )

    def wait_for_task(self, task_id: str) -> SeedanceStatus:
        deadline = time.time() + self.settings.timeout_seconds
        while time.time() < deadline:
            status = self.get_task(task_id)
            if status.status in {"completed", "failed", "cancelled"}:
                return status
            time.sleep(self.settings.poll_interval_seconds)
        raise SeedanceError(f"Timed out waiting for Seedance task {task_id}.")

    def _request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        headers = kwargs.pop("headers", {})
        headers.update(
            {
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            }
        )
        try:
            response = requests.request(method, url, headers=headers, timeout=60, **kwargs)
        except requests.RequestException as exc:
            raise SeedanceError(f"Seedance request failed: {exc}") from exc

        if response.status_code >= 400:
            raise SeedanceError(f"Seedance API error {response.status_code}: {response.text}")

        try:
            return response.json()
        except ValueError as exc:
            raise SeedanceError(f"Seedance API returned non-JSON response: {response.text}") from exc


def _extract_result_urls(data: dict[str, Any]) -> list[str]:
    nested = data.get("data") if isinstance(data.get("data"), dict) else {}
    results = nested.get("results") or data.get("results") or []
    return [str(item) for item in results if item]
