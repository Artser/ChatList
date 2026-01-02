"""
Скрипт для генерации иконки приложения app.ico
Создает красный круг на синем фоне в различных размерах.
"""
from PIL import Image, ImageDraw


def create_icon_image(size: int) -> Image.Image:
    """
    Создает изображение иконки заданного размера.
    
    Args:
        size: Размер изображения (ширина и высота в пикселях)
    
    Returns:
        Объект PIL Image с красным кругом на синем фоне
    """
    # Создаем изображение с синим фоном
    image = Image.new('RGBA', (size, size), color=(0, 0, 255, 255))  # Синий фон
    
    # Создаем объект для рисования
    draw = ImageDraw.Draw(image)
    
    # Вычисляем параметры круга
    # Оставляем небольшой отступ от краев (5% от размера)
    margin = int(size * 0.05)
    circle_coords = [
        margin,  # x0
        margin,  # y0
        size - margin,  # x1
        size - margin  # y1
    ]
    
    # Рисуем красный круг
    draw.ellipse(circle_coords, fill=(255, 0, 0, 255))  # Красный круг
    
    return image


def create_ico_file(output_path: str = "app.ico"):
    """
    Создает файл иконки в формате ICO с несколькими размерами.
    
    Args:
        output_path: Путь к выходному файлу (по умолчанию "app.ico")
    """
    # Размеры для иконки
    sizes = [256, 128, 64, 48, 32, 16]
    
    # Создаем список изображений для всех размеров
    images = []
    for size in sizes:
        img = create_icon_image(size)
        images.append(img)
    
    # Сохраняем все размеры в один ICO файл
    # Для ICO формата с несколькими размерами нужно использовать метод save
    # с параметром sizes, который указывает список кортежей (width, height)
    # PIL автоматически включит все указанные размеры в ICO файл
    # Используем самое большое изображение как основное
    images[0].save(
        output_path,
        format='ICO',
        sizes=[(size, size) for size in sizes]
    )
    
    print(f"Иконка успешно создана: {output_path}")
    print(f"Размеры: {', '.join([f'{s}x{s}' for s in sizes])}")


def main():
    """Главная функция."""
    print("Генерация иконки приложения...")
    print("Создание красного круга на синем фоне...")
    
    # Создаем иконку
    create_ico_file("app.ico")
    
    print("\nГотово!")


if __name__ == "__main__":
    main()

