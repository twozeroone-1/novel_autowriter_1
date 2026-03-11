import tempfile
import unittest
from pathlib import Path

from core.model_catalog import get_available_models, get_model_pricing, load_model_catalog


class TestModelCatalog(unittest.TestCase):
    def test_load_model_catalog_from_config_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "models.json"
            config_path.write_text(
                """
{
    "models": [
        {"name": "model-a"},
        {"name": "model-b", "pricing": {"input": 1.0, "output": 2.0}}
    ]
}
""".strip(),
                encoding="utf-8",
            )

            load_model_catalog.cache_clear()
            catalog = load_model_catalog(config_path)

            self.assertEqual(catalog["models"][0]["name"], "model-a")
            self.assertEqual(catalog["models"][1]["pricing"]["input"], 1.0)
            self.assertEqual(catalog["models"][1]["pricing"]["output"], 2.0)

    def test_load_model_catalog_falls_back_for_invalid_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "models.json"
            config_path.write_text('{"models": "bad"}', encoding="utf-8")

            load_model_catalog.cache_clear()
            catalog = load_model_catalog(config_path)

            self.assertGreater(len(catalog["models"]), 0)
            self.assertIn("name", catalog["models"][0])

    def test_getters_use_default_catalog(self):
        load_model_catalog.cache_clear()

        available_models = get_available_models()
        pricing = get_model_pricing("gemini-2.5-flash")

        self.assertIn("gemini-2.5-flash", available_models)
        self.assertEqual(pricing, {"input": 0.3, "output": 2.5})


if __name__ == "__main__":
    unittest.main()
