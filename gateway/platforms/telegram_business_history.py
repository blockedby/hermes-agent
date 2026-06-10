"""Persistent bounded history for Telegram Business dashboard events."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

from hermes_constants import get_hermes_home
from utils import atomic_replace

logger = logging.getLogger(__name__)

MAX_HISTORY_EVENTS_PER_CHAT = 50
MAX_HISTORY_PREVIEW_CHARS = 500

BUSINESS_HISTORY_EVENT_TYPES = {
    "inbound",
    "owner_outbound",
    "draft_requested",
    "draft_generated",
    "approval_created",
    "approval_sent",
    "approval_cancelled",
    "approval_failed",
    "approval_partial",
    "outbound_sent",
    "mode_changed",
    "settings_changed",
    "rule_matched",
    "media_received",
    "voice_transcribed",
    "event",
}

_EVENT_ALIASES = {
    "business_draft_sent": "approval_sent",
    "business_draft_cancelled": "approval_cancelled",
    "business_draft_failed": "approval_failed",
    "business_draft_partial": "approval_partial",
    "partial_manual_review": "approval_partial",
    "failed_partial": "approval_partial",
}

_STRING_FIELDS = (
    "event_id",
    "message_id",
    "approval_id",
    "mode",
    "actor_user_id",
    "actor_user_name",
    "classification",
    "delivery",
    "rule_id",
    "rule_label",
    "status",
    "source",
    "media_type",
    "transcription_status",
    "transcription_provider",
)

_TEXT_FIELDS = {
    "transcript": 4000,
    "prompt": 1000,
    "error": 1000,
}

_LIST_STRING_FIELDS = {"message_ids", "media_urls", "media_types", "fields"}


class TelegramBusinessHistoryStore:
    """Small private JSON store for recent Telegram Business events.

    Events are keyed by ``business_connection_id|customer_chat_id|topic_id`` and
    bounded per chat. Corrupt or invalid JSON fails closed by returning an empty
    history so dashboard reads never break the gateway.
    """

    def __init__(self, path: Optional[Path] = None, *, max_events_per_chat: int = MAX_HISTORY_EVENTS_PER_CHAT) -> None:
        self.path = path or (
            Path(get_hermes_home())
            / "gateway"
            / "platforms"
            / "telegram"
            / "business_history.json"
        )
        self.max_events_per_chat = max(1, int(max_events_per_chat))

    @staticmethod
    def key(business_connection_id: Any, customer_chat_id: Any, direct_messages_topic_id: Any = None) -> str:
        connection = str(business_connection_id or "").strip()
        chat = str(customer_chat_id or "").strip()
        topic = str(direct_messages_topic_id or "").strip()
        if not connection or not chat:
            raise ValueError("business_connection_id and customer_chat_id are required")
        return f"{connection}|{chat}|{topic}"

    def load(self) -> Dict[str, list[Dict[str, Any]]]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.error("Failed to load Telegram Business history store %s: %s", self.path, exc)
            return {}
        events = raw.get("events") if isinstance(raw, dict) else None
        if not isinstance(events, dict):
            logger.error("Invalid Telegram Business history store shape in %s", self.path)
            return {}

        normalized: Dict[str, list[Dict[str, Any]]] = {}
        changed = False
        for key, items in events.items():
            if not isinstance(items, list):
                changed = True
                continue
            kept: list[Dict[str, Any]] = []
            for item in items:
                event = self._normalize_event(item) if isinstance(item, dict) else None
                if event:
                    kept.append(event)
                else:
                    changed = True
            pruned = kept[-self.max_events_per_chat :]
            if len(pruned) != len(kept):
                changed = True
            normalized[str(key)] = pruned

        if changed:
            try:
                self.save(normalized)
            except Exception:
                logger.debug("Failed to compact Telegram Business history store", exc_info=True)
        return normalized

    def save(self, events: Dict[str, list[Dict[str, Any]]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.path.parent, 0o700)
        except OSError:
            pass
        bounded = {
            str(key): [event for event in items[-self.max_events_per_chat :] if isinstance(event, dict)]
            for key, items in events.items()
            if isinstance(items, list)
        }
        payload = {"version": 1, "updated_at": time.time(), "events": bounded}
        fd, tmp_path = tempfile.mkstemp(dir=str(self.path.parent), prefix=".business_history_", suffix=".tmp")
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
                f.flush()
                os.fsync(f.fileno())
            atomic_replace(tmp_path, self.path)
            try:
                os.chmod(self.path, 0o600)
            except OSError:
                pass
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def append_event(self, chat_key: str, event: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._normalize_event(event)
        if not normalized:
            normalized = self._normalize_event({"type": "event", "created_at": time.time(), "preview": ""}) or {}
        events = self.load()
        bucket = list(events.get(str(chat_key), []))
        bucket.append(normalized)
        events[str(chat_key)] = bucket[-self.max_events_per_chat :]
        self.save(events)
        return normalized

    def list_events(self, chat_key: str, *, limit: int = MAX_HISTORY_EVENTS_PER_CHAT, cursor: Any = None) -> list[Dict[str, Any]]:
        page, _next = self.list_events_page(chat_key, limit=limit, cursor=cursor)
        return page

    def list_events_page(
        self,
        chat_key: str,
        *,
        limit: int = MAX_HISTORY_EVENTS_PER_CHAT,
        cursor: Any = None,
    ) -> tuple[list[Dict[str, Any]], Optional[str]]:
        items = list(reversed(self.load().get(str(chat_key), [])))
        bounded_limit = max(1, min(int(limit or self.max_events_per_chat), self.max_events_per_chat))
        try:
            start = max(0, int(str(cursor or "0")))
        except (TypeError, ValueError):
            start = 0
        page = items[start : start + bounded_limit]
        next_offset = start + len(page)
        next_cursor = str(next_offset) if next_offset < len(items) else None
        return page, next_cursor

    @classmethod
    def _normalize_event(cls, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        raw_type = str(event.get("type") or "event").strip().lower()
        event_type = _EVENT_ALIASES.get(raw_type, raw_type)
        if event_type not in BUSINESS_HISTORY_EVENT_TYPES:
            event_type = "event"
        created_at = _coerce_float(event.get("created_at")) or time.time()
        preview = cls.preview(str(event.get("preview") or ""), MAX_HISTORY_PREVIEW_CHARS)
        normalized: Dict[str, Any] = {
            "type": event_type,
            "created_at": created_at,
            "preview": preview,
        }
        for key in _STRING_FIELDS:
            value = event.get(key)
            if value not in (None, ""):
                normalized[key] = str(value)[:200]
        for key, limit in _TEXT_FIELDS.items():
            value = event.get(key)
            if value not in (None, ""):
                normalized[key] = cls.preview(str(value), limit)
        for key in _LIST_STRING_FIELDS:
            value = event.get(key)
            if isinstance(value, (list, tuple)):
                normalized[key] = [str(item)[:500] for item in value if item not in (None, "")][:20]
        normalized.setdefault("event_id", cls._event_id(normalized))
        return normalized

    @staticmethod
    def preview(text: str, limit: int = MAX_HISTORY_PREVIEW_CHARS) -> str:
        value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", str(text or ""))
        value = re.sub(r"\s+", " ", value).strip()
        return value[: max(0, limit - 1)] + "…" if len(value) > limit else value

    @staticmethod
    def _event_id(event: Dict[str, Any]) -> str:
        basis = "|".join(
            str(event.get(field) or "")
            for field in ("type", "created_at", "preview", "message_id", "approval_id", "mode")
        )
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def _coerce_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
