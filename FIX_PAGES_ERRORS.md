# Исправление ошибок GitHub Pages

## Возможные причины ошибок

### 1. Проблемы с правами доступа

**Решение:**
1. Перейдите в **Settings** → **Actions** → **General**
2. В разделе **Workflow permissions** выберите:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**
3. Нажмите **Save**

### 2. Проблемы с environment

**Решение:**
1. Перейдите в **Settings** → **Pages**
2. Убедитесь, что **Source** установлен на **GitHub Actions**
3. Если нужно, создайте environment вручную:
   - Перейдите в **Settings** → **Environments**
   - Создайте environment с именем `github-pages`

### 3. Проблемы с путем к файлам

**Проверка:**
- Убедитесь, что папка `docs/` существует
- Убедитесь, что файл `docs/index.html` существует
- Проверьте, что файлы закоммичены в репозиторий

### 4. Устаревшие версии actions

**Решение:**
Обновлен workflow с использованием последних версий:
- `actions/checkout@v4`
- `actions/configure-pages@v4`
- `actions/upload-pages-artifact@v3`
- `actions/deploy-pages@v3`

## Пошаговое исправление

### Шаг 1: Обновите workflow

Файл `.github/workflows/pages.yml` уже обновлен с последними версиями actions.

### Шаг 2: Проверьте настройки репозитория

```powershell
# Убедитесь, что файлы закоммичены
git status

# Если есть изменения, закоммитьте их
git add .github/workflows/pages.yml docs/index.html
git commit -m "Fix GitHub Pages workflow"
git push origin main
```

### Шаг 3: Настройте права доступа

1. **Settings** → **Actions** → **General**
2. **Workflow permissions**: **Read and write permissions**
3. **Save**

### Шаг 4: Запустите workflow заново

1. Перейдите в **Actions**
2. Выберите workflow "Deploy GitHub Pages"
3. Нажмите **"Run workflow"** → **"Run workflow"**

### Шаг 5: Проверьте логи

Если ошибка повторится:
1. Откройте failed run (#3)
2. Посмотрите логи каждого шага
3. Найдите красные сообщения об ошибках
4. Исправьте проблему согласно сообщению

## Типичные ошибки и решения

### Ошибка: "Resource not accessible by integration"
**Решение:** Настройте права доступа (см. Шаг 3)

### Ошибка: "Path './docs' does not exist"
**Решение:** Убедитесь, что папка `docs/` существует и закоммичена

### Ошибка: "Environment 'github-pages' not found"
**Решение:** 
- Перейдите в **Settings** → **Pages**
- Убедитесь, что Source = **GitHub Actions**
- GitHub создаст environment автоматически

### Ошибка: "Permission denied"
**Решение:** Проверьте права доступа в Settings → Actions → General

## Проверка после исправления

После исправления:
1. Подождите 1-2 минуты
2. Проверьте статус workflow в **Actions**
3. Если успешно (зеленый ✅), перейдите в **Settings** → **Pages**
4. Кнопка **"Visit Site"** должна появиться!

## Если проблема не решена

1. Скопируйте полный текст ошибки из логов
2. Проверьте документацию GitHub Pages
3. Создайте Issue в репозитории с описанием проблемы



