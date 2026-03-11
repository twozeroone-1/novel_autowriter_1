import unittest

from ui.app import normalize_project_name


class TestUiHelpers(unittest.TestCase):
    def test_normalize_project_name_collapses_spaces(self):
        normalized, error = normalize_project_name("  my   project   name  ")

        self.assertEqual(normalized, "my project name")
        self.assertIsNone(error)

    def test_normalize_project_name_rejects_reserved_name(self):
        normalized, error = normalize_project_name("default_project")

        self.assertIsNone(normalized)
        self.assertIsNotNone(error)

    def test_normalize_project_name_rejects_sample_name(self):
        normalized, error = normalize_project_name("sample")

        self.assertIsNone(normalized)
        self.assertIsNotNone(error)

    def test_normalize_project_name_rejects_path_characters(self):
        normalized, error = normalize_project_name("bad/name")

        self.assertIsNone(normalized)
        self.assertIsNotNone(error)


if __name__ == "__main__":
    unittest.main()
