"""
Модуль для работы с моделями нейросетей.
Содержит класс Model и функции для управления моделями.
"""
from typing import List, Optional, Tuple
import db


class Model:
    """Класс для представления модели нейросети."""
    
    def __init__(self, id: int, name: str, api_url: str, api_id: str, is_active: int = 1):
        self.id = id
        self.name = name
        self.api_url = api_url
        self.api_id = api_id
        self.is_active = bool(is_active)
    
    def __repr__(self):
        return f"Model(id={self.id}, name='{self.name}', is_active={self.is_active})"
    
    def to_dict(self) -> dict:
        """Преобразует модель в словарь."""
        return {
            'id': self.id,
            'name': self.name,
            'api_url': self.api_url,
            'api_id': self.api_id,
            'is_active': 1 if self.is_active else 0
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Model':
        """Создает объект Model из словаря."""
        return cls(
            id=data['id'],
            name=data['name'],
            api_url=data['api_url'],
            api_id=data['api_id'],
            is_active=data.get('is_active', 1)
        )


def load_models() -> List[Model]:
    """Загружает все модели из базы данных."""
    models_data = db.get_all_models()
    return [Model.from_dict(m) for m in models_data]


def load_active_models() -> List[Model]:
    """Загружает только активные модели из базы данных."""
    models_data = db.get_active_models()
    return [Model.from_dict(m) for m in models_data]


def get_model_by_id(model_id: int) -> Optional[Model]:
    """Получает модель по ID."""
    models_data = db.get_all_models()
    for m in models_data:
        if m['id'] == model_id:
            return Model.from_dict(m)
    return None


def validate_model_data(name: str, api_url: str, api_id: str) -> Tuple[bool, Optional[str]]:
    """
    Валидирует данные модели.
    Возвращает (is_valid, error_message).
    """
    if not name or not name.strip():
        return False, "Название модели не может быть пустым"
    
    if not api_url or not api_url.strip():
        return False, "API URL не может быть пустым"
    
    if not api_url.startswith(('http://', 'https://')):
        return False, "API URL должен начинаться с http:// или https://"
    
    if not api_id or not api_id.strip():
        return False, "API ID (имя переменной окружения) не может быть пустым"
    
    return True, None


def create_model(name: str, api_url: str, api_id: str, is_active: int = 1) -> Optional[Model]:
    """Создает новую модель в базе данных."""
    is_valid, error = validate_model_data(name, api_url, api_id)
    if not is_valid:
        raise ValueError(error)
    
    model_id = db.create_model(name, api_url, api_id, is_active)
    return get_model_by_id(model_id)


def update_model(model_id: int, **kwargs) -> Optional[Model]:
    """Обновляет модель в базе данных."""
    # Валидация, если переданы соответствующие поля
    if 'name' in kwargs or 'api_url' in kwargs or 'api_id' in kwargs:
        name = kwargs.get('name', '')
        api_url = kwargs.get('api_url', '')
        api_id = kwargs.get('api_id', '')
        
        # Получаем текущие данные модели
        current_model = get_model_by_id(model_id)
        if not current_model:
            return None
        
        # Заполняем недостающие поля текущими значениями
        name = name or current_model.name
        api_url = api_url or current_model.api_url
        api_id = api_id or current_model.api_id
        
        is_valid, error = validate_model_data(name, api_url, api_id)
        if not is_valid:
            raise ValueError(error)
    
    success = db.update_model(model_id, **kwargs)
    if success:
        return get_model_by_id(model_id)
    return None


def toggle_model_active(model_id: int) -> Optional[Model]:
    """Переключает активность модели."""
    success = db.toggle_model_active(model_id)
    if success:
        return get_model_by_id(model_id)
    return None


def delete_model(model_id: int) -> bool:
    """Удаляет модель из базы данных."""
    return db.delete_model(model_id)

