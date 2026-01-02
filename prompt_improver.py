"""
Модуль для улучшения промтов с помощью AI-моделей.
Инкапсулирует логику улучшения промтов.
"""
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Шаблон промта для улучшения
IMPROVEMENT_PROMPT_TEMPLATE = """Ты - эксперт по написанию эффективных промтов для AI-моделей.

Проанализируй и улучши следующий промт:
- Сделай его более четким и конкретным
- Добавь структуру, если необходимо
- Убедись, что инструкции понятны
- Оптимизируй для получения лучших результатов

Исходный промт:
{original_prompt}

Верни только улучшенную версию промта без дополнительных комментариев или объяснений."""


def generate_improvement_prompt(original: str) -> str:
    """
    Формирует промт для улучшения на основе исходного промта.
    
    Args:
        original: Исходный промт для улучшения
    
    Returns:
        Сформированный промт для отправки в модель
    """
    if not original or not original.strip():
        raise ValueError("Исходный промт не может быть пустым")
    
    return IMPROVEMENT_PROMPT_TEMPLATE.format(original_prompt=original.strip())


def parse_improved_prompt(response: str) -> str:
    """
    Извлекает улучшенный промт из ответа модели.
    Удаляет лишние форматирования и комментарии.
    
    Args:
        response: Ответ модели
    
    Returns:
        Очищенный улучшенный промт
    """
    if not response:
        return ""
    
    # Удаляем markdown код-блоки
    # Убираем ```prompt или ``` в начале и конце
    response = re.sub(r'^```(?:prompt|text|markdown)?\s*\n?', '', response, flags=re.MULTILINE)
    response = re.sub(r'\n?```\s*$', '', response, flags=re.MULTILINE)
    
    # Удаляем префиксы типа "Улучшенный промт:", "Вот улучшенная версия:" и т.д.
    prefixes = [
        r'^улучшенный промт:\s*',
        r'^вот улучшенная версия:\s*',
        r'^улучшенная версия:\s*',
        r'^improved prompt:\s*',
        r'^here is the improved version:\s*',
        r'^improved version:\s*',
    ]
    for prefix in prefixes:
        response = re.sub(prefix, '', response, flags=re.IGNORECASE | re.MULTILINE)
    
    # Удаляем лишние пробелы в начале и конце
    response = response.strip()
    
    # Если ответ пустой после очистки, возвращаем исходный ответ
    if not response:
        logger.warning("После парсинга ответ оказался пустым")
        return response
    
    return response


def improve_prompt(original_prompt: str, model_name: str, model_data: dict) -> Tuple[Optional[str], Optional[str]]:
    """
    Улучшает промт с помощью указанной модели.
    
    Args:
        original_prompt: Исходный промт для улучшения
        model_name: Имя модели для улучшения (для логирования)
        model_data: Словарь с данными модели (api_url, api_id и т.д.)
    
    Returns:
        Кортеж (улучшенный_промт, ошибка): (текст улучшенного промта или None, текст ошибки или None)
    """
    try:
        # Импортируем здесь, чтобы избежать циклических зависимостей
        import network
        
        # Формируем промт для улучшения
        improvement_prompt = generate_improvement_prompt(original_prompt)
        
        logger.info(f"Отправка запроса на улучшение промта в модель {model_name}")
        
        # Отправляем запрос к модели
        response, error = network.send_prompt_to_model(improvement_prompt, model_data)
        
        if error:
            logger.error(f"Ошибка при улучшении промта: {error}")
            return None, error
        
        if not response:
            error_msg = "Получен пустой ответ от модели"
            logger.error(error_msg)
            return None, error_msg
        
        # Парсим ответ
        improved_prompt = parse_improved_prompt(response)
        
        if not improved_prompt:
            error_msg = "Не удалось извлечь улучшенный промт из ответа модели"
            logger.error(error_msg)
            return None, error_msg
        
        logger.info(f"Промт успешно улучшен. Длина: {len(improved_prompt)} символов")
        return improved_prompt, None
        
    except ValueError as e:
        error_msg = str(e)
        logger.error(f"Ошибка валидации: {error_msg}")
        return None, error_msg
    except Exception as e:
        error_msg = f"Неожиданная ошибка при улучшении промта: {str(e)}"
        logger.error(error_msg)
        return None, error_msg

