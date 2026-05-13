"""Persistent Telegram Business per-chat mode registry."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from hermes_constants import get_hermes_home
from utils import atomic_replace

logger = logging.getLogger(__name__)

BUSINESS_CHAT_MODES = {"ignored", "watch", "draft", "auto"}
DEFAULT_BUSINESS_CHAT_MODE = "watch"
DEFAULT_BUSINESS_BOT_MODE = "ignored"


class TelegramBusinessChatRegistry:
    """Small private JSON store for Telegram Business per-customer policy.

    Entries are keyed by BusinessConnection + customer chat + optional private
    topic id. Display names are metadata only and are never used for routing.
    """

    def __init__(
        self,
        path: Optional[Path] = None,
        *,
        default_mode: str = DEFAULT_BUSINESS_CHAT_MODE,
        bot_default_mode: str = DEFAULT_BUSINESS_BOT_MODE,
    ) -> None:
        self.path = path or (
            Path(get_hermes_home())
            / "gateway"
            / "platforms"
            / "telegram"
            / "business_chats.json"
        )
        self.default_mode = self.normalize_mode(default_mode) or DEFAULT_BUSINESS_CHAT_MODE
        self.bot_default_mode = self.normalize_mode(bot_default_mode) or DEFAULT_BUSINESS_BOT_MODE

    @staticmethod
    def normalize_mode(mode: Any) -> Optional[str]:
        value = str(mode or "").strip().lower().replace("notify", "watch")
        aliases = {"ignore": "ignored", "manual": "draft", "agent": "draft"}
        value = aliases.get(value, value)
        return value if value in BUSINESS_CHAT_MODES else None

    @staticmethod
    def key(
        business_connection_id: Any,
        customer_chat_id: Any,
        direct_messages_topic_id: Any = None,
    ) -> str:
        connection = str(business_connection_id or "").strip()
        chat = str(customer_chat_id or "").strip()
        topic = str(direct_messages_topic_id or "").strip()
        if not connection or not chat:
            raise ValueError("business_connection_id and customer_chat_id are required")
        return f"{connection}|{chat}|{topic}"

    @staticmethod
    def token_for_key(key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

    def load(self) -> Dict[str, Dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.error("Failed to load Telegram Business chat registry %s: %s", self.path, exc)
            return {}
        chats = raw.get("chats") if isinstance(raw, dict) else None
        if not isinstance(chats, dict):
            logger.error("Invalid Telegram Business chat registry shape in %s", self.path)
            return {}
        kept: Dict[str, Dict[str, Any]] = {}
        changed = False
        for key, entry in chats.items():
            if not isinstance(entry, dict) or not self._is_valid_entry(str(key), entry):
                changed = True
                continue
            normalized = dict(entry)
            normalized["mode"] = self.normalize_mode(normalized.get("mode")) or self.default_mode
            normalized["token"] = str(normalized.get("token") or self.token_for_key(str(key)))
            kept[str(key)] = normalized
            if normalized != entry:
                changed = True
        if changed:
            try:
                self.save(kept)
            except Exception:
                logger.debug("Failed to compact Telegram Business chat registry", exc_info=True)
        return kept

    def save(self, chats: Dict[str, Dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.path.parent, 0o700)
        except OSError:
            pass
        payload = {"version": 1, "updated_at": time.time(), "chats": chats}
        fd, tmp_path = tempfile.mkstemp(dir=str(self.path.parent), prefix=".business_chats_", suffix=".tmp")
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

    def get(self, business_connection_id: Any, customer_chat_id: Any, direct_messages_topic_id: Any = None) -> Optional[Dict[str, Any]]:
        key = self.key(business_connection_id, customer_chat_id, direct_messages_topic_id)
        return self.load().get(key)

    def find_by_token(self, token: str) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
        needle = str(token or "").strip()
        if not needle:
            return None, None
        for key, entry in self.load().items():
            if str(entry.get("token") or self.token_for_key(key)) == needle:
                return key, entry
        return None, None

    def upsert_from_message(
        self,
        *,
        business_connection_id: Any,
        customer_chat_id: Any,
        direct_messages_topic_id: Any = None,
        text: str = "",
        message_id: Any = None,
        display_name: str = "",
        username: str = "",
        user_id: Any = None,
        user_name: str = "",
        is_bot: bool = False,
        now: Optional[float] = None,
    ) -> tuple[Dict[str, Any], bool]:
        key = self.key(business_connection_id, customer_chat_id, direct_messages_topic_id)
        chats = self.load()
        now_ts = time.time() if now is None else float(now)
        is_new = key not in chats
        text_value = str(text or "")
        preview = self.preview(text_value)
        entry = dict(chats.get(key) or {})
        entry.setdefault("created_at", now_ts)
        entry.setdefault("first_seen_at", now_ts)
        entry.update(
            {
                "business_connection_id": str(business_connection_id),
                "customer_chat_id": str(customer_chat_id),
                "direct_messages_topic_id": str(direct_messages_topic_id) if direct_messages_topic_id else None,
                "display_name": str(display_name or "").strip()[:120],
                "username": str(username or "").strip().lstrip("@")[:64],
                "is_bot": bool(is_bot),
                "last_seen_at": now_ts,
                "last_message_text": text_value,
                "last_message_preview": preview,
                "last_message_id": str(message_id) if message_id is not None else None,
                "customer_user_id": str(user_id) if user_id is not None else None,
                "customer_user_name": str(user_name or display_name or "").strip()[:120],
                "token": self.token_for_key(key),
            }
        )
        if is_new or self.normalize_mode(entry.get("mode")) is None:
            entry["mode"] = self.bot_default_mode if is_bot else self.default_mode
        chats[key] = entry
        self.save(chats)
        return entry, is_new

    def set_mode_by_token(self, token: str, mode: str) -> Optional[Dict[str, Any]]:
        key, entry = self.find_by_token(token)
        normalized = self.normalize_mode(mode)
        if key is None or entry is None or normalized is None:
            return None
        chats = self.load()
        entry = dict(chats.get(key) or entry)
        entry["mode"] = normalized
        entry["updated_at"] = time.time()
        chats[key] = entry
        self.save(chats)
        return entry

    def update_entry_by_token(self, token: str, **updates: Any) -> Optional[Dict[str, Any]]:
        key, entry = self.find_by_token(token)
        if key is None or entry is None:
            return None
        chats = self.load()
        entry = dict(chats.get(key) or entry)
        entry.update(updates)
        entry["updated_at"] = time.time()
        chats[key] = entry
        self.save(chats)
        return entry

    def all(self) -> Dict[str, Dict[str, Any]]:
        return self.load()

    def add_rule_by_token(self, token: str, condition: str, *, label: str = "") -> Optional[Dict[str, Any]]:
        condition = str(condition or "").strip()
        if not condition:
            return None
        key, entry = self.find_by_token(token)
        if key is None or entry is None:
            return None
        chats = self.load()
        entry = dict(chats.get(key) or entry)
        rules = [r for r in entry.get("rules", []) if isinstance(r, dict)]
        rule_id = hashlib.sha256(f"{token}:{condition}:{time.time()}".encode()).hexdigest()[:10]
        rules.append({
            "id": rule_id,
            "label": str(label or condition)[:80],
            "condition": condition[:500],
            "action": "notify",
            "enabled": True,
            "created_at": time.time(),
        })
        entry["rules"] = rules
        entry["updated_at"] = time.time()
        chats[key] = entry
        self.save(chats)
        return entry

    @staticmethod
    def matching_rules(entry: Dict[str, Any], text: str) -> list[Dict[str, Any]]:
        haystack = str(text or "").lower()
        matches: list[Dict[str, Any]] = []
        for rule in entry.get("rules", []) if isinstance(entry.get("rules"), list) else []:
            if not isinstance(rule, dict) or not rule.get("enabled", True):
                continue
            condition = str(rule.get("condition") or "").lower().strip()
            if not condition:
                continue
            terms = [t for t in re.findall(r"[\wа-яё]+", condition, re.IGNORECASE) if len(t) >= 3]
            if terms and all(term in haystack for term in terms[:6]):
                matches.append(rule)
        return matches

    @staticmethod
    def preview(text: str, limit: int = 500) -> str:
        value = re.sub(r"\s+", " ", str(text or "")).strip()
        return value[: max(0, limit - 1)] + "…" if len(value) > limit else value

    @staticmethod
    def _is_valid_entry(key: str, entry: Dict[str, Any]) -> bool:
        try:
            connection, chat, _topic = key.split("|", 2)
        except ValueError:
            return False
        if not connection or not chat:
            return False
        if entry.get("business_connection_id") in (None, "") or entry.get("customer_chat_id") in (None, ""):
            return False
        return TelegramBusinessChatRegistry.normalize_mode(entry.get("mode")) is not None


def user_looks_like_bot(*, username: str = "", display_name: str = "", is_bot: Any = False) -> bool:
    if bool(is_bot):
        return True
    uname = str(username or "").strip().lower().lstrip("@")
    name = str(display_name or "").strip().lower()
    return bool(uname.endswith("bot") or " bot" in f" {name} " or name.endswith("бот"))
