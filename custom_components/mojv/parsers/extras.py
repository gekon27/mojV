"""Safe parsers for additional read-only school modules."""
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from ..models import (
    AttendanceExcuse,
    AttendanceExcuses,
    CompletedLesson,
    FreeDay,
    HomeroomTeacher,
    ImportantToday,
    LuckyNumber,
    SchoolInfo,
    Teacher,
)
from .common import parse_date, text


def _rows(payload: Any, *keys: str) -> list[dict[str, Any]]:
    current = payload
    for _ in range(3):
        if isinstance(current, list):
            return [row for row in current if isinstance(row, dict)]
        if not isinstance(current, dict):
            return []
        for key in keys:
            value = current.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        nested = current.get("data") if isinstance(current.get("data"), (dict, list)) else current.get("result")
        if nested is current or not isinstance(nested, (dict, list)):
            break
        current = nested
    return []


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return text(value).lower() in {"1", "true", "yes", "tak"}


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _public_id(value: Any, fallback: str) -> str:
    raw = text(value) or fallback
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def parse_lucky_number(payload: Any, now: datetime) -> LuckyNumber | None:
    """Parse the real daily lucky number without exposing its portal ID."""
    current = payload
    for _ in range(3):
        if not isinstance(current, dict):
            return None
        if current.get("numer") is not None:
            value = text(current.get("numer"))
            return LuckyNumber(date=now, value=value) if value else None
        nested = current.get("data") if isinstance(current.get("data"), dict) else current.get("result")
        if not isinstance(nested, dict):
            return None
        current = nested
    return None


def parse_free_days(payload: Any) -> tuple[FreeDay, ...]:
    """Parse named school-free date ranges."""
    result: list[FreeDay] = []
    for row in _rows(payload, "dniWolne"):
        start = parse_date(row.get("dataOd") or row.get("od"))
        end = parse_date(row.get("dataDo") or row.get("do"))
        name = text(row.get("nazwa") or row.get("opis"))
        if start is None or end is None or not name:
            continue
        result.append(FreeDay(start=start, end=end, name=name))
    return tuple(sorted(result, key=lambda item: item.start))


def parse_teachers(payload: Any) -> tuple[Teacher, ...]:
    """Whitelist teacher display fields and discard mailbox routing metadata."""
    result: list[Teacher] = []
    for row in _rows(payload, "nauczyciele"):
        name = text(row.get("imieNazwisko"))
        if not name:
            name = " ".join(part for part in (text(row.get("imie")), text(row.get("nazwisko"))) if part)
        if not name:
            continue
        result.append(
            Teacher(
                name=name,
                subject=text(row.get("przedmiot") or row.get("nazwaPrzedmiotu")),
                homeroom=_bool(row.get("wychowawca")),
            )
        )
    return tuple(result)


def parse_homeroom_teachers(payload: Any) -> tuple[HomeroomTeacher, ...]:
    """Parse homeroom teachers without global mailbox keys."""
    result: list[HomeroomTeacher] = []
    for row in _rows(payload, "wychowawcy"):
        name = text(row.get("imieNazwisko") or row.get("nazwa"))
        if not name:
            continue
        result.append(HomeroomTeacher(name=name, primary=_bool(row.get("isGlowny"))))
    return tuple(result)


def _director_name(value: Any) -> str:
    if isinstance(value, str):
        return text(value)
    if not isinstance(value, dict):
        return ""
    direct = text(value.get("imieNazwisko") or value.get("nazwa"))
    if direct:
        return direct
    return " ".join(
        part for part in (text(value.get("imie")), text(value.get("nazwisko"))) if part
    )


