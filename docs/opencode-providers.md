# OpenCode провайдеры в MultiManager

## Где хранятся провайдеры OpenCode

Провайдеры OpenCode лежат в файле `~/.config/opencode/opencode.json` в ключе `"provider"`.

Структура:

```json
{
  "provider": {
    "zai-coding-plan": {
      "options": {
        "apiKey": "секретный_ключ",
        "baseURL": "https://api.z.ai/v1"
      }
    },
    "bezrabotnyi": {
      "name": "bezrabotnyi Ollama",
      "options": {
        "apiKey": "any-key",
        "baseURL": "https://llm.bezrabotnyi.com/v1"
      },
      "models": {
        "qwen3-coder:30b": { "name": "qwen3-coder:30b" }
      }
    }
  }
}
```

У каждого провайдера:
- **ключ** — уникальный ID (`"zai-coding-plan"`, `"bezrabotnyi"`, и т.д.)
- `options.apiKey` — ключ API
- `options.baseURL` — URL (опционально)
- `name` — человеческое имя (опционально, для отображения в OpenCode UI)
- `models` — список моделей (опционально)

---

## Multi-provider архитектура

OpenCode — единственная программа в MultiManager с флагом `multi_provider = True`.

Это значит:
- OpenCode может иметь **несколько активных провайдеров одновременно**
- Аккаунты **добавляются** (ADD), а не заменяют друг друга (REPLACE)
- Остальные программы (Claude Code, Codex, Cline, Roo Code, Claude Desktop) — single-provider, только один активный

### UI: Лево/Право

При клике на аккаунт в левой панели, правая панель показывает:

| Тип программы | Действие при checked | Действие при unchecked |
|---|---|---|
| **Single-provider** | `REPLACE` — заменяет текущий активный аккаунт | Ничего (оставляет текущий) |
| **Multi-provider** | `ADD` — добавляет аккаунт в программу | `REMOVE` — убирает аккаунт из программы |

Тип действия явно подписан на каждом чекбоксе.

---

## Импорт (Import)

`import_accounts()` в `accounts.py` при импорте из OpenCode:
- Итерирует все `provider.*` из `opencode.json`
- Для каждого создаёт аккаунт с полем `opencode_provider_id: pname`
- Пропускает только дубликаты по apiKey или baseUrl
- Определяет тип провайдера через `detect_provider(base_url)`

## Apply (запись обратно)

`apply_account()` для OpenCode:
- Берёт `opencode_provider_id` из аккаунта (или генерирует из имени)
- Пишет/обновляет `provider.{prov_id}.options.{apiKey,baseURL}` в `opencode.json`
- Работает для **любого** провайдера (не только zai)

## Remove (удаление из программы)

`remove_account_from_program()`:
- Удаляет `provider.{opencode_provider_id}` из `opencode.json`
- Используется когда в UI снимают чекбокс с активного multi-provider аккаунта

---

## Разница между OpenCode провайдерами и MultiManager аккаунтами

| | OpenCode провайдеры | MultiManager аккаунты |
|---|---|---|
| **Где** | `~/.config/opencode/opencode.json` | `~/.multimanager/config.json` |
| **Структура** | `provider.{id}.options.{apiKey,baseURL}` | `accounts[].{id,provider,api_key,base_url}` |
| **Для чего** | Выбор модели в OpenCode | Управление и роутинг ключей |
| **Импорт** | Из OpenCode → в MultiManager (кнопка Import) | Вручную через UI (+) |
| **Apply (запись обратно)** | Generic — любой провайдер | — |
| **Multi-provider** | Да — все провайдеры активны | Каждый аккаунт — один провайдер |

---

## Бэкенд: ключевые файлы

| Файл | Что делает |
|---|---|
| `multimanager/programs/base.py` | `multi_provider: bool`, `detect_all_active()` |
| `multimanager/programs/opencode.py` | `multi_provider = True`, generic import/apply/remove |
| `multimanager/accounts.py` | `import_accounts()`, `apply_account()`, `remove_account_from_program()` |
| `multimanager/handler.py` | `/api/account-remove-from-program`, `/api/programs` c `multi_provider` |
| `multimanager/templates/app.js` | UI лево/право с ADD/REPLACE/REMOVE семантикой |
