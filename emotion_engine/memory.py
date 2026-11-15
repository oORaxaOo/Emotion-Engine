"""User-memory review, export, retention, and deletion operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .errors import RecordValidationError
from .models import UserEventRecord
from .store import SQLiteEmotionStore


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    """An explicit maximum age for stored memories; there is no implicit default."""

    max_age: timedelta

    def __post_init__(self) -> None:
        if not isinstance(self.max_age, timedelta) or self.max_age.total_seconds() <= 0:
            raise RecordValidationError("max_age must be a positive timedelta")


class MemoryLifecycle:
    """Small application-facing facade for user-controlled memory operations."""

    def __init__(
        self,
        store: SQLiteEmotionStore,
        *,
        retention_policy: RetentionPolicy | None = None,
    ) -> None:
        if not isinstance(store, SQLiteEmotionStore):
            raise RecordValidationError("store must be a SQLiteEmotionStore")
        if retention_policy is not None and not isinstance(
            retention_policy, RetentionPolicy
        ):
            raise RecordValidationError(
                "retention_policy must be a RetentionPolicy or None"
            )
        self._store = store
        self._retention_policy = retention_policy

    def review(self, *, limit: int = 100) -> tuple[UserEventRecord, ...]:
        """Return recent user memories for review."""
        return self._store.list_user_events(limit=limit)

    def export(self) -> str:
        """Return a portable JSON export; writing it to disk is the caller's choice."""
        return self._store.export_user_events()

    def forget(self, record_id: str) -> bool:
        """Delete one user memory."""
        return self._store.delete_user_event(record_id)

    def forget_all(self) -> int:
        """Delete all user memories, for example after consent withdrawal."""
        return self._store.delete_all_user_events()

    def apply_retention(self, *, now: datetime | None = None) -> int:
        """Delete memories older than the explicitly configured retention policy."""
        if self._retention_policy is None:
            raise RecordValidationError(
                "automatic retention requires an explicit RetentionPolicy"
            )
        effective_now = now or datetime.now(timezone.utc)
        if (
            not isinstance(effective_now, datetime)
            or effective_now.tzinfo is None
            or effective_now.utcoffset() is None
        ):
            raise RecordValidationError("now must be a timezone-aware datetime")
        cutoff = effective_now - self._retention_policy.max_age
        return self._store.delete_user_events_before(cutoff)