def parse_school_info(payload: Any) -> SchoolInfo | None:
    """Parse public school information while deliberately excluding phone/PII fields."""
    current = payload
    for _ in range(3):
        if not isinstance(current, dict):
            return None
        if current.get("nazwa") is not None:
            break
        nested = current.get("data") if isinstance(current.get("data"), dict) else current.get("result")
        if not isinstance(nested, dict):
            return None
        current = nested

    name = text(current.get("nazwa"))
    if not name:
        return None
    city = text(current.get("miejscowosc"))
    street = text(current.get("ulica"))
    house = text(current.get("nrDomu"))
    apartment = text(current.get("nrMieszkania"))
    postal = text(current.get("kodPocztowy"))
    number = house + (f"/{apartment}" if apartment else "")
    street_line = " ".join(part for part in (street, number) if part)
    locality = " ".join(part for part in (postal, city) if part)
    address = ", ".join(part for part in (street_line, locality) if part)
    directors_raw = current.get("dyrektorzy")
    directors = tuple(
        name_value
        for name_value in (
            _director_name(value) for value in directors_raw if isinstance(directors_raw, list)
        )
        if name_value
    ) if isinstance(directors_raw, list) else ()
    return SchoolInfo(
        name=name,
        city=city,
        address=address,
        website=text(current.get("stronaWwwUrl") or current.get("www")),
        email=text(current.get("mail") or current.get("email")),
        directors=directors,
    )


def parse_important_today(payload: Any) -> tuple[ImportantToday, ...]:
    """Parse portal-provided important-today labels and safe detail text."""
    result: list[ImportantToday] = []
    for row in _rows(payload, "wazneDzisiaj"):
        title = text(row.get("nazwa") or row.get("tytul"))
        if not title:
            continue
        result.append(
            ImportantToday(
                subject=text(row.get("przedmiot")),
                kind=text(row.get("nazwaZdarzenia") or row.get("rodzaj")),
                title=title,
                description=text(
                    row.get("opis")
                    or row.get("tresc")
                    or row.get("szczegoly")
                    or row.get("podtytul")
                ),
            )
        )
    return tuple(result)


def parse_completed_lessons(payload: Any) -> tuple[CompletedLesson, ...]:
    """Parse lesson topics and replace portal IDs with stable public hashes."""
    result: list[CompletedLesson] = []
    for index, row in enumerate(_rows(payload, "realizacjaZajec")):
        date = parse_date(row.get("data") or row.get("dataCzas"))
        subject = text(row.get("przedmiot"))
        if date is None or not subject:
            continue
        fallback = f"{date.isoformat()}|{subject}|{row.get('nrLekcji')}|{index}"
        result.append(
            CompletedLesson(
                lesson_id=_public_id(row.get("id"), fallback),
                date=date,
                subject=subject,
                teacher=text(row.get("nauczyciel")),
                topic=text(row.get("tematOpis") or row.get("temat")),
                lesson_number=_int(row.get("nrLekcji") or row.get("numerLekcji")),
                online_url=text(row.get("online")),
            )
        )
    return tuple(sorted(result, key=lambda item: item.date, reverse=True))


def parse_excuses(payload: Any) -> AttendanceExcuses:
    """Parse attendance excuse capability and status without retaining raw IDs."""
    current = payload
    for _ in range(3):
        if not isinstance(current, dict):
            return AttendanceExcuses()
        if "usprawiedliwieniaAktywne" in current or "usprawiedliwienia" in current:
            break
        nested = current.get("data") if isinstance(current.get("data"), dict) else current.get("result")
        if not isinstance(nested, dict):
            return AttendanceExcuses()
        current = nested

    entries: list[AttendanceExcuse] = []
    raw_entries = current.get("usprawiedliwienia")
    if isinstance(raw_entries, list):
        for row in raw_entries:
            if not isinstance(row, dict):
                continue
            date = parse_date(row.get("dzien") or row.get("data"))
            if date is None:
                continue
            raw_number = row.get("numerLekcji")
            lesson_number = None if raw_number in (None, "") else _int(raw_number)
            entries.append(
                AttendanceExcuse(
                    date=date,
                    lesson_number=lesson_number,
                    status=_int(row.get("status")),
                )
            )
    blocked_value = current.get("usprawiedliwieniaBlokada")
    blocked = blocked_value not in (None, "", False, 0, [], {})
    return AttendanceExcuses(
        active=_bool(current.get("usprawiedliwieniaAktywne")),
        entries=tuple(sorted(entries, key=lambda item: item.date, reverse=True)),
        blocked=blocked,
    )
