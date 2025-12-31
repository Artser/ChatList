"""
Модуль для отправки запросов к API нейросетей.
Содержит клиенты для разных API и функции для отправки промтов.
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Исключение для ошибок API."""
    pass


class BaseAPIClient(ABC):
    """Базовый класс для API-клиентов."""
    
    def __init__(self, api_key: str, api_url: str, timeout: int = 30):
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout
        self.headers = self._get_headers()
    
    def _get_headers(self) -> Dict[str, str]:
        """Возвращает заголовки для запроса."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    @abstractmethod
    def _prepare_request_data(self, prompt: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Подготавливает данные для запроса."""
        pass
    
    @abstractmethod
    def _extract_response(self, response_data: Dict[str, Any]) -> str:
        """Извлекает текст ответа из ответа API."""
        pass
    
    def send_request(self, prompt: str, model_name: Optional[str] = None) -> str:
        """
        Отправляет запрос к API и возвращает ответ.
        
        Args:
            prompt: Текст промта
            model_name: Имя модели (опционально)
        
        Returns:
            Текст ответа от модели
        
        Raises:
            APIError: При ошибке запроса
        """
        try:
            data = self._prepare_request_data(prompt, model_name)
            
            logger.info(f"Отправка запроса к {self.api_url}")
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            result = self._extract_response(response_data)
            logger.info(f"Получен ответ длиной {len(result)} символов")
            return result
            
        except requests.exceptions.Timeout:
            error_msg = f"Таймаут при запросе к {self.api_url}"
            logger.error(error_msg)
            raise APIError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Ошибка запроса к {self.api_url}: {str(e)}"
            logger.error(error_msg)
            raise APIError(error_msg)
        except (KeyError, ValueError) as e:
            error_msg = f"Ошибка парсинга ответа: {str(e)}"
            logger.error(error_msg)
            raise APIError(error_msg)


class OpenAIClient(BaseAPIClient):
    """Клиент для OpenAI API."""
    
    def _get_headers(self) -> Dict[str, str]:
        """Заголовки для OpenAI."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def _prepare_request_data(self, prompt: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Подготавливает данные для OpenAI API."""
        model = model_name or "gpt-4"
        return {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
    
    def _extract_response(self, response_data: Dict[str, Any]) -> str:
        """Извлекает ответ из OpenAI API."""
        return response_data["choices"][0]["message"]["content"]


class DeepSeekClient(BaseAPIClient):
    """Клиент для DeepSeek API."""
    
    def _get_headers(self) -> Dict[str, str]:
        """Заголовки для DeepSeek."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def _prepare_request_data(self, prompt: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Подготавливает данные для DeepSeek API."""
        model = model_name or "deepseek-chat"
        return {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
    
    def _extract_response(self, response_data: Dict[str, Any]) -> str:
        """Извлекает ответ из DeepSeek API."""
        return response_data["choices"][0]["message"]["content"]


class GroqClient(BaseAPIClient):
    """Клиент для Groq API."""
    
    def _get_headers(self) -> Dict[str, str]:
        """Заголовки для Groq."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def _prepare_request_data(self, prompt: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Подготавливает данные для Groq API."""
        model = model_name or "llama-3.1-70b-versatile"
        return {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
    
    def _extract_response(self, response_data: Dict[str, Any]) -> str:
        """Извлекает ответ из Groq API."""
        return response_data["choices"][0]["message"]["content"]


def get_api_key(api_id: str) -> Optional[str]:
    """
    Получает API-ключ из переменных окружения.
    
    Args:
        api_id: Имя переменной окружения с API-ключом
    
    Returns:
        API-ключ или None, если не найден
    """
    api_key = os.getenv(api_id)
    if not api_key:
        logger.warning(f"API-ключ {api_id} не найден в переменных окружения")
    return api_key


def create_client(model_data: Dict[str, Any]) -> Optional[BaseAPIClient]:
    """
    Создает клиент для работы с API на основе данных модели.
    
    Args:
        model_data: Словарь с данными модели (name, api_url, api_id)
    
    Returns:
        Экземпляр клиента или None, если не удалось создать
    """
    api_id = model_data.get('api_id')
    api_url = model_data.get('api_url')
    name = model_data.get('name', '').lower()
    
    if not api_id or not api_url:
        logger.error("Не указаны api_id или api_url для модели")
        return None
    
    api_key = get_api_key(api_id)
    if not api_key:
        logger.error(f"Не найден API-ключ для {api_id}")
        return None
    
    # Определяем тип клиента по URL или имени
    if 'openai' in api_url.lower() or 'openai' in name:
        return OpenAIClient(api_key, api_url)
    elif 'deepseek' in api_url.lower() or 'deepseek' in name:
        return DeepSeekClient(api_key, api_url)
    elif 'groq' in api_url.lower() or 'groq' in name:
        return GroqClient(api_key, api_url)
    else:
        # По умолчанию используем OpenAI-совместимый клиент
        return OpenAIClient(api_key, api_url)


def send_prompt_to_model(prompt: str, model_data: Dict[str, Any]) -> Optional[str]:
    """
    Отправляет промт в модель и возвращает ответ.
    
    Args:
        prompt: Текст промта
        model_data: Словарь с данными модели
    
    Returns:
        Текст ответа или None при ошибке
    """
    try:
        client = create_client(model_data)
        if not client:
            return None
        
        response = client.send_request(prompt)
        return response
    except APIError as e:
        logger.error(f"Ошибка API: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
        return None


def send_prompt_to_models_async(prompt: str, models_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Отправляет промт в несколько моделей параллельно.
    
    Args:
        prompt: Текст промта
        models_list: Список словарей с данными моделей
    
    Returns:
        Список словарей с результатами: {'model_id': int, 'model_name': str, 'response': str, 'error': str}
    """
    import concurrent.futures
    
    results = []
    
    def send_to_model(model_data):
        model_id = model_data.get('id')
        model_name = model_data.get('name', 'Unknown')
        try:
            response = send_prompt_to_model(prompt, model_data)
            if response:
                return {
                    'model_id': model_id,
                    'model_name': model_name,
                    'response': response,
                    'error': None
                }
            else:
                return {
                    'model_id': model_id,
                    'model_name': model_name,
                    'response': None,
                    'error': 'Не удалось получить ответ'
                }
        except Exception as e:
            return {
                'model_id': model_id,
                'model_name': model_name,
                'response': None,
                'error': str(e)
            }
    
    # Используем ThreadPoolExecutor для параллельной отправки
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(send_to_model, model) for model in models_list]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    return results



