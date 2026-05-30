# Claude Desktop API Documentation (v1.8555.2)

> Reverse-engineered from `app.asar` (Electron bundle) — main process `index.js` (12MB), preload `index.pre.js` (840KB),
> renderer `ion-dist/assets/v1/*.js` (~780 files), and embedded `@anthropic-ai/claude-agent-sdk` v0.3.149.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [OAuth & Authentication](#2-oauth--authentication)
3. [API Endpoints (claude.ai/api/*)](#3-api-endpoints-claudeaiapi)
4. [Anthropic API Endpoints (api.anthropic.com)](#4-anthropic-api-endpoints-apianthropiccom)
5. [Platform OAuth Endpoints (platform.claude.com)](#5-platform-oauth-endpoints-platformclaudecom)
6. [Billing & Subscription](#6-billing--subscription)
7. [Rate Limiting](#7-rate-limiting)
8. [MCP Authentication](#8-mcp-authentication)
9. [Sessions (Claude Code)](#9-sessions-claude-code)
10. [Electron IPC Architecture](#10-electron-ipc-architecture)
11. [Data Storage & Config Files](#11-data-storage--config-files)
12. [Feature Flags](#12-feature-flags)
13. [Update System](#13-update-system)
14. [Enterprise Configuration](#14-enterprise-configuration)

---

## 1. Architecture Overview

### Bundle Structure

| File | Size | Role |
|------|------|------|
| `.vite/build/index.js` | 12.4 MB | Main process (Electron) |
| `.vite/build/index.pre.js` | 840 KB | Preload script |
| `mcp-runtime/directMcpHost.js` | 15,882 lines | MCP JSON-RPC host |
| `mcp-runtime/nodeHost.js` | — | Node.js MCP host |
| `mainView.js` | 187 KB | Main renderer view |
| `mainWindow.js` | 162 KB | Main window manager |
| `quickWindow.js` | 162 KB | Quick window renderer |
| `aboutWindow.js` | 142 KB | About window |
| `buddy.js` | 59 KB | Buddy/cowork module |
| `findInPage.js` | 140 KB | Find in page |
| Renderer bundles | ~780 files | `ion-dist/assets/v1/*.js` |

### Build Info
- **Builder**: Vite
- **Sentry release**: `a476c316c741715263e34f9c9d2bc45b6d0f21c7`
- **Sentry DSN**: `https://o1158394.ingest.us.sentry.io`
- **@sentry/electron**: v7.4.0
- **@anthropic-ai/claude-agent-sdk**: v0.3.149

### Allowed Origins (IPC origin validation / CSP)
```
https://claude.ai
https://preview.claude.ai
https://claude.com
https://preview.claude.com
app://localhost
*.ant.dev (when dev URL override enabled)
localhost (when dev URL override enabled)
```

### Hostnames Used
```
claude.ai                  — main web app
preview.claude.ai          — preview environment
claude.com                 — authentication / CAI
console.anthropic.com      — console (OAuth callbacks)
platform.claude.com        — platform auth, OAuth
api.anthropic.com          — backend API
assets.claude.ai           — font assets
downloads.claude.ai        — download server
pivot.claude.ai            — pivot/manifest
support.claude.com         — support
privacy.claude.com         — privacy
code.claude.com            — Claude Code docs
microsoft365.mcp.claude.com — Microsoft 365 MCP
```

---

## 2. OAuth & Authentication

### 2.1 OAuth Configuration (from `index.js`)

```javascript
// Production OAuthConfig
{
  BASE_API_URL:           "https://api.anthropic.com",
  CONSOLE_AUTHORIZE_URL:  "https://platform.claude.com/oauth/authorize",
  CLAUDE_AI_AUTHORIZE_URL:"https://claude.com/cai/oauth/authorize",
  CLAUDE_AI_ORIGIN:       "https://claude.ai",
  TOKEN_URL:              "https://platform.claude.com/v1/oauth/token",
  API_KEY_URL:            "https://api.anthropic.com/api/oauth/claude_cli/create_api_key",
  ROLES_URL:              "https://api.anthropic.com/api/oauth/claude_cli/roles",
  CONSOLE_SUCCESS_URL:    "https://platform.claude.com/buy_credits?returnUrl=/oauth/code/success%3Fapp%3Dclaude-code",
  CLAUDEAI_SUCCESS_URL:   "https://platform.claude.com/oauth/code/success?app=claude-code",
  MANUAL_REDIRECT_URL:    "https://platform.claude.com/oauth/code/callback",
  CLIENT_ID:              "9d1c250a-e61b-44d9-88ed-5944d1962f5e",
  OAUTH_FILE_SUFFIX:      "",
  MCP_PROXY_URL:          "https://mcp-proxy.anthropic.com",
  MCP_PROXY_PATH:         "/v1/mcp/{server_id}"
}
```

### 2.2 OAuth Grant Types

#### a) Refresh Token Grant (`grant_type=refresh_token`)

```
POST https://platform.claude.com/v1/oauth/token

Content-Type: application/json

{
  "grant_type": "refresh_token",
  "refresh_token": "<refresh_token>",
  "client_id": "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
}

Response:
{
  "access_token": "<new_access_token>",
  "id_token": "<new_id_token>",
  "token_type": "Bearer",
  "expires_in": <seconds>,
  "refresh_token": "<new_refresh_token (optional, may rotate)>"
}
```

#### b) JWT Bearer Grant (OIDC Federation)

```
POST https://platform.claude.com/v1/oauth/token

Headers:
  anthropic-beta: oauth-2025-04-20, oidc-federation-2026-04-01

Body (JSON):
{
  "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
  "assertion": "<JWT_token>",
  "federation_rule_id": "<rule_id>",
  "organization_id": "<org_id>",
  "service_account_id": "<sa_id>",     // optional
  "workspace_id": "<ws_id>"            // optional
}
```

#### c) Authorization Code Flow (Interactive)

```
GET https://platform.claude.com/oauth/authorize
  ?client_id=9d1c250a-e61b-44d9-88ed-5944d1962f5e
  &redirect_uri=<desktop_callback>
  &response_type=code
  &code_challenge=<S256_challenge>
  &code_challenge_method=S256

POST https://platform.claude.com/v1/oauth/token
  grant_type=authorization_code
  &code=<code>
  &code_verifier=<verifier>
  &client_id=9d1c250a-e61b-44d9-88ed-5944d1962f5e
  &redirect_uri=<desktop_callback>
```

Also available:
```
GET https://claude.com/cai/oauth/authorize  // CAI-specific flow
```

### 2.3 Google OAuth (Vertex AI)

```
Authorization URL:  https://accounts.google.com/o/oauth2/v2/auth
Token URL:          https://oauth2.googleapis.com/token
Revoke URL:         https://oauth2.googleapis.com/revoke
STS URL:            https://sts.googleapis.com
IAM Credentials:    https://iamcredentials.googleapis.com
Default Scopes:     openid, email, https://www.googleapis.com/auth/cloud-platform
Timeout:            10,000ms
```

### 2.4 Token Provider Architecture

From `@anthropic-ai/claude-agent-sdk` v0.3.149:

- **`OidcFederationProvider`**: JWT assertion-based; configurable federation rule ID, org, workspace, service account
- **`UserOAuthProvider`**: Refresh-token-based; caches credentials to file; supports `forceRefresh`
- **`CachedTokenProvider`**: Wraps another provider; in-memory caching; background refresh; advisory error handling

**Refresh threshold**: 30 seconds before token expiry (in-memory cache), 24h for config-level refresh

### 2.5 Credential File Format

```
~/.config/anthropic/configs/<profile>.json       — OAuth config (token endpoint, client_id, scopes)
~/.config/anthropic/credentials/<profile>.json    — OAuth credentials (access_token, refresh_token, id_token)
~/.config/anthropic/active_config                 — plain text: name of active profile
```

**Config file** (`configs/<profile>.json`):
```json
{
  "version": "1.0",
  "auth_type": "user_oauth",
  "client_id": "9d1c250a-e61b-44d9-88ed-5944d1962f5e",
  "token_url": "https://platform.claude.com/v1/oauth/token",
  "scopes": ["openid", "email", "profile"]
}
```

**Credential file** (`credentials/<profile>.json`):
```json
{
  "access_token": "<token>",
  "refresh_token": "<token>",
  "id_token": "<jwt>",
  "token_type": "Bearer",
  "expires_in": 3600,
  "expires_at": <unix_timestamp>
}
```

**Permissions**: `chmod 600` enforced (must not be group/world readable or writable)

---

## 3. API Endpoints (claude.ai/api/*)

Found in `ion-dist/assets/v1/*.js` (renderer bundles):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/desktop/darwin/universal/dmg/latest/redirect` | GET | Desktop app download redirect |
| `/api/desktop/win32/x64/setup/latest/redirect` | GET | Desktop app download redirect (Windows) |
| `/api/mcp/auth_callback` | GET/POST | MCP OAuth callback handler |

Found in `index.js` (main process):

| Endpoint | Description |
|----------|-------------|
| `/api/account` | Account info |
| `/api/account/settings` | Account settings |
| `/api/account_profile` | Account profile |
| `/api/bootstrap` | Bootstrap config (initialization data) |
| `/api/bootstrap/` | Bootstrap (with trailing slash variant) |
| `/api/claude_code/memory` | Claude Code memory storage |
| `/api/desktop/` | Desktop-specific API base |
| `/api/desktop/features` | Feature flags for desktop |
| `/api/directory/` | Directory/marketplace |
| `/api/event_logging/` | Telemetry events |
| `/api/organizations/` | Organizations base |

From `@anthropic-ai/claude-agent-sdk` API client:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/messages` | POST | Send message |
| `/v1/messages/count_tokens` | POST | Count tokens |
| `/v1/messages?beta=true` | POST | Messages with beta features |
| `/v1/code/sessions` | POST | Create Claude Code session |
| `/v1/code/sessions/{id}/bridge` | POST | Bridge to session |
| `/v1/sessions/{id}/events` | GET/POST | Session events |
| `/v1/models` | GET | List models |
| `/v1/models/{id}` | GET | Get model details |
| `/v1/environments` | GET/POST/DELETE | Managed agent environments |
| `/v1/environments/{id}/archive` | POST | Archive environment |
| `/v1/files` | GET/DELETE | File management |
| `/v1/oauth/token` | POST | OAuth token endpoint (relative) |

### Beta Headers used:
- `anthropic-beta: oauth-2025-04-20`
- `anthropic-beta: oidc-federation-2026-04-01`
- `anthropic-beta: managed-agents-2026-04-01`
- `anthropic-beta: files-api-2025-04-14`
- `anthropic-beta: token-counting-2024-11-01`
- `anthropic-beta: structured-outputs-2025-12-15`

### API Version Header:
- `anthropic-version: 2023-06-01`

---

## 4. Anthropic API Endpoints (api.anthropic.com)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/desktop/{platform}/{arch}/{installer}/update?device_id={id}` | GET | Check for desktop updates |
| `/api/oauth/claude_cli/create_api_key` | POST | Create API key for CLI auth |
| `/api/oauth/claude_cli/roles` | GET | List available roles |
| `/api/event_logging/` | POST | Telemetry event logging |

**Platform variants**: `darwin`, `win32`
**Arch variants**: `universal`, `x64`, `arm64`
**Installer variants**: `squirrel`, `msix`

---

## 5. Platform OAuth Endpoints (platform.claude.com)

| Endpoint | Purpose |
|----------|---------|
| `https://platform.claude.com/oauth/authorize` | Authorization endpoint (OAuth code flow) |
| `https://platform.claude.com/v1/oauth/token` | Token endpoint (refresh_token, authorization_code, JWT bearer) |
| `https://platform.claude.com/oauth/code/callback` | OAuth callback handler (manual redirect) |
| `https://platform.claude.com/oauth/code/success?app=claude-code` | Success redirect for Claude Code |
| `https://platform.claude.com/buy_credits?returnUrl=/oauth/code/success%3Fapp%3Dclaude-code` | Buy credits redirect |

### Console URLs (console.anthropic.com)

| Endpoint | Purpose |
|----------|---------|
| `https://console.anthropic.com/oauth/code/callback` | Console OAuth callback |
| `https://console.staging.ant.dev/oauth/code/callback` | Staging OAuth callback |

### Desktop Callback URLs (local)

| Endpoint | Purpose |
|----------|---------|
| `http://localhost:3000/oauth/code/callback` | Local dev callback |
| `http://127.0.0.1:3000/oauth/code/callback` | Local dev callback (IP) |

### Client IDs

| Environment | Client ID |
|-------------|-----------|
| Production | `9d1c250a-e61b-44d9-88ed-5944d1962f5e` |
| Local dev | `22422756-60c9-4084-8eb7-27705fd5cf9a` |

---

## 6. Billing & Subscription

### API Key Provisioning

```
POST https://api.anthropic.com/api/oauth/claude_cli/create_api_key

Headers:
  Authorization: Bearer <access_token>
  Content-Type: application/json
  anthropic-version: 2023-06-01

Response:
{
  "api_key": "sk-ant-...",
  "key_id": "...",
  "name": "...",
  "created_at": "...",
  "expires_at": "..."
}
```

### Roles

```
GET https://api.anthropic.com/api/oauth/claude_cli/roles

Headers:
  Authorization: Bearer <access_token>
```

### Buy Credits

```
GET https://platform.claude.com/buy_credits?returnUrl=/oauth/code/success%3Fapp%3Dclaude-code
```

### Session-Level Budget Tracking

Variables tracked per session:
- `maxThinkingTokens`, `maxTurns`, `maxBudgetUsd`, `taskBudget`
- `totalCostUSD`, `totalAPIDuration`, `totalToolDuration`
- `hasUnknownModelCost` (flag)
- `modelUsage` (Map per-model usage)

---

## 7. Rate Limiting

### HTTP 429 Handling
- Dedicated error class for 429 responses with `retryAfter` parsing
- Full error hierarchy: 400/401/403/404/409/422/429/500+
- Headers: `request-id`, `retry-after`

### OpenTelemetry Rate Limiting Attributes
- `aspnetcore.rate_limiting.policy`
- `aspnetcore.rate_limiting.result` (acquired, endpoint_limiter, global_limiter, request_canceled)
- `aspnetcore.request.is_unhandled`
- Metrics: `ASPNETCORE_RATE_LIMITING_REQUESTS`, `ASPNETCORE_RATE_LIMITING_REQUEST_LEASE_DURATION`, `ASPNETCORE_RATE_LIMITING_REQUEST_TIME_IN_QUEUE`

### VM Diagnostics Rate Limiting
- Rate-limited to once every 30 seconds

---

## 8. MCP Authentication

### MCP Auth Callback
```
Path: claude.ai/api/mcp/auth_callback
Host: https://claude.ai

Used for OAuth-based MCP server authorization
```

### Direct MCP Server Auth (IPC)
```
IPC Channel: claude.web._LocalAgentModeSessions
  └─ authorizeDirectMcpServer(name)
  └─ pendingOAuthMcpConfig(name)
  └─ disconnectDirectMcpServer(name)
  └─ getDirectMcpServerStatuses()
  └─ triggerInteractiveAuth()
  └─ revokeInteractiveAuth()
```

### MCP Proxy
```
Production: https://mcp-proxy.anthropic.com/v1/mcp/{server_id}
```

### OAuth Scopes for MCP (from bundle)
```
anthropic-console
anthropic-marketplace
anthropic-plugins
agent-skills
anthropic-agent-skills
life-sciences
knowledge-work-plugins
claude-for-legal
claude-for-financial-services
financial-services-plugins
```

### MCP Auth Provider Types
- `anthropic` — built-in OAuth
- `gateway` — custom gateway
- `vertex` — GCP Vertex AI
- `bedrock` — AWS Bedrock
- `foundry` — custom foundry

### Auth Provider Config Schema
```typescript
{
  provider: "anthropic" | "gateway" | "vertex" | "bedrock" | "foundry",
  apiKey?: string,
  organizationKey?: string,
  credentialKind?: "oauth" | "none",
  credentialHelper?: any,
  // + per-provider fields
}
```

---

## 9. Sessions (Claude Code)

### Session Create
```
POST {api_base}/v1/code/sessions

Headers:
  Authorization: Bearer <token>
  anthropic-version: 2023-06-01
  User-Agent: ClaudeDesktop/...

Body:
{
  "title": "<session_title>",
  "bridge": {},
  "tags": ["<tags>"],
  "config": { "cwd": "<cwd>" }
}

Response:
{
  "session": { "id": "cse_<uuid>" }
}
```

### Session Bridge
```
POST {api_base}/v1/code/sessions/{session_id}/bridge

Response:
{
  "worker_jwt": "<jwt>",
  "expires_in": <seconds>,
  "api_base_url": "<url>",
  "worker_epoch": <number>
}
```

### Session Event Stream
```
GET {api_base}/v1/code/sessions/{session_id}/events/stream
  (Server-Sent Events)
```

### Session IDs
- Start with `cse_` prefix
- Also `session_` prefix variant

### Activity Handoff (macOS)
```swift
// Universal Links / NSUserActivity
activityType = "com.anthropic.claude.code.session"
userInfo: { "v": 1, "sessionId": "<id>" }
```

---

## 10. Electron IPC Architecture

### IPC Naming Convention
```
$eipc_message$_<uuid>_$_<namespace>_$_<interface>_$_<method>
```
UUID: `4b4c74b4-c95b-4330-ad93-13e1112df630`

### Identified IPC Namespaces

| Namespace | Interface | Methods |
|-----------|-----------|---------|
| `claude.web` | `_LocalAgentModeSessions` | `authorizeDirectMcpServer`, `disconnectDirectMcpServer`, `pendingOAuthMcpConfig`, `getDirectMcpServerStatuses`, `triggerInteractiveAuth`, `revokeInteractiveAuth` |
| `claude.simulator` | `_Simulator` | `attach`, `detach`, `listDevices`, `installAndLaunch`, `gesture` |
| — | — | `RequestOpenMcpSettings` |

### WebContents Send Channels (Renderer ← Main)
- `cu-teach:show` — Show computer use teaching overlay
- `cu-teach:hide` — Hide computer use teaching overlay
- `$eipc_message$_<uuid>_$_...$store$_update` — State store updates

### Preload Exposed APIs
- `window.api.getAccessToken()`
- `window.api.getTrustedDeviceToken()`
- `window.api.getBuildProps()`
- `window.api.getAppName()`
- `window.api.getSupport()`

---

## 11. Data Storage & Config Files

### Desktop App Data Paths
```
~/Library/Application Support/Claude/                    — default instance
~/Library/Application Support/Claude-3p/                  — third-party instance

config.json                                              — Electron app config
claude_desktop_config.json                               — user settings (MCP, prefs)
developer_settings.json                                  — dev settings

configLibrary/                                           — JSON config library
  <uuid>.json                                            — individual config entry
  _meta.json                                             — metadata index

claude-code-sessions/                                    — session history
local-agent-mode-sessions/                               — local MCP sessions

Claude Extensions Settings/                              — extension settings
extensions-installations.json                            — installed extensions

bridge-state.json                                        — session bridge state
extensions-blocklist.json                                — blocked extensions
cowork-enabled-cli-ops.json                             — cowork ops
window-state.json                                        — window position/state
git-worktrees.json                                       — git worktree state
sentry/                                                  — Sentry error reports
```

### macOS Managed Preferences
```
/Library/Managed Preferences/com.anthropic.claudefordesktop.plist
```

### Config Library Schema
Each entry in `configLibrary/` has:
- `content/<name>` — JSON data file
- `_meta.json` — index of all entries

### Third-Party Instance Detection
- `Claude-3p` suffix in `userData` path
- Separate icon, process name, and config namespace

---

## 12. Feature Flags

### Feature Support Matrix

| Feature | Requirements |
|---------|-------------|
| `nativeQuickEntry` | macOS 13+ |
| `quickEntryDictation` | macOS 14+, mic not restricted |
| `chillingSlothFeat` | Gateway dependency |
| `chillingSlothEnterprise` | Enterprise policy |
| `chillingSlothLocal` | Always supported |
| `yukonSilver` | Cowork VM (macOS 14+ or Win32) |
| `yukonSilverGems` | Derived from yukonSilver |
| `wakeScheduler` | macOS 13+ with feature flag |
| `desktopTopBar` | Always supported |
| `ccdPlugins` | Always supported |
| `computerUse` | Platform-dependent |
| `coworkKappa` | Currently `unavailable` |
| `framebufferPreview` | Feature flag gated |
| `iosSimulator` | macOS only |
| `grandPrix` / `grandPrixRequest` | Feature flag gated |
| `loudPenguin` | Feature flag 4116586025 |
| `plushRaccoon` | Gated |
| `quietPenguin` | macOS/Win32 only |

### GrowthBook Feature Flags
Feature flags evaluated via numeric IDs:
- `2976814254`, `3246569822`, `1143815894`, `123929380`
- `1696890383`, `2307090146`, `2940196192`
- `574905726`, `1101873029`, `3150971238`

### Telemetry Services & Toggle Keys
| Service | Toggle Key | Endpoints |
|---------|-----------|-----------|
| `anthropic-telemetry` | `disableNonessentialTelemetry` | `claude.ai/api/event_logging/` |
| `anthropic-mcp-registry` | `disableNonessentialServices` | `claude.ai/mcp-registry/`, `claude.ai/api/directory/` |
| `connector-favicons` | `disableNonessentialServices` | Google favicons services |
| `artifact-sandbox` | `disableNonessentialServices` | Sandbox frame-src |

---

## 13. Update System

### Update Check URL
```
GET https://api.anthropic.com/api/desktop/{platform}/{arch}/{installer}/update?device_id=<device_id>
```

### Update Flow
1. Check for updates at startup + periodic
2. Download in background via VM warm download
3. Prompt user to restart (72-hour enforcement delay before forced restart)
4. On macOS: ShipIt job manager for rollback/unstage

### Device ID
- Generated via `PQ()` function
- Persisted across app instances
- Used for update targeting

### Auto-Update Policies
- Enterprise MDM: `disableAutoUpdates` config
- Enforcement delay: 72 hours default

---

## 14. Enterprise Configuration

### MDM Policy Keys (macOS)
Managed via `com.anthropic.claudefordesktop` plist:
```
/Library/Managed Preferences/com.anthropic.claudefordesktop.plist
```

### Windows Policy
```
HKEY_CURRENT_USER\SOFTWARE\Policies\Claude
HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Claude
```

### Configurable Settings
- Inference provider override: `anthropic`, `gateway`, `vertex`, `bedrock`, `foundry`
- Custom API base URL
- Feature flags via policy
- Auto-update disable
- Egress allowlist
- Telemetry disable

### Deployment Modes
- `1p` — first-party (standard)
- `3p` — third-party (reseller/managed)
- `clear` — reset
- OAuth and credentials scoped by deployment mode

### Scoped Configuration
```typescript
{
  source: "desktop" | "user_settings" | "managed_settings" | "coder",
  provider?: "anthropic" | "gateway" | "vertex" | "bedrock" | "foundry",
  bootstrapHost?: string,
  // + per-source overrides
}
```

---

*Generated from reverse-engineered Claude Desktop v1.8555.2 bundles (May 2026).*
