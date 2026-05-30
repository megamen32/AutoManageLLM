"""Paths, constants, program definitions, provider helpers."""
from pathlib import Path

HOME = Path.home()
CONFIG_DIR = HOME / ".multimanager"
CONFIG_FILE = CONFIG_DIR / "config.json"
BACKUP_DIR = CONFIG_DIR / "backups"
MASTER_DIR = CONFIG_DIR / "master"
MASTER_SKILLS = MASTER_DIR / "skills"
MASTER_MCP = MASTER_DIR / "mcp.json"

CLAUDE_DESKTOP_DIR = HOME / "Library" / "Application Support"
CLAUDE_DESKTOP_CFG = CLAUDE_DESKTOP_DIR / "Claude" / "claude_desktop_config.json"
CLAUDE_DESKTOP_SKILLS = HOME / "Library" / "Application Support" / "Claude" / "skills"
CC_SETTINGS = HOME / ".claude" / "settings.json"
CX_CONFIG = HOME / ".codex" / "config.toml"
CX_AUTH = HOME / ".codex" / "auth.json"
OPENCODE_CFG = HOME / ".config" / "opencode" / "opencode.json"
CLINE_CFG = HOME / ".cline" / "mcp_settings.json"
ROO_CFG = HOME / ".roo" / "mcp_settings.json"

ANTHROPIC_DIR = HOME / ".config" / "anthropic"
ANTHROPIC_CREDENTIALS_DIR = ANTHROPIC_DIR / "credentials"
ANTHROPIC_CONFIGS_DIR = ANTHROPIC_DIR / "configs"
ANTHROPIC_ACTIVE_CONFIG = ANTHROPIC_DIR / "config"

APP_NAME = "MultiManager"
CD_OAUTH_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
CD_OAUTH_TOKEN_URL = "https://platform.claude.com/v1/oauth/token"

class _ProgramsList(list):
    def __init__(self):
        self._built = False

    def _ensure(self):
        if not self._built:
            self._built = True
            from .programs import all_dicts
            self.extend(all_dicts())

    def __iter__(self):
        self._ensure()
        return super().__iter__()

    def __getitem__(self, key):
        self._ensure()
        return super().__getitem__(key)

    def __len__(self):
        self._ensure()
        return super().__len__()

    def __bool__(self):
        self._ensure()
        return super().__bool__()

PROGRAMS = _ProgramsList()


def get_programs():
    return list(PROGRAMS)

DEFAULT_CONFIG = {
    "accounts": [],
    "auto_backup": True,
    "custom_skill_roots": [],
}


def provider_color(provider):
    return {"anthropic": "#d97757", "openai": "#10a37f", "gemini": "#4285f4",
            "mistral": "#ff7000", "ollama": "#000", "deepseek": "#4d6bfe",
            "openrouter": "#6c63ff", "xai": "#1d1d1f", "groq": "#f55036"}.get(provider, "#6b7280")


def detect_provider(url):
    if not url: return "openai"
    u = url.lower()
    for kw, p in [("z.ai", "anthropic"), ("anthropic", "anthropic"), ("bigmodel", "anthropic"),
                  ("openrouter", "openrouter"), ("deepseek", "deepseek"), ("mistral", "mistral"),
                  ("groq", "groq"), ("xai", "xai"), ("gemini", "gemini"), ("ollama", "ollama"),
                  ("localhost:11434", "ollama")]:
        if kw in u: return p
    return "openai"


def decode_jwt(token):
    import json, base64
    try:
        parts = token.split(".")
        if len(parts) < 2: return {}
        payload = parts[1]
        payload += "=" * (4 - len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except: return {}


def expand_path(p):
    import os
    return Path(os.path.expandvars(os.path.expanduser(str(p)))).resolve()
