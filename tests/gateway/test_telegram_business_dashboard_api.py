"""Tests for the Telegram Business Dashboard VPS API service layer."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from gateway.platforms.telegram_business_approvals import TelegramBusinessApprovalStore
from gateway.platforms.telegram_business_chats import TelegramBusinessChatRegistry
from gateway.platforms.telegram_business_dashboard_api import BusinessDashboardAPI
from gateway.platforms.telegram_business_history import TelegramBusinessHistoryStore


API_TOKEN = "test-dashboard-token"


def _auth(token: str = API_TOKEN) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "X-Telegram-User-Id": "4242"}


@pytest.fixture
def registry(tmp_path: Path) -> TelegramBusinessChatRegistry:
    return TelegramBusinessChatRegistry(tmp_path / "business_chats.json")


@pytest.fixture
def approvals(tmp_path: Path) -> TelegramBusinessApprovalStore:
    return TelegramBusinessApprovalStore(tmp_path / "business_approvals.json")


@pytest.fixture
def history(tmp_path: Path) -> TelegramBusinessHistoryStore:
    return TelegramBusinessHistoryStore(tmp_path / "business_history.json")


def _add_chat(
    registry: TelegramBusinessChatRegistry,
    *,
    connection: str,
    chat_id: str,
    text: str,
    mode: str = "watch",
    display_name: str = "Customer",
    username: str = "customer",
    message_id: str | None = "55",
    now: float = 100.0,
    topic_id: str | None = None,
):
    entry, _ = registry.upsert_from_message(
        business_connection_id=connection,
        customer_chat_id=chat_id,
        direct_messages_topic_id=topic_id,
        text=text,
        message_id=message_id,
        display_name=display_name,
        username=username,
        now=now,
    )
    if mode != entry["mode"]:
        entry = registry.set_mode_by_token(entry["token"], mode)
    return entry


def _api(registry, approvals, history, *, enqueue=None) -> BusinessDashboardAPI:
    return BusinessDashboardAPI(
        token=API_TOKEN,
        chat_registry=registry,
        approval_store=approvals,
        history_store=history,
        enqueue_draft=enqueue,
    )


def test_auth_rejects_missing_and_unknown_token(registry, approvals, history):
    api = _api(registry, approvals, history)

    missing = api.handle_request("GET", "/api/business/chats", headers={})
    wrong = api.handle_request("GET", "/api/business/chats", headers=_auth("wrong"))

    assert missing.status == 401
    assert missing.body["error"]["code"] == "missing_bearer_token"
    assert wrong.status == 403
    assert wrong.body["error"]["code"] == "invalid_bearer_token"


def test_auth_requires_valid_telegram_user_header(registry, approvals, history):
    api = _api(registry, approvals, history)
    bearer_only = {"Authorization": f"Bearer {API_TOKEN}"}
    malformed = {**bearer_only, "X-Telegram-User-Id": "not-a-user"}

    missing = api.handle_request("GET", "/api/business/chats", headers=bearer_only)
    invalid = api.handle_request("POST", "/api/business/chats/token/mode", headers=malformed, body={"mode": "watch"})

    assert missing.status == 400
    assert missing.body["error"]["code"] == "missing_telegram_user_id"
    assert invalid.status == 400
    assert invalid.body["error"]["code"] == "invalid_telegram_user_id"


def test_chats_list_is_filterable_sorted_and_hides_internal_ids(registry, approvals, history):
    older = _add_chat(
        registry,
        connection="bc-old",
        chat_id="100",
        text="old question",
        mode="watch",
        display_name="Alice Old",
        now=10,
    )
    newer = _add_chat(
        registry,
        connection="bc-new",
        chat_id="200",
        text="new draft question",
        mode="draft",
        display_name="Zoe New",
        username="zoe",
        now=20,
        topic_id="777",
    )
    approvals.save(
        {
            "pending-1": {
                "approval_id": "pending-1",
                "status": "pending",
                "created_at": time.time(),
                "customer_chat_id": "200",
                "business_connection_id": "bc-new",
                "direct_messages_topic_id": "777",
                "draft": "Draft body",
                "owner_chat_id": "999",
                "approval_message_id": "44",
            }
        }
    )

    all_resp = _api(registry, approvals, history).handle_request(
        "GET", "/api/business/chats", headers=_auth(), query={"mode": "all"}
    )
    filtered_resp = _api(registry, approvals, history).handle_request(
        "GET", "/api/business/chats", headers=_auth(), query={"mode": "draft", "q": "zoe"}
    )

    assert all_resp.status == 200
    assert [chat["token"] for chat in all_resp.body["chats"]] == [newer["token"], older["token"]]
    assert filtered_resp.status == 200
    assert [chat["token"] for chat in filtered_resp.body["chats"]] == [newer["token"]]
    chat = filtered_resp.body["chats"][0]
    assert chat["displayName"] == "Zoe New"
    assert chat["pendingDraftCount"] == 1
    assert chat["hasDirectTopic"] is True
    assert "customer_chat_id" not in chat
    assert "business_connection_id" not in chat
    assert "direct_messages_topic_id" not in chat


def test_history_store_normalizes_prunes_truncates_and_paginates(tmp_path: Path):
    store = TelegramBusinessHistoryStore(tmp_path / "business_history.json", max_events_per_chat=3)
    long_preview = "<b>Hello</b>\n" + ("x" * 700) + "\x00hidden"

    for index in range(5):
        store.append_event(
            "bc-1|123|",
            {
                "type": "inbound" if index != 4 else "unexpected custom type",
                "created_at": 100 + index,
                "preview": long_preview if index == 4 else f"event {index}",
                "message_id": index,
                "actor_user_id": "owner" if index == 4 else None,
            },
        )

    loaded = TelegramBusinessHistoryStore(tmp_path / "business_history.json", max_events_per_chat=3)
    first_page, next_cursor = loaded.list_events_page("bc-1|123|", limit=2)
    second_page, final_cursor = loaded.list_events_page("bc-1|123|", limit=2, cursor=next_cursor)

    assert (loaded.path.stat().st_mode & 0o777) == 0o600
    assert [event["created_at"] for event in loaded.list_events("bc-1|123|")] == [104.0, 103.0, 102.0]
    assert first_page[0]["type"] == "event"
    assert first_page[0]["preview"].startswith("<b>Hello</b> x")
    assert "\x00" not in first_page[0]["preview"]
    assert len(first_page[0]["preview"]) <= 500
    assert next_cursor == "2"
    assert [event["created_at"] for event in second_page] == [102.0]
    assert final_cursor is None


def test_history_store_corrupt_file_falls_back_safely(tmp_path: Path):
    path = tmp_path / "business_history.json"
    path.write_text("{not json", encoding="utf-8")

    store = TelegramBusinessHistoryStore(path)

    assert store.load() == {}
    assert store.list_events("bc-1|123|") == []


def test_chat_detail_joins_approval_and_history_summary(registry, approvals, history):
    entry = _add_chat(registry, connection="bc-1", chat_id="123", text="please reply", mode="watch")
    approvals.save(
        {
            "failed-1": {
                "approval_id": "failed-1",
                "status": "failed",
                "created_at": time.time(),
                "customer_chat_id": "123",
                "business_connection_id": "bc-1",
                "draft": "Draft body",
                "owner_chat_id": "999",
                "approval_message_id": "44",
            }
        }
    )
    history.append_event("bc-1|123|", {"type": "inbound", "preview": "please reply", "created_at": 11})

    resp = _api(registry, approvals, history).handle_request(
        "GET", f"/api/business/chats/{entry['token']}", headers=_auth()
    )

    assert resp.status == 200
    assert resp.body["chat"]["failedDraftCount"] == 1
    assert resp.body["chat"]["latestMessage"]["preview"] == "please reply"
    assert resp.body["history"][0]["type"] == "inbound"
    assert "customer_chat_id" not in resp.body["chat"]


def test_mode_change_to_watch_updates_registry_and_records_actor_metadata(registry, approvals, history):
    entry = _add_chat(registry, connection="bc-1", chat_id="123", text="hello", mode="draft")

    resp = _api(registry, approvals, history).handle_request(
        "POST",
        f"/api/business/chats/{entry['token']}/mode",
        headers=_auth(),
        body={"mode": "watch"},
    )

    assert resp.status == 200
    assert resp.body["chat"]["mode"] == "watch"
    assert "modeChange" not in resp.body
    stored = registry.find_by_token(entry["token"])[1]
    assert stored["mode"] == "watch"
    assert stored["last_dashboard_actor_user_id"] == "4242"
    assert history.list_events("bc-1|123|")[0]["type"] == "mode_changed"


def test_mode_change_to_draft_invokes_latest_message_enqueue_callback(registry, approvals, history):
    entry = _add_chat(registry, connection="bc-1", chat_id="123", text="Please draft", mode="watch")
    calls = []

    def enqueue(event, *, chat_entry, actor_user_id, reason):
        calls.append((event, chat_entry, actor_user_id, reason))
        return True

    resp = _api(registry, approvals, history, enqueue=enqueue).handle_request(
        "POST",
        f"/api/business/chats/{entry['token']}/mode",
        headers=_auth(),
        body={"mode": "draft"},
    )

    assert resp.status == 200
    assert resp.body["chat"]["mode"] == "draft"
    assert resp.body["modeChange"] == {"status": "queued", "enqueuedLatestMessage": True}
    assert len(calls) == 1
    event, chat_entry, actor_user_id, reason = calls[0]
    assert event.text == "Please draft"
    assert chat_entry["token"] == entry["token"]
    assert actor_user_id == "4242"
    assert reason == "mode_change"
    stored = registry.find_by_token(entry["token"])[1]
    assert stored["last_dashboard_mode_enqueue_status"] == "queued"
    assert stored["last_mode_action_fingerprint"] == "draft:55"
    assert history.list_events("bc-1|123|")[0]["type"] == "draft_requested"


def test_mode_change_to_auto_without_enqueue_callback_records_no_enqueue_status(registry, approvals, history):
    entry = _add_chat(registry, connection="bc-1", chat_id="123", text="Please draft", mode="watch")

    resp = _api(registry, approvals, history).handle_request(
        "POST",
        f"/api/business/chats/{entry['token']}/mode",
        headers=_auth(),
        body={"mode": "auto"},
    )

    assert resp.status == 200
    assert resp.body["chat"]["mode"] == "auto"
    assert resp.body["modeChange"] == {"status": "no_enqueue_callback", "enqueuedLatestMessage": False}
    stored = registry.find_by_token(entry["token"])[1]
    assert stored["last_dashboard_mode_enqueue_status"] == "no_enqueue_callback"
    assert stored.get("last_mode_action_fingerprint") is None
    assert all(event["type"] != "draft_requested" for event in history.list_events("bc-1|123|"))


def test_invalid_mode_and_unknown_chat_return_safe_errors(registry, approvals, history):
    entry = _add_chat(registry, connection="bc-1", chat_id="123", text="hello", mode="watch")
    api = _api(registry, approvals, history)

    invalid_mode = api.handle_request(
        "POST", f"/api/business/chats/{entry['token']}/mode", headers=_auth(), body={"mode": "manual-send"}
    )
    unknown = api.handle_request("GET", "/api/business/chats/not-a-token", headers=_auth())

    assert invalid_mode.status == 400
    assert invalid_mode.body["error"]["code"] == "invalid_mode"
    assert unknown.status == 404
    assert unknown.body["error"]["code"] == "chat_not_found"


def test_history_endpoint_returns_bounded_pages_with_cursor(registry, approvals, history):
    entry = _add_chat(registry, connection="bc-1", chat_id="123", text="hello", mode="watch")
    for index in range(4):
        history.append_event("bc-1|123|", {"type": "inbound", "created_at": 10 + index, "preview": f"event {index}"})

    resp = _api(registry, approvals, history).handle_request(
        "GET",
        f"/api/business/chats/{entry['token']}/history",
        headers=_auth(),
        query={"limit": "2"},
    )
    next_resp = _api(registry, approvals, history).handle_request(
        "GET",
        f"/api/business/chats/{entry['token']}/history",
        headers=_auth(),
        query={"limit": "2", "cursor": resp.body["nextCursor"]},
    )

    assert resp.status == 200
    assert [event["preview"] for event in resp.body["history"]] == ["event 3", "event 2"]
    assert resp.body["nextCursor"] == "2"
    assert [event["preview"] for event in next_resp.body["history"]] == ["event 1", "event 0"]
    assert next_resp.body["nextCursor"] is None


def test_draft_request_without_enqueue_callback_returns_not_connected(registry, approvals, history):
    entry = _add_chat(registry, connection="bc-1", chat_id="123", text="Please draft this", mode="watch")

    resp = _api(registry, approvals, history).handle_request(
        "POST", f"/api/business/chats/{entry['token']}/draft", headers=_auth(), body={"source": "latest"}
    )

    assert resp.status == 503
    assert resp.body["error"]["code"] == "not_connected"
    stored = registry.find_by_token(entry["token"])[1]
    assert stored.get("last_dashboard_draft_status") != "queued"
    assert history.list_events("bc-1|123|") == []


def test_draft_request_enqueues_latest_message_without_sending_customer_text(registry, approvals, history):
    entry = _add_chat(registry, connection="bc-1", chat_id="123", text="Please draft this", mode="watch")
    calls = []

    def enqueue(event, *, chat_entry, actor_user_id, reason):
        calls.append((event, chat_entry, actor_user_id, reason))
        return True

    resp = _api(registry, approvals, history, enqueue=enqueue).handle_request(
        "POST", f"/api/business/chats/{entry['token']}/draft", headers=_auth(), body={"source": "latest", "prompt": "focus on warranty"}
    )

    assert resp.status == 202
    assert resp.body["draft"]["status"] == "queued"
    assert resp.body["draft"]["sentToCustomer"] is False
    assert resp.body["draft"]["prompt"] == "focus on warranty"
    assert "Please draft this" not in json.dumps(resp.body, ensure_ascii=False)
    assert len(calls) == 1
    event, chat_entry, actor_user_id, reason = calls[0]
    assert event.text == "Please draft this"
    assert event.metadata["business_dashboard_prompt"] == "focus on warranty"
    assert "focus on warranty" in event.channel_context
    assert chat_entry["token"] == entry["token"]
    assert actor_user_id == "4242"
    assert reason == "draft_request"
    stored = registry.find_by_token(entry["token"])[1]
    assert stored["last_dashboard_draft_status"] == "queued"
    [history_event] = history.list_events("bc-1|123|")
    assert history_event["prompt"] == "focus on warranty"


def test_draft_request_requires_latest_message_context(registry, approvals, history):
    entry = _add_chat(registry, connection="bc-1", chat_id="123", text="", mode="watch", message_id=None)

    resp = _api(registry, approvals, history).handle_request(
        "POST", f"/api/business/chats/{entry['token']}/draft", headers=_auth(), body={"source": "latest"}
    )

    assert resp.status == 409
    assert resp.body["error"]["code"] == "missing_latest_message"


def test_corrupted_stores_fail_closed_without_breaking_dashboard(tmp_path: Path):
    registry_path = tmp_path / "business_chats.json"
    history_path = tmp_path / "business_history.json"
    registry_path.write_text("{not json", encoding="utf-8")
    history_path.write_text("{not json", encoding="utf-8")
    registry = TelegramBusinessChatRegistry(registry_path)
    approvals = TelegramBusinessApprovalStore(tmp_path / "business_approvals.json")
    history = TelegramBusinessHistoryStore(history_path)

    resp = _api(registry, approvals, history).handle_request(
        "GET", "/api/business/chats", headers=_auth()
    )
    hist = history.list_events("missing|chat|")

    assert resp.status == 200
    assert resp.body["chats"] == []
    assert hist == []
