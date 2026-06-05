from django.test import SimpleTestCase

from ai_nlp.analyzer import (
    _extract_requirement_keywords,
    _normalize_keyword_phrase,
)
from core.utils import _is_meaningful_requirement_phrase, _normalize_requirement_phrase


class ATSKeywordNormalizationTests(SimpleTestCase):
    def test_analyzer_strips_leading_conjunctions(self):
        self.assertEqual(_normalize_keyword_phrase("and api development"), "api development")
        self.assertEqual(_normalize_keyword_phrase("the rest api"), "rest api")

    def test_requirement_extraction_drops_broken_keyword_phrases(self):
        keywords = _extract_requirement_keywords(
            "and api development, django, postgresql",
            ["django"],
        )
        self.assertEqual(keywords, ["api development", "django", "postgresql"])

    def test_fallback_requirement_cleaning_matches_analyzer_cleaning(self):
        self.assertEqual(_normalize_requirement_phrase("and api development"), "api development")
        self.assertTrue(_is_meaningful_requirement_phrase("api development"))
        self.assertFalse(_is_meaningful_requirement_phrase("and"))
