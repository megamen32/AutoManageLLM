"""OpenCode program — opencode.json, provider options."""
import json, uuid
from pathlib import Path
from ..settings import OPENCODE_CFG, detect_provider
from .. import history


class OpenCodeProgram:
    id = "opencode"
    name = "OpenCode"
    letter = "O"
    config_path = OPENCODE_CFG
    config_type = "json"
    skills_dir = Path.home() / ".config" / "opencode" / "skills"
    mcp_key = "mcpServers"

    def read_config(self) -> dict:
        if not OPENCODE_CFG.exists(): return {}
        try: return json.loads(OPENCODE_CFG.read_text())
        except: return {}

    def write_config(self, data: dict):
        history.save_current(OPENCODE_CFG)
        OPENCODE_CFG.parent.mkdir(parents=True, exist_ok=True)
        OPENCODE_CFG.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def import_accounts(self, accounts, existing_keys, existing_urls):
        imported = []
        oc = self.read_config()
        for pname, pdata in (oc.get("provider") or {}).items():
            if not isinstance(pdata, dict): continue
            opts = pdata.get("options", {})
            key, url = opts.get("apiKey", ""), opts.get("baseUrl", "")
            if not key or key[:20] in existing_keys or url.rstrip("/") in existing_urls: continue
            accounts.append({
                "id": uuid.uuid4().hex[:8], "name": f"OpenCode ({pname})",
                "provider": "openai", "api_key": key, "base_url": url, "model": "",
                "source_path": str(OPENCODE_CFG),
            })
            imported.append(f"OpenCode ({pname})")
        return imported

    def apply_account(self, acc, current_config=None):
        if current_config is None: current_config = self.read_config()
        oc = dict(current_config)
        prov = oc.setdefault("provider", {})
        base_url = acc.get("base_url", "")
        api_key = acc.get("api_key", "")
        if "z.ai" in base_url or "zai" in acc.get("provider", ""):
            zai = prov.setdefault("zai-coding-plan", {})
            opts = zai.setdefault("options", {})
            if api_key: opts["apiKey"] = api_key
            if base_url: opts["baseUrl"] = base_url
        self.write_config(oc)
        return True, f"OpenCode: {acc['name']}"

    def detect_active(self, accounts):
        oc = self.read_config()
        for pname, pdata in (oc.get("provider") or {}).items():
            if not isinstance(pdata, dict): continue
            opts = pdata.get("options", {})
            key, url = opts.get("apiKey", ""), opts.get("baseUrl", "")
            if not key: continue
            best, best_score = None, 0
            for acc in accounts:
                score = 0
                if acc.get("api_key") and acc["api_key"][:20] == key[:20]: score += 3
                if acc.get("base_url") and url and acc["base_url"] in url: score += 2
                if score > best_score: best_score = score; best = acc
            if best and best_score >= 2: return best["id"]
        return None

    def fetch_usage(self, acc):
        import urllib.request, urllib.error
        base_url = acc.get("base_url", "")
        api_key = acc.get("api_key", "")
        if ("z.ai" in (base_url or "").lower() or "bigmodel" in (base_url or "").lower()) and api_key:
            try:
                req = urllib.request.Request("https://open.bigmodel.cn/api/llm/balance", headers={
                    "Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    return {"type": "zai", "data": json.loads(r.read())}
            except Exception:
                return {"type": "zai", "note": "quota via MCP"}
        return {}
