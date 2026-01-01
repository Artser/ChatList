"""
Простой скрипт для тестирования базы данных.
Проверяет создание таблиц и основные CRUD операции.
"""
import db
import models


def test_database():
    """Тестирует базу данных."""
    print("=" * 50)
    print("Тестирование базы данных ChatList")
    print("=" * 50)
    
    # Инициализация БД
    print("\n1. Инициализация базы данных...")
    db.init_database()
    print("   [OK] База данных инициализирована")
    
    # Тест промтов
    print("\n2. Тестирование операций с промтами...")
    prompt_id = db.create_prompt("Тестовый промт", "тест, проверка")
    print(f"   [OK] Промт создан (ID: {prompt_id})")
    
    prompt = db.get_prompt_by_id(prompt_id)
    assert prompt is not None, "Промт не найден"
    print(f"   [OK] Промт получен: {prompt['prompt']}")
    
    prompts = db.get_all_prompts()
    print(f"   [OK] Всего промтов: {len(prompts)}")
    
    search_results = db.search_prompts("тест")
    print(f"   [OK] Найдено промтов по запросу 'тест': {len(search_results)}")
    
    # Тест моделей
    print("\n3. Тестирование операций с моделями...")
    model_id = db.create_model("Тестовая модель", "https://api.test.com/v1", "TEST_API_KEY", 1)
    print(f"   [OK] Модель создана (ID: {model_id})")
    
    all_models = db.get_all_models()
    print(f"   [OK] Всего моделей: {len(all_models)}")
    
    active_models = db.get_active_models()
    print(f"   [OK] Активных моделей: {len(active_models)}")
    
    # Тест результатов
    print("\n4. Тестирование операций с результатами...")
    results_list = [{
        'prompt_id': prompt_id,
        'model_id': model_id,
        'response_text': 'Тестовый ответ от модели'
    }]
    saved_count = db.save_results(results_list)
    print(f"   [OK] Сохранено результатов: {saved_count}")
    
    all_results = db.get_all_results()
    print(f"   [OK] Всего результатов: {len(all_results)}")
    
    # Тест настроек
    print("\n5. Тестирование операций с настройками...")
    db.set_setting('test_key', 'test_value')
    value = db.get_setting('test_key')
    assert value == 'test_value', "Настройка не сохранена"
    print(f"   [OK] Настройка сохранена и получена: {value}")
    
    # Очистка тестовых данных
    print("\n6. Очистка тестовых данных...")
    db.delete_result(all_results[0]['id'])
    db.delete_model(model_id)
    db.delete_prompt(prompt_id)
    print("   [OK] Тестовые данные удалены")
    
    print("\n" + "=" * 50)
    print("Все тесты пройдены успешно!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        test_database()
    except Exception as e:
        print(f"\n[ERROR] Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

