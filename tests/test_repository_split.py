from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_hacs_repository_no_longer_embeds_home_assistant_app() -> None:
    assert not (ROOT / "repository.yaml").exists()
    assert not (ROOT / "mojv_auth_helper").exists()
    assert not (ROOT / ".github" / "workflows" / "publish-helper.yml").exists()


def test_hacs_keeps_runtime_gateway_and_secret_protocol() -> None:
    component = ROOT / "custom_components" / "mojv"
    assert (component / "helper_gateway.py").is_file()
    assert (component / "helper_protocol.py").is_file()


def test_hacs_repository_points_to_standalone_helper_repository() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "https://github.com/gekon27/mojv-auth-helper" in readme
    assert "mojV Auth Helper 0.1.8" in readme


def test_release_metadata_tracks_manifest_without_freezing_patch_version() -> None:
    manifest = json.loads(
        (ROOT / "custom_components" / "mojv" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    version = manifest["version"]

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"HACS {version}" in readme
    assert f"## [{version}]" in changelog
