# Инструкция по публикации релиза ChatList

## Подготовка к релизу

### 1. Обновление версии
1. Откройте файл `version.py`
2. Обновите версию (например, с `1.0.0` на `1.0.1`):
   ```python
   __version__ = "1.0.1"
   ```
3. Сохраните файл

### 2. Сборка исполняемого файла и инсталлятора
```powershell
.\build_installer.ps1
```

Или вручную:
```powershell
# Получить версию
$version = python -c "import version; print(version.__version__)"

# Собрать исполняемый файл
pyinstaller --onefile --windowed --name "ChatList_v$version" --icon=app.ico main.py

# Создать инсталлятор (если установлен Inno Setup)
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss
```

### 3. Проверка файлов
Убедитесь, что созданы:
- `dist\ChatList_v{version}.exe` - исполняемый файл
- `installer\ChatList_Setup_v{version}.exe` - инсталлятор

## Создание GitHub Release

### Вариант 1: Через веб-интерфейс GitHub

1. Перейдите на страницу репозитория: `https://github.com/ваш-username/ChatList`
2. Нажмите на "Releases" в правой панели
3. Нажмите "Create a new release" или "Draft a new release"
4. Заполните форму:
   - **Tag version**: `v1.0.0` (соответствует версии в `version.py`)
   - **Release title**: `ChatList v1.0.0`
   - **Description**: Используйте шаблон из `RELEASE_NOTES_TEMPLATE.md`
5. Загрузите файлы:
   - `dist\ChatList_v{version}.exe` - как "ChatList_v{version}.exe"
   - `installer\ChatList_Setup_v{version}.exe` - как "ChatList_Setup_v{version}.exe"
6. Нажмите "Publish release"

### Вариант 2: Через GitHub CLI (gh)

```powershell
# Установите GitHub CLI если еще не установлен
# https://cli.github.com/

# Авторизуйтесь
gh auth login

# Создайте релиз
gh release create v1.0.0 `
  --title "ChatList v1.0.0" `
  --notes-file RELEASE_NOTES_TEMPLATE.md `
  "dist\ChatList_v1.0.0.exe#ChatList v1.0.0 (Portable)" `
  "installer\ChatList_Setup_v1.0.0.exe#ChatList v1.0.0 (Installer)"
```

### Вариант 3: Автоматически через GitHub Actions

Используйте workflow из `.github/workflows/release.yml` (будет создан автоматически при push тега).

## Настройка GitHub Pages

### 1. Включение GitHub Pages
1. Перейдите в Settings → Pages
2. В разделе "Source" выберите:
   - Branch: `gh-pages` (или `main`)
   - Folder: `/docs` (или `/root`)
3. Нажмите "Save"

### 2. Подготовка файлов для Pages
```powershell
# Скопируйте index.html в папку docs
Copy-Item index.html docs\index.html
```

### 3. Публикация
```powershell
git add docs/index.html
git commit -m "Add GitHub Pages landing page"
git push origin main
```

GitHub Pages автоматически обновится через несколько минут.

## Структура файлов для релиза

```
ChatList/
├── dist/
│   └── ChatList_v1.0.0.exe          # Исполняемый файл
├── installer/
│   └── ChatList_Setup_v1.0.0.exe    # Инсталлятор
├── docs/
│   └── index.html                    # Лендинг для GitHub Pages
├── .github/
│   └── workflows/
│       └── release.yml               # Автоматизация релизов
└── RELEASE_NOTES_TEMPLATE.md         # Шаблон заметок о релизе
```

## Чеклист перед релизом

- [ ] Версия обновлена в `version.py`
- [ ] Все изменения закоммичены
- [ ] Исполняемый файл собран и протестирован
- [ ] Инсталлятор создан и протестирован
- [ ] Заметки о релизе подготовлены
- [ ] Теги созданы в Git (`git tag v1.0.0`)
- [ ] Теги отправлены в репозиторий (`git push origin v1.0.0`)
- [ ] GitHub Release создан
- [ ] Файлы загружены в Release
- [ ] GitHub Pages обновлен (если нужно)

## Автоматизация (опционально)

Для автоматической публикации при создании тега используйте GitHub Actions workflow (см. `.github/workflows/release.yml`).




