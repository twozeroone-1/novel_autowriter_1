import unittest

from core.llm import _extract_last_json_object


class TestGeminiCliJsonParser(unittest.TestCase):
    def test_prefers_top_level_response_object(self):
        raw = """
noise line
{
  "session_id": "abc",
  "response": "hello",
  "stats": {"tools": {"totalCalls": 0}}
}
"""
        parsed = _extract_last_json_object(raw)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.get("response"), "hello")

    def test_fallback_when_response_field_missing(self):
        raw = '{"a":1}\n{"b":2}'
        parsed = _extract_last_json_object(raw)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.get("b"), 2)

    def test_returns_none_for_non_json(self):
        parsed = _extract_last_json_object("not json at all")
        self.assertIsNone(parsed)


if __name__ == "__main__":
    unittest.main()
