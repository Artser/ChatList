# Схема базы данных ChatList

База данных использует SQLite и состоит из четырех основных таблиц.

## Таблица: prompts (Промты)

Хранит сохраненные пользовательские запросы (промты).

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| id | INTEGER | Первичный ключ, автоинкремент | PRIMARY KEY, AUTOINCREMENT |
| date | TEXT | Дата и время создания промта | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| prompt | TEXT | Текст промта | NOT NULL |
| tags | TEXT | Теги для категоризации (через запятую или JSON) | NULL |

### Индексы:
- `idx_prompts_date` на поле `date` для быстрого поиска по дате
- `idx_prompts_tags` на поле `tags` для поиска по тегам

### Пример данных:
```sql
INSERT INTO prompts (date, prompt, tags) VALUES 
('2024-01-15 10:30:00', 'Объясни квантовую физику', 'наука, физика'),
('2024-01-15 11:00:00', 'Напиши код на Python', 'программирование');
```

---

## Таблица: models (Модели нейросетей)

Хранит информацию о доступных моделях нейросетей и их API-конфигурации.

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| id | INTEGER | Первичный ключ, автоинкремент | PRIMARY KEY, AUTOINCREMENT |
| name | TEXT | Название модели (например, "GPT-4", "DeepSeek") | NOT NULL, UNIQUE |
| api_url | TEXT | URL API для отправки запросов | NOT NULL |
| api_id | TEXT | Идентификатор переменной окружения с API-ключом (например, "OPENAI_API_KEY") | NOT NULL |
| is_active | INTEGER | Флаг активности модели (1 - активна, 0 - неактивна) | NOT NULL, DEFAULT 1 |

### Индексы:
- `idx_models_name` на поле `name` для быстрого поиска
- `idx_models_active` на поле `is_active` для фильтрации активных моделей

### Пример данных:
```sql
INSERT INTO models (name, api_url, api_id, is_active) VALUES 
('GPT-4', 'https://api.openai.com/v1/chat/completions', 'OPENAI_API_KEY', 1),
('DeepSeek', 'https://api.deepseek.com/v1/chat/completions', 'DEEPSEEK_API_KEY', 1),
('Groq', 'https://api.groq.com/openai/v1/chat/completions', 'GROQ_API_KEY', 0);
```

**Важно:** API-ключи хранятся в файле `.env`, а не в базе данных. В таблице хранится только имя переменной окружения.

---

## Таблица: results (Результаты)

Хранит сохраненные ответы от моделей на промты.

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| id | INTEGER | Первичный ключ, автоинкремент | PRIMARY KEY, AUTOINCREMENT |
| prompt_id | INTEGER | Ссылка на промт из таблицы prompts | NOT NULL, FOREIGN KEY |
| model_id | INTEGER | Ссылка на модель из таблицы models | NOT NULL, FOREIGN KEY |
| response_text | TEXT | Текст ответа от модели | NOT NULL |
| created_at | TEXT | Дата и время создания записи | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

### Внешние ключи:
- `prompt_id` → `prompts(id)` ON DELETE CASCADE
- `model_id` → `models(id)` ON DELETE RESTRICT

### Индексы:
- `idx_results_prompt` на поле `prompt_id` для быстрого поиска по промту
- `idx_results_model` на поле `model_id` для поиска по модели
- `idx_results_created` на поле `created_at` для сортировки по дате

### Пример данных:
```sql
INSERT INTO results (prompt_id, model_id, response_text, created_at) VALUES 
(1, 1, 'Квантовая физика изучает...', '2024-01-15 10:35:00'),
(1, 2, 'Квантовая механика - это раздел...', '2024-01-15 10:35:05');
```

---

## Таблица: settings (Настройки)

Хранит настройки приложения в формате ключ-значение.

| Поле | Тип | Описание | Ограничения |
|------|-----|----------|-------------|
| id | INTEGER | Первичный ключ, автоинкремент | PRIMARY KEY, AUTOINCREMENT |
| key | TEXT | Ключ настройки | NOT NULL, UNIQUE |
| value | TEXT | Значение настройки (может быть JSON) | NULL |

### Индексы:
- `idx_settings_key` на поле `key` для быстрого поиска

### Пример данных:
```sql
INSERT INTO settings (key, value) VALUES 
('default_timeout', '30'),
('max_retries', '3'),
('export_format', 'markdown'),
('theme', 'light');
```

---

## Диаграмма связей

```
prompts (1) ──< (N) results
                │
                └──> (N) models (1)
```

- Один промт может иметь множество результатов
- Одна модель может иметь множество результатов
- Результат всегда связан с одним промтом и одной моделью

---

## SQL-скрипт создания базы данных

```sql
-- Таблица prompts
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    prompt TEXT NOT NULL,
    tags TEXT
);

CREATE INDEX IF NOT EXISTS idx_prompts_date ON prompts(date);
CREATE INDEX IF NOT EXISTS idx_prompts_tags ON prompts(tags);

-- Таблица models
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    api_url TEXT NOT NULL,
    api_id TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_models_name ON models(name);
CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active);

-- Таблица results
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER NOT NULL,
    model_id INTEGER NOT NULL,
    response_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_results_prompt ON results(prompt_id);
CREATE INDEX IF NOT EXISTS idx_results_model ON results(model_id);
CREATE INDEX IF NOT EXISTS idx_results_created ON results(created_at);

-- Таблица settings
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT
);

CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key);
```

---

## Примечания

1. **Временная таблица результатов** не хранится в БД. Она создается в памяти приложения при отправке запроса и удаляется при очистке или новом запросе.

2. **API-ключи** хранятся в файле `.env` в корне проекта. Пример:
   ```
   OPENAI_API_KEY=sk-...
   DEEPSEEK_API_KEY=sk-...
   GROQ_API_KEY=gsk_...
   ```

3. **Теги в таблице prompts** можно хранить как:
   - Простую строку через запятую: `"наука, физика, кванты"`
   - JSON массив: `["наука", "физика", "кванты"]`

4. **Даты** хранятся в формате ISO 8601: `YYYY-MM-DD HH:MM:SS`








