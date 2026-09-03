from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "custom_components" / "mojv" / "client.py"


def test_client_uses_unified_snapshot_builder_for_extended_live_data() -> None:
    source = CLIENT.read_text(encoding="utf-8")

    assert "from .snapshot_builder import build_student_snapshot" in source
    assert "classification_periods=row.get(\"classification_periods\")" in source
    assert "grades_by_period=row.get(\"grades_by_period\")" in source
    assert "schoolwork=row.get(\"schoolwork\")" in source
    assert "classification_periods=bundle.classification_periods" in source
    assert "grades_by_period=bundle.grades_by_period" in source
    assert "schoolwork=bundle.schoolwork" in source
    assert "return build_student_snapshot(" in source
