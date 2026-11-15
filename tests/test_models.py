"""Tests for Emotion Engine's typed, validated records."""

import unittest
from datetime import datetime

from emotion_engine import (
    AffectCoordinates,
    Appraisal,
    ClaimStatus,
    ConsentStatus,
    EmotionLabel,
    EvidenceOrigin,
    RecordValidationError,
    StateTransitionRecord,
    UserEventRecord,
)


class ModelValidationTests(unittest.TestCase):
    def test_affect_coordinates_accept_documented_boundaries(self):
        value = AffectCoordinates(valence=-1.0, arousal=1.0)
        self.assertEqual(value.valence, -1.0)
        self.assertEqual(value.arousal, 1.0)

    def test_affect_coordinates_reject_out_of_range_values(self):
        with self.assertRaises(RecordValidationError):
            AffectCoordinates(valence=1.01, arousal=0.5)
        with self.assertRaises(RecordValidationError):
            AffectCoordinates(valence=0.0, arousal=-0.1)

    def test_affect_coordinates_reject_non_finite_values(self):
        with self.assertRaises(RecordValidationError):
            AffectCoordinates(valence=float("nan"), arousal=0.5)
        with self.assertRaises(RecordValidationError):
            AffectCoordinates(valence=0.0, arousal=float("inf"))

    def test_appraisal_rejects_invalid_goal_congruence(self):
        with self.assertRaises(RecordValidationError):
            Appraisal(goal_congruence=1.1)

    def test_model_inference_cannot_be_marked_as_reported_or_confirmed(self):
        with self.assertRaises(RecordValidationError):
            EmotionLabel(
                "disappointment",
                EvidenceOrigin.MODEL_INFERRED,
                ClaimStatus.CONFIRMED,
            )
        with self.assertRaises(RecordValidationError):
            EmotionLabel(
                "disappointment",
                EvidenceOrigin.MODEL_INFERRED,
                ClaimStatus.REPORTED,
            )

    def test_user_reported_label_keeps_its_provenance(self):
        label = EmotionLabel(
            "relief",
            EvidenceOrigin.USER_REPORTED,
            ClaimStatus.REPORTED,
        )
        self.assertEqual(label.origin, EvidenceOrigin.USER_REPORTED)
        self.assertEqual(label.status, ClaimStatus.REPORTED)

    def test_user_event_rejects_naive_timestamps(self):
        with self.assertRaises(RecordValidationError):
            UserEventRecord(
                summary="A synthetic test event",
                source_origin=EvidenceOrigin.USER_REPORTED,
                occurred_at=datetime(2026, 1, 1),
            )

    def test_user_event_normalises_mutable_sequences_to_tuples(self):
        label = EmotionLabel("relief", EvidenceOrigin.USER_REPORTED, ClaimStatus.REPORTED)
        record = UserEventRecord(
            summary="Synthetic fixture",
            source_origin=EvidenceOrigin.USER_REPORTED,
            consent_status=ConsentStatus.GRANTED,
            emotion_labels=[label],
            uncertainties=["Cause not established"],
        )
        self.assertIsInstance(record.emotion_labels, tuple)
        self.assertIsInstance(record.uncertainties, tuple)

    def test_state_transition_rejects_nested_values(self):
        with self.assertRaises(RecordValidationError):
            StateTransitionRecord(
                state_key="uncertainty",
                previous_value=0.2,
                new_value={"value": 0.7},
                reason="Synthetic test transition",
            )

    def test_state_transition_rejects_non_finite_values(self):
        with self.assertRaises(RecordValidationError):
            StateTransitionRecord(
                state_key="activation",
                previous_value=0.1,
                new_value=float("nan"),
                reason="Synthetic test transition",
            )


if __name__ == "__main__":
    unittest.main()
