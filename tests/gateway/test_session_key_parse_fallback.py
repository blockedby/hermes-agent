"""Regression tests for lossless session-key fallback parsing.

The primary gateway path should prefer persisted ``SessionEntry.origin``.
These tests cover the legacy/fallback path that only has a string session key.
Telegram Business routing encodes colon-delimited data in ``thread_id`` and
must survive that fallback intact.
"""

from gateway.config import Platform
from gateway.run import GatewayRunner, _parse_session_key


def test_parse_session_key_preserves_business_thread_id_without_topic():
    parsed = _parse_session_key(
        "agent:main:telegram:dm:12345:business:bc-42"
    )

    assert parsed == {
        "platform": "telegram",
        "chat_type": "dm",
        "chat_id": "12345",
        "thread_id": "business:bc-42",
    }


def test_parse_session_key_preserves_business_thread_id_with_topic():
    parsed = _parse_session_key(
        "agent:main:telegram:dm:12345:business:bc-42:topic:338575"
    )

    assert parsed == {
        "platform": "telegram",
        "chat_type": "dm",
        "chat_id": "12345",
        "thread_id": "business:bc-42:topic:338575",
    }


def test_process_event_source_fallback_preserves_business_thread_id_with_topic():
    """Synthetic process/watch events must not degrade Business routing.

    This path is used when the gateway has only ``session_key`` metadata and no
    persisted/cached ``SessionSource``. It should still reconstruct the full
    Business lane discriminator instead of truncating it to ``business``.
    """
    runner = object.__new__(GatewayRunner)
    session_key = "agent:main:telegram:dm:12345:business:bc-42:topic:338575"

    source = runner._build_process_event_source({"session_key": session_key})

    assert source is not None
    assert source.platform == Platform.TELEGRAM
    assert source.chat_type == "dm"
    assert source.chat_id == "12345"
    assert source.thread_id == "business:bc-42:topic:338575"
