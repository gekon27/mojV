from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "custom_components" / "mojv" / "client.py"
PANEL = ROOT / "custom_components" / "mojv" / "panel.py"


def test_mailbox_routing_key_stays_inside_live_transport() -> None:
    source = CLIENT.read_text(encoding="utf-8")
    panel = PANEL.read_text(encoding="utf-8")
    assert "globalKeySkrzynka" in source
    assert "mailbox_key" in source
    assert "globalKeySkrzynka" not in panel
    assert '"mailbox_key"' not in panel
