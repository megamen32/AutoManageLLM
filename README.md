# MultiManager

A unified multi-account/profile manager for **Claude Desktop**, **Claude Code**, and **Codex** — all in one local web UI.

Manage profiles, presets, scenes, MCP servers, plugins, skill sync, backups, and data migration between instances without touching config files manually.

## Features

| Tab | What it does |
|-----|-------------|
| **Claude Desktop** | Save/switch/delete profiles per Claude Desktop instance; auto-backup on switch |
| **Claude Code** | Manage presets with environment variables (API keys, models, base URLs); inline env editor |
| **Codex** | Save/switch/delete Codex profiles; manage custom OpenAI-compatible endpoints |
| **Scenes** | Apply a combo of CD + CC + Codex profiles in one click |
| **Skills** | Scan skill directories, sync SKILL.md between master and target roots, diff viewer |
| **Codex endpoint** | Set a custom `OPENAI_BASE_URL` and generate a wrapper script |
| **MCP** | View all MCP servers from all tools; add/edit/delete/toggle |
| **Plugins** | View and toggle Claude Code and Codex plugins |
| **Settings** | Auto-backup toggle, manual backup/restore, quick-launch alias generator, Claude Desktop data sync (IndexedDB copy between instances) |

## Quick Start

```bash
python3 app.py
```

Then open the URL printed in the terminal (usually `http://127.0.0.1:5xxxx/`).

The UI will open automatically in your default browser on first run.

### .app Bundle (macOS)

A `MultiManager.app` bundle is included. Double-click it to launch without opening Terminal.

## Requirements

- Python 3.11+ (uses `tomllib` from stdlib for Codex TOML parsing)
- macOS (paths are hardcoded for `~/Library/Application Support/Claude*`, `~/.claude/`, `~/.codex/`)
- Claude Desktop / Claude Code / Codex installed (optional — app works with whatever is present)

## How It Works

- Config is stored in `~/.multimanager/config.json` (separate from tool configs)
- Backups go to `~/.multimanager/backups/`
- The app runs a local HTTP server bound to `127.0.0.1` on a random free port
- All editing is done directly on the tool's config files (JSON or TOML)
- Claude Desktop skills are synced via file copy; other tools can use symlinks

## Security

- The app server only listens on `127.0.0.1` (localhost)
- No telemetry, no network calls except localhost
- Credentials stay in your existing config files (no copies stored by MultiManager)

## File Structure

```
.
├── app.py                          # Main application (Python + embedded HTML/JS)
├── MultiManager.app/               # macOS .app bundle wrapper
│   └── Contents/
│       ├── Info.plist
│       ├── MacOS/
│       │   ├── MultiManager        # Launch script
│       │   └── app.py              # Copy of main app
│       └── Resources/
│           └── app.py              # Symlink or copy
├── README.md
└── .gitignore
```
