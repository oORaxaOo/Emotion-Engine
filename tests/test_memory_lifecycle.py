"""Memory lifecycle tests using encrypted in-memory SQLite storage."""

import json
import unittest
from datetime import datetime, timedelta, timezone

from emotion_engine import (
    ConsentStatus,
    EmotionLabel,
    EvidenceOrigin,
    MemoryLifecycle,
    RetentionPolicy,
    SQLiteEmotionStore,
    UserEventRecord,
)


KEY = bytes(reversed(range(32)))


def event(record_id, recorded_at):
    return UserEventRecord(
        record_id=record_id,
        summary=f"Synthetic memory {record_id}",
        source_origin=EvidenceOrigin.USER_REPORTED,
        consent_status=ConsentStatus.GRANTED,
        recorded_at=recorded_at,
        occurred_at=recorded_at,
        emotion_labels=(
            EmotionLabel("relief", EvidenceOrigin.USER_REPORTED),
        ),
    )


class MemoryLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.store = SQLiteEmotionStore(
            ":memory:",
            encryption_key=KEY,
            consent_verifier=lambda record: True,
        )

    def tearDown(self):
        self.store.close()

    def test_review_and_export_are_user_memory_only(self):
        from emotion_engine import ActionOutcome, AgentActionRecord

        timestamp = datetime(2026, 11, 15, tzinfo=timezone.utc)
        memory = event("memory-1", timestamp)
        self.store.save_user_event(memory)
        self.store.record_agent_action(
            AgentActionRecord(
                component="test",
                action="synthetic",
                summary="Operational-only record",
                outcome=ActionOutcome.SUCCESS,
            )
        )
        lifecycle = MemoryLifecycle(self.store)

        self.assertEqual(lifecycle.review(), (memory,))
        payload = json.loads(lifecycle.export())
        self.assertEqual(payload["record_count"], 1)
        self.assertEqual(
            [item["record_id"] for item in payload["records"]],
            ["memory-1"],
        )
        self.assertNotIn("Operational-only record", lifecycle.export())

    def test_retention_policy_expires_only_old_memories(self):
        now = datetime(2026, 11, 15, tzinfo=timezone.utc)
        self.store.save_user_event(
            event("expired", now - timedelta(days=45))
        )
        self.store.save_user_event(
            event("retained", now - timedelta(days=5))
        )
        lifecycle = MemoryLifecycle(
            self.store,
            retention_policy=RetentionPolicy(max_age=timedelta(days=30)),
        )

        self.assertEqual(lifecycle.apply_retention(now=now), 1)
        self.assertIsNone(self.store.get_user_event("expired"))
        self.assertIsNotNone(self.store.get_user_event("retained"))

    def test_retention_cannot_run_without_an_explicit_policy(self):
        lifecycle = MemoryLifecycle(self.store)

        with self.assertRaises(ValueError):
            lifecycle.apply_retention(
                now=datetime(2026, 11, 15, tzinfo=timezone.utc)
            )

    def test_forget_all_removes_every_user_memory(self):
        timestamp = datetime(2026, 11, 15, tzinfo=timezone.utc)
        self.store.save_user_event(event("one", timestamp))
        self.store.save_user_event(event("two", timestamp))
        lifecycle = MemoryLifecycle(self.store)

        self.assertEqual(lifecycle.forget_all(), 2)
        self.assertEqual(lifecycle.review(), ())


if __name__ == "__main__":
    unittest.main()
