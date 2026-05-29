import io
from datetime import datetime, timedelta, timezone
import unittest
from contextlib import redirect_stderr
from unittest.mock import Mock, patch

import script


class ScriptTests(unittest.TestCase):
    def test_get_request_headers_includes_token(self):
        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}, clear=True):
            headers = script.get_request_headers()

        self.assertEqual(headers["Authorization"], "Bearer test-token")

    def test_get_all_users_raises_on_api_error(self):
        response = Mock()
        response.ok = False
        response.status_code = 403
        response.json.return_value = {"message": "API rate limit exceeded"}

        with patch("script.requests.get", return_value=response):
            with self.assertRaises(RuntimeError) as exc:
                script.get_all_users("following")

        self.assertIn("API rate limit exceeded", str(exc.exception))

    def test_main_exits_on_api_error(self):
        response = Mock()
        response.ok = False
        response.status_code = 403
        response.json.return_value = {"message": "API rate limit exceeded"}

        stderr = io.StringIO()
        with patch("script.requests.get", return_value=response):
            with redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as exc:
                    script.main()

        self.assertEqual(exc.exception.code, 1)
        self.assertIn("GitHub API error for following", stderr.getvalue())

    def test_get_inactivity_bucket_classifies_time_ranges(self):
        now = datetime(2026, 6, 28, tzinfo=timezone.utc)

        self.assertIsNone(script.get_inactivity_bucket(now - timedelta(days=7), now=now))
        self.assertEqual(script.get_inactivity_bucket(now - timedelta(days=15), now=now), "2-4 weeks")
        self.assertEqual(script.get_inactivity_bucket(now - timedelta(days=35), now=now), "4 weeks-6 months")
        self.assertEqual(script.get_inactivity_bucket(now - timedelta(days=200), now=now), "6 months-1 year")
        self.assertEqual(script.get_inactivity_bucket(now - timedelta(days=400), now=now), "1 year+")
        self.assertEqual(script.get_inactivity_bucket(None, now=now), "Unknown")

    def test_unfollow_user_deletes_follow(self):
        response = Mock()
        response.ok = True
        response.status_code = 204

        with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}, clear=True):
            with patch("script.requests.delete", return_value=response) as delete_mock:
                result = script.unfollow_user("someuser")

        self.assertTrue(result)
        delete_mock.assert_called_once_with(
            "https://api.github.com/user/following/someuser",
            headers={"User-Agent": "Mozilla/5.0", "Authorization": "Bearer test-token"},
            timeout=30,
        )

    def test_unfollow_user_requires_token(self):
        response = Mock()
        response.ok = True
        response.status_code = 204

        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError):
                script.unfollow_user("someuser")


if __name__ == "__main__":
    unittest.main()
