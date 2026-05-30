"""SQLite version history for config files — save/restore/snapshot."""
import json, sqlite3, time, threading
from pathlib import Path
from .settings import CONFIG_DIR, get_programs

DB_PATH = CONFIG_DIR / "history.db"
_lock = threading.Lock()


def _tracked_files():
    tracked = []
    for p in get_programs():
        if p["id"] == "codex":
            tracked.append("auth.json")
            tracked.append("config.toml")
        else:
            tracked.append(Path(p["config_path"]).name)
    tracked.append("config.json")
    return tracked


TRACKED_FILES = None


def _db():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""CREATE TABLE IF NOT EXISTS versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at REAL NOT NULL,
        label TEXT DEFAULT ''
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_v_path ON versions(file_path)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_v_time ON versions(created_at)")
    conn.row_factory = sqlite3.Row
    return conn


def save_version(file_path, content, label=""):
    if isinstance(content, (dict, list)):
        content = json.dumps(content, ensure_ascii=False, indent=2)
    elif not isinstance(content, str):
        return
    with _lock:
        db = _db()
        db.execute("INSERT INTO versions (file_path, content, created_at, label) VALUES (?, ?, ?, ?)",
                   (str(file_path), content, time.time(), label))
        db.commit()
        db.close()


def save_current(file_path, label=""):
    p = Path(file_path).expanduser()
    if not p.exists():
        return
    content = p.read_text()
    save_version(str(file_path), content, label)


def get_versions(file_path=None, limit=50):
    with _lock:
        db = _db()
        if file_path:
            rows = db.execute(
                "SELECT id, file_path, created_at, label FROM versions WHERE file_path=? ORDER BY id DESC LIMIT ?",
                (str(file_path), limit)).fetchall()
        else:
            rows = db.execute(
                "SELECT id, file_path, created_at, label FROM versions ORDER BY id DESC LIMIT ?",
                (limit,)).fetchall()
        db.close()
    result = []
    for r in rows:
        result.append({
            "id": r["id"], "file_path": r["file_path"],
            "created_at": r["created_at"], "label": r["label"],
        })
    return result


def get_version_content(version_id):
    with _lock:
        db = _db()
        r = db.execute("SELECT file_path, content FROM versions WHERE id=?", (version_id,)).fetchone()
        db.close()
    return dict(r) if r else None


def restore_version(version_id):
    v = get_version_content(version_id)
    if not v:
        return False, "Version not found"
    p = Path(v["file_path"]).expanduser()
    # Save current before overwriting
    if p.exists():
        save_current(v["file_path"], "before-restore")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(v["content"])
    return True, f"Restored {p.name}"


def snapshot_all(label=""):
    count = 0
    paths = set()
    for p in get_programs():
        cp = Path(p["config_path"])
        if cp.exists():
            paths.add(str(cp))
    # Add auth.json if exists
    from .settings import CX_AUTH
    if CX_AUTH.exists():
        paths.add(str(CX_AUTH))
    # Add master config
    from .settings import CONFIG_FILE
    if CONFIG_FILE.exists():
        paths.add(str(CONFIG_FILE))
    for p in paths:
        save_current(p, label or f"snapshot-{int(time.time())}")
        count += 1
    return count


def cleanup(keep_per_file=100):
    with _lock:
        db = _db()
        for path, in db.execute("SELECT DISTINCT file_path FROM versions").fetchall():
            ids = [r[0] for r in db.execute(
                "SELECT id FROM versions WHERE file_path=? ORDER BY id DESC", (path,)).fetchall()]
            if len(ids) > keep_per_file:
                delete_ids = ids[keep_per_file:]
                placeholders = ",".join("?" * len(delete_ids))
                db.execute(f"DELETE FROM versions WHERE id IN ({placeholders})", delete_ids)
        db.commit()
        db.close()
