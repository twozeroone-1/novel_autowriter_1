import unittest

from core.llm import _extract_first_json_value, _extract_last_json_object


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

    def test_extracts_json_array_from_fenced_block_with_preface(self):
        raw = """
설명을 먼저 적을게요.

```json
[
  {"id": "char_001", "name": "주인공"}
]
```
"""
        parsed = _extract_first_json_value(raw, expected_type=list)
        self.assertEqual(parsed, [{"id": "char_001", "name": "주인공"}])

    def test_extracts_first_matching_json_type(self):
        raw = 'prefix {"ignored": true} then [{"kept": true}] suffix'
        parsed = _extract_first_json_value(raw, expected_type=list)
        self.assertEqual(parsed, [{"kept": True}])


if __name__ == "__main__":
    unittest.main()
