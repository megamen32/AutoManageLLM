"""HTTP request handler — all API routes."""
import json, os, re, threading, time, uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path

from .settings import get_programs, provider_color, detect_provider, MASTER_SKILLS, MASTER_MCP, PROGRAMS
from .config import ensure_defaults, save_config, do_backup
from .accounts import import_accounts, detect_active_accounts, apply_account
from .usage import fetch_account_usage, _USAGE_CACHE
from .skills import scan_master_skills, scan_all_skill_dirs, sync_skill_to_programs, sync_all_skills, collect_skill_to_master, delete_skill_from_master
from .mcp_ import scan_master_mcp, save_master_mcp, scan_program_mcp, sync_mcp_to_programs, delete_mcp_from_program
from .usage import fetch_account_usage, _USAGE_CACHE
from . import history

_HERE = Path(__file__).parent


def _decode_diff_content(text, file_path=""):
    if not text or file_path.endswith(".toml"):
        return text
    try:
        data = json.loads(text)
    except Exception:
        return text
    changed = _walk_decode(data)
    if changed:
        return json.dumps(data, ensure_ascii=False, indent=2)
    return text


def _walk_decode(obj):
    changed = False
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if isinstance(v, str):
                decoded = _try_decode_value(v, k)
                if decoded != v:
                    obj[k + "_decoded"] = decoded
                    changed = True
            elif isinstance(v, (int, float)) and _is_ts_key(k):
                try:
                    ts = float(v)
                    if 1_000_000_000 <= ts <= 2_000_000_000:
                        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                        obj[k + "_decoded"] = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                        changed = True
                except Exception:
                    pass
            elif isinstance(v, (dict, list)):
                if _walk_decode(v):
                    changed = True
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, (dict, list)):
                if _walk_decode(v):
                    changed = True
    return changed


def _is_ts_key(k):
    return any(x in k.lower() for x in ("exp", "iat", "expires", "created_at", "updated_at", "timestamp", "time", "date", "_at"))


_UNIX_RE = re.compile(r'^\d{9,10}(\.\d+)?$')
_B64JWT_RE = re.compile(r'^eyJ[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+){2,}$')
_ISO_TS_RE = re.compile(r'^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}')


