import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import core.context as context_module
from core.generator import Generator
from core.storage import InMemoryProjectStorage


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

    def test_save_markdown_document_writes_to_storage_backend(self):
        storage = InMemoryProjectStorage()
        generator = Generator(project_name="sample", storage=storage)

        saved_path = generator.save_markdown_document("1화", "본문", heading_title="1화")
        stored_text = storage.read_text("sample", "chapters/1화.md")

        self.assertEqual(saved_path, "chapters/1화.md")
        self.assertEqual(stored_text, "# 1화\n\n본문")

    def test_list_saved_chapter_files_reads_from_storage_backend(self):
        storage = InMemoryProjectStorage()
        storage.write_text("sample", "chapters/2화.md", "# 2화\n\n본문")
        storage.write_text("sample", "chapters/1화_검수리포트.md", "# report")
        generator = Generator(project_name="sample", storage=storage)

        files = generator.list_saved_chapter_files()

        self.assertEqual(files, ["1화_검수리포트.md", "2화.md"])

    def test_read_saved_document_reads_from_storage_backend(self):
        storage = InMemoryProjectStorage()
        storage.write_text("sample", "chapters/2화.md", "# 2화\n\n본문")
        generator = Generator(project_name="sample", storage=storage)

        content = generator.read_saved_document("2화.md")

        self.assertEqual(content, "# 2화\n\n본문")


if __name__ == "__main__":
    unittest.main()
