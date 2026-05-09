"""Regression coverage for Telegram session-key isolation.

Telegram ordinary DMs, supergroup/forum threads, and Business customer chats
can reuse overlapping numeric chat IDs.  The session key must include the
chat type, chat ID, and thread discriminator so those lanes cannot collide.
"""

from gateway.config import Platform
from gateway.session import SessionSource, build_session_key


def test_telegram_dm_group_thread_and_business_keys_are_isolated():
    dm = SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="123",
        chat_type="dm",
    )
    group_thread = SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="-1001234567890",
        chat_type="group",
        thread_id="42",
    )
    business = SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="123",
        chat_type="dm",
        thread_id="business:connection_id",
    )

    dm_key = build_session_key(dm)
    group_thread_key = build_session_key(group_thread)
    business_key = build_session_key(business)

    assert dm_key == "agent:main:telegram:dm:123"
    assert group_thread_key == "agent:main:telegram:group:-1001234567890:42"
    assert business_key == "agent:main:telegram:dm:123:business:connection_id"

    assert len({dm_key, group_thread_key, business_key}) == 3
    assert dm_key != business_key
