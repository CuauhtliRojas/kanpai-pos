from __future__ import annotations

from app.services.print_profile import PrintProfile, get_print_profile


def test_print_profile_defaults_when_file_missing(tmp_path) -> None:
    profile = get_print_profile(tmp_path / "missing.json")

    assert profile.brand_name == "SOMOS KANPAI"
    assert "ありがとう" in profile.ticket_message
    assert profile.show_decimals is False


def test_print_profile_reads_json_file(tmp_path) -> None:
    path = tmp_path / "print_profile.json"
    path.write_text(
        """
        {
          "brand_name": "SOMOS KANPAI QA",
          "ticket_message": "Mensaje QA",
          "ascii_ticket_message": "Mensaje ASCII QA",
          "show_decimals": true
        }
        """,
        encoding="utf-8",
    )

    profile = get_print_profile(path)

    assert profile.brand_name == "SOMOS KANPAI QA"
    assert profile.ticket_message == "Mensaje QA"
    assert profile.ascii_ticket_message == "Mensaje ASCII QA"
    assert profile.show_decimals is True


def test_print_profile_model_dump() -> None:
    payload = PrintProfile().model_dump()

    assert payload["brand_name"] == "SOMOS KANPAI"
    assert "ticket_message" in payload
