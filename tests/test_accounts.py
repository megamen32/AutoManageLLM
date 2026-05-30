"""Tests for account import — new account on auth.json change, diff decode."""
import json, os, sys, tempfile, time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

FAKE_JWT_BODY_OLD = {
    "https://api.openai.com/profile": {"email": "old@example.com"},
    "https://api.openai.com/auth": {"user_id": "user-old-111", "chatgpt_plan_type": "free"},
    "exp": 1700000000,
}

FAKE_JWT_BODY_NEW = {
    "https://api.openai.com/profile": {"email": "newguy@proton.me"},
    "https://api.openai.com/auth": {"user_id": "user-new-222", "chatgpt_plan_type": "plus"},
    "exp": 1800000000,
}


def _b64url_encode(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _make_jwt(payload: dict) -> str:
    header = _b64url_encode(json.dumps({"alg": "RS256"}).encode())
    body = _b64url_encode(json.dumps(payload).encode())
    return f"{header}.{body}.fakesig"


@pytest.fixture
def tmp_env(tmp_path):
    cfg_dir = tmp_path / ".multimanager"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "config.json"
    cfg_file.write_text('{"accounts": [], "auto_backup": true}')

    codex_dir = tmp_path / ".codex"
    codex_dir.mkdir()
    auth_file = codex_dir / "auth.json"
    config_file = codex_dir / "config.toml"

    cc_dir = tmp_path / ".claude"
    cc_dir.mkdir()
    cc_file = cc_dir / "settings.json"
    cc_file.write_text("{}")

    ant_dir = tmp_path / ".config" / "anthropic"
    ant_dir.mkdir(parents=True)
    ant_dir_cred = ant_dir / "credentials"
    ant_dir_cred.mkdir()

    op_dir = tmp_path / ".config" / "opencode"
    op_dir.mkdir(parents=True)
    op_file = op_dir / "opencode.json"
    op_file.write_text("{}")

    patches = [
        patch("multimanager.settings.CONFIG_DIR", cfg_dir),
        patch("multimanager.settings.CONFIG_FILE", cfg_file),
        patch("multimanager.settings.CX_AUTH", auth_file),
        patch("multimanager.settings.CX_CONFIG", config_file),
        patch("multimanager.settings.CC_SETTINGS", cc_file),
        patch("multimanager.settings.ANTHROPIC_CREDENTIALS_DIR", ant_dir_cred),
        patch("multimanager.settings.OPENCODE_CFG", op_file),
        patch("multimanager.accounts.CX_AUTH", auth_file),
        patch("multimanager.accounts.CX_CONFIG", config_file),
        patch("multimanager.accounts.CC_SETTINGS", cc_file),
        patch("multimanager.accounts.ANTHROPIC_CREDENTIALS_DIR", ant_dir_cred),
        patch("multimanager.accounts.OPENCODE_CFG", op_file),
        patch("multimanager.config.CONFIG_DIR", cfg_dir),
        patch("multimanager.config.CONFIG_FILE", cfg_file),
        patch("multimanager.config.CC_SETTINGS", cc_file),
        patch("multimanager.config.CX_CONFIG", config_file),
        patch("multimanager.config.CX_AUTH", auth_file),
        patch("multimanager.config.OPENCODE_CFG", op_file),
        patch("multimanager.history.CONFIG_DIR", cfg_dir),
        patch("multimanager.history.DB_PATH", cfg_dir / "history.db"),
    ]
    for p in patches:
        p.start()
    yield {
        "cfg_dir": cfg_dir, "cfg_file": cfg_file,
        "auth_file": auth_file, "config_file": config_file,
    }
    for p in patches:
        p.stop()


def _write_codex_auth(auth_file, email, plan, user_id, access_token=None):
    token_body = {
        "https://api.openai.com/profile": {"email": email},
        "https://api.openai.com/auth": {"user_id": user_id, "chatgpt_plan_type": plan},
        "exp": int(time.time()) + 3600,
    }
    if access_token is None:
        access_token = _make_jwt(token_body)
    auth = {
        "auth_mode": "chatgpt",
        "tokens": {
            "access_token": access_token,
            "refresh_token": "rt_fake",
            "id_token": _make_jwt({"email": email}),
            "account_id": user_id,
        },
    }
    auth_file.write_text(json.dumps(auth))


def _write_codex_config(config_file, model="gpt-5"):
    config_file.write_text(f'model = "{model}"\n')


def _read_accounts(cfg_file):
    return json.loads(cfg_file.read_text()).get("accounts", [])


def test_import_creates_first_codex_account(tmp_env):
    _write_codex_auth(tmp_env["auth_file"], "alice@example.com", "plus", "uid-alice")
    _write_codex_config(tmp_env["config_file"])

    from multimanager.accounts import import_accounts
    import_accounts()

    accs = _read_accounts(tmp_env["cfg_file"])
    codex_accs = [a for a in accs if a.get("codex_provider") is not None and a.get("api_key") == ""]
    assert len(codex_accs) == 1
    assert "alice@example.com" in codex_accs[0]["name"] or codex_accs[0].get("email") == "alice@example.com"


def test_same_account_updates_not_duplicates(tmp_env):
    _write_codex_auth(tmp_env["auth_file"], "alice@example.com", "plus", "uid-alice")
    _write_codex_config(tmp_env["config_file"])

    from multimanager.accounts import import_accounts
    import_accounts()
    import_accounts()

    accs = _read_accounts(tmp_env["cfg_file"])
    codex_accs = [a for a in accs if a.get("codex_provider") is not None and a.get("api_key") == ""]
    assert len(codex_accs) == 1


def test_different_email_creates_new_account(tmp_env):
    _write_codex_auth(tmp_env["auth_file"], "alice@example.com", "plus", "uid-alice")
    _write_codex_config(tmp_env["config_file"])

    from multimanager.accounts import import_accounts
    import_accounts()

    accs_before = _read_accounts(tmp_env["cfg_file"])
    alice = [a for a in accs_before if a.get("email") == "alice@example.com"]
    assert len(alice) == 1
    alice_id = alice[0]["id"]

    _write_codex_auth(tmp_env["auth_file"], "bob@proton.me", "free", "uid-bob")

    import_accounts()

    accs_after = _read_accounts(tmp_env["cfg_file"])
    codex_accs = [a for a in accs_after if a.get("codex_provider") is not None and a.get("api_key") == ""]
    assert len(codex_accs) == 2, f"Expected 2 accounts, got {len(codex_accs)}: {[a['name'] for a in codex_accs]}"

    alice_still = [a for a in codex_accs if a["id"] == alice_id]
    assert len(alice_still) == 1, "Original alice account must be preserved"

    bob = [a for a in codex_accs if a.get("email") == "bob@proton.me"]
    assert len(bob) == 1, "New bob account must be created"


def test_same_email_different_account_id_creates_new(tmp_env):
    _write_codex_auth(tmp_env["auth_file"], "shared@example.com", "plus", "uid-first")

    from multimanager.accounts import import_accounts
    import_accounts()

    accs_before = _read_accounts(tmp_env["cfg_file"])
    first = [a for a in accs_before if a.get("_codex_account_id") == "uid-first"]
    assert len(first) == 1

    _write_codex_auth(tmp_env["auth_file"], "shared@example.com", "free", "uid-second")
    import_accounts()

    accs_after = _read_accounts(tmp_env["cfg_file"])
    codex_accs = [a for a in accs_after if a.get("codex_provider") is not None and a.get("api_key") == ""]
    assert len(codex_accs) == 2


def test_diff_decode_base64_jwt():
    from multimanager.handler import _decode_diff_content
    payload = {"email": "test@example.com", "exp": 1700000000}
    jwt_str = _make_jwt(payload)
    content = json.dumps({"id_token": jwt_str, "name": "test"}, indent=2)
    result = _decode_diff_content(content, "auth.json")
    assert "id_token_decoded" in result
    assert "test@example.com" in result


def test_diff_decode_unix_timestamp_int():
    from multimanager.handler import _decode_diff_content
    content = json.dumps({"expires_at": 1700000000}, indent=2)
    result = _decode_diff_content(content, "auth.json")
    assert "expires_at_decoded" in result
    assert "2023-11-14" in result


def test_diff_decode_unix_timestamp_string():
    from multimanager.handler import _decode_diff_content
    content = json.dumps({"exp": "1700000000"}, indent=2)
    result = _decode_diff_content(content, "auth.json")
    assert "exp_decoded" in result
    assert "2023-11-14" in result


def test_diff_decode_leaves_toml_alone():
    from multimanager.handler import _decode_diff_content
    content = 'model = "gpt-4"\nexp = 1700000000\n'
    result = _decode_diff_content(content, "config.toml")
    assert result == content
