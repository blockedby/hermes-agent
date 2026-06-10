"""SQLite-backed Telegram Business dialog profile settings store."""

from __future__ import annotations

import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Mapping, Optional

from hermes_constants import get_hermes_home

from .telegram_business_chats import TelegramBusinessChatRegistry

VALID_INVOCATION_POLICIES = frozenset({"off", "mention_draft", "mention_direct"})
DEFAULT_ASSISTANT_DISPLAY_NAME = "Hermes"
DEFAULT_ASSISTANT_PREFIX = "🤖 Hermes:"
MAX_ASSISTANT_DISPLAY_NAME_LENGTH = 80
MAX_ASSISTANT_PREFIX_LENGTH = 80
MAX_DIALOG_PROMPT_LENGTH = 4000
MAX_DIALOG_NOTES_LENGTH = 4000

_PROFILE_FIELDS = (
    "dialog_key",
    "token",
    "business_connection_id",
    "customer_chat_id",
    "direct_messages_topic_id",
    "assistant_display_name",
    "assistant_prefix",
    "dialog_prompt",
    "dialog_notes",
    "invocation_policy",
    "created_at",
    "updated_at",
    "updated_by_user_id",
)
_MUTABLE_FIELDS = {
    "assistant_display_name",
    "assistant_prefix",
    "dialog_prompt",
    "dialog_notes",
    "invocation_policy",
}
_TEXT_LIMITS = {
    "assistant_display_name": MAX_ASSISTANT_DISPLAY_NAME_LENGTH,
    "assistant_prefix": MAX_ASSISTANT_PREFIX_LENGTH,
    "dialog_prompt": MAX_DIALOG_PROMPT_LENGTH,
    "dialog_notes": MAX_DIALOG_NOTES_LENGTH,
}
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS telegram_business_dialog_profiles (
  dialog_key TEXT PRIMARY KEY,
  token TEXT NOT NULL UNIQUE,
  business_connection_id TEXT NOT NULL,
  customer_chat_id TEXT NOT NULL,
  direct_messages_topic_id TEXT,
  assistant_display_name TEXT NOT NULL DEFAULT 'Hermes',
  assistant_prefix TEXT NOT NULL DEFAULT '🤖 Hermes:',
  dialog_prompt TEXT NOT NULL DEFAULT '',
  dialog_notes TEXT NOT NULL DEFAULT '',
  invocation_policy TEXT NOT NULL DEFAULT 'off',
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL,
  updated_by_user_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_tbdp_token
  ON telegram_business_dialog_profiles(token);
"""


def normalize_invocation_policy(value: Any) -> Optional[str]:
    """Return a canonical invocation policy, or ``None`` for unknown values."""

    normalized = str(value or "").strip().lower()
    return normalized if normalized in VALID_INVOCATION_POLICIES else None


class TelegramBusinessDialogProfileStore:
    """Small private SQLite store for Telegram Business dialog settings."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        if db_path is not None and connection is not None:
            raise ValueError("Provide db_path or connection, not both")
        self.db_path = self._default_db_path() if db_path is None and connection is None else db_path
        self._owns_connection = connection is None
        self._conn = connection or self._connect(Path(db_path) if isinstance(db_path, Path) else db_path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    @staticmethod
    def _default_db_path() -> Path:
        return Path(get_hermes_home()) / "gateway" / "platforms" / "telegram" / "business_profiles.db"

    @staticmethod
    def _connect(db_path: str | Path | None) -> sqlite3.Connection:
        path = db_path if db_path is not None else TelegramBusinessDialogProfileStore._default_db_path()
        if path != ":memory:":
            path_obj = Path(path)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            try:
                path_obj.parent.chmod(0o700)
            except OSError:
                pass
            conn = sqlite3.connect(str(path_obj), check_same_thread=False)
            try:
                path_obj.chmod(0o600)
            except OSError:
                pass
            return conn
        return sqlite3.connect(":memory:", check_same_thread=False)

    normalize_invocation_policy = staticmethod(normalize_invocation_policy)

    def close(self) -> None:
        if self._owns_connection:
            self._conn.close()

    def _ensure_schema(self) -> None:
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    def default_profile_for_entry(self, entry: Mapping[str, Any]) -> dict[str, Any]:
        dialog_key = self._dialog_key_for_entry(entry)
        now = time.time()
        return {
            "dialog_key": dialog_key,
            "token": self._token_for_entry(entry, dialog_key),
            "business_connection_id": str(entry.get("business_connection_id") or "").strip(),
            "customer_chat_id": str(entry.get("customer_chat_id") or "").strip(),
            "direct_messages_topic_id": self._optional_str(entry.get("direct_messages_topic_id")),
            "assistant_display_name": DEFAULT_ASSISTANT_DISPLAY_NAME,
            "assistant_prefix": DEFAULT_ASSISTANT_PREFIX,
            "dialog_prompt": "",
            "dialog_notes": "",
            "invocation_policy": "off",
            "created_at": now,
            "updated_at": now,
            "updated_by_user_id": None,
        }

    def get_by_key(self, dialog_key: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            f"SELECT {', '.join(_PROFILE_FIELDS)} FROM telegram_business_dialog_profiles WHERE dialog_key = ?",
            (str(dialog_key),),
        ).fetchone()
        return self._row_to_profile(row)

    def get_by_token(self, token: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            f"SELECT {', '.join(_PROFILE_FIELDS)} FROM telegram_business_dialog_profiles WHERE token = ?",
            (str(token or "").strip(),),
        ).fetchone()
        return self._row_to_profile(row)

    def upsert_for_chat_entry(
        self,
        entry: Mapping[str, Any],
        updates: Mapping[str, Any] | None = None,
        actor_user_id: Any = None,
    ) -> dict[str, Any]:
        profile = self.default_profile_for_entry(entry)
        update_values = self._validate_updates(updates or {})
        now = time.time()
        updated_by = self._optional_str(actor_user_id)
        values = {**profile, **update_values, "updated_at": now, "updated_by_user_id": updated_by}

        assignments = ", ".join(
            f"{field} = excluded.{field}"
            for field in (
                "token",
                "business_connection_id",
                "customer_chat_id",
                "direct_messages_topic_id",
                "updated_at",
                "updated_by_user_id",
            )
        )
        if update_values:
            assignments += ", " + ", ".join(f"{field} = excluded.{field}" for field in update_values)

        placeholders = ", ".join("?" for _ in _PROFILE_FIELDS)
        columns = ", ".join(_PROFILE_FIELDS)
        params = tuple(values[field] for field in _PROFILE_FIELDS)
        with self._conn:
            self._conn.execute(
                f"""
                INSERT INTO telegram_business_dialog_profiles ({columns})
                VALUES ({placeholders})
                ON CONFLICT(dialog_key) DO UPDATE SET {assignments}
                """,
                params,
            )
        stored = self.get_by_key(profile["dialog_key"])
        if stored is None:  # pragma: no cover - defensive SQLite invariant
            raise RuntimeError("Telegram Business dialog profile upsert did not persist")
        return stored

    def update_by_token(
        self,
        token: str,
        updates: Mapping[str, Any],
        actor_user_id: Any = None,
    ) -> dict[str, Any] | None:
        current = self.get_by_token(token)
        if current is None:
            return None
        update_values = self._validate_updates(updates)
        if not update_values:
            return current
        update_values["updated_at"] = time.time()
        update_values["updated_by_user_id"] = self._optional_str(actor_user_id)
        assignments = ", ".join(f"{field} = ?" for field in update_values)
        params = tuple(update_values.values()) + (current["token"],)
        with self._conn:
            self._conn.execute(
                f"UPDATE telegram_business_dialog_profiles SET {assignments} WHERE token = ?",
                params,
            )
        return self.get_by_token(current["token"])

    def clear_prompt_by_token(self, token: str, actor_user_id: Any = None) -> dict[str, Any] | None:
        return self.update_by_token(token, {"dialog_prompt": ""}, actor_user_id=actor_user_id)

    @staticmethod
    def _dialog_key_for_entry(entry: Mapping[str, Any]) -> str:
        return TelegramBusinessChatRegistry.key(
            entry.get("business_connection_id"),
            entry.get("customer_chat_id"),
            entry.get("direct_messages_topic_id"),
        )

    @staticmethod
    def _token_for_entry(entry: Mapping[str, Any], dialog_key: str) -> str:
        token = str(entry.get("token") or "").strip()
        return token or TelegramBusinessChatRegistry.token_for_key(dialog_key)

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _clean_text(value: Any) -> str:
        return _CONTROL_CHARS_RE.sub("", str(value or ""))

    def _validate_updates(self, updates: Mapping[str, Any]) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for field, value in updates.items():
            if field not in _MUTABLE_FIELDS:
                raise ValueError(f"Unknown Telegram Business profile field: {field}")
            if field == "invocation_policy":
                policy = normalize_invocation_policy(value)
                if policy is None:
                    raise ValueError("Invalid invocation_policy")
                values[field] = policy
                continue
            text = self._clean_text(value)
            limit = _TEXT_LIMITS[field]
            if len(text) > limit:
                raise ValueError(f"{field} must be at most {limit} characters")
            values[field] = text
        return values

    @staticmethod
    def _row_to_profile(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return {field: row[field] for field in _PROFILE_FIELDS}
