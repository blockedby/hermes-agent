"""Tiny authenticated API/service layer for Telegram Business dashboard data.

The module keeps the behavior testable without a network server.  The
``BusinessDashboardAPI`` class exposes endpoint-shaped handler functions and an
optional aiohttp app wrapper for VPS deployment.  Draft requests only enqueue a
synthetic gateway event through an injected callback (when embedded) and/or mark
registry state for a separate service; this module never sends customer-facing
Telegram messages.
"""

from __future__ import annotations

import argparse
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional

try:  # Optional runtime dependency used only by create_app/run_server.
    from aiohttp import web

    AIOHTTP_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised by import in minimal envs
    web = None  # type: ignore[assignment]
    AIOHTTP_AVAILABLE = False

from gateway.config import Platform
from gateway.platforms.base import MessageEvent, MessageType
from gateway.platforms.telegram_business_approvals import TelegramBusinessApprovalStore
from gateway.platforms.telegram_business_chats import BUSINESS_CHAT_MODES, TelegramBusinessChatRegistry
from gateway.platforms.telegram_business_history import TelegramBusinessHistoryStore
from gateway.session import SessionSource

logger = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
_DASHBOARD_TOKEN_ENV = "HERMES_DASHBOARD_API_TOKEN"

_PENDING_APPROVAL_STATUSES = {"pending", "sending"}
_FAILED_APPROVAL_STATUSES = {"failed", "failed_retryable"}

@dataclass(frozen=True)
class APIResponse:
    """Small endpoint response container usable by tests and aiohttp handlers."""

    status: int
    body: Dict[str, Any]
    headers: Dict[str, str] | None = None



