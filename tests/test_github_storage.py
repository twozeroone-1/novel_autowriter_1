import base64
import json
import unittest

from core.github_storage import GitHubProjectStorage


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self.payload = payload


class TestGitHubStorage(unittest.TestCase):
    def test_github_storage_reads_and_decodes_file_contents(self):
        requests: list[dict] = []

        def fake_request(method: str, url: str, *, headers: dict, body: dict | None = None):
            requests.append({"method": method, "url": url, "headers": headers, "body": body})
            return FakeResponse(
                200,
                {
                    "content": base64.b64encode("hello cloud".encode("utf-8")).decode("ascii"),
                    "encoding": "base64",
                    "sha": "abc123",
                },
            )

        storage = GitHubProjectStorage(
            repo="owner/repo",
            token="secret-token",
            request=fake_request,
        )

        value = storage.read_text("sample", "config.json")

        self.assertEqual(value, "hello cloud")
        self.assertEqual(requests[0]["method"], "GET")
        self.assertIn("/repos/owner/repo/contents/projects/sample/config.json", requests[0]["url"])
        self.assertEqual(requests[0]["headers"]["Authorization"], "Bearer secret-token")

    def test_github_storage_puts_base64_encoded_content_with_sha_when_updating(self):
        requests: list[dict] = []

        def fake_request(method: str, url: str, *, headers: dict, body: dict | None = None):
            requests.append({"method": method, "url": url, "headers": headers, "body": body})
            if method == "GET":
                return FakeResponse(
                    200,
                    {
                        "content": base64.b64encode("old".encode("utf-8")).decode("ascii"),
                        "encoding": "base64",
                        "sha": "old-sha",
                    },
                )
            return FakeResponse(200, {"content": {"sha": "new-sha"}})

        storage = GitHubProjectStorage(
            repo="owner/repo",
            token="secret-token",
            request=fake_request,
        )

        storage.write_text("sample", "chapters/1화.md", "# 1화\n\n본문")

        put_request = requests[-1]
        self.assertEqual(put_request["method"], "PUT")
        self.assertEqual(put_request["body"]["sha"], "old-sha")
        self.assertEqual(
            base64.b64decode(put_request["body"]["content"]).decode("utf-8"),
            "# 1화\n\n본문",
        )


if __name__ == "__main__":
    unittest.main()
