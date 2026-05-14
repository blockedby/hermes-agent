"""Tests for durable Telegram Business chat history storage."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from gateway.config import Platform
from gateway.platforms.base import MessageEvent
from gateway.run import GatewayRunner
from gateway.session import SessionSource, build_session_key


def _store(tmp_path: Path):
    from gateway.platforms.telegram_business_history import TelegramBusinessHistoryStore

    return TelegramBusinessHistoryStore(tmp_path / "business_history.db")


def test_schema_init_is_idempotent_and_uses_profile_default_path(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes-home"))
    from gateway.platforms.telegram_business_history import TelegramBusinessHistoryStore

    store = TelegramBusinessHistoryStore()
    assert store.path == tmp_path / "hermes-home" / "gateway" / "platforms" / "telegram" / "business_history.db"

    store.init_schema()
    store.init_schema()

    with sqlite3.connect(store.path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] >= 1
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    assert {"business_threads", "business_messages", "business_media", "business_message_media"} <= tables


def test_last_dialog_messages_returns_max_20_oldest_first_and_excludes_non_dialog(tmp_path):
    store = _store(tmp_path)
    for index in range(25):
        store.record_message(
            business_connection_id="bc-1",
            customer_chat_id="123",
            telegram_message_id=str(index),
            role="customer",
            direction="inbound",
            text=f"customer {index}",
            message_date=float(index),
        )
    store.record_message(
        business_connection_id="bc-1",
        customer_chat_id="123",
        telegram_message_id="internal",
        role="internal",
        direction="internal",
        text="internal note",
        message_date=99,
    )
    draft = store.record_message(
        business_connection_id="bc-1",
        customer_chat_id="123",
        telegram_message_id="draft",
        role="draft",
        direction="draft",
        text="draft note",
        message_date=100,
    )
    deleted = store.record_message(
        business_connection_id="bc-1",
        customer_chat_id="123",
        telegram_message_id="deleted",
        role="customer",
        direction="inbound",
        text="deleted note",
        message_date=101,
    )
    store.mark_deleted(business_connection_id="bc-1", customer_chat_id="123", telegram_message_ids=["deleted"])

    messages = store.last_dialog_messages(business_connection_id="bc-1", customer_chat_id="123", limit=20)

    assert [m["text"] for m in messages] == [f"customer {i}" for i in range(5, 25)]
    assert all(m["id"] not in {draft["id"], deleted["id"]} for m in messages)


def test_context_block_labels_roles_and_renders_oldest_first(tmp_path):
    store = _store(tmp_path)
    rows = [
        ("1", "customer", "inbound", "hello"),
        ("2", "owner_manual", "outbound", "manual reply"),
        ("3", "hermes_approved", "outbound", "approved reply"),
        ("4", "hermes_auto", "outbound", "auto reply"),
    ]
    for index, (message_id, role, direction, text) in enumerate(rows):
        store.record_message(
            business_connection_id="bc-1",
            customer_chat_id="123",
            telegram_message_id=message_id,
            role=role,
            direction=direction,
            text=text,
            message_date=float(index),
        )

    block = store.build_context_block(business_connection_id="bc-1", customer_chat_id="123", limit=20)

    assert "Telegram Business recent chat history" in block
    assert block.index("Customer: hello") < block.index("Owner: manual reply")
    assert "Owner (Hermes-approved): approved reply" in block
    assert "Owner (auto): auto reply" in block


def test_media_metadata_dedupes_by_file_unique_id_and_renders_pending_marker(tmp_path):
    store = _store(tmp_path)
    first = store.record_message(
        business_connection_id="bc-1",
        customer_chat_id="123",
        telegram_message_id="1",
        role="customer",
        direction="inbound",
        text="",
        media=[{"media_type": "voice", "file_id": "file-a", "file_unique_id": "unique-1", "duration": 4}],
        message_date=1,
    )
    second = store.record_message(
        business_connection_id="bc-1",
        customer_chat_id="123",
        telegram_message_id="2",
        role="customer",
        direction="inbound",
        text="caption",
        media=[{"media_type": "voice", "file_id": "file-b", "file_unique_id": "unique-1", "duration": 5}],
        message_date=2,
    )

    assert first["media"][0]["id"] == second["media"][0]["id"]
    block = store.build_context_block(business_connection_id="bc-1", customer_chat_id="123")

    assert "Customer: [voice: transcription pending]" in block
    assert "Customer: caption [voice: transcription pending]" in block


def test_edit_and_delete_state_transitions(tmp_path):
    store = _store(tmp_path)
    store.record_message(
        business_connection_id="bc-1",
        customer_chat_id="123",
        telegram_message_id="55",
        role="customer",
        direction="inbound",
        text="before",
        message_date=1,
    )

    edited = store.mark_edited(
        business_connection_id="bc-1",
        customer_chat_id="123",
        telegram_message_id="55",
        text="after",
        edited_at=2,
    )
    assert edited["text"] == "after"
    assert edited["edited_at"] == 2
    assert store.last_dialog_messages(business_connection_id="bc-1", customer_chat_id="123")[0]["text"] == "after"

    store.mark_deleted(business_connection_id="bc-1", customer_chat_id="123", telegram_message_ids=["55"], deleted_at=3)

    assert store.last_dialog_messages(business_connection_id="bc-1", customer_chat_id="123") == []


@pytest.mark.asyncio
async def test_gateway_prepends_business_history_context_but_not_normal_telegram(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes-home"))
    from gateway.platforms.telegram_business_history import TelegramBusinessHistoryStore

    store = TelegramBusinessHistoryStore()
    store.record_message(
        business_connection_id="bc-ctx",
        customer_chat_id="12345",
        telegram_message_id="1",
        role="owner_manual",
        direction="outbound",
        text="previous owner reply",
        message_date=1,
    )
    store.record_message(
        business_connection_id="bc-ctx",
        customer_chat_id="12345",
        telegram_message_id="2",
        role="customer",
        direction="inbound",
        text="current customer question",
        message_date=2,
    )

    runner = object.__new__(GatewayRunner)
    runner.config = SimpleNamespace(group_sessions_per_user=True, thread_sessions_per_user=False)
    runner.adapters = {}
    runner._consume_pending_native_image_paths = lambda _session_key: []
    runner._session_key_for_source = lambda source: build_session_key(source)

    business_source = SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="12345",
        chat_type="dm",
        user_id="67890",
        user_name="Customer",
        thread_id="business:bc-ctx",
        chat_topic="Telegram Business",
    )
    business_event = MessageEvent(text="current customer question", source=business_source, message_id="2")

    prepared = await runner._prepare_inbound_message_text(event=business_event, source=business_source, history=[])

    assert prepared.startswith("[Telegram Business recent chat history")
    assert "Owner: previous owner reply" in prepared
    assert "current customer question" in prepared

    normal_source = SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="12345",
        chat_type="dm",
        user_id="67890",
        user_name="Customer",
    )
    normal_event = MessageEvent(text="normal hello", source=normal_source, message_id="3")

    assert await runner._prepare_inbound_message_text(event=normal_event, source=normal_source, history=[]) == "normal hello"
