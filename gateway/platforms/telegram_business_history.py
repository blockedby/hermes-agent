"""Durable SQLite history for Telegram Business customer chats."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Iterable, Optional

from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1
_DIALOG_EXCLUDED_ROLES = {"internal", "system", "draft"}
_DIALOG_EXCLUDED_DIRECTIONS = {"internal", "system", "draft"}


class TelegramBusinessHistoryStore:
    """Profile-local durable store for Telegram Business rolling context.

    The store is intentionally small and synchronous: Telegram Business update
    handling already runs in-process, and SQLite WAL is sufficient for the
    gateway's light write volume.  Callers should store only compact text and
    metadata, not downloaded media bytes or full PII-heavy Bot API payloads.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or (
            Path(get_hermes_home())
            / "gateway"
            / "platforms"
            / "telegram"
            / "business_history.db"
        )
        self._lock = threading.RLock()
        self.init_schema()

    def init_schema(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.path.parent, 0o700)
        except OSError:
            pass
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS business_threads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_connection_id TEXT NOT NULL,
                    customer_chat_id TEXT NOT NULL,
                    direct_messages_topic_id TEXT NOT NULL DEFAULT '',
                    created_at REAL NOT NULL,
                    last_seen_at REAL NOT NULL,
                    metadata_json TEXT,
                    UNIQUE (business_connection_id, customer_chat_id, direct_messages_topic_id)
                );

                CREATE TABLE IF NOT EXISTS business_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id INTEGER NOT NULL REFERENCES business_threads(id) ON DELETE CASCADE,
                    telegram_message_id TEXT,
                    role TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    text TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'active',
                    is_deleted INTEGER NOT NULL DEFAULT 0,
                    message_date REAL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    edited_at REAL,
                    deleted_at REAL,
                    source_update_id TEXT,
                    raw_payload_json TEXT,
                    UNIQUE (thread_id, telegram_message_id)
                );

                CREATE TABLE IF NOT EXISTS business_media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_unique_id TEXT UNIQUE,
                    file_id TEXT,
                    media_type TEXT NOT NULL,
                    mime_type TEXT,
                    file_name TEXT,
                    file_size INTEGER,
                    width INTEGER,
                    height INTEGER,
                    duration REAL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    raw_metadata_json TEXT
                );

                CREATE TABLE IF NOT EXISTS business_message_media (
                    message_id INTEGER NOT NULL REFERENCES business_messages(id) ON DELETE CASCADE,
                    media_id INTEGER NOT NULL REFERENCES business_media(id) ON DELETE CASCADE,
                    ordinal INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (message_id, media_id, ordinal)
                );

                CREATE TABLE IF NOT EXISTS business_outbox (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id INTEGER NOT NULL REFERENCES business_threads(id) ON DELETE CASCADE,
                    approval_id TEXT,
                    text TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_business_messages_thread_date
                    ON business_messages(thread_id, COALESCE(message_date, created_at), id);
                CREATE INDEX IF NOT EXISTS idx_business_messages_dialog
                    ON business_messages(thread_id, is_deleted, role, direction);
                """
            )
            conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
            conn.commit()
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def record_message(
        self,
        *,
        business_connection_id: Any,
        customer_chat_id: Any,
        telegram_message_id: Any = None,
        role: str = "customer",
        direction: str = "inbound",
        text: str = "",
        direct_messages_topic_id: Any = None,
        message_date: Any = None,
        source_update_id: Any = None,
        media: Optional[Iterable[dict[str, Any]]] = None,
        raw_payload: Any = None,
        now: Optional[float] = None,
    ) -> dict[str, Any]:
        """Insert or update one Business message plus optional media metadata."""
        now_ts = time.time() if now is None else float(now)
        msg_id = self._string_or_none(telegram_message_id)
        thread_key = self._thread_values(business_connection_id, customer_chat_id, direct_messages_topic_id)
        role_value = str(role or "customer")
        direction_value = str(direction or "inbound")
        text_value = str(text or "")
        message_ts = self._float_or_none(message_date)
        raw_json = self._compact_json(raw_payload)
        with self._lock, self._connect() as conn:
            thread_id = self._upsert_thread(conn, *thread_key, now_ts=now_ts)
            existing = None
            if msg_id is not None:
                existing = conn.execute(
                    "SELECT id FROM business_messages WHERE thread_id=? AND telegram_message_id=?",
                    (thread_id, msg_id),
                ).fetchone()
            if existing:
                message_id = int(existing["id"])
                conn.execute(
                    """
                    UPDATE business_messages
                       SET role=?, direction=?, text=?, message_date=COALESCE(?, message_date),
                           updated_at=?, source_update_id=COALESCE(?, source_update_id),
                           raw_payload_json=COALESCE(?, raw_payload_json)
                     WHERE id=?
                    """,
                    (role_value, direction_value, text_value, message_ts, now_ts,
                     self._string_or_none(source_update_id), raw_json, message_id),
                )
            else:
                cur = conn.execute(
                    """
                    INSERT INTO business_messages (
                        thread_id, telegram_message_id, role, direction, text, message_date,
                        created_at, updated_at, source_update_id, raw_payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (thread_id, msg_id, role_value, direction_value, text_value, message_ts,
                     now_ts, now_ts, self._string_or_none(source_update_id), raw_json),
                )
                message_id = int(cur.lastrowid)
            media_rows = self._replace_message_media(conn, message_id, list(media or []), now_ts=now_ts)
            conn.commit()
            row = self._message_by_id(conn, message_id)
        result = self._row_to_message(row)
        result["media"] = media_rows
        return result

    upsert_message = record_message

    def mark_edited(
        self,
        *,
        business_connection_id: Any,
        customer_chat_id: Any,
        telegram_message_id: Any,
        text: str = "",
        direct_messages_topic_id: Any = None,
        edited_at: Any = None,
        media: Optional[Iterable[dict[str, Any]]] = None,
        role: str = "customer",
        direction: str = "inbound",
    ) -> dict[str, Any]:
        edited_ts = self._float_or_none(edited_at) or time.time()
        row = self.record_message(
            business_connection_id=business_connection_id,
            customer_chat_id=customer_chat_id,
            direct_messages_topic_id=direct_messages_topic_id,
            telegram_message_id=telegram_message_id,
            role=role,
            direction=direction,
            text=text,
            media=media,
            now=edited_ts,
        )
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE business_messages SET edited_at=?, updated_at=? WHERE id=?",
                (edited_ts, edited_ts, row["id"]),
            )
            conn.commit()
            updated = self._row_to_message(self._message_by_id(conn, row["id"]))
        return updated

    def mark_deleted(
        self,
        *,
        business_connection_id: Any,
        customer_chat_id: Any,
        telegram_message_ids: Iterable[Any],
        direct_messages_topic_id: Any = None,
        deleted_at: Any = None,
    ) -> int:
        deleted_ts = self._float_or_none(deleted_at) or time.time()
        ids = [str(v) for v in telegram_message_ids if v is not None]
        if not ids:
            return 0
        thread_key = self._thread_values(business_connection_id, customer_chat_id, direct_messages_topic_id)
        with self._lock, self._connect() as conn:
            thread = self._find_thread(conn, *thread_key)
            if not thread:
                return 0
            placeholders = ",".join("?" for _ in ids)
            cur = conn.execute(
                f"""
                UPDATE business_messages
                   SET is_deleted=1, status='deleted', deleted_at=?, updated_at=?
                 WHERE thread_id=? AND telegram_message_id IN ({placeholders})
                """,
                (deleted_ts, deleted_ts, int(thread["id"]), *ids),
            )
            conn.commit()
            return int(cur.rowcount or 0)

    def record_media_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        with self._lock, self._connect() as conn:
            row = self._upsert_media(conn, metadata, now_ts=time.time())
            conn.commit()
            return row

    def last_dialog_messages(
        self,
        *,
        business_connection_id: Any,
        customer_chat_id: Any,
        direct_messages_topic_id: Any = None,
        limit: int = 20,
        exclude_telegram_message_id: Any = None,
    ) -> list[dict[str, Any]]:
        max_rows = max(1, int(limit or 20))
        thread_key = self._thread_values(business_connection_id, customer_chat_id, direct_messages_topic_id)
        exclude_id = self._string_or_none(exclude_telegram_message_id)
        with self._lock, self._connect() as conn:
            thread = self._find_thread(conn, *thread_key)
            if not thread:
                return []
            params: list[Any] = [int(thread["id"]), *_DIALOG_EXCLUDED_ROLES, *_DIALOG_EXCLUDED_DIRECTIONS]
            extra = ""
            if exclude_id is not None:
                extra = " AND COALESCE(telegram_message_id, '') != ?"
                params.append(exclude_id)
            params.append(max_rows)
            rows = conn.execute(
                f"""
                SELECT * FROM (
                    SELECT *
                      FROM business_messages
                     WHERE thread_id=?
                       AND is_deleted=0
                       AND role NOT IN ({','.join('?' for _ in _DIALOG_EXCLUDED_ROLES)})
                       AND direction NOT IN ({','.join('?' for _ in _DIALOG_EXCLUDED_DIRECTIONS)})
                       {extra}
                     ORDER BY COALESCE(message_date, created_at) DESC, id DESC
                     LIMIT ?
                )
                ORDER BY COALESCE(message_date, created_at) ASC, id ASC
                """,
                params,
            ).fetchall()
            messages = [self._row_to_message(row) for row in rows]
            for msg in messages:
                msg["media"] = self._media_for_message(conn, int(msg["id"]))
            return messages

    def build_context_block(
        self,
        *,
        business_connection_id: Any,
        customer_chat_id: Any,
        direct_messages_topic_id: Any = None,
        limit: int = 20,
        exclude_telegram_message_id: Any = None,
    ) -> str:
        messages = self.last_dialog_messages(
            business_connection_id=business_connection_id,
            customer_chat_id=customer_chat_id,
            direct_messages_topic_id=direct_messages_topic_id,
            limit=limit,
            exclude_telegram_message_id=exclude_telegram_message_id,
        )
        if not messages:
            return ""
        lines = [f"[Telegram Business recent chat history — oldest first, last {len(messages)} message(s):]"]
        for msg in messages:
            label = self._role_label(str(msg.get("role") or ""), str(msg.get("direction") or ""))
            content = self._message_content_with_media(msg)
            if content:
                lines.append(f"{label}: {content}")
        lines.append("[End Telegram Business recent chat history]")
        return "\n".join(lines)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            logger.debug("Telegram Business history WAL unavailable; using default journal", exc_info=True)
        return conn

    def _upsert_thread(
        self,
        conn: sqlite3.Connection,
        business_connection_id: str,
        customer_chat_id: str,
        direct_messages_topic_id: str,
        *,
        now_ts: float,
    ) -> int:
        conn.execute(
            """
            INSERT INTO business_threads (
                business_connection_id, customer_chat_id, direct_messages_topic_id, created_at, last_seen_at
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(business_connection_id, customer_chat_id, direct_messages_topic_id)
            DO UPDATE SET last_seen_at=excluded.last_seen_at
            """,
            (business_connection_id, customer_chat_id, direct_messages_topic_id, now_ts, now_ts),
        )
        row = self._find_thread(conn, business_connection_id, customer_chat_id, direct_messages_topic_id)
        if row is None:
            raise RuntimeError("failed to create Telegram Business history thread")
        return int(row["id"])

    def _find_thread(
        self,
        conn: sqlite3.Connection,
        business_connection_id: str,
        customer_chat_id: str,
        direct_messages_topic_id: str,
    ) -> Optional[sqlite3.Row]:
        return conn.execute(
            """
            SELECT * FROM business_threads
             WHERE business_connection_id=? AND customer_chat_id=? AND direct_messages_topic_id=?
            """,
            (business_connection_id, customer_chat_id, direct_messages_topic_id),
        ).fetchone()

    def _replace_message_media(
        self,
        conn: sqlite3.Connection,
        message_id: int,
        media: list[dict[str, Any]],
        *,
        now_ts: float,
    ) -> list[dict[str, Any]]:
        if media:
            conn.execute("DELETE FROM business_message_media WHERE message_id=?", (message_id,))
        rows: list[dict[str, Any]] = []
        for index, item in enumerate(media):
            if not isinstance(item, dict):
                continue
            media_row = self._upsert_media(conn, item, now_ts=now_ts)
            conn.execute(
                """
                INSERT OR IGNORE INTO business_message_media (message_id, media_id, ordinal)
                VALUES (?, ?, ?)
                """,
                (message_id, media_row["id"], index),
            )
            rows.append(media_row)
        return rows

    def _upsert_media(self, conn: sqlite3.Connection, metadata: dict[str, Any], *, now_ts: float) -> dict[str, Any]:
        file_unique_id = self._string_or_none(metadata.get("file_unique_id"))
        values = {
            "file_unique_id": file_unique_id,
            "file_id": self._string_or_none(metadata.get("file_id")),
            "media_type": str(metadata.get("media_type") or metadata.get("type") or "media"),
            "mime_type": self._string_or_none(metadata.get("mime_type")),
            "file_name": self._string_or_none(metadata.get("file_name")),
            "file_size": self._int_or_none(metadata.get("file_size")),
            "width": self._int_or_none(metadata.get("width")),
            "height": self._int_or_none(metadata.get("height")),
            "duration": self._float_or_none(metadata.get("duration")),
            "raw_metadata_json": self._compact_json(metadata),
        }
        if file_unique_id:
            conn.execute(
                """
                INSERT INTO business_media (
                    file_unique_id, file_id, media_type, mime_type, file_name, file_size,
                    width, height, duration, created_at, updated_at, raw_metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_unique_id) DO UPDATE SET
                    file_id=COALESCE(excluded.file_id, business_media.file_id),
                    media_type=excluded.media_type,
                    mime_type=COALESCE(excluded.mime_type, business_media.mime_type),
                    file_name=COALESCE(excluded.file_name, business_media.file_name),
                    file_size=COALESCE(excluded.file_size, business_media.file_size),
                    width=COALESCE(excluded.width, business_media.width),
                    height=COALESCE(excluded.height, business_media.height),
                    duration=COALESCE(excluded.duration, business_media.duration),
                    updated_at=excluded.updated_at,
                    raw_metadata_json=COALESCE(excluded.raw_metadata_json, business_media.raw_metadata_json)
                """,
                (values["file_unique_id"], values["file_id"], values["media_type"], values["mime_type"],
                 values["file_name"], values["file_size"], values["width"], values["height"], values["duration"],
                 now_ts, now_ts, values["raw_metadata_json"]),
            )
            row = conn.execute("SELECT * FROM business_media WHERE file_unique_id=?", (file_unique_id,)).fetchone()
        else:
            cur = conn.execute(
                """
                INSERT INTO business_media (
                    file_unique_id, file_id, media_type, mime_type, file_name, file_size,
                    width, height, duration, created_at, updated_at, raw_metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (None, values["file_id"], values["media_type"], values["mime_type"], values["file_name"],
                 values["file_size"], values["width"], values["height"], values["duration"], now_ts, now_ts,
                 values["raw_metadata_json"]),
            )
            row = conn.execute("SELECT * FROM business_media WHERE id=?", (int(cur.lastrowid),)).fetchone()
        return self._row_to_dict(row)

    def _message_by_id(self, conn: sqlite3.Connection, message_id: int) -> sqlite3.Row:
        row = conn.execute("SELECT * FROM business_messages WHERE id=?", (message_id,)).fetchone()
        if row is None:
            raise RuntimeError(f"Telegram Business history message missing after write: {message_id}")
        return row

    def _media_for_message(self, conn: sqlite3.Connection, message_id: int) -> list[dict[str, Any]]:
        rows = conn.execute(
            """
            SELECT bm.*
              FROM business_media bm
              JOIN business_message_media bmm ON bmm.media_id=bm.id
             WHERE bmm.message_id=?
             ORDER BY bmm.ordinal ASC, bm.id ASC
            """,
            (message_id,),
        ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    @staticmethod
    def _row_to_dict(row: Optional[sqlite3.Row]) -> dict[str, Any]:
        return dict(row) if row is not None else {}

    def _row_to_message(self, row: sqlite3.Row) -> dict[str, Any]:
        return self._row_to_dict(row)

    @staticmethod
    def _thread_values(business_connection_id: Any, customer_chat_id: Any, direct_messages_topic_id: Any = None) -> tuple[str, str, str]:
        connection = str(business_connection_id or "").strip()
        chat = str(customer_chat_id or "").strip()
        topic = str(direct_messages_topic_id or "").strip()
        if not connection or not chat:
            raise ValueError("business_connection_id and customer_chat_id are required")
        return connection, chat, topic

    @staticmethod
    def _string_or_none(value: Any) -> Optional[str]:
        if value is None or isinstance(value, bool):
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _float_or_none(value: Any) -> Optional[float]:
        if value is None or isinstance(value, bool):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _int_or_none(value: Any) -> Optional[int]:
        if value is None or isinstance(value, bool):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _compact_json(value: Any) -> Optional[str]:
        if value in (None, ""):
            return None
        try:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
        except (TypeError, ValueError):
            return None
        return text if len(text) <= 8192 else None

    @staticmethod
    def _role_label(role: str, direction: str) -> str:
        role = (role or "").strip().lower()
        direction = (direction or "").strip().lower()
        if role == "customer" or direction == "inbound":
            return "Customer"
        if role == "hermes_approved":
            return "Owner (Hermes-approved)"
        if role == "hermes_auto":
            return "Owner (auto)"
        return "Owner"

    @classmethod
    def _message_content_with_media(cls, msg: dict[str, Any]) -> str:
        text = str(msg.get("text") or "").strip()
        markers = [cls._media_marker(item) for item in msg.get("media") or []]
        markers = [m for m in markers if m]
        if text and markers:
            return f"{text} {' '.join(markers)}"
        if markers:
            return " ".join(markers)
        return text

    @staticmethod
    def _media_marker(media: dict[str, Any]) -> str:
        media_type = str(media.get("media_type") or "media").lower()
        mime = str(media.get("mime_type") or "").lower()
        if media_type in {"voice", "audio"} or mime.startswith("audio/"):
            return "[voice: transcription pending]" if media_type == "voice" else "[audio: transcription pending]"
        if media_type in {"photo", "image"} or mime.startswith("image/"):
            return "[image: description pending]"
        if media_type in {"video", "animation"} or mime.startswith("video/"):
            return "[video: description pending]"
        if media_type == "sticker":
            return "[sticker: description pending]"
        if media_type == "document":
            return "[document: processing pending]"
        return f"[{media_type}: processing pending]"
