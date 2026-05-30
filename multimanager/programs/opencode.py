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
    multi_provider = True

    def extra_files(self):
        return []

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
            if key and key[:20] in existing_keys: continue
            if url and url.rstrip("/") in existing_urls: continue
            prov_type = detect_provider(url) if url else "openai"
            accounts.append({
                "id": uuid.uuid4().hex[:8], "name": f"OpenCode ({pname})",
                "provider": prov_type, "api_key": key, "base_url": url, "model": "",
                "source_path": str(OPENCODE_CFG),
                "opencode_provider_id": pname,
            })
            imported.append(f"OpenCode ({pname})")
        return imported

    def apply_account(self, acc, current_config=None):
        if current_config is None: current_config = self.read_config()
        oc = dict(current_config)
        prov = oc.setdefault("provider", {})
        base_url = acc.get("base_url", "")
        api_key = acc.get("api_key", "")
        prov_id = acc.get("opencode_provider_id") or self._make_provider_id(acc)
        entry = prov.setdefault(prov_id, {})
        opts = entry.setdefault("options", {})
        if api_key: opts["apiKey"] = api_key
        if base_url: opts["baseUrl"] = base_url
        self.write_config(oc)
        return True, f"OpenCode: {prov_id}"

    def remove_account(self, prov_id):
        oc = self.read_config()
        prov = oc.get("provider", {})
        if prov_id in prov:
            del prov[prov_id]
            self.write_config(oc)
            return True, f"Removed {prov_id} from OpenCode"
        return False, f"Provider {prov_id} not found"

    def detect_active(self, accounts):
        oc = self.read_config()
        for pname, pdata in (oc.get("provider") or {}).items():
            if not isinstance(pdata, dict): continue
            opts = pdata.get("options", {})
            key, url = opts.get("apiKey", ""), opts.get("baseUrl", "")
            if not key: continue
            best, best_score = None, 0
            for acc in accounts:
                if acc.get("opencode_provider_id") == pname:
                    best, best_score = acc, 6
                    break
                score = 0
                if acc.get("api_key") and acc["api_key"][:20] == key[:20]: score += 3
                if acc.get("base_url") and url and acc["base_url"] in url: score += 2
                if score > best_score: best_score = score; best = acc
            if best and best_score >= 2: return best["id"]
        return None

    def detect_all_active(self, accounts):
        oc = self.read_config()
        provider_names = set((oc.get("provider") or {}).keys())
        result = []
        for acc in accounts:
            pid = acc.get("opencode_provider_id", "")
            if pid in provider_names:
                result.append(acc["id"])
                continue
            key = acc.get("api_key", "")
            if not key: continue
            for pname, pdata in (oc.get("provider") or {}).items():
                if not isinstance(pdata, dict): continue
                opts = pdata.get("options", {})
                if opts.get("apiKey", "")[:20] == key[:20]:
                    result.append(acc["id"])
                    break
        return result

    def _make_provider_id(self, acc):
        base = acc.get("name", "provider").lower().replace(" ", "-").replace("(", "").replace(")", "")
        pid = base
        n = 1
        while pid != base or n > 1:
            pid = f"{base}-{n}"
            n += 1
        return pid

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