def _try_decode_value(val, key=""):
    if not isinstance(val, str):
        return val
    if _UNIX_RE.match(val.strip()):
        try:
            ts = float(val.strip())
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except Exception:
            pass
    if _ISO_TS_RE.match(val.strip()):
        return val
    if _B64JWT_RE.match(val.strip()) and val.strip().count('.') >= 2:
        try:
            parts = val.strip().split('.')
            if len(parts) >= 2:
                payload = parts[1]
                payload += '=' * (4 - len(payload) % 4)
                decoded_bytes = __import__('base64').urlsafe_b64decode(payload)
                decoded_json = json.loads(decoded_bytes)
                pretty = json.dumps(decoded_json, ensure_ascii=False, indent=2)
                return pretty
        except Exception:
            pass
    return val


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, s=200):
        d = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(s)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(d)))
        self.end_headers()
        self.wfile.write(d)

    def _html(self):
        html_path = _HERE / "templates" / "index.html"
        if html_path.exists():
            d = html_path.read_bytes()
        else:
            d = b"<html><body><h1>MultiManager</h1><p>Template not found.</p></body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(d)))
        self.end_headers()
        self.wfile.write(d)

    def _serve_static(self, name, mime):
        p = _HERE / "templates" / name
        if not p.exists():
            self.send_error(404); return
        d = p.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(d)))
        self.end_headers()
        self.wfile.write(d)

    def _err(self, msg, s=400):
        self._json({"error": msg}, s)

    def _body(self):
        n = int(self.headers.get("Content-Length", "0") or "0")
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/": self._html(); return
        if u.path == "/styles.css": self._serve_static("styles.css", "text/css; charset=utf-8"); return
        if u.path.startswith("/app.js"): self._serve_static("app.js", "application/javascript; charset=utf-8"); return
        if u.path == "/favicon.ico": self.send_error(204); return
        cfg = ensure_defaults()

        if u.path == "/api/accounts":
            accounts = cfg.get("accounts", [])
            active = detect_active_accounts()
            enriched = []
            for a in accounts:
                p = a.get("provider", "openai")
                if a.get("base_url"): p = detect_provider(a["base_url"])
                usage = fetch_account_usage(a)
                enriched.append({**a, "_color": provider_color(p), "_prov": p, "_usage": usage})
            self._json({"accounts": enriched, "active": active, "programs": PROGRAMS})
            return

        if u.path == "/api/skills":
            master = scan_master_skills()
            prog_skills = scan_all_skill_dirs()
            self._json({"master": master, "programs": prog_skills})
            return

        if u.path == "/api/programs":
            active = detect_active_accounts()
            prog_mcp = scan_program_mcp()
            prog_skills = scan_all_skill_dirs()
            key_map = {a["id"]: a["name"] for a in cfg.get("accounts", [])}
            list_data = []
            for p in PROGRAMS:
                pid = p["id"]
                list_data.append({
                    "id": pid, "name": p["name"], "letter": p["letter"],
                    "config_path": p["config_path"],
                    "skills_count": len(prog_skills.get(pid, [])),
                    "mcp_count": len(prog_mcp.get(pid, {})),
                    "active_account": key_map.get(active.get(pid), None),
                    "type": p["type"],
                })
            self._json({"programs": list_data}); return

        if u.path == "/api/mcp":
            master = scan_master_mcp()
            prog_mcp = scan_program_mcp()
            all_names = set(master.keys())
            for v in prog_mcp.values(): all_names.update(v.keys())
            servers = []
            for name in sorted(all_names):
                in_master = name in master
                config = master.get(name, next((v.get(name, {}) for v in prog_mcp.values() if name in v), {}))
                progs = {pid: name in pmcp for pid, pmcp in prog_mcp.items()}
                servers.append({"name": name, "in_master": in_master, "config": config, "programs": progs})
            self._json({"servers": servers, "program_names": {p["id"]: p["name"] for p in PROGRAMS}})
            return

        if u.path == "/api/get-settings":
            self._json(cfg); return
        if u.path == "/api/shutdown":
            self._json({"ok": True}); threading.Timer(0.1, lambda: os._exit(0)).start(); return
        self.send_error(404)

    def do_POST(self):
        u = urlparse(self.path); b = self._body(); cfg = ensure_defaults()

        # ACCOUNTS
        if u.path == "/api/import":
            names = import_accounts()
            self._json({"imported": names, "total": len(ensure_defaults().get("accounts", []))})
            return
        if u.path == "/api/import-file":
            fp = b.get("file_path", "").strip()
            if not fp: return self._err("file_path required")
            p = Path(os.path.expandvars(os.path.expanduser(fp)))
            if not p.exists(): return self._err("file not found")
            try:
                data = json.loads(p.read_text())
            except Exception:
                return self._err("invalid json")
            cfg = ensure_defaults()
            accounts = cfg.setdefault("accounts", [])
            imported = []
            existing_keys = {a.get("api_key", "")[:20] for a in accounts}
            if "tokens" in data or "OPENAI_API_KEY" in data:
                tokens = data.get("tokens", {})
                key = data.get("OPENAI_API_KEY", tokens.get("access_token", ""))
                if key:
                    from .settings import decode_jwt
                    claims = decode_jwt(tokens.get("access_token", ""))
                    profile = claims.get("https://api.openai.com/profile", {})
                    oa = claims.get("https://api.openai.com/auth", {})
                    email = profile.get("email", "")
                    plan = oa.get("chatgpt_plan_type", "")
                    if key[:20] not in existing_keys:
                        accounts.append({
                            "id": uuid.uuid4().hex[:8],
                            "name": f"Codex (imported)", "provider": "openai",
                            "api_key": "", "base_url": "", "model": "",
                            "email": email, "plan": plan,
                            "source_path": str(p),
                        })
                        imported.append("Codex (imported)")
            elif "access_token" in data or "refresh_token" in data:
                from .settings import decode_jwt
                claims = decode_jwt(data.get("id_token", data.get("access_token", "")))
                email = claims.get("email", "")
                exp = data.get("expires_at", 0) or claims.get("exp", 0)
                name_str = f"Claude Desktop ({email or 'imported'})"
                if not any(a.get("name") == name_str for a in accounts):
                    accounts.append({
                        "id": uuid.uuid4().hex[:8], "name": name_str,
                        "provider": "anthropic", "api_key": "", "base_url": "",
                        "model": "", "claude_oauth_cred": p.stem,
                        "claude_oauth_email": email,
                        "claude_oauth_expires_at": exp,
                        "claude_oauth_expires_in": max(0, exp - time.time()) if exp else 0,
                        "claude_oauth_has_refresh": bool(data.get("refresh_token", "")),
                        "source_path": str(p),
                    })
                    imported.append(name_str)
            else:
                env = data.get("env", {})
                key = env.get("ANTHROPIC_AUTH_TOKEN", "") or env.get("ANTHROPIC_API_KEY", "")
                if not key:
                    for k, v in data.items():
                        if isinstance(v, str) and len(v) > 20 and ("key" in k.lower() or "token" in k.lower()):
                            key = v
                            break
                if key and key[:20] not in existing_keys:
                    accounts.append({
                        "id": uuid.uuid4().hex[:8],
                        "name": f"Imported ({key[:8]}...)", "provider": "openai",
                        "api_key": key, "base_url": "", "model": "",
                        "source_path": str(p),
                    })
                    imported.append(f"Imported ({key[:8]}...)")
            save_config(cfg)
            self._json({"imported": imported, "total": len(accounts)})
            return
        if u.path == "/api/refresh-token":
            aid = b.get("account_id", "")
            acc = next((a for a in cfg.get("accounts", []) if a["id"] == aid), None)
            if not acc: return self._err("account not found")
            if not acc.get("claude_oauth_has_refresh"): return self._err("no refresh token")
            cred_name = acc.get("claude_oauth_cred", "")
            if not cred_name: return self._err("no credential name")
            from .settings import ANTHROPIC_CREDENTIALS_DIR, CD_OAUTH_TOKEN_URL, CD_OAUTH_CLIENT_ID
            cred_file = ANTHROPIC_CREDENTIALS_DIR / f"{cred_name}.json"
            if not cred_file.exists(): return self._err("credential file not found")
            try:
                cred_data = json.loads(cred_file.read_text())
                refresh_t = cred_data.get("refresh_token", "")
                if not refresh_t: return self._err("no refresh_token in file")
                import urllib.request
                import urllib.parse
                rbody = urllib.parse.urlencode({
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_t,
                    "client_id": CD_OAUTH_CLIENT_ID,
                }).encode()
                req = urllib.request.Request(CD_OAUTH_TOKEN_URL, data=rbody, method="POST",
                    headers={"Content-Type": "application/x-www-form-urlencoded"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    result = json.loads(r.read())
                if result.get("access_token"):
                    cred_data["access_token"] = result["access_token"]
                    if result.get("refresh_token"): cred_data["refresh_token"] = result["refresh_token"]
                    if result.get("expires_in"):
                        cred_data["expires_at"] = int(time.time()) + result.get("expires_in", 0)
                    import threading as _thr
                    _thr.Thread(target=lambda: cred_file.write_text(json.dumps(cred_data, indent=2)), daemon=True).start()
                    acc["claude_oauth_expires_in"] = result.get("expires_in", 0)
                    save_config(cfg)
                    self._json({"ok": True})
                else:
                    self._json({"ok": False, "error": "refresh failed"})
            except Exception as e:
                self._json({"ok": False, "error": str(e)[:80]})
            return
        if u.path == "/api/account-create":
            name = b.get("name", "").strip()
            if not name: return self._err("name required")
            import uuid
            acc = {"id": uuid.uuid4().hex[:8], "name": name,
                   "provider": b.get("provider", "anthropic"),
                   "api_key": b.get("api_key", ""), "base_url": b.get("base_url", ""),
                   "model": b.get("model", ""), "email": b.get("email", "")}
            for k in ("claude_overrides", "codex_provider"):
                if b.get(k): acc[k] = b[k]
            cfg.setdefault("accounts", []).append(acc)
            save_config(cfg)
            self._json({"ok": True, "account": acc}); return
        if u.path == "/api/account-delete":
            aid = b.get("id", "")
            cfg["accounts"] = [a for a in cfg.get("accounts", []) if a["id"] != aid]
            save_config(cfg); self._json({"ok": True}); return
        if u.path == "/api/account-update":
            aid = b.get("id", "")
            for a in cfg.get("accounts", []):
                if a["id"] == aid:
                    for k in ("name", "provider", "api_key", "base_url", "model", "email", "claude_overrides", "codex_provider"):
                        if k in b: a[k] = b[k]
                    break
            save_config(cfg); self._json({"ok": True}); return
        if u.path == "/api/apply":
            aid = b.get("account_id", ""); pids = b.get("programs", [])
            if not aid: return self._err("account_id required")
            results = []
            for pid in pids:
                ok, msg = apply_account(aid, pid)
                results.append({"program": pid, "ok": ok, "message": msg})
            self._json({"results": results}); return

        # SKILLS
        if u.path == "/api/skill-sync":
            sn = b.get("skill", ""); pids = b.get("programs", [])
            if not sn: return self._err("skill name required")
            ok, msg = sync_skill_to_programs(sn, pids)
            self._json({"ok": ok, "message": msg}); return
        if u.path == "/api/skill-sync-all":
            results = sync_all_skills()
            self._json({"ok": True, "results": results}); return
        if u.path == "/api/skill-collect":
            sn = b.get("skill", ""); pid = b.get("program", "")
            ok, msg = collect_skill_to_master(sn, pid)
            self._json({"ok": ok, "message": msg}); return
        if u.path == "/api/skill-delete":
            sn = b.get("skill", "")
            delete_skill_from_master(sn)
            self._json({"ok": True}); return
        if u.path == "/api/skill-upload":
            sn = b.get("name", "").strip(); content = b.get("content", "")
            if not sn: return self._err("name required")
            dst = MASTER_SKILLS / sn
            dst.mkdir(parents=True, exist_ok=True)
            (dst / "SKILL.md").write_text(content)
            self._json({"ok": True}); return
        if u.path == "/api/skills-import-from-program":
            pid = b.get("program", "")
            if not pid: return self._err("program required")
            prog = next(p for p in PROGRAMS if p["id"] == pid)
            from .settings import expand_path
            src = expand_path(prog["skills_dir"])
            if not src.exists(): return self._json({"imported": []})
            import shutil
            MASTER_SKILLS.mkdir(parents=True, exist_ok=True)
            names = []
            for d in sorted(src.iterdir()):
                if d.is_dir() and (d / "SKILL.md").exists():
                    dst = MASTER_SKILLS / d.name
                    if dst.exists(): continue
                    shutil.copytree(str(d), str(dst))
                    names.append(d.name)
            self._json({"imported": names})
            return
        if u.path == "/api/skills-import-from-folder":
            folder = b.get("folder", "").strip()
            if not folder: return self._err("folder path required")
            src = Path(os.path.expandvars(os.path.expanduser(folder)))
            if not src.exists(): return self._err("folder not found")
            import shutil
            MASTER_SKILLS.mkdir(parents=True, exist_ok=True)
            names = []
            for d in sorted(src.iterdir()):
                if d.is_dir() and (d / "SKILL.md").exists():
                    dst = MASTER_SKILLS / d.name
                    if dst.exists(): continue
                    shutil.copytree(str(d), str(dst))
                    names.append(d.name)
            self._json({"imported": names})
            return

        # MCP
        if u.path == "/api/mcp-add":
            name = b.get("name", "").strip()
            if not name: return self._err("name required")
            config = {}
            if b.get("url"): config["url"] = b["url"]
            else: config = {"command": b.get("command", ""), "args": b.get("args", [])}
            master = scan_master_mcp()
            master[name] = config
            save_master_mcp(master)
            pids = b.get("programs", [])
            if pids: msg = sync_mcp_to_programs(name, config, pids)
            self._json({"ok": True}); return
        if u.path == "/api/mcp-sync":
            name = b.get("name", ""); pids = b.get("programs", [])
            master = scan_master_mcp()
            if name not in master: return self._err("not in master")
            msg = sync_mcp_to_programs(name, master[name], pids)
            self._json({"ok": True, "message": msg}); return
        if u.path == "/api/mcp-sync-all":
            master = scan_master_mcp()
            results = []
            for name, config in master.items():
                msg = sync_mcp_to_programs(name, config, [p["id"] for p in PROGRAMS])
                results.append(f"{name}: {msg}")
            self._json({"ok": True, "results": results}); return
        if u.path == "/api/mcp-delete":
            name = b.get("name", ""); pid = b.get("program", "")
            if pid: delete_mcp_from_program(name, pid)
            else:
                master = scan_master_mcp()
                master.pop(name, None)
                save_master_mcp(master)
            self._json({"ok": True}); return

        # USAGE
        if u.path == "/api/usage-refresh":
            aid = b.get("account_id", "")
            if aid: _USAGE_CACHE.pop(aid, None)
            else: _USAGE_CACHE.clear()
            self._json({"ok": True}); return

        # SETTINGS
        if u.path == "/api/backup-now":
            do_backup(cfg); self._json({"ok": True}); return
        if u.path == "/api/set-auto-backup":
            cfg["auto_backup"] = b.get("enabled", True); save_config(cfg); self._json({"ok": True}); return

        # HISTORY
        if u.path == "/api/history-list":
            fp = b.get("file_path", "")
            self._json({"versions": history.get_versions(fp or None, 200)}); return
        if u.path == "/api/history-restore":
            vid = b.get("version_id", 0)
            ok, msg = history.restore_version(vid)
            self._json({"ok": ok, "message": msg}); return
        if u.path == "/api/history-snapshot":
            count = history.snapshot_all(b.get("label", ""))
            self._json({"ok": True, "count": count}); return
        if u.path == "/api/history-diff":
            vid = b.get("version_id", 0)
            compare_to = b.get("compare_to", "current")
            v = history.get_version_content(vid)
            if not v:
                return self._err("version not found")
            v_path = Path(v["file_path"])
            v_content = v["content"]
            if compare_to == "current":
                other_content = v_path.read_text() if v_path.exists() else ""
                left_title = f"v#{vid}"
                right_title = "current"
            else:
                prev_vers = [x for x in history.get_versions(v["file_path"], 200) if x["id"] != vid]
                if prev_vers:
                    pv = history.get_version_content(prev_vers[0]["id"])
                    other_content = pv["content"] if pv else ""
                    right_title = f"v#{prev_vers[0]['id']}"
                else:
                    other_content = ""
                    right_title = "(none)"
                left_title = f"v#{vid}"
            import difflib
            diff = difflib.HtmlDiff(tabsize=2)
            other_lines = _decode_diff_content(other_content, str(v_path)).splitlines()
            v_lines = _decode_diff_content(v_content, str(v_path)).splitlines()
            ctx = 3 if len(other_lines) < 500 else 0
            html = diff.make_table(other_lines, v_lines,
                                   fromdesc=right_title, todesc=left_title,
                                   context=True, numlines=ctx)
            self._json({"html": html, "left_title": left_title, "right_title": right_title}); return

        # PROGRAM FILES
        if u.path == "/api/program-files":
            pid = b.get("program_id", "")
            from .programs import get
            prog = get(pid)
            files = []
            if prog:
                files.append({"name": Path(prog.config_path).name, "path": str(prog.config_path), "desc": "config"})
                for f in prog.extra_files():
                    files.append(f)
            self._json({"files": files}); return

        # UTILS
        if u.path == "/api/open-folder":
            path = b.get("path", "")
            if path:
                import subprocess, os
                p = Path(os.path.expanduser(path))
                target = p if p.exists() else p.parent
                if target.exists():
                    subprocess.Popen(["open", "-R", str(target.resolve())])
                    self._json({"ok": True}); return
            self._json({"ok": False, "error": "not found"}); return

        self.send_error(404)

    def log_message(self, *a): pass
