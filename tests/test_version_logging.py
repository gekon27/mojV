from pathlib import Path


def test_integration_startup_logs_manifest_version() -> None:
    source = Path("custom_components/mojv/__init__.py").read_text(encoding="utf-8")
    assert 'mojV integration version=%s' in source
    assert 'manifest.json' in source


def test_helper_startup_logs_runtime_version() -> None:
    source = Path("mojv_auth_helper/rootfs/app/server.py").read_text(encoding="utf-8")
    assert 'mojV Auth Helper version=%s' in source
    assert '_VERSION' in source
