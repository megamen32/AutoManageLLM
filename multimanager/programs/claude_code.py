"""Claude Code program — settings.json, env vars, API keys, Anthropic usage."""
import json, uuid
from pathlib import Path
from ..settings import CC_SETTINGS, decode_jwt, detect_provider
from .. import history


class ClaudeCodeProgram:
    id = "claude-code"
    name = "Claude Code"
    letter = "C"
    config_path = CC_SETTINGS
    config_type = "json"
    skills_dir = Path.home() / ".claude" / "skills"
    mcp_key = "mcpServers"

    def extra_files(self):
        return []

    def read_config(self) -> dict:
        if not CC_SETTINGS.exists(): return {}
        try: return json.loads(CC_SETTINGS.read_text())
        except: return {}

    def write_config(self, data: dict):
        history.save_current(CC_SETTINGS)
        CC_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        CC_SETTINGS.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def import_accounts(self, accounts, existing_keys, existing_urls):
        imported = []
        cc = self.read_config()
        env = cc.get("env", {})
        cc_url = env.get("ANTHROPIC_BASE_URL", "")
        cc_key = env.get("ANTHROPIC_AUTH_TOKEN", "") or env.get("ANTHROPIC_API_KEY", "")
        cc_model = cc.get("model", "")
        if not cc_key or cc_key[:20] in existing_keys:
            return imported
        name = "Z.AI (GLM)" if "z.ai" in (cc_url or "") else "Claude Code"
        accounts.append({
            "id": uuid.uuid4().hex[:8], "name": name, "provider": "anthropic",
            "api_key": cc_key, "base_url": cc_url, "model": cc_model or "sonnet",
            "source_path": str(CC_SETTINGS), "claude_overrides": {
                k.replace("ANTHROPIC_DEFAULT_", "").replace("_MODEL", "").lower(): v
                for k, v in env.items()
                if k.startswith("ANTHROPIC_DEFAULT_") and k.endswith("_MODEL")
            },
        })
        imported.append(name)
        return imported

    def apply_account(self, acc, current_config=None):
        if current_config is None: current_config = self.read_config()
        cc = dict(current_config)
        env = cc.setdefault("env", {})
        for k in ["ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY"]:
            env.pop(k, None)
        base_url = acc.get("base_url", "")
        api_key = acc.get("api_key", "")
        if base_url:
            env["ANTHROPIC_BASE_URL"] = base_url
            env["ANTHROPIC_AUTH_TOKEN"] = api_key
        elif api_key:
            env["ANTHROPIC_API_KEY"] = api_key
        model = acc.get("model", "")
        if model: cc["model"] = model
        if acc.get("claude_overrides"):
            co = acc["claude_overrides"]
            for key, env_key in [("sonnet", "ANTHROPIC_DEFAULT_SONNET_MODEL"),
                                   ("opus", "ANTHROPIC_DEFAULT_OPUS_MODEL"),
                                   ("haiku", "ANTHROPIC_DEFAULT_HAIKU_MODEL")]:
                if co.get(key): env[env_key] = co[key]
        self.write_config(cc)
        return True, f"Claude Code: {acc['name']}"

    def detect_active(self, accounts):
        cc = self.read_config()
        env = cc.get("env", {})
        cc_url = env.get("ANTHROPIC_BASE_URL", "")
        cc_key = env.get("ANTHROPIC_AUTH_TOKEN", "") or env.get("ANTHROPIC_API_KEY", "")
        cc_model = cc.get("model", "")
        best, best_score = None, 0
        for acc in accounts:
            score = 0
            if acc.get("base_url") and cc_url and acc["base_url"].rstrip("/") == cc_url.rstrip("/"): score += 3
            if acc.get("api_key") and cc_key and acc["api_key"][:20] == cc_key[:20]: score += 3
            if acc.get("model") and cc_model and acc["model"] == cc_model: score += 1
            if score > best_score: best_score = score; best = acc
        return best["id"] if best and best_score >= 2 else None

    def fetch_usage(self, acc):
        import urllib.request, urllib.error
        api_key = acc.get("api_key", "")
        base_url = acc.get("base_url", "")
        if not api_key: return {}
        result = {"type": "claude-code"}
        if "z.ai" in (base_url or "").lower() or "bigmodel" in (base_url or "").lower():
            try:
                url = base_url.rstrip("/")
                req = urllib.request.Request(url + "/v1/dashboard/billing/usage", headers={
                    "Authorization": f"Bearer {api_key}", "Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    result["data"] = json.loads(r.read())
            except Exception:
                result["note"] = "quota via MCP"
            return result
        try:
            req = urllib.request.Request("https://api.anthropic.com/v1/organizations/me", headers={
                "x-api-key": api_key, "anthropic-version": "2023-06-01", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            result.update({"org_id": data.get("id", ""), "name": data.get("name", "")})
            for ep in ["/v1/credits", "/v1/usage/tokens"]:
                try:
                    req2 = urllib.request.Request(f"https://api.anthropic.com{ep}", headers={
                        "x-api-key": api_key, "anthropic-version": "2023-06-01", "Accept": "application/json"})
                    with urllib.request.urlopen(req2, timeout=10) as r2:
                        result[ep.split("/")[-1]] = json.loads(r2.read())
                except Exception: pass
        except urllib.error.HTTPError as e:
            result["error"] = f"HTTP {e.code}"
        except Exception as e:
            result["error"] = str(e)[:80]
        return result
