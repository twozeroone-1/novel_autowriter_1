import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import core.context as context_module
from core.generator import Generator


class TestGeneratorStorage(unittest.TestCase):
    def test_build_output_path_sanitizes_title(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(context_module, "BASE_DATA_DIR", Path(tmpdir)):
                generator = Generator(project_name="sample")

                output_path = generator.build_output_path('  <제목>: "1화"?  ', ".md")

                self.assertEqual(output_path.name, "제목 1화.md")

    def test_build_output_path_adds_suffix_for_duplicates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(context_module, "BASE_DATA_DIR", Path(tmpdir)):
                generator = Generator(project_name="sample")
                first_path = generator.build_output_path("중복 제목", ".md")
                first_path.write_text("first", encoding="utf-8")

                second_path = generator.build_output_path("중복 제목", ".md")

                self.assertEqual(second_path.name, "중복 제목_2.md")


if __name__ == "__main__":
    unittest.main()
