from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"


def test_validate_workflow_checks_all_executable_school_frontend_modules() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    required = (
        "school-panel.js",
        "school-panel-live.js",
        "school-panel-hub-base.js",
        "school-panel-details.js",
        "school-panel-lesson-states.js",
        "school-panel-hub.js",
        "school-dashboard.js",
    )
    for filename in required:
        assert f"node --check custom_components/mojv/frontend/{filename}" in source
