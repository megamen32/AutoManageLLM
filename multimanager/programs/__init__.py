"""Program registry — auto-registers all programs."""
from . import base as _base
from .claude_code import ClaudeCodeProgram
from .claude_desktop import ClaudeDesktopProgram
from .codex import CodexProgram
from .opencode import OpenCodeProgram
from .cline import ClineProgram
from .roo_code import RooCodeProgram

register = _base.register
get = _base.get
Program = _base.Program

_progs = [ClaudeCodeProgram(), ClaudeDesktopProgram(), CodexProgram(),
           OpenCodeProgram(), ClineProgram(), RooCodeProgram()]
for p in _progs:
    _base.register(p)


def all():
    return list(_base._registry.values())


def all_dicts():
    result = []
    for p in all():
        d = {"id": p.id, "name": p.name, "letter": p.letter,
             "config_path": str(p.config_path), "type": p.config_type,
             "skills_dir": str(p.skills_dir), "mcp_key": p.mcp_key,
             "multi_provider": getattr(p, "multi_provider", False),
             "installed": (getattr(p, "is_installed", None) or (lambda: True))()}
        try:
            ef = p.extra_files()
            d["extra_files"] = [{"name": f["name"], "path": f.get("path", ""), "desc": f.get("desc", "")} for f in ef]
        except Exception:
            d["extra_files"] = []
        result.append(d)
    return result


__all__ = ["register", "get", "all", "all_dicts", "Program"]
