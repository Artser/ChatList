# Настройка GitHub Pages

## Почему нет кнопки "Visit Site"?

Кнопка "Visit Site" появляется **только после успешного развертывания** GitHub Pages. Сейчас нужно настроить развертывание.

## Пошаговая настройка

### Шаг 1: Настройка источника в GitHub

1. Перейдите в **Settings** → **Pages**
2. В разделе **Source** выберите:
   - **Source**: `GitHub Actions` (уже выбрано)
3. Сохраните изменения

### Шаг 2: Настройка workflow

1. На странице GitHub Pages нажмите на карточку **"Static HTML"**
2. Нажмите кнопку **"Configure"**
3. GitHub создаст файл `.github/workflows/pages.yml` (если его еще нет)
4. Или используйте существующий файл `.github/workflows/pages.yml` из репозитория

### Шаг 3: Запуск развертывания

Есть два способа:

#### Вариант A: Автоматически (при push)
```powershell
# Закоммитьте и отправьте файлы
git add docs/index.html .github/workflows/pages.yml
git commit -m "Add GitHub Pages landing page"
git push origin main
```

GitHub Actions автоматически запустит workflow и развернет Pages.

#### Вариант B: Вручную через интерфейс
1. Перейдите в **Actions** на GitHub
2. Найдите workflow "Deploy GitHub Pages"
3. Нажмите **"Run workflow"** → **"Run workflow"**

### Шаг 4: Ожидание развертывания

1. Перейдите в **Actions** → выберите запущенный workflow
2. Дождитесь завершения (обычно 1-2 минуты)
3. После успешного завершения вернитесь в **Settings** → **Pages**
4. Кнопка **"Visit Site"** появится вверху страницы!

## Проверка статуса

После запуска workflow:
- ✅ Зеленый статус = успешно, кнопка появится
- ❌ Красный статус = ошибка, проверьте логи

## URL вашего сайта

После развертывания сайт будет доступен по адресу:
```
https://Artser.github.io/ChatList/
```

## Решение проблем

### Проблема: Workflow не запускается
- Убедитесь, что файл `.github/workflows/pages.yml` существует
- Проверьте, что Actions включены в Settings → Actions → General

### Проблема: Workflow завершается с ошибкой
- Проверьте логи в Actions
- Убедитесь, что папка `docs/` содержит `index.html`
- Проверьте права доступа в Settings → Actions → General

### Проблема: Кнопка все еще не появляется
- Подождите 2-3 минуты (развертывание не мгновенное)
- Обновите страницу Settings → Pages
- Проверьте, что workflow завершился успешно

## Быстрая проверка

После настройки выполните:
```powershell
git add docs/index.html .github/workflows/pages.yml
git commit -m "Setup GitHub Pages"
git push origin main
```

Затем:
1. Подождите 2-3 минуты
2. Перейдите в Settings → Pages
3. Кнопка "Visit Site" должна появиться!


