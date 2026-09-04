from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LESSON_STATES_JS = ROOT / "custom_components" / "mojv" / "frontend" / "school-panel-lesson-states.js"
HUB_JS = ROOT / "custom_components" / "mojv" / "frontend" / "school-panel-hub.js"


def test_lesson_state_module_has_all_temporal_states_and_labels() -> None:
    assert LESSON_STATES_JS.exists(), "lesson state frontend module is not implemented yet"
    source = LESSON_STATES_JS.read_text(encoding="utf-8")
    assert "_mojvLessonState" in source
    for token in ("cancelled", "current", "completed", "upcoming"):
        assert f'"{token}"' in source
    assert "Teraz" in source
    assert "Odbyta" in source
    assert "Odwołana" in source


def test_lesson_state_styles_are_explicit_and_not_color_only() -> None:
    assert LESSON_STATES_JS.exists(), "lesson state frontend module is not implemented yet"
    source = LESSON_STATES_JS.read_text(encoding="utf-8")
    for selector in (
        ".lesson-state-current",
        ".lesson-state-completed",
        ".lesson-state-upcoming",
        ".lesson-state-cancelled",
    ):
        assert selector in source
    assert "lesson-state-label" in source


def test_replacement_badge_remains_additive_to_temporal_state() -> None:
    assert LESSON_STATES_JS.exists(), "lesson state frontend module is not implemented yet"
    source = LESSON_STATES_JS.read_text(encoding="utf-8")
    assert "lesson.replacement" in source
    assert "Zastępstwo" in source
    assert "lesson-state-${state}" in source


def test_hub_imports_lesson_state_patch() -> None:
    hub = HUB_JS.read_text(encoding="utf-8")
    assert 'import "./school-panel-lesson-states.js"' in hub
