import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from retrieval_utils import score_chunk_relevance, expand_query_terms


class RetrievalUtilsTests(unittest.TestCase):
    def test_expanded_query_terms_capture_paraphrases(self):
        query = "How do I request time off for vacation?"
        chunk = "Employees can apply for annual leave and holiday time according to company policy."

        expanded = expand_query_terms(query)
        score = score_chunk_relevance(query, chunk)

        self.assertIn("leave", expanded)
        self.assertIn("vacation", expanded)
        self.assertGreater(score, 0.25)

    def test_relevance_score_is_stronger_for_matching_concepts(self):
        query = "What benefits are included in the package?"
        chunk = "The compensation plan includes health insurance, bonuses, and other perks."

        score = score_chunk_relevance(query, chunk)

        self.assertGreater(score, 0.2)


if __name__ == "__main__":
    unittest.main()
