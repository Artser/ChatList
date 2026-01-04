# Скрипт для сборки исполняемого файла
# Получаем версию из version.py
$version = python -c "import version; print(version.__version__)"
$appName = "ChatList"
$appNameWithVersion = "${appName}_v${version}"

Write-Host "Версия приложения: $version" -ForegroundColor Cyan
Write-Host "Установка зависимостей..." -ForegroundColor Green
pip install -r requirements.txt

Write-Host ""
Write-Host "Сборка исполняемого файла..." -ForegroundColor Green
pyinstaller --onefile --windowed --name "$appNameWithVersion" --icon=app.ico main.py

Write-Host ""
Write-Host "Готово! Исполняемый файл находится в папке dist" -ForegroundColor Green
Write-Host "Имя файла: $appNameWithVersion.exe" -ForegroundColor Cyan
