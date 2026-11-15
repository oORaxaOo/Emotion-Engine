"""Tests for the versioned psychological concept catalogue."""
import unittest

from emotion_engine.knowledge import CATALOGUE_VERSION, get_concept, list_concepts


class KnowledgeCatalogueTests(unittest.TestCase):
    def test_catalogue_has_version_and_unique_keys(self):
        concepts = list_concepts()
        self.assertTrue(CATALOGUE_VERSION)
        keys = [item.key for item in concepts]
        self.assertEqual(len(keys), len(set(keys)))

    def test_known_concept_is_retrievable(self):
        concept = get_concept("goal_congruence")
        self.assertIsNotNone(concept)
        self.assertIn("stated goal", concept.definition)

    def test_unknown_concept_returns_none(self):
        self.assertIsNone(get_concept("mind_reading"))

    def test_concepts_include_limitations_and_research_basis(self):
        for concept in list_concepts():
            self.assertTrue(concept.limitations)
            self.assertTrue(concept.research_basis)


if __name__ == "__main__":
    unittest.main()
