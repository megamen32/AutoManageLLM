"""Tests for usage.py — all provider fetchers."""
import json, time, unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from multimanager.usage import (
    _get_codex_auth,
    _fetch_chatgpt_usage,
    _fetch_claude_code_usage,
    fetch_account_usage,
    _USAGE_CACHE,
)


class TestGetCodexAuth(unittest.TestCase):
    def setUp(self):
        _USAGE_CACHE.clear()

    @patch("multimanager.usage.CX_AUTH", Path("/nonexistent/auth.json"))
    def test_returns_empty_when_no_auth_file(self):
        result = _get_codex_auth()
        self.assertEqual(result, {})

    @patch("multimanager.usage.CX_AUTH")
    def test_reads_auth_file(self, mock_path):
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "tokens": {
                "access_token": "tok123",
                "account_id": "acc456",
            }
        })
        with patch("multimanager.usage.decode_jwt", return_value={}):
            result = _get_codex_auth()
        self.assertEqual(result["access_token"], "tok123")
        self.assertEqual(result["account_id"], "acc456")


class TestFetchChatGPTUsage(unittest.TestCase):
    def setUp(self):
        _USAGE_CACHE.clear()

    def test_returns_empty_on_no_token(self):
        result = _fetch_chatgpt_usage("", "")
        self.assertEqual(result, {})

    @patch("multimanager.usage.urllib.request.urlopen")
    def test_parses_both_windows(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "rate_limit": {
                "primary_window": {"used_percent": 45.2, "limit_window_seconds": 18000, "reset_at": 1234567890},
                "secondary_window": {"used_percent": 12.1, "limit_window_seconds": 604800, "reset_at": 1234999999},
                "allowed": True,
                "limit_reached": False,
            }
        }).encode()
        mock_urlopen.return_value.__enter__ = MagicMock(return_value=mock_resp)
        mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)

        result = _fetch_chatgpt_usage("tok", "acc")
        self.assertEqual(result["type"], "codex")
        self.assertEqual(result["used_pct"], 45.2)
        self.assertEqual(len(result["windows"]), 2)
        self.assertEqual(result["windows"][0]["label"], "5h")
        self.assertEqual(result["windows"][0]["used_pct"], 45.2)
        self.assertEqual(result["windows"][1]["label"], "7d")
        self.assertEqual(result["windows"][1]["used_pct"], 12.1)
        self.assertTrue(result["allowed"])

    @patch("multimanager.usage.urllib.request.urlopen")
    def test_handles_http_error(self, mock_urlopen):
        from urllib.error import HTTPError
        mock_urlopen.side_effect = HTTPError("url", 401, "", {}, None)
        result = _fetch_chatgpt_usage("bad_tok", "acc")
        self.assertEqual(result["error"], "HTTP 401")


class TestFetchClaudeCodeUsage(unittest.TestCase):
    def setUp(self):
        _USAGE_CACHE.clear()

    @patch("multimanager.usage.urllib.request.urlopen")
    def test_anthropic_org_and_credits(self, mock_urlopen):
        def make_resp(data):
            m = MagicMock()
            m.read.return_value = json.dumps(data).encode()
            m.__enter__ = MagicMock(return_value=m)
            m.__exit__ = MagicMock(return_value=False)
            return m
        mock_urlopen.side_effect = [
            make_resp({"id": "org-1", "name": "My Org"}),
            make_resp({"balance": 42.5}),
            make_resp({"tokens": 1000}),
        ]

        result = _fetch_claude_code_usage("sk-ant-123", "")
        self.assertEqual(result["type"], "claude-code")
        self.assertEqual(result["org_id"], "org-1")
        self.assertEqual(result["name"], "My Org")
        self.assertEqual(result["balance"], 42.5)

    @patch("multimanager.usage.urllib.request.urlopen")
    def test_zai_proxy(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"usage": 100}).encode()
        mock_urlopen.return_value.__enter__ = MagicMock(return_value=mock_resp)
        mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)

        result = _fetch_claude_code_usage("key", "https://open.bigmodel.cn/api/paas/v4")
        self.assertEqual(result["type"], "claude-code")
        self.assertIn("data", result)

    @patch("multimanager.usage.urllib.request.urlopen")
    def test_handles_http_error(self, mock_urlopen):
        from urllib.error import HTTPError
        def make_error_resp():
            m = MagicMock()
            m.read.return_value = b""
            m.__enter__ = MagicMock(return_value=m)
            m.__exit__ = MagicMock(return_value=False)
            return m
        mock_urlopen.side_effect = HTTPError("url", 403, "", {}, make_error_resp())
        result = _fetch_claude_code_usage("bad-key", "")
        self.assertEqual(result["error"], "HTTP 403")


