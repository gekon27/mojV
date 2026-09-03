"""Small shared parsing helpers for live school payloads."""
from __future__ import annotations

from datetime import datetime
from html.parser import HTMLParser
from typing import Any


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[no-untyped-def]
        if tag in {"br", "p", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def text(value: Any) -> str:
    return str(value or "").strip()


def parse_date(value: Any) -> datetime | None:
    raw = text(value)
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


def strip_html(value: Any) -> str:
    raw = text(value)
    if not raw:
        return ""
    parser = _TextExtractor()
    try:
        parser.feed(raw)
    except Exception:
        return raw
    lines = [" ".join(line.split()) for line in "".join(parser.parts).splitlines()]
    return "\n".join(line for line in lines if line).strip()
