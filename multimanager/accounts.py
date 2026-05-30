"""Account CRUD, import from programs, detect active, apply."""
import json, uuid, shutil, os, time
from pathlib import Path
from .settings import (
    CC_SETTINGS, CX_CONFIG, CX_AUTH, OPENCODE_CFG, CONFIG_DIR, MASTER_DIR,
    PROGRAMS, decode_jwt, expand_path, detect_provider,
    ANTHROPIC_CREDENTIALS_DIR, ANTHROPIC_CONFIGS_DIR, ANTHROPIC_ACTIVE_CONFIG,
)
from .config import ensure_defaults, save_config, do_backup
from .toml_utils import parse_toml_simple, write_toml_simple
from . import history


def _read_json(path):
    if not Path(path).exists(): return {}
    try: return json.loads(Path(path).read_text())
    except: return {}

def _write_json(path, data):
    history.save_current(path)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2))

def _read_cc(): return _read_json(CC_SETTINGS)
def _write_cc(d): _write_json(CC_SETTINGS, d)

def _read_cx():
    if not CX_CONFIG.exists(): return {}
    return parse_toml_simple(CX_CONFIG.read_text())
def _write_cx(data):
    history.save_current(CX_CONFIG)
    order = ["model", "model_provider", "model_reasoning_effort", "personality",
             "approval_policy", "sandbox_mode", "notify", "openai_base_url"]
    CX_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CX_CONFIG.write_text(write_toml_simple(data, order))


def import_from_claude_desktop(cfg, accounts, existing_keys, existing_urls):
    """Import Claude Desktop OAuth credentials as accounts."""
    imported = []
    if not ANTHROPIC_CREDENTIALS_DIR.exists():
        return imported
    for f in sorted(ANTHROPIC_CREDENTIALS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            access_token = data.get("access_token", "")
            if not access_token:
                continue
            claims = decode_jwt(data.get("id_token", access_token))
            email = claims.get("email", "")
            exp = data.get("expires_at", 0) or claims.get("exp", 0)
            name = f.stem
            name_str = f"Claude Desktop ({email or name})"
            if any(a.get("name") == name_str for a in accounts):
                continue
            accounts.append({
                "id": uuid.uuid4().hex[:8], "name": name_str,
                "provider": "anthropic", "api_key": "", "base_url": "",
                "model": "", "claude_oauth_cred": name,
                "claude_oauth_email": email,
                "claude_oauth_expires_at": exp,
                "claude_oauth_expires_in": max(0, exp - time.time()) if exp else 0,
                "claude_oauth_has_refresh": bool(data.get("refresh_token", "")),
                "source_path": str(f),
            })
            imported.append(name_str)
        except Exception:
            pass
    return imported


def import_from_cline_roo(cfg, accounts, existing_keys, existing_urls):
    """Import Cline / Roo Code configs as accounts."""
    imported = []
    for prog in ("cline", "roo-code"):
        cp = next((p for p in PROGRAMS if p["id"] == prog), None)
        if not cp: continue
        p = Path(cp["config_path"])
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text())
        except Exception:
            continue
        # Extract API keys from MCP settings (apiKey in any env field)
        seen = set()
        api_key = ""
        base_url = ""
        # Check top-level mcpServers
        mcp_servers = data.get("mcpServers", {}) if isinstance(data, dict) else {}
        for sname, sdata in mcp_servers.items():
            if isinstance(sdata, dict):
                env = sdata.get("env", {}) if isinstance(sdata.get("env"), dict) else {}
                for k, v in env.items():
                    if v and isinstance(v, str) and len(v) > 10 and any(prefix in k.upper() for prefix in ("API_KEY", "AUTH_TOKEN")):
                        if v[:20] not in seen:
                            seen.add(v[:20])
                            api_key = v
                            break
        # Also check top-level env
        tenv = data.get("env", {}) if isinstance(data, dict) else {}
        for k, v in tenv.items():
            if v and isinstance(v, str) and len(v) > 10 and any(prefix in k.upper() for prefix in ("API_KEY", "AUTH_TOKEN")):
                if v[:20] not in seen:
                    seen.add(v[:20])
                    api_key = v
                    break
        # Fallback: check settings sub-dir
        settings_dir = p.parent / "settings"
        if not api_key and settings_dir.exists():
            for sf in sorted(settings_dir.glob("*.json")):
                try:
                    sd = json.loads(sf.read_text())
                    for k in ("apiKey", "api_key"):
                        if sd.get(k):
                            api_key = sd[k]
                            break
                    for sk, sv in sd.get("env", {}).items():
                        if sv and isinstance(sv, str) and len(sv) > 10:
                            api_key = sv
                            break
                except Exception:
                    pass
                if api_key:
                    break
        if not api_key:
            continue
        if api_key[:20] in existing_keys:
            continue
        name_str = f"{cp['name']} ({api_key[:8]}...)"
        accounts.append({
            "id": uuid.uuid4().hex[:8], "name": name_str,
            "provider": "openai" if api_key.startswith("sk-") else (
                "anthropic" if api_key.startswith("sk-ant-") else "openai"
            ),
            "api_key": api_key, "base_url": base_url, "model": "",
            "source_path": str(p),
        })
        imported.append(name_str)
    return imported


