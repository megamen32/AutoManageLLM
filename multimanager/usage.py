"""Usage/limit cache with per-provider fetchers."""
import json, time, urllib.request, urllib.error
from pathlib import Path
from .settings import CX_AUTH, ANTHROPIC_CREDENTIALS_DIR
from .settings import decode_jwt

_USAGE_CACHE = {}
_USAGE_CACHE_TTL = 120


def _get_codex_auth():
    """Read access_token + account_id from Codex auth.json."""
    try:
        if CX_AUTH.exists():
            auth = json.loads(CX_AUTH.read_text())
            tokens = auth.get("tokens", {})
            access_token = tokens.get("access_token", "")
            account_id = tokens.get("account_id", "")
            # Also extract plan & email from JWT for fallback
            claims = decode_jwt(access_token) if access_token else {}
            profile = claims.get("https://api.openai.com/profile", {})
            oa = claims.get("https://api.openai.com/auth", {})
            token_exp = claims.get("exp", 0)
            now = time.time()
            return {
                "access_token": access_token,
                "account_id": account_id,
                "email": profile.get("email", ""),
                "plan": oa.get("chatgpt_plan_type", ""),
                "token_expires_in": max(0, token_exp - now) if token_exp else None,
            }
    except: pass
    return {}


def _fetch_chatgpt_usage(access_token, account_id):
    """Call ChatGPT /wham/usage API — same as codex-auth."""
    if not access_token:
        return {}
    try:
        req = urllib.request.Request(
            "https://chatgpt.com/backend-api/wham/usage",
            headers={
                "Authorization": f"Bearer {access_token}",
                "ChatGPT-Account-Id": account_id,
                "User-Agent": "MultiManager",
                "Accept": "application/json",
            })
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}"}
    except Exception as e:
        return {"error": str(e)[:80]}

    rl = data.get("rate_limit", {})
    pw = rl.get("primary_window", {})
    sw = rl.get("secondary_window", {})

    pw_used = pw.get("used_percent")
    sw_used = sw.get("used_percent")
    pw_window = pw.get("limit_window_seconds", 0)
    sw_window = sw.get("limit_window_seconds", 0)
    pw_reset = pw.get("reset_at")
    sw_reset = sw.get("reset_at")

    # Calculate overall usage % as max of both windows
    pct = max(
        pw_used if pw_used is not None else 0,
        sw_used if sw_used is not None else 0,
    ) if pw_used is not None or sw_used is not None else None

    result = {"type": "codex"}
    if pct is not None:
        result["used_pct"] = round(pct, 1)

    # Build windows info
    windows = []
    if pw_used is not None:
        windows.append({
            "label": f"{pw_window//3600}h" if pw_window else "5h",
            "used_pct": round(pw_used, 1),
            "reset_at": pw_reset,
            "remaining_pct": round(100 - pw_used, 1),
        })
    if sw_used is not None:
        windows.append({
            "label": f"{sw_window//3600//24}d" if sw_window >= 86400 else f"{sw_window//3600}h",
            "used_pct": round(sw_used, 1),
            "reset_at": sw_reset,
            "remaining_pct": round(100 - sw_used, 1),
        })
    result["windows"] = windows
    result["allowed"] = rl.get("allowed")
    result["limit_reached"] = rl.get("limit_reached")

    return result


def _fetch_claude_code_usage(api_key, base_url):
    """Fetch Claude Code usage — try Anthropic billing API or Z.AI proxy."""
    result = {"type": "claude-code"}
    url = (base_url.rstrip("/") if base_url else "https://api.anthropic.com")
    is_proxy = "z.ai" in url or "bigmodel" in url
    if is_proxy:
        try:
            req = urllib.request.Request(
                url + "/v1/dashboard/billing/usage",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json",
                })
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            result["data"] = data
        except Exception:
            result["note"] = "quota via MCP"
        return result
    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/organizations/me",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Accept": "application/json",
            })
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        result["org_id"] = data.get("id", "")
        result["name"] = data.get("name", "")
        # Try billing endpoint
        try:
            req2 = urllib.request.Request(
                "https://api.anthropic.com/v1/credits",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Accept": "application/json",
                })
            with urllib.request.urlopen(req2, timeout=10) as r2:
                credits = json.loads(r2.read())
            result["credits"] = credits
            balance = credits.get("balance", None)
            if balance is not None:
                result["balance"] = balance
        except Exception:
            pass
        # Try usage/tokens endpoint
        try:
            req3 = urllib.request.Request(
                "https://api.anthropic.com/v1/usage/tokens",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Accept": "application/json",
                })
            with urllib.request.urlopen(req3, timeout=10) as r3:
                usage = json.loads(r3.read())
            result["usage"] = usage
        except Exception:
            pass
    except urllib.error.HTTPError as e:
        result["error"] = f"HTTP {e.code}"
    except Exception as e:
        result["error"] = str(e)[:80]
    return result


