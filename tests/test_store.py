"""Persistence and consent tests using an in-memory SQLite database."""

import dataclasses
import sqlite3
import unittest
from datetime import datetime, timezone

from emotion_engine import (
    ActionOutcome,
    AffectCoordinates,
    AgentActionRecord,
    Appraisal,
    ClaimStatus,
    ConsentRequiredError,
    ConsentStatus,
    EmotionLabel,
    EvidenceOrigin,
    RecordNotFoundError,
    RecordValidationError,
    SQLiteEmotionStore,
    StateTransitionRecord,
    UserEventRecord,
)


FIXED_TIME = datetime(2026, 11, 15, 10, 30, tzinfo=timezone.utc)


def approved_event(record_id="event-001"):
    return UserEventRecord(
        record_id=record_id,
        summary="Synthetic event used only by the automated test suite",
        source_origin=EvidenceOrigin.USER_REPORTED,
        consent_status=ConsentStatus.GRANTED,
        occurred_at=FIXED_TIME,
        recorded_at=FIXED_TIME,
        appraisal=Appraisal(
            relevance=0.8,
            expectedness=0.2,
            goal_congruence=-0.4,
            coping_potential=0.6,
            normative_significance=0.5,
        ),
        affect=AffectCoordinates(valence=-0.2, arousal=0.7),
        emotion_labels=(
            EmotionLabel(
                "frustration",
                EvidenceOrigin.USER_REPORTED,
                ClaimStatus.REPORTED,
            ),
            EmotionLabel(
                "disappointment",
                EvidenceOrigin.MODEL_INFERRED,
                ClaimStatus.HYPOTHESIS,
            ),
        ),
        uncertainties=("The cause has not been confirmed",),
    )


class SQLiteEmotionStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = SQLiteEmotionStore(":memory:")

    def tearDown(self):
        self.store.close()

    def test_user_event_round_trips_without_losing_provenance(self):
        event = approved_event()
        self.store.save_user_event(event)

        restored = self.store.get_user_event(event.record_id)

        self.assertEqual(restored, event)
        self.assertEqual(
            restored.emotion_labels[1].origin,
            EvidenceOrigin.MODEL_INFERRED,
        )
        self.assertEqual(
            restored.emotion_labels[1].status,
            ClaimStatus.HYPOTHESIS,
        )

    def test_event_without_granted_consent_is_not_persisted(self):
        event = dataclasses.replace(
            approved_event(),
            record_id="event-pending",
            consent_status=ConsentStatus.PENDING,
        )

        with self.assertRaises(ConsentRequiredError):
            self.store.save_user_event(event)

        self.assertIsNone(self.store.get_user_event("event-pending"))

    def test_ephemeral_and_revoked_events_are_not_persisted(self):
        for status in (ConsentStatus.EPHEMERAL, ConsentStatus.REVOKED):
            event = dataclasses.replace(
                approved_event(),
                record_id=f"event-{status.value}",
                consent_status=status,
            )
            with self.subTest(status=status):
                with self.assertRaises(ConsentRequiredError):
                    self.store.save_user_event(event)

    def test_update_corrects_an_existing_memory(self):
        event = approved_event()
        self.store.save_user_event(event)
        corrected = dataclasses.replace(
            event,
            summary="Corrected synthetic event summary",
        )

        self.store.update_user_event(corrected)

        self.assertEqual(
            self.store.get_user_event(event.record_id).summary,
            "Corrected synthetic event summary",
        )

    def test_update_requires_existing_record(self):
        with self.assertRaises(RecordNotFoundError):
            self.store.update_user_event(approved_event("missing-event"))

    def test_update_rechecks_consent(self):
        event = approved_event()
        self.store.save_user_event(event)
        revoked = dataclasses.replace(event, consent_status=ConsentStatus.REVOKED)

        with self.assertRaises(ConsentRequiredError):
            self.store.update_user_event(revoked)

        self.assertEqual(self.store.get_user_event(event.record_id), event)

    def test_delete_removes_memory_and_is_idempotent(self):
        event = approved_event()
        self.store.save_user_event(event)

        self.assertTrue(self.store.delete_user_event(event.record_id))
        self.assertIsNone(self.store.get_user_event(event.record_id))
        self.assertFalse(self.store.delete_user_event(event.record_id))

    def test_delete_all_user_events_returns_count(self):
        self.store.save_user_event(approved_event("event-001"))
        self.store.save_user_event(approved_event("event-002"))

        self.assertEqual(self.store.delete_all_user_events(), 2)
        self.assertEqual(self.store.list_user_events(), ())
        self.assertEqual(self.store.delete_all_user_events(), 0)

    def test_user_event_listing_is_bounded(self):
        self.store.save_user_event(approved_event())
        self.assertEqual(len(self.store.list_user_events(limit=1)), 1)
        with self.assertRaises(RecordValidationError):
            self.store.list_user_events(limit=0)
        with self.assertRaises(RecordValidationError):
            self.store.list_user_events(limit=True)

    def test_agent_action_and_state_transition_are_separate_records(self):
        action = AgentActionRecord(
            action_id="action-001",
            component="self_observation",
            action="review_completed_task",
            summary="Synthetic action record for a unit test",
            outcome=ActionOutcome.SUCCESS,
            occurred_at=FIXED_TIME,
            evidence_refs=("test://fixture-001",),
        )
        self.store.record_agent_action(action)
        self.assertEqual(self.store.get_agent_action(action.action_id), action)

        transition = StateTransitionRecord(
            transition_id="transition-001",
            state_key="uncertainty",
            previous_value=0.2,
            new_value=0.4,
            reason="The test fixture introduced an unresolved question",
            occurred_at=FIXED_TIME,
            cause_action_id=action.action_id,
        )
        self.store.record_state_transition(transition)

        self.assertEqual(
            self.store.list_state_transitions(state_key="uncertainty"),
            (transition,),
        )

    def test_state_transition_rejects_unknown_action_reference(self):
        transition = StateTransitionRecord(
            state_key="uncertainty",
            previous_value=0.2,
            new_value=0.3,
            reason="Synthetic orphan reference test",
            cause_action_id="missing-action",
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.record_state_transition(transition)

    def test_duplicate_agent_action_is_rejected(self):
        action = AgentActionRecord(
            action_id="action-duplicate",
            component="test",
            action="synthetic_action",
            summary="Synthetic duplicate-action test",
        )
        self.store.record_agent_action(action)
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.record_agent_action(action)

    def test_closed_store_rejects_further_operations(self):
        self.store.close()
        with self.assertRaises(RuntimeError):
            self.store.list_user_events()


if __name__ == "__main__":
    unittest.main()
