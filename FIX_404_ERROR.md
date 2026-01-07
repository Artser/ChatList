# Исправление ошибки 404 при развертывании GitHub Pages

## Ошибка
```
Error: Failed to create deployment (status: 404)
Ensure GitHub Pages has been enabled
```

## Решение

### Шаг 1: Включите GitHub Pages (ОБЯЗАТЕЛЬНО!)

1. Перейдите по ссылке: https://github.com/Artser/ChatList/settings/pages
2. Или вручную: **Settings** → **Pages**
3. В разделе **"Build and deployment"**:
   - **Source**: выберите **"GitHub Actions"**
4. Нажмите **Save**

### Шаг 2: Настройте права доступа

1. Перейдите в **Settings** → **Actions** → **General**
2. Прокрутите до **"Workflow permissions"**
3. Выберите:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**
4. Нажмите **Save**

### Шаг 3: Проверьте, что environment создан

После настройки Source = GitHub Actions, GitHub автоматически создаст environment `github-pages`.

Проверка:
1. Перейдите в **Settings** → **Environments**
2. Должен быть environment с именем `github-pages`
3. Если его нет, вернитесь в Settings → Pages и сохраните настройки еще раз

### Шаг 4: Запустите workflow заново

1. Перейдите в **Actions**
2. Выберите "Deploy GitHub Pages"
3. Нажмите **"Run workflow"** → **"Run workflow"**

### Шаг 5: Ожидание

1. Подождите 1-2 минуты
2. Проверьте статус в Actions
3. Если успешно (зеленый ✅), перейдите в Settings → Pages
4. Кнопка **"Visit Site"** появится!

## Важно!

**Ошибка 404 означает, что GitHub Pages не включен в настройках репозитория.**

Обязательно выполните **Шаг 1** - это критически важно!



