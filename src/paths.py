from __future__ import annotations

import sys
from pathlib import Path


def resource_path(*parts: str) -> Path:
    base_path = getattr(sys, "_MEIPASS", None)
    if isinstance(base_path, str):
        return Path(base_path, *parts)
    return Path(__file__).resolve().parent.parent.joinpath(*parts)


def source_resource_path(*parts: str) -> Path:
    return resource_path("src", *parts)
