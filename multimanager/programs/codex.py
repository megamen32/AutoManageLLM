"""Codex program — config.toml, auth.json, ChatGPT OAuth, usage."""
import json, time, uuid
from pathlib import Path
from ..settings import CX_CONFIG, CX_AUTH, decode_jwt
from .. import history
from ..toml_utils import parse_toml_simple, write_toml_simple


class CodexProgram:
    id = "codex"
    name = "Codex"
    letter = "X"
    config_path = CX_CONFIG
    config_type = "toml"
    skills_dir = Path.home() / ".codex" / "skills"
    mcp_key = "mcp_servers"

    def read_config(self) -> dict:
        if not CX_CONFIG.exists(): return {}
        return parse_toml_simple(CX_CONFIG.read_text())

    def write_config(self, data: dict):
        history.save_current(CX_CONFIG)
        order = ["model", "model_provider", "model_reasoning_effort", "personality",
                 "approval_policy", "sandbox_mode", "notify", "openai_base_url"]
        CX_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CX_CONFIG.write_text(write_toml_simple(data, order))

    def extra_files(self):
        return [{"name": "auth.json", "path": str(CX_AUTH), "desc": "OAuth tokens"}]

    def import_accounts(self, accounts, existing_keys, existing_urls):
        imported = []
        cx = self.read_config()
        cx_model = cx.get("model", "")
        cx_auth_data = {}
        if CX_AUTH.exists():
            try: cx_auth_data = json.loads(CX_AUTH.read_text())
            except: pass
        tokens = cx_auth_data.get("tokens", {})
        cx_key = cx_auth_data.get("OPENAI_API_KEY", tokens.get("access_token", ""))
        email, plan, token_exp = "", "", 0
        if tokens.get("access_token"):
            claims = decode_jwt(tokens["access_token"])
            profile = claims.get("https://api.openai.com/profile", {})
            oa = claims.get("https://api.openai.com/auth", {})
            email = profile.get("email", "")
            plan = oa.get("chatgpt_plan_type", "")
            token_exp = claims.get("exp", 0)

        has_codex = any(a.get("api_key") == "" and a.get("provider") == "openai"
                        and "codex_provider" in a for a in accounts)

        if not cx_key:
            return imported

        if has_codex:
            existing = next((a for a in accounts if "codex_provider" in a), None)
            if existing and token_exp:
                old_exp = existing.get("_codex_token_exp", 0)
                if token_exp > old_exp:
                    existing["_codex_token_exp"] = token_exp
                    existing["source_path"] = str(CX_AUTH)
                    existing["email"] = email or existing.get("email", "")
                    existing["plan"] = plan or existing.get("plan", "")
                    imported.append(f"{existing['name']} (token updated)")
            return imported

        if cx_key[:20] in existing_keys:
            return imported

        mps = cx.get("model_providers", {})
        base_url, codex_provider = "", cx.get("model_provider", "")
        if codex_provider and isinstance(mps, dict):
            mp = mps.get(codex_provider, {})
            if isinstance(mp, dict): base_url = mp.get("base_url", "")

        name = f"Codex ({cx_model or 'default'})"
        accounts.append({
            "id": uuid.uuid4().hex[:8], "name": name, "provider": "openai",
            "api_key": "", "base_url": base_url, "model": cx_model,
            "email": email, "plan": plan, "codex_provider": codex_provider,
            "source_path": str(CX_AUTH), "_codex_token_exp": token_exp,
        })
        imported.append(name)
        return imported

    def apply_account(self, acc, current_config=None):
        if current_config is None:
            current_config = self.read_config()
        cx = dict(current_config)
        model = acc.get("model", "")
        base_url = acc.get("base_url", "")
        codex_prov = acc.get("codex_provider", "")
        if model: cx["model"] = model
        if base_url and codex_prov:
            cx["model_provider"] = codex_prov
            mps = cx.setdefault("model_providers", {})
            mps[codex_prov] = {"name": acc.get("name", codex_prov), "base_url": base_url}
            env_key_name = codex_prov.upper().replace("-", "_") + "_API_KEY"
            mps[codex_prov]["env_key"] = env_key_name
        elif base_url:
            cx["openai_base_url"] = base_url
        self.write_config(cx)
        return True, f"Codex: {acc['name']}"

    def detect_active(self, accounts):
        cx = self.read_config()
        cx_model = cx.get("model", "")
        cx_provider = cx.get("model_provider", "")
        mps = cx.get("model_providers", {})
        cx_base_url = ""
        if cx_provider and isinstance(mps, dict):
            mp_data = mps.get(cx_provider, {})
            if isinstance(mp_data, dict): cx_base_url = mp_data.get("base_url", "")
        best, best_score = None, 0
        for acc in accounts:
            score = 0
            if acc.get("base_url") and cx_base_url and acc["base_url"].rstrip("/") == cx_base_url.rstrip("/"): score += 3
            if acc.get("model") and cx_model and acc["model"] == cx_model: score += 1
            if acc.get("codex_provider") and acc["codex_provider"] == cx_provider: score += 3
            if score > best_score: best_score = score; best = acc
        return best["id"] if best and best_score >= 1 else None

    def fetch_usage(self, acc):
        import urllib.request, urllib.error
        from .base import get as prog_get
        if not CX_AUTH.exists(): return {}
        try:
            auth = json.loads(CX_AUTH.read_text())
            tokens = auth.get("tokens", {})
            at, aid = tokens.get("access_token", ""), tokens.get("account_id", "")
        except: return {}
        if not at: return {"type": "codex", "error": "no token"}
        try:
            req = urllib.request.Request("https://chatgpt.com/backend-api/wham/usage", headers={
                "Authorization": f"Bearer {at}", "ChatGPT-Account-Id": aid,
                "User-Agent": "MultiManager", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=12) as r:
                data = json.loads(r.read())
        except urllib.error.HTTPError as e:
            return {"type": "codex", "error": f"HTTP {e.code}"}
        except Exception as e:
            return {"type": "codex", "error": str(e)[:80]}
        rl = data.get("rate_limit", {})
        pw, sw = rl.get("primary_window", {}), rl.get("secondary_window", {})
        windows = []
        for w, key in [(pw, "5h"), (sw, "7d")]:
            used = w.get("used_percent")
            if used is not None:
                ws = w.get("limit_window_seconds", 0)
                if key == "7d" and ws >= 86400: lbl = f"{ws//86400}d"
                elif ws: lbl = f"{ws//3600}h"
                else: lbl = key
                windows.append({"label": lbl, "used_pct": round(used, 1),
                                "remaining_pct": round(100 - used, 1), "reset_at": w.get("reset_at")})
        return {"type": "codex", "windows": windows, "allowed": rl.get("allowed"),
                "limit_reached": rl.get("limit_reached")}
