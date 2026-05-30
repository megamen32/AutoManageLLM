"""Cline program — mcp_settings.json, env-based API keys."""
import json, uuid
from pathlib import Path
from ..settings import CLINE_CFG


class ClineProgram:
    id = "cline"
    name = "Cline"
    letter = "L"
    config_path = CLINE_CFG
    config_type = "json"
    skills_dir = Path.home() / ".cline" / "skills"
    mcp_key = "mcpServers"

    def _extract_key(self, data):
        seen, api_key, base_url = set(), "", ""
        for sdata in (data.get("mcpServers") or {}).values():
            if isinstance(sdata, dict):
                env = sdata.get("env", {})
                if isinstance(env, dict):
                    for k, v in env.items():
                        if v and isinstance(v, str) and len(v) > 10 and "API_KEY" in k.upper():
                            if v[:20] not in seen: seen.add(v[:20]); api_key = v; break
        for k, v in (data.get("env") or {}).items():
            if v and isinstance(v, str) and len(v) > 10:
                if v[:20] not in seen: seen.add(v[:20]); api_key = v; break
        return api_key, base_url

    def read_config(self) -> dict:
        if not CLINE_CFG.exists(): return {}
        try: return json.loads(CLINE_CFG.read_text())
        except: return {}

    def write_config(self, data: dict):
        CLINE_CFG.parent.mkdir(parents=True, exist_ok=True)
        CLINE_CFG.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def import_accounts(self, accounts, existing_keys, existing_urls):
        imported = []
        data = self.read_config()
        if not data: return imported
        api_key, base_url = self._extract_key(data)
        if not api_key or api_key[:20] in existing_keys: return imported
        accounts.append({
            "id": uuid.uuid4().hex[:8], "name": f"Cline ({api_key[:8]}...)",
            "provider": "openai" if api_key.startswith("sk-") else "openai",
            "api_key": api_key, "base_url": base_url, "model": "",
            "source_path": str(CLINE_CFG),
        })
        imported.append(f"Cline ({api_key[:8]}...)")
        return imported

    def apply_account(self, acc, current_config=None):
        return False, "cline: edit mcp_settings.json manually"

    def detect_active(self, accounts):
        data = self.read_config()
        if not data: return None
        api_key, _ = self._extract_key(data)
        if not api_key: return None
        best, best_score = None, 0
        for acc in accounts:
            if acc.get("api_key") and acc["api_key"][:20] == api_key[:20]: score = 3
            else: continue
            if score > best_score: best_score = score; best = acc
        return best["id"] if best and best_score >= 2 else None

    def fetch_usage(self, acc):
        return {}
