# Codex CLI & VS Code Extension — Research Notes

## Source Code
- **Repo**: https://github.com/openai/codex
- **Config loading**: https://github.com/openai/codex/blob/abeafbdca17f6102099ac5b792761b6883c52d35/codex-rs/core/src/config/mod.rs#L1544
- **Language**: Rust (core) + TypeScript (extension/shells)

## CLI Binary
- **Path**: `/opt/homebrew/bin/codex` -> symlink to `/opt/homebrew/Caskroom/codex/0.130.0/codex-aarch64-apple-darwin`
- **Type**: Mach-O 64-bit executable arm64 (~200MB), написан на Rust
- **Config**: `~/.codex/config.toml`, `~/.codex/auth.json`
- **Env**: `OPENAI_API_KEY`, `CODEX_HOME` (default: `~/.codex`)

## VS Code Extension: `openai.chatgpt`
- **Version tested**: `26.519.32039-darwin-arm64`
- **Встроенный бинарник**: `bin/macos-aarch64/codex` (~192MB, Mach-O ARM64) — тот же CLI
- **Запуск**: `spawn(extensionUri + "/bin/macos-aarch64/codex", ["app-server", "--analytics-default-enabled"])`
- **Общение**: stdin/stdout JSON-RPC (MCP-подобный протокол)
- **Extension НЕ шлёт запросы к API напрямую** — всё делает бинарник

### Как это работает:
1. Расширение спавнит `codex app-server` как дочерний процесс
2. Передаёт `CODEX_INTERNAL_ORIGINATOR_OVERRIDE` env var (для аналитики)
3. Через stdin/stdout идут JSON-RPC сообщения
4. Бинарник сам ходит в API провайдера

### Конфигурация — те же файлы, что и у CLI:
| Файл | Назначение |
|------|-----------|
| `~/.codex/config.toml` | model_provider, model, MCP servers, features |
| `~/.codex/auth.json` | OAuth токены ChatGPT / API ключи |
| `~/.codex/skills/` | Skills |
| `~/.codex/plugins/` | Plugins |
| `~/.codex/worktrees/` | Git worktrees |
| `ENV: OPENAI_API_KEY` | API ключ OpenAI |
| `ENV: CODEX_HOME` | Override директории (default `~/.codex`) |

## Custom Providers (Кастомные провайдеры)

Codex CLI **нативно поддерживает** другие провайдеры через OpenAI Chat Completions API.

### Способы указать провайдера:
1. **Флаг CLI**: `codex --provider openrouter "prompt"`
2. **config.toml** (рекомендуемый для MultiManager): `model_provider = "openrouter"`

### config.toml — провайдеры и кастомные:
Из исходника (`load_config_with_layer_stack`):
- `model_provider` — задаёт провайдера (строка, ключ из `model_providers` или встроенный)
- `model` — имя модели
- `model_providers` — секция для кастомных провайдеров с полями `base_url`, `api_key`, etc.
- `profiles` — именованные наборы настроек (можно переключать через `config_profile`)
- Мерж: встроенные провайдеры -> пользовательские `model_providers` из config.toml (user-defined не перезаписывают built-in если уже есть)

Пример config.toml для кастомного провайдера:
```toml
model_provider = "glm"
model = "glm-4-flash"

[model_providers.glm]
base_url = "https://open.bigmodel.cn/api/paas/v4"
api_key_env = "GLM_API_KEY"
```

### Встроенные провайдеры:
| Provider | Env var для API key |
|----------|-------------------|
| `openai` (default) | `OPENAI_API_KEY` |
| `openrouter` | `OPENROUTER_API_KEY` |
| `azure` | `AZURE_API_KEY` |
| `gemini` | `GEMINI_API_KEY` |
| `ollama` | `OLLAMA_API_KEY` |
| `mistral` | `MISTRAL_API_KEY` |
| `deepseek` | `DEEPSEEK_API_KEY` |
| `xai` | `XAI_API_KEY` |
| `groq` | `GROQ_API_KEY` |
| `arceeai` | `ARCEEAI_API_KEY` |
| **любой другой** | `<PROVIDER>_API_KEY` |

### Любой кастомный провайдер:
```bash
export <provider>_API_KEY="your-key"
export <provider>_BASE_URL="https://your-api-base-url"
codex --provider <provider>
```

### Для .env файла (в корне проекта):
```
OPENAI_API_KEY=your-key
# или для кастомного:
MYPROVIDER_API_KEY=your-key
MYPROVIDER_BASE_URL=https://my-provider.com/v1
```
Codex автоматически подгрузит через `dotenv/config`.

## Импликации для MultiManager

### Переключение провайдера Codex:
1. Меняем `model_provider` в `~/.codex/config.toml`
2. Меняем API ключ (env var или auth.json)
3. Если кастомный провайдер — добавляем `PROVIDER_BASE_URL` в env
4. Расширение VS Code подхватит автоматически (те же файлы)

### Расширение VS Code `openai.chatgpt`:
- Переключение профиля в MultiManager **автоматически** переключает и расширение
- Оба читают `~/.codex/config.toml` и `~/.codex/auth.json`
- Нет отдельной конфигурации для расширения

### Proxy / Gateway подход:
- Можно направить Codex на свой proxy (LiteLLM, OpenRouter) который транслирует запросы
- Это позволяет использовать ЛЮБОЙ LLM, включая GLM/Z.AI
- Формат: OpenAI Chat Completions API — это стандарт де-факто
