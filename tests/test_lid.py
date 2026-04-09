"""Tests for LID resolution."""

from __future__ import annotations

from wacli_api.lid import normalize_jid, _lid_map


class TestNormalizeJid:
    def setup_method(self) -> None:
        _lid_map.clear()
        _lid_map["195769072144617"] = "33650633719"

    def teardown_method(self) -> None:
        _lid_map.clear()

    def test_passthrough_phone_jid(self) -> None:
        assert normalize_jid("33650633719@s.whatsapp.net") == "33650633719@s.whatsapp.net"

    def test_passthrough_group_jid(self) -> None:
        assert normalize_jid("123456-789@g.us") == "123456-789@g.us"

    def test_resolves_lid(self) -> None:
        assert normalize_jid("195769072144617@lid") == "33650633719@s.whatsapp.net"

    def test_strips_device_suffix(self) -> None:
        assert normalize_jid("195769072144617:23@lid") == "33650633719@s.whatsapp.net"

    def test_unknown_lid_passthrough(self) -> None:
        assert normalize_jid("999999999@lid") == "999999999@lid"
