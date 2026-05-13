"""Serve centralised tooltip content for the GUI."""
import os
from typing import Any

import yaml
from fastapi import APIRouter

router = APIRouter()

_TOOLTIPS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tooltips.yml')
_cache: dict[str, Any] | None = None


def _load_tooltips() -> dict[str, Any]:
    global _cache
    if _cache is None:
        with open(_TOOLTIPS_FILE, 'r') as f:
            _cache = yaml.safe_load(f) or {}
    return _cache


@router.get("/")
async def get_tooltips() -> dict[str, Any]:
    return _load_tooltips()
