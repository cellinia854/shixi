from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Settings:
    api_key: str = ""
    api_base: str = "https://ark.cn-beijing.volces.com/api/v3"
    model: str = "doubao-seedance-2-0-260128"
    poll_interval_seconds: int = 5
    timeout_seconds: int = 600

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            api_key=os.getenv("SEEDANCE_API_KEY", ""),
            api_base=os.getenv(
                "SEEDANCE_API_BASE",
                "https://ark.cn-beijing.volces.com/api/v3",
            ).rstrip("/"),
            model=os.getenv("SEEDANCE_MODEL", "doubao-seedance-2-0-260128"),
            poll_interval_seconds=int(os.getenv("SEEDANCE_POLL_INTERVAL_SECONDS", "5")),
            timeout_seconds=int(os.getenv("SEEDANCE_TIMEOUT_SECONDS", "600")),
        )