class TestFetchAccountUsage(unittest.TestCase):
    def setUp(self):
        _USAGE_CACHE.clear()

    def test_codex_account(self):
        with patch("multimanager.usage._get_codex_auth", return_value={
            "access_token": "tok", "account_id": "acc", "email": "a@b.c",
            "plan": "plus", "token_expires_in": 3600,
        }), patch("multimanager.usage._fetch_chatgpt_usage", return_value={
            "type": "codex", "used_pct": 30, "windows": [
                {"label": "5h", "used_pct": 30, "reset_at": None, "remaining_pct": 70},
            ], "allowed": True,
        }):
            result = fetch_account_usage({"id": "x1", "codex_provider": "openai", "api_key": "", "provider": "openai"})
        self.assertEqual(result["type"], "codex")
        self.assertEqual(result["used_pct"], 30)
        self.assertEqual(result["email"], "a@b.c")

    def test_claude_desktop_oauth(self):
        with patch("multimanager.usage.ANTHROPIC_CREDENTIALS_DIR", Path("/nonexistent")):
            result = fetch_account_usage({
                "id": "cd1", "provider": "anthropic", "claude_oauth_cred": "user1",
                "claude_oauth_expires_in": 43200,
                "claude_oauth_has_refresh": True,
                "claude_oauth_email": "a@b.c",
            })
        self.assertEqual(result["type"], "claude-desktop")
        self.assertEqual(len(result["windows"]), 1)
        self.assertTrue(result["has_refresh"])

    def test_claude_code_anthropic(self):
        with patch("multimanager.usage._fetch_claude_code_usage", return_value={
            "type": "claude-code", "org_id": "org1", "name": "Org",
            "balance": 10.0, "credits": {"balance": 10.0},
        }):
            result = fetch_account_usage({"id": "cc1", "provider": "anthropic", "api_key": "sk-ant-xxx"})
        self.assertEqual(result["type"], "claude-code")
        self.assertEqual(result["org_id"], "org1")

    def test_openai_api_key(self):
        with patch("multimanager.usage.urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps([
                {"remaining": 90, "max_requests": 100}
            ]).encode()
            mock_urlopen.return_value.__enter__ = MagicMock(return_value=mock_resp)
            mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)
            result = fetch_account_usage({"id": "o1", "provider": "openai", "api_key": "sk-proj-xxx"})
        self.assertEqual(result["type"], "openai")
        self.assertEqual(result["used_pct"], 10.0)

    def test_zai_account(self):
        with patch("multimanager.usage.urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"balance": 100}).encode()
            mock_urlopen.return_value.__enter__ = MagicMock(return_value=mock_resp)
            mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)
            result = fetch_account_usage({
                "id": "z1", "provider": "anthropic", "api_key": "key",
                "base_url": "https://open.bigmodel.cn/api/paas/v4",
            })
        self.assertEqual(result["type"], "zai")

    def test_unknown_provider(self):
        result = fetch_account_usage({"id": "u1", "provider": "unknown", "api_key": ""})
        self.assertEqual(result, {})

    def test_caching(self):
        call_count = 0
        def mock_fetch(api_key, base_url):
            nonlocal call_count
            call_count += 1
            return {"type": "test"}
        with patch("multimanager.usage._fetch_claude_code_usage", side_effect=mock_fetch):
            acc = {"id": "cc2", "provider": "anthropic", "api_key": "sk-ant-xxx"}
            r1 = fetch_account_usage(acc)
            r2 = fetch_account_usage(acc)
        self.assertEqual(r1["type"], "test")
        self.assertEqual(r2["type"], "test")
        self.assertEqual(call_count, 1)


if __name__ == "__main__":
    unittest.main()
