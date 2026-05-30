"""Integration tests for MultiManager API."""
import json, threading, urllib.request, urllib.error, socket, time, pytest
from http.server import ThreadingHTTPServer
from multimanager.handler import Handler


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0)); return s.getsockname()[1]


@pytest.fixture(scope="module")
def server():
    port = free_port()
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    time.sleep(0.3)
    yield port
    srv.shutdown()


def api(port, path, data=None):
    url = f"http://127.0.0.1:{port}{path}"
    b = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=b, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()}


def test_get_accounts(server):
    d = api(server, "/api/accounts")
    assert "accounts" in d


def test_get_skills(server):
    d = api(server, "/api/skills")
    assert "master" in d
    assert "programs" in d


def test_get_programs(server):
    d = api(server, "/api/programs")
    assert "programs" in d


def test_get_mcp(server):
    d = api(server, "/api/mcp")
    assert "servers" in d
    assert "program_names" in d


def test_get_settings(server):
    d = api(server, "/api/get-settings")
    assert isinstance(d, dict)


def test_history_list(server):
    d = api(server, "/api/history-list", {})
    assert "versions" in d


def test_history_snapshot(server):
    d = api(server, "/api/history-snapshot", {"label": "test"})
    assert d.get("ok") is True


def test_backup_now(server):
    d = api(server, "/api/backup-now", {})
    assert d.get("ok") is True


def test_usage_refresh(server):
    d = api(server, "/api/usage-refresh", {})
    assert d.get("ok") is True


def test_import(server):
    d = api(server, "/api/import", {})
    assert "imported" in d
    assert "total" in d


def test_shutdown(server):
    """Don't actually test shutdown — it kills the server."""
    pass
