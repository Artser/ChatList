# Включение GitHub Actions для репозитория

## Проблема
Видите предупреждение: "Actions is currently unavailable for your repository"

Это означает, что **GitHub Actions отключен** для вашего репозитория.

## Решение: Включите GitHub Actions

### Шаг 1: Откройте настройки Actions

1. Перейдите в **Settings** → **Actions** → **General**
   - Или по прямой ссылке: https://github.com/Artser/ChatList/settings/actions

### Шаг 2: Включите Actions

1. Найдите раздел **"Actions permissions"**
2. Выберите один из вариантов:
   - ✅ **"Allow all actions and reusable workflows"** (рекомендуется)
   - Или **"Allow local actions and reusable workflows"**
3. Нажмите **Save**

### Шаг 3: Настройте Workflow permissions

В том же разделе **Settings** → **Actions** → **General**:

1. Прокрутите до раздела **"Workflow permissions"**
2. Выберите:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**
3. Нажмите **Save**

### Шаг 4: Вернитесь в настройки Pages

1. Перейдите в **Settings** → **Pages**
2. Убедитесь, что **Source** = **"GitHub Actions"**
3. Если нужно, выберите и сохраните

### Шаг 5: Запустите workflow

1. Перейдите в **Actions**
2. Выберите **"Deploy GitHub Pages"**
3. Нажмите **"Run workflow"** → **"Run workflow"**
4. Подождите 2-3 минуты

## После включения Actions

1. Предупреждение в Settings → Pages должно исчезнуть
2. Workflow сможет выполниться успешно
3. GitHub Pages будет развернут автоматически
4. Кнопка **"Visit Site"** появится в Settings → Pages

## Проверка

После выполнения всех шагов:
- ✅ Actions включен (Settings → Actions → General)
- ✅ Workflow permissions настроены
- ✅ Source = "GitHub Actions" в Settings → Pages
- ✅ Workflow запущен и выполнен успешно

Ваш сайт будет доступен: `https://Artser.github.io/ChatList/`