def import_accounts():
    cfg = ensure_defaults()
    accounts = cfg.setdefault("accounts", [])
    imported = []
    existing_keys = {a.get("api_key", "")[:20] for a in accounts}
    existing_urls = {a.get("base_url", "").rstrip("/") for a in accounts}

    # Claude Code settings.json
    cc = _read_cc()
    env = cc.get("env", {})
    cc_url = env.get("ANTHROPIC_BASE_URL", "")
    cc_key = (env.get("ANTHROPIC_AUTH_TOKEN", "") or env.get("ANTHROPIC_API_KEY", ""))
    cc_model = cc.get("model", "")
    cc_overrides = {}
    for k in ("ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL"):
        if env.get(k): cc_overrides[k.replace("ANTHROPIC_DEFAULT_", "").replace("_MODEL", "").lower()] = env[k]
    if cc_key and cc_key[:20] not in existing_keys:
        name = "Z.AI (GLM)" if "z.ai" in (cc_url or "") else "Claude Code"
        accounts.append({
            "id": uuid.uuid4().hex[:8], "name": name, "provider": "anthropic",
            "api_key": cc_key, "base_url": cc_url, "model": cc_model or "sonnet",
            "claude_overrides": cc_overrides,
            "source_path": str(CC_SETTINGS),
        })
        imported.append(name)

    # Codex config.toml + auth.json
    cx = _read_cx()
    cx_model = cx.get("model", "")
    cx_auth_data = _read_json(CX_AUTH)
    tokens = cx_auth_data.get("tokens", {})
    cx_key = cx_auth_data.get("OPENAI_API_KEY", tokens.get("access_token", ""))
    email = ""
    plan = ""
    if tokens.get("access_token"):
        claims = decode_jwt(tokens["access_token"])
        profile = claims.get("https://api.openai.com/profile", {})
        oa = claims.get("https://api.openai.com/auth", {})
        email = profile.get("email", "")
        plan = oa.get("chatgpt_plan_type", "")
    cx_account_id = ""
    if tokens.get("access_token"):
        cx_account_id = decode_jwt(tokens["access_token"]).get("https://api.openai.com/auth", {}).get("user_id", "")
    if cx_key:
        existing_codex = [a for a in accounts if a.get("api_key") == "" and a.get("provider") == "openai" and a.get("codex_provider") is not None]
        matched = None
        if cx_account_id:
            matched = next((a for a in existing_codex if a.get("_codex_account_id") == cx_account_id), None)
        if not matched and not cx_account_id and email:
            matched = next((a for a in existing_codex if a.get("email") == email and not a.get("_codex_account_id")), None)
        if matched:
            changed = False
            if plan and matched.get("plan") != plan:
                matched["plan"] = plan
                changed = True
            if cx_model and matched.get("model") != cx_model:
                matched["model"] = cx_model
                changed = True
            if email and matched.get("email") != email:
                matched["email"] = email
                changed = True
            if cx_account_id:
                matched["_codex_account_id"] = cx_account_id
            if changed:
                imported.append(matched["name"] + " (updated)")
        else:
            mps = cx.get("model_providers", {})
            base_url = ""
            codex_provider = cx.get("model_provider", "")
            if codex_provider and isinstance(mps, dict):
                mp = mps.get(codex_provider, {})
                if isinstance(mp, dict): base_url = mp.get("base_url", "")
            name = f"Codex ({email or cx_model or 'default'})"
            accounts.append({
                "id": uuid.uuid4().hex[:8], "name": name, "provider": "openai",
                "api_key": "", "base_url": base_url, "model": cx_model,
                "email": email, "plan": plan, "codex_provider": codex_provider,
                "source_path": str(CX_AUTH),
            })
            if cx_account_id:
                accounts[-1]["_codex_account_id"] = cx_account_id
            imported.append(name)

    # OpenCode config
    oc = _read_json(OPENCODE_CFG)
    for pname, pdata in (oc.get("provider") or {}).items():
        if isinstance(pdata, dict):
            opts = pdata.get("options", {})
            key = opts.get("apiKey", "")
            url = opts.get("baseUrl", "")
            if key and key[:20] in existing_keys: continue
            if url and url.rstrip("/") in existing_urls: continue
            prov_type = detect_provider(url) if url else "openai"
            n = f"OpenCode ({pname})"
            accounts.append({
                "id": uuid.uuid4().hex[:8], "name": n, "provider": prov_type,
                "api_key": key, "base_url": url, "model": "",
                "source_path": str(OPENCODE_CFG),
                "opencode_provider_id": pname,
            })
            imported.append(n)

    # Claude Desktop OAuth credentials
    imported += import_from_claude_desktop(cfg, accounts, existing_keys, existing_urls)

    # Cline / Roo Code configs
    imported += import_from_cline_roo(cfg, accounts, existing_keys, existing_urls)

    # Migration: fill missing fields on existing accounts
    migrated = False
    for a in accounts:
        if a.get("name", "").startswith("Codex") and not a.get("codex_provider"):
            a["codex_provider"] = cx.get("model_provider", "")
            migrated = True
        if not a.get("source_path"):
            if a.get("claude_oauth_cred"): a["source_path"] = str(ANTHROPIC_CREDENTIALS_DIR / (a["claude_oauth_cred"] + ".json"))
            elif a.get("codex_provider") is not None: a["source_path"] = str(CX_AUTH)
            elif a.get("claude_overrides"): a["source_path"] = str(CC_SETTINGS)
            migrated = True
    if migrated:
        save_config(cfg)

    save_config(cfg)
    return imported


