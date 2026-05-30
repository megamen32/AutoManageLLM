"""Claude Desktop program — OAuth credentials, token refresh, config."""
import json, time, uuid
from pathlib import Path
from ..settings import (CLAUDE_DESKTOP_CFG, CLAUDE_DESKTOP_SKILLS,
                         ANTHROPIC_CREDENTIALS_DIR, ANTHROPIC_ACTIVE_CONFIG,
                         ANTHROPIC_CONFIGS_DIR, decode_jwt)


class ClaudeDesktopProgram:
    id = "claude-desktop"
    name = "Claude Desktop"
    letter = "D"
    config_path = CLAUDE_DESKTOP_CFG
    config_type = "json"
    skills_dir = CLAUDE_DESKTOP_SKILLS
    mcp_key = "mcpServers"

    def read_config(self) -> dict:
        if not CLAUDE_DESKTOP_CFG.exists(): return {}
        try: return json.loads(CLAUDE_DESKTOP_CFG.read_text())
        except: return {}

    def write_config(self, data: dict):
        CLAUDE_DESKTOP_CFG.parent.mkdir(parents=True, exist_ok=True)
        CLAUDE_DESKTOP_CFG.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def extra_files(self):
        return [{"name": "credentials/", "path": str(ANTHROPIC_CREDENTIALS_DIR), "desc": "OAuth tokens"},
                {"name": "configs/", "path": str(ANTHROPIC_CONFIGS_DIR), "desc": "Active config"}]

    def import_accounts(self, accounts, existing_keys, existing_urls):
        imported = []
        if not ANTHROPIC_CREDENTIALS_DIR.exists():
            return imported
        for f in sorted(ANTHROPIC_CREDENTIALS_DIR.glob("*.json")):
            try:
                data = json.loads(f.read_text())
                access_token = data.get("access_token", "")
                if not access_token: continue
                claims = decode_jwt(data.get("id_token", access_token))
                email = claims.get("email", "")
                exp = data.get("expires_at", 0) or claims.get("exp", 0)
                name_str = f"Claude Desktop ({email or f.stem})"
                existing = next((a for a in accounts if a.get("name") == name_str), None)
                if existing:
                    old_exp = existing.get("claude_oauth_expires_at", 0)
                    if exp > old_exp:
                        existing["claude_oauth_expires_at"] = exp
                        existing["claude_oauth_expires_in"] = max(0, exp - time.time())
                        existing["claude_oauth_has_refresh"] = bool(data.get("refresh_token", ""))
                        existing["source_path"] = str(f)
                        existing["claude_oauth_email"] = email or existing.get("claude_oauth_email", "")
                        imported.append(f"{name_str} (token updated)")
                    continue
                accounts.append({
                    "id": uuid.uuid4().hex[:8], "name": name_str,
                    "provider": "anthropic", "api_key": "", "base_url": "", "model": "",
                    "claude_oauth_cred": f.stem, "claude_oauth_email": email,
                    "claude_oauth_expires_at": exp,
                    "claude_oauth_expires_in": max(0, exp - time.time()) if exp else 0,
                    "claude_oauth_has_refresh": bool(data.get("refresh_token", "")),
                    "source_path": str(f),
                })
                imported.append(name_str)
            except Exception: pass
        return imported

    def apply_account(self, acc, current_config=None):
        return False, f"claude-desktop: managed by Claude Desktop app"

    def detect_active(self, accounts):
        if not ANTHROPIC_ACTIVE_CONFIG.exists(): return None
        active_name = ANTHROPIC_ACTIVE_CONFIG.read_text().strip()
        best, best_score = None, 0
        for acc in accounts:
            if acc.get("claude_oauth_cred") == active_name: score = 3
            elif acc.get("claude_oauth_cred"): score = 1
            else: continue
            if score > best_score: best_score = score; best = acc
        return best["id"] if best and best_score >= 2 else None

    def fetch_usage(self, acc):
        cred_name = acc.get("claude_oauth_cred", "")
        expires_in = acc.get("claude_oauth_expires_in", 0)
        has_refresh = acc.get("claude_oauth_has_refresh", False)
        email = acc.get("claude_oauth_email", "")
        if ANTHROPIC_CREDENTIALS_DIR.exists() and cred_name:
            cred_file = ANTHROPIC_CREDENTIALS_DIR / f"{cred_name}.json"
            if cred_file.exists():
                try:
                    cred_data = json.loads(cred_file.read_text())
                    raw_exp = cred_data.get("expires_at", 0) or 0
                    expires_in = max(0, raw_exp - time.time())
                    has_refresh = bool(cred_data.get("refresh_token", ""))
                    if not email:
                        id_token = cred_data.get("id_token", "")
                        claims = decode_jwt(id_token) if id_token else {}
                        email = claims.get("email", "")
                except Exception: pass
        total_secs = 86400
        if expires_in > 0:
            used_pct = round(max(0, min(100, (1 - expires_in / total_secs) * 100)), 1)
        else:
            used_pct = 100 if expires_in == 0 else None
        return {
            "type": "claude-desktop", "used_pct": used_pct,
            "email": email, "expires_in_seconds": expires_in,
            "expires_in_hours": round(expires_in / 3600, 1) if expires_in > 0 else 0,
            "has_refresh": has_refresh,
            "windows": [{"label": "token", "used_pct": used_pct,
                         "remaining_pct": round(100 - used_pct, 1) if used_pct is not None else None}],
        }
