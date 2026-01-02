"""
Модуль для работы с базой данных SQLite.
Инкапсулирует все операции с БД.
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple


DB_NAME = "chatlist.db"


def get_db_connection():
    """Создает и возвращает соединение с базой данных."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
    return conn


def init_database():
    """Инициализирует базу данных, создает все необходимые таблицы."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Таблица prompts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            prompt TEXT NOT NULL,
            tags TEXT
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_prompts_date ON prompts(date)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_prompts_tags ON prompts(tags)
    """)
    
    # Таблица models
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            api_url TEXT NOT NULL,
            api_id TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_models_name ON models(name)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active)
    """)
    
    # Таблица results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_id INTEGER NOT NULL,
            model_id INTEGER NOT NULL,
            response_text TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
            FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE RESTRICT
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_results_prompt ON results(prompt_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_results_model ON results(model_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_results_created ON results(created_at)
    """)
    
    # Таблица settings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key)
    """)
    
    # Таблица prompt_versions для хранения истории улучшений
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_prompt_id INTEGER,
            improved_prompt TEXT NOT NULL,
            model_used TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (original_prompt_id) REFERENCES prompts(id) ON DELETE SET NULL
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_prompt_versions_prompt ON prompt_versions(original_prompt_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_prompt_versions_created ON prompt_versions(created_at)
    """)
    
    conn.commit()
    conn.close()


# ==================== CRUD операции для prompts ====================

def create_prompt(prompt: str, tags: Optional[str] = None) -> int:
    """Создает новый промт и возвращает его ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO prompts (prompt, tags) VALUES (?, ?)",
        (prompt, tags)
    )
    prompt_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return prompt_id


def get_all_prompts() -> List[Dict]:
    """Возвращает все промты."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prompts ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_prompt_by_id(prompt_id: int) -> Optional[Dict]:
    """Возвращает промт по ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def search_prompts(query: str) -> List[Dict]:
    """Поиск промтов по тексту или тегам."""
    conn = get_db_connection()
    cursor = conn.cursor()
    search_pattern = f"%{query}%"
    cursor.execute(
        "SELECT * FROM prompts WHERE prompt LIKE ? OR tags LIKE ? ORDER BY date DESC",
        (search_pattern, search_pattern)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_prompt(prompt_id: int, prompt: str, tags: Optional[str] = None) -> bool:
    """Обновляет промт."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE prompts SET prompt = ?, tags = ? WHERE id = ?",
        (prompt, tags, prompt_id)
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def delete_prompt(prompt_id: int) -> bool:
    """Удаляет промт."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


# ==================== CRUD операции для models ====================

def create_model(name: str, api_url: str, api_id: str, is_active: int = 1) -> int:
    """Создает новую модель и возвращает ее ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO models (name, api_url, api_id, is_active) VALUES (?, ?, ?, ?)",
        (name, api_url, api_id, is_active)
    )
    model_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return model_id


def get_all_models() -> List[Dict]:
    """Возвращает все модели."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM models ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_active_models() -> List[Dict]:
    """Возвращает только активные модели."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM models WHERE is_active = 1 ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_model(model_id: int, **kwargs) -> bool:
    """Обновляет модель. Принимает именованные параметры: name, api_url, api_id, is_active."""
    if not kwargs:
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    allowed_fields = ['name', 'api_url', 'api_id', 'is_active']
    updates = []
    values = []
    
    for key, value in kwargs.items():
        if key in allowed_fields:
            updates.append(f"{key} = ?")
            values.append(value)
    
    if not updates:
        conn.close()
        return False
    
    values.append(model_id)
    query = f"UPDATE models SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, values)
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def toggle_model_active(model_id: int) -> bool:
    """Переключает активность модели."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE models SET is_active = NOT is_active WHERE id = ?",
        (model_id,)
    )
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def delete_model(model_id: int) -> bool:
    """Удаляет модель."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


# ==================== CRUD операции для results ====================

def save_results(results_list: List[Dict]) -> int:
    """
    Сохраняет список результатов в БД.
    Каждый элемент списка должен содержать: prompt_id, model_id, response_text
    Возвращает количество сохраненных записей.
    """
    if not results_list:
        return 0
    
    conn = get_db_connection()
    cursor = conn.cursor()
    count = 0
    
    for result in results_list:
        cursor.execute(
            "INSERT INTO results (prompt_id, model_id, response_text) VALUES (?, ?, ?)",
            (result['prompt_id'], result['model_id'], result['response_text'])
        )
        count += 1
    
    conn.commit()
    conn.close()
    return count


def get_all_results() -> List[Dict]:
    """Возвращает все результаты с информацией о промтах и моделях."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, p.prompt, p.tags, m.name as model_name
        FROM results r
        LEFT JOIN prompts p ON r.prompt_id = p.id
        LEFT JOIN models m ON r.model_id = m.id
        ORDER BY r.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_results_by_prompt(prompt_id: int) -> List[Dict]:
    """Возвращает результаты по промту."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, p.prompt, p.tags, m.name as model_name
        FROM results r
        LEFT JOIN prompts p ON r.prompt_id = p.id
        LEFT JOIN models m ON r.model_id = m.id
        WHERE r.prompt_id = ?
        ORDER BY r.created_at DESC
    """, (prompt_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def search_results(query: str) -> List[Dict]:
    """Поиск результатов по тексту ответа, промту или модели."""
    conn = get_db_connection()
    cursor = conn.cursor()
    search_pattern = f"%{query}%"
    cursor.execute("""
        SELECT r.*, p.prompt, p.tags, m.name as model_name
        FROM results r
        LEFT JOIN prompts p ON r.prompt_id = p.id
        LEFT JOIN models m ON r.model_id = m.id
        WHERE r.response_text LIKE ? OR p.prompt LIKE ? OR m.name LIKE ?
        ORDER BY r.created_at DESC
    """, (search_pattern, search_pattern, search_pattern))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_result(result_id: int) -> bool:
    """Удаляет результат."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM results WHERE id = ?", (result_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


# ==================== Операции для settings ====================

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Получает значение настройки по ключу."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else default


def set_setting(key: str, value: str) -> bool:
    """Устанавливает значение настройки."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()
    return True


# ==================== Операции для prompt_versions ====================

def create_prompt_version(original_prompt_id: Optional[int], improved_prompt: str, model_used: Optional[str] = None) -> int:
    """Создает новую версию улучшенного промта и возвращает его ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO prompt_versions (original_prompt_id, improved_prompt, model_used) VALUES (?, ?, ?)",
        (original_prompt_id, improved_prompt, model_used)
    )
    version_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return version_id


def get_prompt_versions_by_prompt(prompt_id: int) -> List[Dict]:
    """Возвращает все версии улучшений для указанного промта."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM prompt_versions WHERE original_prompt_id = ? ORDER BY created_at DESC",
        (prompt_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_prompt_versions() -> List[Dict]:
    """Возвращает все версии улучшенных промтов."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prompt_versions ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_prompt_version(version_id: int) -> bool:
    """Удаляет версию улучшенного промта."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM prompt_versions WHERE id = ?", (version_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success