def detect_active_accounts():
    result = {}
    accounts = ensure_defaults().get("accounts", [])

    # Claude Code
    cc = _read_cc()
    env = cc.get("env", {})
    cc_url = env.get("ANTHROPIC_BASE_URL", "")
    cc_key = env.get("ANTHROPIC_AUTH_TOKEN", "") or env.get("ANTHROPIC_API_KEY", "")
    cc_model = cc.get("model", "")
    best = None; best_score = 0
    for acc in accounts:
        score = 0
        a_url = acc.get("base_url", "")
        a_key = acc.get("api_key", "")
        a_model = acc.get("model", "")
        if a_url and cc_url and a_url.rstrip("/") == cc_url.rstrip("/"): score += 3
        if a_key and cc_key and (a_key == cc_key or a_key[:20] == cc_key[:20]): score += 3
        if a_model and cc_model and a_model == cc_model: score += 1
        if score > best_score: best_score = score; best = acc
    result["claude-code"] = best["id"] if best and best_score >= 2 else None

    # Codex
    cx = _read_cx()
    cx_model = cx.get("model", "")
    cx_provider = cx.get("model_provider", "")
    cx_base_url = ""
    mps = cx.get("model_providers", {})
    if cx_provider and isinstance(mps, dict):
        mp_data = mps.get(cx_provider, {})
        if isinstance(mp_data, dict):
            cx_base_url = mp_data.get("base_url", "")
    best = None; best_score = 0
    for acc in accounts:
        score = 0
        a_model = acc.get("model", "")
        a_url = acc.get("base_url", "")
        if a_url and cx_base_url and a_url.rstrip("/") == cx_base_url.rstrip("/"): score += 3
        if a_model and cx_model and a_model == cx_model: score += 1
        if acc.get("codex_provider") and acc["codex_provider"] == cx_provider: score += 3
        if score > best_score: best_score = score; best = acc
    result["codex"] = best["id"] if best and best_score >= 1 else None

    # OpenCode
    oc = _read_json(OPENCODE_CFG)
    ocp = oc.get("provider") or {}
    provider_names = set(ocp.keys())
    opencode_ids = []
    for acc in accounts:
        pid = acc.get("opencode_provider_id", "")
        if pid in provider_names:
            opencode_ids.append(acc["id"])
            continue
        key = acc.get("api_key", "")
        if not key: continue
        for pname, pdata in ocp.items():
            if not isinstance(pdata, dict): continue
            opts = pdata.get("options", {})
            if opts.get("apiKey", "")[:20] == key[:20]:
                opencode_ids.append(acc["id"])
                break
    result["opencode"] = opencode_ids

    # Claude Desktop
    if ANTHROPIC_ACTIVE_CONFIG.exists():
        active_name = ANTHROPIC_ACTIVE_CONFIG.read_text().strip()
        best = None; best_score = 0
        for acc in accounts:
            if acc.get("claude_oauth_cred") == active_name:
                score = 3
            elif acc.get("claude_oauth_cred"):
                score = 1
            else:
                continue
            if score > best_score: best_score = score; best = acc
        result["claude-desktop"] = best["id"] if best and best_score >= 2 else None

    # Cline / Roo Code — check if their configs use matching keys
    for prog_id in ("cline", "roo-code"):
        cp = next((p for p in PROGRAMS if p["id"] == prog_id), None)
        if not cp: continue
        p = Path(cp["config_path"])
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text())
        except Exception:
            continue
        # Find first key in the config
        config_key = ""
        mcp_servers = data.get("mcpServers", {}) if isinstance(data, dict) else {}
        for sdata in mcp_servers.values():
            if isinstance(sdata, dict):
                env = sdata.get("env", {}) if isinstance(sdata.get("env"), dict) else {}
                for v in env.values():
                    if v and isinstance(v, str) and len(v) > 10:
                        config_key = v
                        break
                if config_key:
                    break
        if not config_key:
            tenv = data.get("env", {}) if isinstance(data, dict) else {}
            for v in tenv.values():
                if v and isinstance(v, str) and len(v) > 10:
                    config_key = v
                    break
        if config_key:
            best = None; best_score = 0
            for acc in accounts:
                score = 0
                if acc.get("api_key") and config_key and acc["api_key"][:20] == config_key[:20]:
                    score = 3
                if score > best_score: best_score = score; best = acc
            result[prog_id] = best["id"] if best and best_score >= 2 else None

    return result


