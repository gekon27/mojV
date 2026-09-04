from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "mojv"
PANEL = COMPONENT / "panel.py"
HUB = COMPONENT / "frontend" / "school-panel-hub.js"


def test_panel_serializes_all_expanded_safe_school_modules() -> None:
    source = PANEL.read_text(encoding="utf-8")
    for marker in (
        '"lucky_number"',
        '"free_days"',
        '"excuses"',
        '"teachers"',
        '"school_info"',
        '"important_today"',
        '"homeroom_teachers"',
        '"completed_lessons"',
    ):
        assert marker in source, marker


def test_school_hub_exposes_information_and_completed_topics_views() -> None:
    source = HUB.read_text(encoding="utf-8")
    for marker in (
        '["info", "Informacje"',
        '["topics", "Tematy"',
        'case "info"',
        'case "topics"',
        "_renderSchoolInfo",
        "_renderCompletedTopics",
    ):
        assert marker in source, marker


def test_dashboard_surfaces_lucky_number_important_today_and_next_free_day() -> None:
    source = HUB.read_text(encoding="utf-8")
    for marker in ("lucky_number", "important_today", "next_free_day"):
        assert marker in source, marker


def test_panel_surface_stays_free_of_sensitive_student_profile_and_routing_fields() -> None:
    combined = PANEL.read_text(encoding="utf-8").lower() + "\n" + HUB.read_text(encoding="utf-8").lower()
    for forbidden in (
        "pesel",
        "adreszamieszkania",
        "adreszameldowania",
        "imieojca",
        "imiematki",
        "globalkeyskrzynka",
        "apiglobalkey",
    ):
        assert forbidden not in combined
