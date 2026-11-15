"""Tests for deterministic, non-diagnostic appraisal assessment."""
import unittest

from emotion_engine import Appraisal
from emotion_engine.appraisal import AppraisalInput, assess_appraisal
from emotion_engine.errors import RecordValidationError


class AppraisalAssessmentTests(unittest.TestCase):
    def test_missing_dimensions_remain_unknown(self):
        result = assess_appraisal(AppraisalInput(Appraisal(relevance=0.4)))
        self.assertEqual(result.supplied_dimensions, ("relevance",))
        self.assertIn("goal_congruence", result.unknown_dimensions)

    def test_review_flags_are_descriptive_not_emotion_labels(self):
        result = assess_appraisal(AppraisalInput(
            Appraisal(
                relevance=0.9,
                coping_potential=0.1,
                expectedness=0.1,
                normative_significance=0.8,
            ),
            stated_goal="Complete the shared project",
        ))
        self.assertIn("high_relevance_low_perceived_coping", result.review_flags)
        self.assertIn("low_expectedness_review_context", result.review_flags)
        self.assertIn("high_normative_significance_review_stated_standard", result.review_flags)
        self.assertFalse(hasattr(result, "emotion"))

    def test_goal_congruence_without_goal_is_flagged(self):
        result = assess_appraisal(AppraisalInput(Appraisal(goal_congruence=-0.7)))
        self.assertIn("goal_congruence_without_stated_goal", result.review_flags)

    def test_no_flags_for_empty_appraisal(self):
        result = assess_appraisal(AppraisalInput(Appraisal()))
        self.assertEqual(result.review_flags, ())
        self.assertEqual(len(result.unknown_dimensions), 5)

    def test_invalid_input_type_is_rejected(self):
        with self.assertRaises(RecordValidationError):
            assess_appraisal("sad")

    def test_empty_context_is_rejected(self):
        with self.assertRaises(RecordValidationError):
            AppraisalInput(Appraisal(), context_note="  ")


if __name__ == "__main__":
    unittest.main()