def _make_oc_provider_id(acc):
    base = acc.get("name", "provider").lower().replace(" ", "-").replace("(", "").replace(")", "")
    pid = base
    n = 1
    seen = set()
    while pid in seen or (n > 1 and pid == base):
        pid = f"{base}-{n}" if n > 1 else base
        n += 1
    return pid


def apply_account(acc_id, program_id):
    cfg = ensure_defaults()
    acc = next((a for a in cfg.get("accounts", []) if a["id"] == acc_id), None)
    if not acc: return False, "Account not found"
    do_backup(cfg)

    if program_id == "claude-code":
        cc = _read_cc()
        env = cc.setdefault("env", {})
        base_url = acc.get("base_url", "")
        api_key = acc.get("api_key", "")
        model = acc.get("model", "")
        for k in ["ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY"]:
            env.pop(k, None)
        if base_url:
            env["ANTHROPIC_BASE_URL"] = base_url
            env["ANTHROPIC_AUTH_TOKEN"] = api_key
        elif api_key:
            env["ANTHROPIC_API_KEY"] = api_key
        if model: cc["model"] = model
        if acc.get("claude_overrides"):
            co = acc["claude_overrides"]
            if co.get("sonnet"): env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = co["sonnet"]
            if co.get("opus"): env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = co["opus"]
            if co.get("haiku"): env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] = co["haiku"]
        _write_cc(cc)
        return True, f"Claude Code: {acc['name']}"

    elif program_id == "codex":
        cx = _read_cx()
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
        _write_cx(cx)
        return True, f"Codex: {acc['name']}"

    elif program_id == "opencode":
        oc = _read_json(OPENCODE_CFG)
        prov = oc.setdefault("provider", {})
        base_url = acc.get("base_url", "")
        api_key = acc.get("api_key", "")
        prov_id = acc.get("opencode_provider_id") or _make_oc_provider_id(acc)
        entry = prov.setdefault(prov_id, {})
        opts = entry.setdefault("options", {})
        if api_key: opts["apiKey"] = api_key
        if base_url: opts["baseUrl"] = base_url
        _write_json(OPENCODE_CFG, oc)
        return True, f"OpenCode: {prov_id}"

    return False, f"{program_id}: not implemented"


def remove_account_from_program(acc_id, program_id):
    cfg = ensure_defaults()
    acc = next((a for a in cfg.get("accounts", []) if a["id"] == acc_id), None)
    if not acc: return False, "Account not found"
    do_backup(cfg)

    if program_id == "opencode":
        oc = _read_json(OPENCODE_CFG)
        prov = oc.get("provider", {})
        prov_id = acc.get("opencode_provider_id", "")
        if prov_id in prov:
            del prov[prov_id]
            _write_json(OPENCODE_CFG, oc)
            return True, f"Removed {prov_id} from OpenCode"
        return False, f"Provider {prov_id} not found in OpenCode"

    return False, f"remove from {program_id}: not supported"
