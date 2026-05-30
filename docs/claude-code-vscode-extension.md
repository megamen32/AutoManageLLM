# Claude Code VS Code Extension — Research Notes

## Source Code
- **Repo**: https://github.com/yasasbanukaofficial/claude-code/tree/main/src
- **Official**: закрытый исходник (Anthropic), но есть community mirror/reverse-eng

## Extension Info
- **ID**: `anthropic.claude-code`
- **Version tested**: `2.1.114`
- **Bundle**: `~1.9MB` extension.js + resources

## Architecture

### Расширение НЕ шлёт HTTP-запросы к API Anthropic напрямую.
### Расширение запускает встроенный бинарник `claude` CLI как дочерний процесс.

#### Как это работает:
1. Бинарник лежит в `resources/native-binary/claude` (~200MB, Mach-O ARM64)
2. Это тот же самый `claude` CLI, скомпилированный как самостоятельный бинарник (Rust + Node.js runtime)
3. Расширение общается с ним через **stdin/stdout JSON-RPC (MCP-подобный протокол)**
4. Поток: VS Code webview <-> extension.ts (JS) <-> spawn("claude") <-> API

#### Конфигурация — те же файлы, что и у CLI:
| Файл | Назначение |
|------|-----------|
| `~/.claude/settings.json` | Основные настройки (API key, model, permissions) |
| `~/.claude/settings.local.json` | Локальные override'ы |
| `~/.config/anthropic/credentials/` | OAuth credentials |
| `~/.config/anthropic/configs/` | OAuth configs |
| `~/.claude/skills/` | Skills (SKILL.md) |
| `~/.claude/agents/` | Subagents |
| `~/.claude/plugins/` | Plugins |
| `ENV: ANTHROPIC_API_KEY` | API ключ (через env) |
| `ENV: ANTHROPIC_BASE_URL` | Кастомный API endpoint |

#### Протокол общения extension <-> binary:
- JSON-RPC через stdin/stdout (line-delimited JSON)
- Методы: `initialize`, `thread/started`, `turn/completed`, MCP requests/responses
- Бинарник возвращает `userAgent` при инициализации
- Поддерживает MCP server multiplexing (provider namespaces с id prefix)

#### Поддержка кастомных провайдеров:
- Через `settings.json` можно задать `"ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic"`
- Или через env var `ANTHROPIC_BASE_URL`
- Claude Code читает model из settings, можно указать любую модель
- Бинарник содержит встроенный Anthropic SDK (TypeScript/JavaScript), который шлёт запросы на `ANTHROPIC_BASE_URL` или `https://api.anthropic.com`

Пример settings.json для кастомного провайдера (Z.AI / GLM):
```json
{
  "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
  "ANTHROPIC_API_KEY": "your-zai-key",
  "model": "claude-sonnet-4-20250514"
}
```
Z.AI предоставляет Anthropic-совместимый endpoint, поэтому Claude Code работает напрямую.

#### Необходимые условия для кастомного провайдера:
- API должен быть совместим с **Anthropic Messages API** (`/v1/messages`)
- Поддержка streaming (SSE)
- Формат ответа должен совпадать (content blocks, tool_use, etc.)
- Для OpenAI-совместимых API нужен proxy (LiteLLM, OpenRouter)

#### Встроенный в binary SDK:
- `@anthropic-ai/sdk` — полный TypeScript SDK
- Поддержка AWS Bedrock (`AnthropicAws` класс)
- Поддержка Google Vertex AI
- `ANTHROPIC_AWS_BASE_URL`, `ANTHROPIC_AWS_API_KEY`, `ANTHROPIC_AWS_WORKSPACE_ID` для AWS

## Импликации для MultiManager
- Переключение профиля Claude Code в MultiManager **автоматически** переключает и расширение VS Code
- Оба читают одни и те же файлы (`~/.claude/settings.json`)
- Нет отдельной конфигурации для расширения — оно полностью зависит от CLI бинарника
