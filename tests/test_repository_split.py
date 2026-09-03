from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_hacs_repository_no_longer_embeds_home_assistant_app() -> None:
    assert not (ROOT / "repository.yaml").exists()
    assert not (ROOT / "mojv_auth_helper").exists()
    assert not (ROOT / ".github" / "workflows" / "publish-helper.yml").exists()


def test_hacs_repository_points_to_standalone_helper_repository() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "https://github.com/gekon27/mojv-auth-helper" in readme
    assert "mojV Auth Helper 0.1.7" in readme


def test_split_release_version_is_0_8_1() -> None:
    manifest = json.loads(
        (ROOT / "custom_components" / "mojv" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["version"] == "0.8.1"

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "HACS 0.8.1" in readme
    assert "## [0.8.1]" in changelog
