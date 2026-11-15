"""Tests for the strict, ephemeral interpretation contract."""
import json
import unittest

from emotion_engine.errors import RecordValidationError
from emotion_engine.interpretation import parse_interpretation, parse_interpretation_json
from emotion_engine.models import ClaimStatus, EvidenceOrigin


def valid_payload():
    return {
        "schema_version": "0.1",
        "event_summary": "A project contribution was not acknowledged.",
        "summary_evidence_refs": ["message-1"],
        "appraisal": {
            "relevance": {
                "value": 0.8,
                "rationale": "The speaker describes substantial personal investment.",
                "evidence_refs": ["message-1"],
            },
            "goal_congruence": {
                "value": -0.4,
                "rationale": "The reported outcome may conflict with the stated goal.",
                "evidence_refs": ["message-2"],
            },
        },
        "meaning_hypotheses": [{
            "statement": "The event may have been interpreted as a lack of recognition.",
            "evidence_refs": ["message-1"],
        }],
        "emotion_hypotheses": [{
            "label": "disappointment",
            "rationale": "A reported expectation may not have been met.",
            "evidence_refs": ["message-2"],
        }],
        "alternative_explanations": [{
            "statement": "The other people may not have noticed the contribution.",
            "evidence_refs": ["message-2"],
        }],
        "unknowns": ["Whether acknowledgement was explicitly expected."],
        "clarifying_questions": ["Was recognition something you expected in this situation?"],
    }


class InterpretationContractTests(unittest.TestCase):
    def parse(self, payload=None):
        return parse_interpretation(
            valid_payload() if payload is None else payload,
            source_event_id="event-42",
            allowed_evidence_ids=("message-1", "message-2"),
        )

    def test_valid_proposal_keeps_inferences_hypothetical(self):
        result = self.parse()
        self.assertEqual(result.source_event_id, "event-42")
        self.assertEqual(result.appraisal.relevance, 0.8)
        self.assertEqual(len(result.appraisal_notes), 2)
        emotion = result.emotion_hypotheses[0].emotion
        self.assertEqual(emotion.origin, EvidenceOrigin.MODEL_INFERRED)
        self.assertEqual(emotion.status, ClaimStatus.HYPOTHESIS)

    def test_missing_appraisal_dimensions_remain_unknown(self):
        result = self.parse()
        self.assertIsNone(result.appraisal.expectedness)
        self.assertIsNone(result.appraisal.coping_potential)
        self.assertIsNone(result.appraisal.normative_significance)

    def test_unknown_top_level_fields_are_rejected(self):
        payload = valid_payload()
        payload["confidence"] = 0.99
        with self.assertRaises(RecordValidationError):
            self.parse(payload)

    def test_unknown_nested_fields_are_rejected(self):
        payload = valid_payload()
        payload["emotion_hypotheses"][0]["diagnosis"] = "not-allowed"
        with self.assertRaises(RecordValidationError):
            self.parse(payload)

    def test_unknown_evidence_reference_is_rejected(self):
        payload = valid_payload()
        payload["summary_evidence_refs"] = ["invented-message"]
        with self.assertRaises(RecordValidationError):
            self.parse(payload)

    def test_appraisal_without_evidence_is_rejected(self):
        payload = valid_payload()
        payload["appraisal"]["relevance"]["evidence_refs"] = []
        with self.assertRaises(RecordValidationError):
            self.parse(payload)

    def test_out_of_range_appraisal_is_rejected(self):
        payload = valid_payload()
        payload["appraisal"]["relevance"]["value"] = 1.5
        with self.assertRaises(RecordValidationError):
            self.parse(payload)

    def test_boolean_is_not_accepted_as_numeric_appraisal(self):
        payload = valid_payload()
        payload["appraisal"]["relevance"]["value"] = True
        with self.assertRaises(RecordValidationError):
            self.parse(payload)

    def test_unknown_schema_version_is_rejected(self):
        payload = valid_payload()
        payload["schema_version"] = "99"
        with self.assertRaises(RecordValidationError):
            self.parse(payload)

    def test_duplicate_emotion_labels_are_rejected(self):
        payload = valid_payload()
        payload["emotion_hypotheses"].append(dict(payload["emotion_hypotheses"][0]))
        with self.assertRaises(RecordValidationError):
            self.parse(payload)

    def test_json_parser_rejects_duplicate_keys(self):
        raw = json.dumps(valid_payload())
        raw = raw.replace('"schema_version": "0.1"', '"schema_version": "0.1", "schema_version": "0.1"')
        with self.assertRaises(RecordValidationError):
            parse_interpretation_json(
                raw, source_event_id="event-42",
                allowed_evidence_ids=("message-1", "message-2"),
            )

    def test_json_parser_rejects_malformed_json(self):
        with self.assertRaises(RecordValidationError):
            parse_interpretation_json(
                "{invalid", source_event_id="event-42",
                allowed_evidence_ids=("message-1",),
            )

    def test_json_parser_rejects_oversized_payload(self):
        with self.assertRaises(RecordValidationError):
            parse_interpretation_json(
                " " * 30001, source_event_id="event-42",
                allowed_evidence_ids=("message-1",),
            )

    def test_parser_requires_evidence_envelope(self):
        with self.assertRaises(RecordValidationError):
            parse_interpretation(
                valid_payload(), source_event_id="event-42",
                allowed_evidence_ids=(),
            )

    def test_text_is_not_accepted_as_evidence_allowlist(self):
        with self.assertRaises(RecordValidationError):
            parse_interpretation(
                valid_payload(), source_event_id="event-42",
                allowed_evidence_ids="message-1",
            )


if __name__ == "__main__":
    unittest.main()
