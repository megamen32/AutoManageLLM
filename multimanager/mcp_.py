"""MCP operations: master config, per-program sync."""
import json
from pathlib import Path
from .settings import MASTER_MCP, PROGRAMS
from .toml_utils import parse_toml_simple
from . import history


def scan_master_mcp():
    if not MASTER_MCP.exists(): return {}
    try: return json.loads(MASTER_MCP.read_text())
    except: return {}

def save_master_mcp(data):
    MASTER_MCP.parent.mkdir(parents=True, exist_ok=True)
    MASTER_MCP.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def scan_program_mcp():
    result = {}
    for prog in PROGRAMS:
        cp = prog["config_path"]
        if not cp: result[prog["id"]] = {}; continue
        if prog["type"] == "json":
            d = _read_config(cp)
            result[prog["id"]] = d.get(prog["mcp_key"], {})
        elif prog["type"] == "toml":
            d = _read_toml_config(cp)
            result[prog["id"]] = d.get("mcp_servers", {})
        else:
            result[prog["id"]] = {}
    return result


def _read_config(path):
    if not Path(path).exists(): return {}
    try: return json.loads(Path(path).read_text())
    except: return {}

def _read_toml_config(path):
    if not Path(path).exists(): return {}
    return parse_toml_simple(Path(path).read_text())

def _write_config(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    history.save_current(path)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2))

def _write_toml(path, data, order):
    history.save_current(path)
    from .toml_utils import write_toml_simple
    Path(path).write_text(write_toml_simple(data, order))


def sync_mcp_to_programs(server_name, server_config, program_ids):
    results = []
    for pid in program_ids:
        prog = next(p for p in PROGRAMS if p["id"] == pid)
        cp = prog["config_path"]
        if not cp: continue
        if prog["type"] == "json":
            d = _read_config(cp)
            mcp = d.setdefault(prog["mcp_key"], {})
            mcp[server_name] = server_config
            _write_config(cp, d)
            results.append(f"{prog['name']}: OK")
        elif prog["type"] == "toml":
            d = _read_toml_config(cp)
            mcp = d.setdefault("mcp_servers", {})
            mcp[server_name] = server_config
            order = ["model", "model_provider", "model_reasoning_effort", "personality",
                     "approval_policy", "sandbox_mode", "notify", "openai_base_url"]
            _write_toml(cp, d, order)
            results.append(f"{prog['name']}: OK")
    return "; ".join(results)


def delete_mcp_from_program(server_name, program_id):
    prog = next(p for p in PROGRAMS if p["id"] == program_id)
    cp = prog["config_path"]
    if not cp: return
    if prog["type"] == "json":
        d = _read_config(cp)
        d.get(prog["mcp_key"], {}).pop(server_name, None)
        _write_config(cp, d)
    elif prog["type"] == "toml":
        d = _read_toml_config(cp)
        d.get("mcp_servers", {}).pop(server_name, None)
        order = ["model", "model_provider", "model_reasoning_effort", "personality",
                 "approval_policy", "sandbox_mode", "notify", "openai_base_url"]
        _write_toml(cp, d, order)
