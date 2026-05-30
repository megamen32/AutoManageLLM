"""Program interface — base mixin and registry."""
from pathlib import Path


class Program:
    id: str = ""
    name: str = ""
    letter: str = ""
    config_path: Path = None
    config_type: str = "json"
    skills_dir: Path = None
    mcp_key: str = "mcpServers"

    def read_config(self) -> dict: ...
    def write_config(self, data: dict): ...
    def import_accounts(self, accounts: list, existing_keys: set, existing_urls: set) -> list: ...
    def apply_account(self, acc: dict, current_config: dict = None) -> tuple: ...
    def detect_active(self, accounts: list) -> str | None: ...
    def fetch_usage(self, acc: dict) -> dict: ...

    def extra_files(self) -> list[dict]:
        return []

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "letter": self.letter,
            "config_path": str(self.config_path), "type": self.config_type,
            "skills_dir": str(self.skills_dir), "mcp_key": self.mcp_key,
            "extra_files": [{"name": f["name"], "desc": f.get("desc","")} for f in self.extra_files()],
        }


_registry: dict[str, Program] = {}


def register(prog: Program):
    _registry[prog.id] = prog


def get(id: str) -> Program | None:
    return _registry.get(id)


def all() -> list[Program]:
    return list(_registry.values())


def all_dicts() -> list[dict]:
    return [p.to_dict() for p in all()]