class BusinessDashboardAPI:
    """Endpoint-shaped Business dashboard API with bearer-token auth."""

    def __init__(
        self,
        *,
        token: Optional[str] = None,
        config: Optional[Mapping[str, Any]] = None,
        chat_registry: Optional[TelegramBusinessChatRegistry] = None,
        approval_store: Optional[TelegramBusinessApprovalStore] = None,
        history_store: Optional[TelegramBusinessHistoryStore] = None,
        enqueue_draft: Optional[Callable[..., bool]] = None,
        enqueue_latest_message: Optional[Callable[..., bool]] = None,
    ) -> None:
        self.token = _resolve_token(token=token, config=config)
        self.chat_registry = chat_registry or TelegramBusinessChatRegistry()
        self.approval_store = approval_store or TelegramBusinessApprovalStore()
        self.history_store = history_store or TelegramBusinessHistoryStore()
        # Backward-compatible name for the embedded gateway callback: callers can
        # inject either enqueue_latest_message or the older enqueue_draft hook.
        self.enqueue_latest_message = enqueue_latest_message or enqueue_draft

    def handle_request(
        self,
        method: str,
        path: str,
        *,
        headers: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        body: Optional[Any] = None,
    ) -> APIResponse:
        """Handle a request using endpoint paths without requiring HTTP."""
        method = str(method or "GET").upper()
        path_parts = [part for part in str(path or "").split("?")[0].strip("/").split("/") if part]
        if path_parts == ["health"]:
            return APIResponse(200, {"status": "ok", "service": "telegram_business_dashboard_api"})

        auth = self._authorize(headers or {})
        if auth.status != 200:
            return auth
        actor_user_id, actor_error = self._actor_user_id(headers or {})
        if actor_error is not None:
            return actor_error

        if path_parts == ["api", "business", "chats"] and method == "GET":
            return self.list_chats(mode=(query or {}).get("mode"), q=(query or {}).get("q"))

        if len(path_parts) == 4 and path_parts[:3] == ["api", "business", "chats"] and method == "GET":
            return self.get_chat(path_parts[3])

        if len(path_parts) == 5 and path_parts[:3] == ["api", "business", "chats"] and path_parts[4] == "history" and method == "GET":
            params = query or {}
            return self.get_history(path_parts[3], limit=params.get("limit"), cursor=params.get("cursor"))

        if len(path_parts) == 5 and path_parts[:3] == ["api", "business", "chats"] and path_parts[4] == "mode" and method == "POST":
            payload = _coerce_body(body)
            return self.set_mode(path_parts[3], payload.get("mode"), actor_user_id=actor_user_id)

        if len(path_parts) == 5 and path_parts[:3] == ["api", "business", "chats"] and path_parts[4] == "draft" and method == "POST":
            payload = _coerce_body(body)
            return self.request_draft(
                path_parts[3],
                source=payload.get("source", "latest"),
                prompt=payload.get("prompt"),
                actor_user_id=actor_user_id,
            )

        if path_parts == ["api", "business", "approvals"] and method == "GET":
            return self.list_approvals(chat_token=(query or {}).get("chatToken"))

        return _error(404, "not_found", "Endpoint not found.")

    def list_chats(self, *, mode: Any = None, q: Any = None) -> APIResponse:
        normalized_mode = str(mode or "all").strip().lower()
        if normalized_mode != "all" and normalized_mode not in BUSINESS_CHAT_MODES:
            return _error(400, "invalid_mode", "Invalid chat mode filter.")
        query = str(q or "").strip().lower()
        chats = []
        for key, entry in self.chat_registry.all().items():
            entry_mode = TelegramBusinessChatRegistry.normalize_mode(entry.get("mode")) or "watch"
            if normalized_mode != "all" and entry_mode != normalized_mode:
                continue
            if query:
                haystack = " ".join(
                    str(entry.get(field) or "")
                    for field in ("display_name", "username", "last_message_preview", "customer_user_name")
                ).lower()
                if query not in haystack:
                    continue
            chats.append(self._chat_view_model(key, entry))
        chats.sort(key=lambda item: (float(item.get("lastSeenAt") or 0), item.get("displayName") or ""), reverse=True)
        return APIResponse(200, {"chats": chats, "count": len(chats)})

    def get_chat(self, token: str) -> APIResponse:
        key, entry = self.chat_registry.find_by_token(token)
        if key is None or entry is None:
            return _error(404, "chat_not_found", "Business chat not found.")
        return APIResponse(200, {"chat": self._chat_detail_view_model(key, entry), "history": self.history_store.list_events(key)})

    def get_history(self, token: str, *, limit: Any = None, cursor: Any = None) -> APIResponse:
        key, entry = self.chat_registry.find_by_token(token)
        if key is None or entry is None:
            return _error(404, "chat_not_found", "Business chat not found.")
        page, next_cursor = self.history_store.list_events_page(key, limit=_coerce_int(limit, default=50), cursor=cursor)
        return APIResponse(
            200,
            {
                "chatToken": str(entry.get("token") or token),
                "history": page,
                "nextCursor": next_cursor,
                "count": len(page),
            },
        )

    def list_approvals(self, *, chat_token: Any = None) -> APIResponse:
        approvals = self.approval_store.load()
        key = None
        entry = None
        if chat_token:
            key, entry = self.chat_registry.find_by_token(str(chat_token))
            if key is None or entry is None:
                return _error(404, "chat_not_found", "Business chat not found.")
        items = []
        for approval_id, approval in approvals.items():
            if entry is not None and not _approval_matches_entry(approval, entry):
                continue
            items.append(_approval_view_model(approval_id, approval))
        items.sort(key=lambda item: float(item.get("createdAt") or 0), reverse=True)
        return APIResponse(200, {"approvals": items, "count": len(items)})

    def set_mode(self, token: str, mode: Any, *, actor_user_id: Optional[str] = None) -> APIResponse:
        normalized = TelegramBusinessChatRegistry.normalize_mode(mode)
        if normalized is None:
            return _error(400, "invalid_mode", "Invalid Business chat mode.")
        key, entry = self.chat_registry.find_by_token(token)
        if key is None or entry is None:
            return _error(404, "chat_not_found", "Business chat not found.")
        entry = self.chat_registry.set_mode_by_token(token, normalized)
        if not entry:
            return _error(404, "chat_not_found", "Business chat not found.")
        updates = {
            "last_dashboard_actor_user_id": str(actor_user_id or "") if actor_user_id else None,
            "last_dashboard_mode_at": time.time(),
        }
        entry = self.chat_registry.update_entry_by_token(token, **updates) or entry
        self.history_store.append_event(
            key,
            {
                "type": "mode_changed",
                "mode": normalized,
                "actor_user_id": actor_user_id,
                "created_at": updates["last_dashboard_mode_at"],
            },
        )
        mode_change = None
        if normalized in {"draft", "auto"}:
            mode_change, entry = self._enqueue_latest_message_for_mode(
                key,
                entry,
                mode=normalized,
                actor_user_id=actor_user_id,
            )
        body: Dict[str, Any] = {"chat": self._chat_detail_view_model(key, entry)}
        if mode_change is not None:
            body["modeChange"] = mode_change
        return APIResponse(200, body)

    def request_draft(
        self,
        token: str,
        *,
        source: Any = "latest",
        prompt: Any = None,
        actor_user_id: Optional[str] = None,
    ) -> APIResponse:
        if str(source or "latest") != "latest":
            return _error(400, "invalid_source", "Only latest-message draft requests are supported.")
        prompt_text = str(prompt or "").strip()
        key, entry = self.chat_registry.find_by_token(token)
        if key is None or entry is None:
            return _error(404, "chat_not_found", "Business chat not found.")
        event = _message_event_from_entry(entry)
        if event is None:
            return _error(409, "missing_latest_message", "Business chat has no latest customer message to draft from.")

        if prompt_text:
            metadata = dict(getattr(event, "metadata", None) or {})
            metadata["business_dashboard_prompt"] = prompt_text
            event.metadata = metadata
            event.channel_context = (
                f"Dashboard draft request prompt/topic: {prompt_text}"
                if not event.channel_context
                else f"{event.channel_context}\nDashboard draft request prompt/topic: {prompt_text}"
            )

        if self.enqueue_latest_message is None:
            return _error(503, "not_connected", "Dashboard API is not embedded with the Telegram enqueue callback.")
        queued = bool(
            self.enqueue_latest_message(
                event,
                chat_entry=dict(entry),
                actor_user_id=str(actor_user_id or "") or None,
                reason="draft_request",
            )
        )
        now_ts = time.time()
        fingerprint = f"dashboard:{entry.get('last_message_id')}:{int(now_ts)}"
        updated = self.chat_registry.update_entry_by_token(
            token,
            last_dashboard_draft_status="queued" if queued else "not_queued",
            last_dashboard_draft_requested_at=now_ts,
            last_dashboard_draft_actor_user_id=str(actor_user_id or "") if actor_user_id else None,
            last_dashboard_draft_fingerprint=fingerprint,
        ) or entry
        if not queued:
            return _error(503, "not_connected", "Dashboard API did not enqueue the latest Business message.")
        self.history_store.append_event(
            key,
            {
                "type": "draft_requested",
                "message_id": entry.get("last_message_id"),
                "actor_user_id": actor_user_id,
                "created_at": now_ts,
                "prompt": prompt_text or None,
            },
        )
        return APIResponse(
            202,
            {
                "draft": {
                    "status": str(updated.get("last_dashboard_draft_status") or "queued"),
                    "chatToken": str(entry.get("token") or token),
                    "source": "latest",
                    "sentToCustomer": False,
                    "prompt": prompt_text or None,
                }
            },
        )

    def _authorize(self, headers: Mapping[str, Any]) -> APIResponse:
        if not self.token:
            return _error(503, "dashboard_token_not_configured", "Dashboard API token is not configured.")
        authorization = _get_header(headers, "Authorization")
        if not authorization or not authorization.strip().lower().startswith("bearer "):
            return _error(401, "missing_bearer_token", "Bearer token is required.")
        provided = authorization.strip()[7:].strip()
        if not provided:
            return _error(401, "missing_bearer_token", "Bearer token is required.")
        if not hmac.compare_digest(provided, self.token):
            return _error(403, "invalid_bearer_token", "Bearer token is invalid.")
        return APIResponse(200, {"ok": True})

    def _actor_user_id(self, headers: Mapping[str, Any]) -> tuple[Optional[str], Optional[APIResponse]]:
        actor_user_id = _get_header(headers, "X-Telegram-User-Id").strip()
        if not actor_user_id:
            return None, _error(400, "missing_telegram_user_id", "X-Telegram-User-Id header is required.")
        if not actor_user_id.isdigit() or int(actor_user_id) <= 0:
            return None, _error(400, "invalid_telegram_user_id", "X-Telegram-User-Id header is invalid.")
        return actor_user_id, None

    def _enqueue_latest_message_for_mode(
        self,
        key: str,
        entry: Dict[str, Any],
        *,
        mode: str,
        actor_user_id: Optional[str],
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        status = "no_enqueue_callback"
        queued = False
        event = _message_event_from_entry(entry)
        message_id = str(entry.get("last_message_id") or "")
        fingerprint = f"{mode}:{message_id}" if message_id else ""
        update_fields: Dict[str, Any] = {
            "last_dashboard_mode_enqueue_status": status,
            "last_dashboard_mode_enqueue_at": time.time(),
        }

        if event is None or not message_id:
            status = "missing_latest_message"
        elif str(entry.get("last_mode_action_fingerprint") or "") == fingerprint:
            status = "already_enqueued"
        elif self.enqueue_latest_message is None:
            status = "no_enqueue_callback"
        else:
            queued = bool(
                self.enqueue_latest_message(
                    event,
                    chat_entry=dict(entry),
                    actor_user_id=str(actor_user_id or "") or None,
                    reason="mode_change",
                )
            )
            status = "queued" if queued else "not_queued"

        update_fields["last_dashboard_mode_enqueue_status"] = status
        if queued:
            update_fields.update(
                {
                    "last_mode_action_fingerprint": fingerprint,
                    "last_mode_action_at": update_fields["last_dashboard_mode_enqueue_at"],
                }
            )
        updated = self.chat_registry.update_entry_by_token(str(entry.get("token") or ""), **update_fields) or entry
        if queued:
            self.history_store.append_event(
                key,
                {
                    "type": "draft_requested",
                    "mode": mode,
                    "message_id": message_id,
                    "actor_user_id": actor_user_id,
                    "created_at": update_fields["last_dashboard_mode_enqueue_at"],
                },
            )
        return {"status": status, "enqueuedLatestMessage": queued}, updated

    def _approval_counts(self, entry: Dict[str, Any]) -> tuple[int, int]:
        pending = 0
        failed = 0
        for approval in self.approval_store.load().values():
            if not _approval_matches_entry(approval, entry):
                continue
            status = str(approval.get("status") or "pending")
            if status in _PENDING_APPROVAL_STATUSES:
                pending += 1
            elif status in _FAILED_APPROVAL_STATUSES:
                failed += 1
        return pending, failed

    def _chat_view_model(self, key: str, entry: Dict[str, Any]) -> Dict[str, Any]:
        pending, failed = self._approval_counts(entry)
        mode = TelegramBusinessChatRegistry.normalize_mode(entry.get("mode")) or "watch"
        username = str(entry.get("username") or "").strip().lstrip("@")
        rules = [rule for rule in entry.get("rules", []) if isinstance(rule, dict)]
        can_reply_value = entry.get("can_reply", entry.get("business_can_reply"))
        return {
            "token": str(entry.get("token") or TelegramBusinessChatRegistry.token_for_key(key)),
            "displayName": str(entry.get("display_name") or entry.get("customer_user_name") or "Customer")[:120],
            "username": username,
            "mode": mode,
            "lastSeenAt": _coerce_float(entry.get("last_seen_at")) or 0,
            "lastMessagePreview": TelegramBusinessChatRegistry.preview(str(entry.get("last_message_preview") or "")),
            "canReply": _can_reply_view(can_reply_value),
            "pendingDraftCount": pending,
            "failedDraftCount": failed,
            "rulesCount": len(rules),
            "hasDirectTopic": bool(entry.get("direct_messages_topic_id")),
            "isBot": bool(entry.get("is_bot", False)),
        }

    def _chat_detail_view_model(self, key: str, entry: Dict[str, Any]) -> Dict[str, Any]:
        view = self._chat_view_model(key, entry)
        view["latestMessage"] = {
            "preview": TelegramBusinessChatRegistry.preview(str(entry.get("last_message_preview") or "")),
            "hasText": bool(str(entry.get("last_message_text") or "")),
            "hasMessageId": bool(entry.get("last_message_id")),
        }
        view["lastDashboardDraftStatus"] = str(entry.get("last_dashboard_draft_status") or "")
        view["lastDashboardModeEnqueueStatus"] = str(entry.get("last_dashboard_mode_enqueue_status") or "")
        return view


def create_app(api: Optional[BusinessDashboardAPI] = None) -> "web.Application":
    """Build the optional aiohttp application for VPS deployment."""
    if not AIOHTTP_AVAILABLE:
        raise RuntimeError("aiohttp is required for the Telegram Business Dashboard API HTTP server.")
    api = api or BusinessDashboardAPI()
    app = web.Application()

    async def handle(request: "web.Request") -> "web.Response":
        body: Any = None
        if request.can_read_body:
            try:
                body = await request.json()
            except Exception:
                body = {}
        response = api.handle_request(
            request.method,
            request.path,
            headers=request.headers,
            query=request.query,
            body=body,
        )
        return web.json_response(response.body, status=response.status, headers=response.headers)

    app.router.add_route("*", "/health", handle)
    app.router.add_route("*", "/api/business/chats", handle)
    app.router.add_route("*", "/api/business/chats/{token}", handle)
    app.router.add_route("*", "/api/business/chats/{token}/mode", handle)
    app.router.add_route("*", "/api/business/chats/{token}/draft", handle)
    app.router.add_route("*", "/api/business/chats/{token}/history", handle)
    app.router.add_route("*", "/api/business/approvals", handle)
    return app


async def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    if not AIOHTTP_AVAILABLE:
        raise RuntimeError("aiohttp is required for the Telegram Business Dashboard API HTTP server.")
    runner = web.AppRunner(create_app(), access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()
    logger.info("Telegram Business Dashboard API listening on http://%s:%d", host, port)
    import asyncio

    await asyncio.Event().wait()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Telegram Business Dashboard API HTTP server")
    parser.add_argument("--host", default=os.getenv("HERMES_BUSINESS_DASHBOARD_API_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.getenv("HERMES_BUSINESS_DASHBOARD_API_PORT", str(DEFAULT_PORT))))
    args = parser.parse_args(argv)
    import asyncio

    asyncio.run(run_server(host=args.host, port=args.port))
    return 0


def _resolve_token(*, token: Optional[str], config: Optional[Mapping[str, Any]]) -> str:
    if token is not None:
        return str(token).strip()
    if config:
        for key in ("dashboard_api_token", "business_dashboard_api_token", "token"):
            value = config.get(key)
            if value:
                return str(value).strip()
    return os.getenv(_DASHBOARD_TOKEN_ENV, "").strip()


def _message_event_from_entry(entry: Dict[str, Any]) -> Optional[MessageEvent]:
    text = str(entry.get("last_message_text") or "")
    business_connection_id = str(entry.get("business_connection_id") or "").strip()
    customer_chat_id = str(entry.get("customer_chat_id") or entry.get("chat_id") or "").strip()
    message_id = entry.get("last_message_id")
    if not text or not business_connection_id or not customer_chat_id or not message_id:
        return None
    topic_id = entry.get("direct_messages_topic_id")
    topic_value = str(topic_id).strip() if topic_id else ""
    thread_id = f"business:{business_connection_id}"
    if topic_value:
        thread_id = f"{thread_id}:topic:{topic_value}"
    source = SessionSource(
        platform=Platform.TELEGRAM,
        chat_id=customer_chat_id,
        chat_name=str(entry.get("display_name") or customer_chat_id),
        chat_type="dm",
        user_id=str(entry.get("customer_user_id") or customer_chat_id),
        user_name=str(entry.get("customer_user_name") or entry.get("display_name") or customer_chat_id),
        thread_id=thread_id,
        chat_topic="Telegram Business",
        message_id=str(message_id),
    )
    return MessageEvent(text=text, message_type=MessageType.TEXT, source=source, raw_message=None, message_id=str(message_id))


def _approval_matches_entry(approval: Dict[str, Any], entry: Dict[str, Any]) -> bool:
    if str(approval.get("business_connection_id") or "") != str(entry.get("business_connection_id") or ""):
        return False
    approval_chat = approval.get("customer_chat_id", approval.get("chat_id"))
    if str(approval_chat or "") != str(entry.get("customer_chat_id") or entry.get("chat_id") or ""):
        return False
    approval_topic = str(approval.get("direct_messages_topic_id") or "")
    entry_topic = str(entry.get("direct_messages_topic_id") or "")
    return approval_topic == entry_topic


def _approval_view_model(approval_id: str, approval: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "approvalId": str(approval.get("approval_id") or approval_id),
        "status": str(approval.get("status") or "pending"),
        "createdAt": _coerce_float(approval.get("created_at")) or 0,
        "resolvedAt": _coerce_float(approval.get("resolved_at")),
        "preview": TelegramBusinessChatRegistry.preview(str(approval.get("draft") or ""), 240),
    }


def _coerce_body(body: Any) -> Dict[str, Any]:
    if isinstance(body, dict):
        return body
    if isinstance(body, (bytes, str)):
        try:
            parsed = json.loads(body)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _get_header(headers: Mapping[str, Any], name: str) -> str:
    needle = name.lower()
    for key, value in headers.items():
        if str(key).lower() == needle:
            return str(value or "")
    return ""


def _coerce_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _can_reply_view(value: Any) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "unknown"


def _error(status: int, code: str, message: str) -> APIResponse:
    return APIResponse(status, {"error": {"code": code, "message": message}})


if __name__ == "__main__":  # pragma: no cover - manual service entrypoint
    raise SystemExit(main())
