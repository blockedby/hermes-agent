"""Tests for DB-backed Telegram Business dialog profiles."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from gateway.platforms.telegram_business_chats import TelegramBusinessChatRegistry
from gateway.platforms.telegram_business_profiles import (
    MAX_ASSISTANT_DISPLAY_NAME_LENGTH,
    MAX_ASSISTANT_PREFIX_LENGTH,
    MAX_DIALOG_NOTES_LENGTH,
    MAX_DIALOG_PROMPT_LENGTH,
    TelegramBusinessDialogProfileStore,
    normalize_invocation_policy,
)


def _entry(*, connection: str = "bc-1", chat_id: str = "123", topic_id: str | None = "777") -> dict[str, object]:
    dialog_key = TelegramBusinessChatRegistry.key(connection, chat_id, topic_id)
    return {
        "business_connection_id": connection,
        "customer_chat_id": chat_id,
        "direct_messages_topic_id": topic_id,
        "token": TelegramBusinessChatRegistry.token_for_key(dialog_key),
    }


def test_profile_store_upserts_default_profile_in_memory_db(monkeypatch: pytest.MonkeyPatch):
    def fail_if_default_home_is_used():  # pragma: no cover - only runs on regression
        raise AssertionError("tests must not write Telegram Business profiles under ~/.hermes")

    monkeypatch.setattr(
        "gateway.platforms.telegram_business_profiles.get_hermes_home",
        fail_if_default_home_is_used,
    )
    store = TelegramBusinessDialogProfileStore(db_path=":memory:")

    table = store._conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'telegram_business_dialog_profiles'"
    ).fetchone()
    profile = store.upsert_for_chat_entry(_entry(topic_id=None))

    assert table is not None
    assert profile["dialog_key"] == "bc-1|123|"
    assert profile["token"] == TelegramBusinessChatRegistry.token_for_key("bc-1|123|")
    assert profile["business_connection_id"] == "bc-1"
    assert profile["customer_chat_id"] == "123"
    assert profile["direct_messages_topic_id"] is None
    assert profile["assistant_display_name"] == "Hermes"
    assert profile["assistant_prefix"] == "🤖 Hermes:"
    assert profile["dialog_prompt"] == ""
    assert profile["dialog_notes"] == ""
    assert profile["invocation_policy"] == "off"
    assert store.get_by_key("bc-1|123|") == profile


def test_profile_store_updates_prompt_prefix_and_invocation_policy():
    store = TelegramBusinessDialogProfileStore(db_path=":memory:")
    profile = store.upsert_for_chat_entry(_entry())

    updated = store.update_by_token(
        profile["token"],
        {
            "assistant_display_name": "Concierge",
            "assistant_prefix": "🤖 Консьерж:",
            "dialog_prompt": "Use the customer order history.",
            "dialog_notes": "VIP customer; keep replies short.",
            "invocation_policy": "mention_direct",
        },
        actor_user_id=4242,
    )

    assert updated is not None
    assert updated["assistant_display_name"] == "Concierge"
    assert updated["assistant_prefix"] == "🤖 Консьерж:"
    assert updated["dialog_prompt"] == "Use the customer order history."
    assert updated["dialog_notes"] == "VIP customer; keep replies short."
    assert updated["invocation_policy"] == "mention_direct"
    assert updated["updated_by_user_id"] == "4242"
    assert store.get_by_key(profile["dialog_key"]) == updated


def test_profile_store_get_by_token_returns_same_profile():
    connection = sqlite3.connect(":memory:")
    store = TelegramBusinessDialogProfileStore(connection=connection)
    profile = store.upsert_for_chat_entry(_entry(connection="bc-2", chat_id="456", topic_id="999"))

    by_token = store.get_by_token(profile["token"])

    assert by_token == profile


def test_profile_store_rejects_unknown_invocation_policy_before_persistence():
    store = TelegramBusinessDialogProfileStore(db_path=":memory:")
    profile = store.upsert_for_chat_entry(_entry())

    assert normalize_invocation_policy("notify") is None
    assert store.normalize_invocation_policy("MENTION_DIRECT") == "mention_direct"
    with pytest.raises(ValueError, match="invocation_policy"):
        store.update_by_token(profile["token"], {"invocation_policy": "notify"})

    assert store.get_by_token(profile["token"])["invocation_policy"] == "off"


@pytest.mark.parametrize(
    ("field", "limit", "initial"),
    [
        ("assistant_display_name", MAX_ASSISTANT_DISPLAY_NAME_LENGTH, "Hermes"),
        ("assistant_prefix", MAX_ASSISTANT_PREFIX_LENGTH, "🤖 Hermes:"),
        ("dialog_prompt", MAX_DIALOG_PROMPT_LENGTH, "short prompt"),
        ("dialog_notes", MAX_DIALOG_NOTES_LENGTH, "short note"),
    ],
)
def test_profile_store_rejects_overlong_text_fields_before_persistence(field: str, limit: int, initial: str):
    store = TelegramBusinessDialogProfileStore(db_path=":memory:")
    profile = store.upsert_for_chat_entry(
        _entry(),
        updates={field: initial},
    )

    with pytest.raises(ValueError, match=field):
        store.update_by_token(profile["token"], {field: "x" * (limit + 1)})

    assert store.get_by_token(profile["token"])[field] == initial


def test_profile_store_empty_prompt_clears_to_empty_string_and_strips_controls():
    store = TelegramBusinessDialogProfileStore(db_path=":memory:")
    profile = store.upsert_for_chat_entry(
        _entry(),
        updates={"dialog_prompt": "existing", "dialog_notes": "note\x00with\x1fcontrols"},
    )

    cleared = store.clear_prompt_by_token(profile["token"], actor_user_id="owner-1")

    assert cleared is not None
    assert cleared["dialog_prompt"] == ""
    assert cleared["dialog_notes"] == "notewithcontrols"
    assert cleared["updated_by_user_id"] == "owner-1"


def test_profile_store_empty_update_is_noop():
    store = TelegramBusinessDialogProfileStore(db_path=":memory:")
    profile = store.upsert_for_chat_entry(_entry(), updates={"dialog_prompt": "existing"})

    updated = store.update_by_token(profile["token"], {}, actor_user_id="owner-1")

    assert updated == profile


def test_profile_store_returns_none_for_unknown_token():
    store = TelegramBusinessDialogProfileStore(db_path=":memory:")

    assert store.get_by_token("missing-token") is None
    assert store.update_by_token("missing-token", {"dialog_prompt": "ignored"}) is None
    assert store.clear_prompt_by_token("missing-token") is None


def test_profile_store_default_path_is_profile_aware(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr("gateway.platforms.telegram_business_profiles.get_hermes_home", lambda: tmp_path)

    store = TelegramBusinessDialogProfileStore()

    assert store.db_path == tmp_path / "gateway" / "platforms" / "telegram" / "business_profiles.db"
