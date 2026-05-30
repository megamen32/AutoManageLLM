"""Config load/save/backup."""
import json
from datetime import datetime
from .settings import CONFIG_DIR, CONFIG_FILE, BACKUP_DIR, CC_SETTINGS, CX_CONFIG, CX_AUTH, OPENCODE_CFG, DEFAULT_CONFIG
from . import history


def load_config():
    if CONFIG_FILE.exists():
        try: return json.loads(CONFIG_FILE.read_text())
        except: return {}
    return {}


def save_config(cfg):
    CONFIG_DIR.mkdir(exist_ok=True)
    if CONFIG_FILE.exists():
        history.save_current(CONFIG_FILE)
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))


def ensure_defaults():
    cfg = load_config()
    changed = False
    for k, v in DEFAULT_CONFIG.items():
        if k not in cfg: cfg[k] = v; changed = True
    # Migration: fill missing codex_provider on Codex accounts
    for a in cfg.get("accounts", []):
        if a.get("name", "").startswith("Codex") and "codex_provider" not in a:
            a["codex_provider"] = ""
            changed = True
    if changed: save_config(cfg)
    return cfg


def do_backup(cfg):
    if not cfg.get("auto_backup"): return
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    bk = {"created_at": stamp, "files": {}}
    for cat, f in [("cc", CC_SETTINGS), ("cx_cfg", CX_CONFIG), ("cx_auth", CX_AUTH), ("opencode", OPENCODE_CFG)]:
        if f.exists():
            try: bk["files"][cat] = {"path": str(f), "content": f.read_text()}
            except: pass
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    (BACKUP_DIR / f"auto-{stamp}.json").write_text(json.dumps(bk, ensure_ascii=False, indent=2))
