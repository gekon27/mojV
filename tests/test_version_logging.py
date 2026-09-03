from pathlib import Path


def test_integration_startup_logs_manifest_version() -> None:
    source = Path("custom_components/mojv/__init__.py").read_text(encoding="utf-8")
    assert 'mojV integration version=%s' in source
    assert 'manifest.json' in source


def test_helper_startup_logs_runtime_version() -> None:
    source = Path(
        "mojv_auth_helper/rootfs/etc/services.d/mojv-auth/run"
    ).read_text(encoding="utf-8")
    assert "mojV Auth Helper version=" in source
    assert "MOJV_HELPER_VERSION" in source
