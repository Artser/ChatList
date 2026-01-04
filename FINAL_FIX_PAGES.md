# Финальное исправление ошибки GitHub Pages (404)

## Текущая ошибка
```
Error: Failed to create deployment (status: 404)
Ensure GitHub Pages has been enabled
```

## Пошаговое решение (выполните ВСЕ шаги!)

### ✅ Шаг 1: Удалите кастомный домен (если он есть)

1. Перейдите в **Settings** → **Pages**
2. Найдите раздел **"Custom domain"**
3. Если там указан домен (например, `artsercheklist.com`):
   - Нажмите красную кнопку **"Remove"**
   - Подтвердите удаление
4. Убедитесь, что поле "Custom domain" пустое

### ✅ Шаг 2: Включите GitHub Pages

1. На той же странице **Settings** → **Pages**
2. Найдите раздел **"Build and deployment"**
3. В поле **"Source"** выберите: **"GitHub Actions"**
4. Нажмите **Save**

**ВАЖНО:** Если опция "GitHub Actions" недоступна или не видна:
- Убедитесь, что файл `.github/workflows/pages.yml` существует в репозитории
- Закоммитьте и отправьте файл, если его нет:
  ```powershell
  git add .github/workflows/pages.yml
  git commit -m "Add GitHub Pages workflow"
  git push origin main
  ```

### ✅ Шаг 3: Настройте права доступа

1. Перейдите в **Settings** → **Actions** → **General**
2. Прокрутите до раздела **"Workflow permissions"**
3. Выберите:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**
4. Нажмите **Save**

### ✅ Шаг 4: Проверьте, что файлы закоммичены

```powershell
# Проверьте статус
git status

# Если есть изменения, закоммитьте их
git add .github/workflows/pages.yml docs/index.html
git commit -m "Fix GitHub Pages setup"
git push origin main
```

### ✅ Шаг 5: Запустите workflow заново

1. Перейдите в **Actions**
2. Выберите workflow **"Deploy GitHub Pages"**
3. Нажмите **"Run workflow"** → **"Run workflow"**
4. Подождите 1-2 минуты

### ✅ Шаг 6: Проверьте результат

1. Откройте запущенный workflow
2. Если все шаги зеленые (✅) - успешно!
3. Перейдите в **Settings** → **Pages**
4. Кнопка **"Visit Site"** должна появиться!

## Чеклист перед запуском

- [ ] Кастомный домен удален (если был)
- [ ] Source = "GitHub Actions" в Settings → Pages
- [ ] Права доступа настроены (Read and write)
- [ ] Файлы закоммичены и отправлены
- [ ] Workflow запущен вручную

## Если ошибка повторится

1. Откройте failed run в Actions
2. Посмотрите, на каком шаге ошибка
3. Проверьте, что все шаги выше выполнены
4. Убедитесь, что в Settings → Pages нет ошибок

## После успешного развертывания

Ваш сайт будет доступен по адресу:
```
https://Artser.github.io/ChatList/
```

Кнопка "Visit Site" появится в Settings → Pages после успешного развертывания.

