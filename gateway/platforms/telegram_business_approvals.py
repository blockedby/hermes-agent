"""Persistent storage for Telegram Business owner-approval drafts."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

from hermes_constants import get_hermes_home
from utils import atomic_replace

logger = logging.getLogger(__name__)

DEFAULT_PENDING_TTL_SECONDS = 24 * 60 * 60
DEFAULT_RESOLVED_RETENTION_SECONDS = 7 * 24 * 60 * 60

_RETRYABLE_STATUSES = {"pending", "sending", "failed", "failed_retryable"}


class TelegramBusinessApprovalStore:
    """Small private JSON store for Telegram Business approval state.

    The store is intentionally platform-local and contains only approval-card
    routing data.  It is not a Telegram session and is never used to route
    ordinary messages.
    """

    def __init__(
        self,
        path: Optional[Path] = None,
        *,
        pending_ttl_seconds: int = DEFAULT_PENDING_TTL_SECONDS,
        resolved_retention_seconds: int = DEFAULT_RESOLVED_RETENTION_SECONDS,
    ) -> None:
        self.path = path or (
            Path(get_hermes_home())
            / "gateway"
            / "platforms"
            / "telegram"
            / "business_approvals.json"
        )
        self.pending_ttl_seconds = max(1, int(pending_ttl_seconds))
        self.resolved_retention_seconds = max(1, int(resolved_retention_seconds))

    def load(self, *, now: Optional[float] = None) -> Dict[str, Dict[str, Any]]:
        """Load non-expired approval entries.

        Corrupt or non-object JSON fails closed by returning no approvals.
        """
        now_ts = time.time() if now is None else float(now)
        if not self.path.exists():
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as exc:
            logger.error("Failed to load Telegram Business approval store %s: %s", self.path, exc)
            return {}

        if isinstance(raw, dict) and isinstance(raw.get("approvals"), dict):
            approvals = raw["approvals"]
        elif isinstance(raw, dict):
            # Legacy/dev shape: direct approval_id -> entry mapping.
            approvals = raw
        else:
            logger.error("Invalid Telegram Business approval store shape in %s", self.path)
            return {}

        kept: Dict[str, Dict[str, Any]] = {}
        changed = False
        for approval_id, entry in approvals.items():
            if not isinstance(entry, dict):
                changed = True
                continue
            if not self._is_valid_entry(str(approval_id), entry):
                changed = True
                continue
            if self.is_expired(entry, now=now_ts):
                changed = True
                continue
            kept[str(approval_id)] = entry

        if changed:
            try:
                self.save(kept)
            except Exception:
                logger.debug("Failed to compact Telegram Business approval store", exc_info=True)
        return kept

    def save(self, approvals: Dict[str, Dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.path.parent, 0o700)
        except OSError:
            pass
        payload = {
            "version": 1,
            "updated_at": time.time(),
            "approvals": approvals,
        }
        fd, tmp_path = tempfile.mkstemp(
            dir=str(self.path.parent),
            prefix=".business_approvals_",
            suffix=".tmp",
        )
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

    def is_expired(self, entry: Dict[str, Any], *, now: Optional[float] = None) -> bool:
        now_ts = time.time() if now is None else float(now)
        expires_at = self._float(entry.get("expires_at"))
        if expires_at is not None:
            return now_ts > expires_at
        created_at = self._float(entry.get("created_at")) or now_ts
        resolved_at = self._float(entry.get("resolved_at"))
        status = str(entry.get("status") or "pending")
        if status in _RETRYABLE_STATUSES:
            return now_ts - created_at > self.pending_ttl_seconds
        if resolved_at is None:
            resolved_at = created_at
        return now_ts - resolved_at > self.resolved_retention_seconds

    def _is_valid_entry(self, approval_id: str, entry: Dict[str, Any]) -> bool:
        """Fail closed for pending/retryable entries missing callback-critical data."""
        status = str(entry.get("status") or "pending")
        if status not in _RETRYABLE_STATUSES:
            return True

        stored_id = entry.get("approval_id")
        if stored_id is None or str(stored_id) != str(approval_id):
            logger.error("Rejecting invalid Telegram Business approval %s: missing/mismatched approval_id", approval_id)
            return False
        if entry.get("customer_chat_id") in (None, "") and entry.get("chat_id") in (None, ""):
            logger.error("Rejecting invalid Telegram Business approval %s: missing customer_chat_id/chat_id", approval_id)
            return False
        for field in ("business_connection_id", "draft", "owner_chat_id", "approval_message_id"):
            if entry.get(field) in (None, ""):
                logger.error("Rejecting invalid Telegram Business approval %s: missing %s", approval_id, field)
                return False
        if self._float(entry.get("created_at")) is None:
            logger.error("Rejecting invalid Telegram Business approval %s: missing/invalid created_at", approval_id)
            return False
        return True

    @staticmethod
    def _float(value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