def fetch_account_usage(account):
    key = account.get("id", "")
    now = time.time()
    cached = _USAGE_CACHE.get(key)
    if cached and now - cached["ts"] < _USAGE_CACHE_TTL:
        return cached["data"]

    api_key = account.get("api_key", "")
    base_url = account.get("base_url", "")
    prov = account.get("provider", "openai")
    from .settings import detect_provider
    if base_url: prov = detect_provider(base_url)
    result = {}

    # Codex accounts (have empty api_key, set during import) — fetch real ChatGPT usage data
    is_codex = account.get("codex_provider") or (prov == "openai" and not api_key and not account.get("base_url"))
    if is_codex:
        auth = _get_codex_auth()
        usage = _fetch_chatgpt_usage(auth.get("access_token", ""), auth.get("account_id", ""))
        if usage.get("error"):
            # Fallback: show plan info from JWT
            result = {"type": "codex", "error": usage["error"],
                      "email": auth.get("email", ""), "plan": auth.get("plan", ""),
                      "token_expires_in": auth.get("token_expires_in")}
        else:
            result = usage
            result["email"] = auth.get("email", "")
            result["plan"] = auth.get("plan", "")
            result["token_expires_in"] = auth.get("token_expires_in")

    # OpenAI accounts with real API key
    elif prov == "openai" and api_key and api_key.startswith("sk-"):
        try:
            req = urllib.request.Request(
                "https://api.openai.com/v1/dashboard/rate_limits",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
                limits = data if isinstance(data, list) else data.get("data", [])
                rem = sum(l.get("remaining", 0) for l in limits if isinstance(l, dict))
                total = sum(l.get("max_requests", 0) for l in limits if isinstance(l, dict))
                pct = round((total - rem) / total * 100, 1) if total > 0 else None
                result = {"type": "openai", "remaining": rem, "total": total, "used_pct": pct}
        except urllib.error.HTTPError as e:
            result = {"type": "openai", "error": f"{e.code}"}
        except Exception as e:
            result = {"type": "openai", "error": str(e)[:80]}

    # Claude Desktop OAuth — read fresh from credential files, show token expiry
    elif account.get("claude_oauth_cred"):
        cred_name = account.get("claude_oauth_cred", "")
        expires_in = account.get("claude_oauth_expires_in", 0)
        has_refresh = account.get("claude_oauth_has_refresh", False)
        email = account.get("claude_oauth_email", "")
        # Try to read fresh from credential file
        if ANTHROPIC_CREDENTIALS_DIR.exists() and cred_name:
            cred_file = ANTHROPIC_CREDENTIALS_DIR / f"{cred_name}.json"
            if cred_file.exists():
                try:
                    cred_data = json.loads(cred_file.read_text())
                    raw_exp = cred_data.get("expires_at", 0) or 0
                    expires_in = max(0, raw_exp - time.time())
                    has_refresh = bool(cred_data.get("refresh_token", ""))
                    if not email:
                        id_token = cred_data.get("id_token", "")
                        claims = decode_jwt(id_token) if id_token else {}
                        email = claims.get("email", "")
                except Exception:
                    pass
        total_secs = 86400
        if expires_in > 0:
            used_pct = round(max(0, min(100, (1 - expires_in / total_secs) * 100)), 1)
        else:
            used_pct = 100 if expires_in == 0 else None
        result = {
            "type": "claude-desktop",
            "used_pct": used_pct,
            "remaining_pct": round(100 - used_pct, 1) if used_pct is not None else None,
            "email": email,
            "expires_in_seconds": expires_in,
            "expires_in_hours": round(expires_in / 3600, 1) if expires_in > 0 else 0,
            "token_expires_in": expires_in,
            "has_refresh": has_refresh,
            "windows": [{
                "label": "token",
                "used_pct": used_pct,
                "remaining_pct": round(100 - used_pct, 1) if used_pct is not None else None,
                "reset_at": None,
            }],
        }

    # Z.AI / GLM — try BigModel balance API (must come before claude-code since bigmodel URLs detect as anthropic)
    elif ("z.ai" in base_url or "bigmodel" in base_url) and api_key:
        try:
            req = urllib.request.Request(
                "https://open.bigmodel.cn/api/llm/balance",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
                result = {"type": "zai", "data": data}
        except Exception:
            result = {"type": "zai", "note": "quota via MCP"}

    # Claude Code (Anthropic API key) — check /v1/messages/count_tokens or billing
    elif prov == "anthropic" and api_key:
        result = _fetch_claude_code_usage(api_key, base_url)
    _USAGE_CACHE[key] = {"ts": now, "data": result}
    return result
