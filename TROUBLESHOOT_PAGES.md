# Решение проблемы: нет кнопки "Visit Site"

## Причина
Кнопка "Visit Site" появляется **только после успешного развертывания** GitHub Pages. Все ваши workflow runs завершились с ошибкой, поэтому кнопка не появилась.

## Пошаговое решение

### Шаг 1: Проверьте логи ошибки

1. Откройте последний failed run (#5)
2. Нажмите на него, чтобы увидеть детали
3. Найдите красные сообщения об ошибках
4. Скопируйте текст ошибки

### Шаг 2: Настройте права доступа (ОБЯЗАТЕЛЬНО!)

1. Перейдите в **Settings** → **Actions** → **General**
2. Прокрутите до раздела **"Workflow permissions"**
3. Выберите:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**
4. Нажмите **Save**

### Шаг 3: Проверьте настройки Pages

1. Перейдите в **Settings** → **Pages**
2. Убедитесь, что:
   - **Source**: `GitHub Actions` (выбрано)
3. Если не выбрано, выберите и сохраните

### Шаг 4: Упростите workflow (если ошибка продолжается)

Если проблема не решается, используйте упрощенный workflow.

### Шаг 5: Проверьте файлы

Убедитесь, что файлы существуют и закоммичены:
- `docs/index.html` - должен существовать
- `.github/workflows/pages.yml` - должен существовать

## Типичные ошибки и решения

### Ошибка: "Resource not accessible by integration"
**Причина:** Недостаточно прав доступа  
**Решение:** Настройте права (Шаг 2)

### Ошибка: "Environment 'github-pages' not found"
**Причина:** Environment не создан  
**Решение:** 
- Перейдите в Settings → Pages
- Выберите Source = GitHub Actions
- GitHub создаст environment автоматически

### Ошибка: "Path './docs' does not exist"
**Причина:** Папка docs не закоммичена  
**Решение:** 
```powershell
git add docs/
git commit -m "Add docs folder"
git push origin main
```

### Ошибка: "Permission denied" или "403"
**Причина:** Недостаточно прав  
**Решение:** Настройте права (Шаг 2)

## Быстрое исправление

1. **Настройте права** (самое важное!):
   - Settings → Actions → General
   - Workflow permissions → Read and write permissions
   - Save

2. **Закоммитьте изменения**:
   ```powershell
   git add .github/workflows/pages.yml docs/index.html
   git commit -m "Fix GitHub Pages deployment"
   git push origin main
   ```

3. **Запустите workflow вручную**:
   - Actions → Deploy GitHub Pages → Run workflow

4. **Подождите 1-2 минуты** и проверьте результат

## После успешного развертывания

Когда workflow завершится успешно (зеленый ✅):
1. Перейдите в **Settings** → **Pages**
2. Кнопка **"Visit Site"** появится вверху страницы!
3. Ваш сайт будет доступен по адресу: `https://Artser.github.io/ChatList/`

