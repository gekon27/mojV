"""Parser for tests, quizzes, class tests and homework."""
from __future__ import annotations

from datetime import datetime
from html.parser import HTMLParser
from typing import Any

from ..models import SchoolWork

_KIND_MAP = {
    1: ("test", "Sprawdzian"),
    2: ("quiz", "Kartkówka"),
    3: ("class_test", "Klasówka"),
    4: ("homework", "Zadanie domowe"),
}


class _TextExtractor(HTMLParser):
    """Small dependency-free HTML-to-text converter for portal descriptions."""

    _BREAK_TAGS = {"br", "p", "div", "li", "tr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[no-untyped-def]
        del attrs
        if tag in {"script", "style"}:
            self._ignored_depth += 1
        elif not self._ignored_depth and tag in self._BREAK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1
        elif not self._ignored_depth and tag in self._BREAK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)


def _plain_text(value: Any) -> str:
    raw = str(value or "")
    if not raw:
        return ""
    parser = _TextExtractor()
    try:
        parser.feed(raw)
        parser.close()
    except (ValueError, TypeError):
        return raw.strip()
    lines = [" ".join(line.split()) for line in "".join(parser.parts).splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _parse_date(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        pass
    for fmt in (
        "%d.%m.%Y",
        "%d.%m.%Y %H:%M",
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _rows(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("data", "result", "items"):
        candidate = payload.get(key)
        if isinstance(candidate, list):
            return candidate
    return []


def parse_schoolwork(
    payload: Any,
    details_by_id: dict[str, Any] | None = None,
) -> tuple[SchoolWork, ...]:
    """Convert schoolwork list/detail responses into mojV models."""
    details = details_by_id if isinstance(details_by_id, dict) else {}
    result: list[SchoolWork] = []

    for item in _rows(payload):
        if not isinstance(item, dict):
            continue
        work_id = str(item.get("id") or "").strip()
        if not work_id:
            continue
        detail = details.get(work_id)
        if not isinstance(detail, dict):
            detail = {}

        type_raw = detail.get("typ", item.get("typ"))
        try:
            type_id = int(type_raw)
        except (TypeError, ValueError):
            type_id = 0
        kind, fallback_title = _KIND_MAP.get(type_id, ("other", "Inne"))

        explicit_due_raw = detail.get("terminOdpowiedzi") or item.get("terminOdpowiedzi")
        due_at = _parse_date(
            explicit_due_raw
            or detail.get("data")
            or item.get("data")
        )
        if due_at is None:
            continue

        # Plus homework details expose ``data`` separately from
        # ``terminOdpowiedzi``. Treat that detail-level value as the entry
        # timestamp only when an explicit homework deadline exists. For tests
        # and quizzes ``data`` is the event date, so we do not invent a
        # creation timestamp.
        created_at = None
        if type_id == 4 and explicit_due_raw:
            created_at = _parse_date(detail.get("data"))

        subject = str(
            detail.get("przedmiotNazwa") or item.get("przedmiotNazwa") or ""
        ).strip()
        teacher = str(
            detail.get("nauczycielImieNazwisko")
            or item.get("nauczycielImieNazwisko")
            or ""
        ).strip()
        title = str(
            detail.get("temat")
            or item.get("temat")
            or detail.get("nazwa")
            or item.get("nazwa")
            or fallback_title
        ).strip()
        description = _plain_text(
            detail.get("opis")
            or item.get("opis")
            or detail.get("tresc")
            or item.get("tresc")
            or ""
        )

        result.append(
            SchoolWork(
                work_id=work_id,
                date=due_at,
                subject=subject,
                title=title or fallback_title,
                kind=kind,
                description=description,
                teacher=teacher,
                created_at=created_at,
                due_at=due_at,
            )
        )

    return tuple(sorted(result, key=lambda row: row.date))
