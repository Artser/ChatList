"""
Модуль для отправки запросов к API нейросетей.
Содержит клиенты для разных API и функции для отправки промтов.
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from abc import ABC, abstractmethod
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения из .env и .env.local
load_dotenv()  # Загружает .env
load_dotenv('.env.local')  # Загружает .env.local (если существует)

# Настройка логирования
import os
from datetime import datetime

# Создаем директорию для логов, если её нет
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Настройка логирования с записью в файл
log_file = os.path.join(log_dir, f"chatlist_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()  # Также выводим в консоль
    ]
)
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
    
    def _get_user_friendly_error(self, response: requests.Response) -> str:
        """Преобразует HTTP ошибку в понятное сообщение для пользователя."""
        status_code = response.status_code
        
        # Пытаемся получить детали ошибки из ответа
        try:
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', '')
            error_type = error_data.get('error', {}).get('type', '')
        except:
            error_message = ''
            error_type = ''
        
        # Формируем понятное сообщение в зависимости от кода ошибки
        if status_code == 400:
            msg = "Неправильный запрос"
            if error_message:
                msg += f": {error_message}"
            return msg
        elif status_code == 401:
            return "Неверный API-ключ. Проверьте правильность ключа в файле .env"
        elif status_code == 402:
            return "Требуется оплата. Пополните баланс аккаунта или выберите другую модель"
        elif status_code == 403:
            return "Доступ запрещен. Проверьте права доступа к API"
        elif status_code == 404:
            if 'openrouter' in self.api_url.lower():
                return f"Модель не найдена. Проверьте правильность имени модели в настройках"
            return "Ресурс не найден. Проверьте URL API"
        elif status_code == 429:
            return "Превышен лимит запросов. Подождите немного и попробуйте снова"
        elif status_code >= 500:
            return f"Ошибка сервера (код {status_code}). Сервис временно недоступен"
        else:
            # Для других кодов используем стандартное сообщение
            msg = f"Ошибка HTTP {status_code}"
            if error_message:
                msg += f": {error_message}"
            return msg
    
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
            
            # Проверяем статус ответа
            if response.status_code >= 400:
                error_msg = self._get_user_friendly_error(response)
                logger.error(f"HTTP {response.status_code}: {error_msg}")
                raise APIError(error_msg)
            
            response_data = response.json()
            
            result = self._extract_response(response_data)
            logger.info(f"Получен ответ длиной {len(result)} символов")
            return result
            
        except APIError:
            # Пробрасываем APIError как есть
            raise
        except requests.exceptions.Timeout:
            error_msg = "Таймаут при запросе. Сервер не ответил вовремя"
            logger.error(error_msg)
            raise APIError(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "Ошибка подключения. Проверьте интернет-соединение"
            logger.error(error_msg)
            raise APIError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Ошибка сети: {str(e)}"
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


class OpenRouterClient(BaseAPIClient):
    """Клиент для OpenRouter API."""
    
    def _get_headers(self) -> Dict[str, str]:
        """Заголовки для OpenRouter."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/Artser/ChatList",  # Опционально, для статистики
            "X-Title": "ChatList"  # Опционально
        }
    
    def _prepare_request_data(self, prompt: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Подготавливает данные для OpenRouter API."""
        # OpenRouter требует указания модели в формате provider/model-name
        # Если модель не указана, используем популярную по умолчанию
        model = model_name or "openai/gpt-4"
        return {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
    
    def _extract_response(self, response_data: Dict[str, Any]) -> str:
        """Извлекает ответ из OpenRouter API."""
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
    
    # Определяем тип клиента по URL или имени
    is_openrouter = 'openrouter' in api_url.lower() or 'openrouter' in name
    
    # Для OpenRouter всегда используем OPENROUTER_API_KEY
    if is_openrouter:
        api_key = get_api_key('OPENROUTER_API_KEY')
        if not api_key:
            logger.error("Не найден API-ключ OPENROUTER_API_KEY")
            return None
        return OpenRouterClient(api_key, api_url)
    else:
        # Для других API используем api_id как имя переменной окружения
        api_key = get_api_key(api_id)
        if not api_key:
            logger.error(f"Не найден API-ключ для {api_id}")
            return None
        
        if 'openai' in api_url.lower() or 'openai' in name:
            return OpenAIClient(api_key, api_url)
        elif 'deepseek' in api_url.lower() or 'deepseek' in name:
            return DeepSeekClient(api_key, api_url)
        elif 'groq' in api_url.lower() or 'groq' in name:
            return GroqClient(api_key, api_url)
        else:
            # По умолчанию используем OpenAI-совместимый клиент
            return OpenAIClient(api_key, api_url)


def send_prompt_to_model(prompt: str, model_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Отправляет промт в модель и возвращает ответ.
    
    Args:
        prompt: Текст промта
        model_data: Словарь с данными модели
    
    Returns:
        Кортеж (ответ, ошибка): (текст ответа или None, текст ошибки или None)
    """
    try:
        client = create_client(model_data)
        if not client:
            return None, "Не удалось создать клиент API"
        
        # Для OpenRouter используем api_id как имя модели
        # Для других API model_name остается None (используется значение по умолчанию)
        api_url = model_data.get('api_url', '').lower()
        name = model_data.get('name', '').lower()
        is_openrouter = 'openrouter' in api_url or 'openrouter' in name
        
        model_name = None
        if is_openrouter:
            # Для OpenRouter api_id содержит имя модели (например, "meta-llama/llama-3.3-70b-instruct")
            model_name = model_data.get('api_id')
        
        response = client.send_request(prompt, model_name=model_name)
        return response, None
    except APIError as e:
        error_msg = str(e)
        logger.error(f"Ошибка API: {error_msg}")
        return None, error_msg
    except Exception as e:
        error_msg = f"Неожиданная ошибка: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


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
            response, error = send_prompt_to_model(prompt, model_data)
            return {
                'model_id': model_id,
                'model_name': model_name,
                'response': response,
                'error': error
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



