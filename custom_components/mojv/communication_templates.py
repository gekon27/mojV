"""Local reusable drafts for school communication in the mojV panel."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any
from uuid import uuid4

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

DATA_COMMUNICATION_TEMPLATES = f"{DOMAIN}_communication_templates"
STORE_VERSION = 1
_KINDS = ("excuse", "reply")


def _text(value: Any, field: str, *, required: bool = False, limit: int = 2000) -> str:
    result = str(value or "").strip()
    if required and not result:
        raise vol.Invalid(f"{field} is required")
    if len(result) > limit:
        raise vol.Invalid(f"{field} is too long")
    return result


def normalize_template(value: Mapping[str, Any], *, template_id: str | None = None) -> dict[str, str]:
    """Validate a local draft; it never accepts portal routing metadata."""
    kind = _text(value.get("kind"), "kind", required=True, limit=20)
    if kind not in _KINDS:
        raise vol.Invalid("kind must be excuse or reply")
    return {
        "id": template_id or uuid4().hex,
        "student_id": _text(value.get("student_id"), "student_id", limit=160),
        "kind": kind,
        "name": _text(value.get("name"), "name", required=True, limit=80),
        "body": _text(value.get("body"), "body", required=True),
    }


class CommunicationTemplateStore:
    """Persist user-owned template text locally in Home Assistant storage."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict[str, list[dict[str, str]]]] = Store(
            hass, STORE_VERSION, DATA_COMMUNICATION_TEMPLATES
        )
        self._templates: list[dict[str, str]] = []

    async def async_load(self) -> None:
        payload = await self._store.async_load() or {}
        rows = payload.get("templates", []) if isinstance(payload, dict) else []
        self._templates = []
        for item in rows:
            if not isinstance(item, Mapping):
                continue
            try:
                self._templates.append(
                    normalize_template(item, template_id=str(item.get("id") or ""))
                )
            except vol.Invalid:
                continue

    def rows_for(self, student_id: str) -> list[dict[str, str]]:
        return deepcopy([
            item
            for item in self._templates
            if not item["student_id"] or item["student_id"] == student_id
        ])

    async def async_add(self, value: Mapping[str, Any]) -> dict[str, str]:
        template = normalize_template(value)
        self._templates.append(template)
        await self._store.async_save({"templates": self._templates})
        return deepcopy(template)

    async def async_remove(self, template_id: str) -> None:
        template_id = _text(template_id, "id", required=True, limit=64)
        prior = len(self._templates)
        self._templates = [item for item in self._templates if item["id"] != template_id]
        if len(self._templates) == prior:
            raise vol.Invalid("template not found")
        await self._store.async_save({"templates": self._templates})
