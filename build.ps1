# Скрипт для сборки исполняемого файла
Write-Host "Установка зависимостей..." -ForegroundColor Green
pip install -r requirements.txt

Write-Host ""
Write-Host "Сборка исполняемого файла..." -ForegroundColor Green
pyinstaller --onefile --windowed --name "ChatList" --icon=NONE main.py

Write-Host ""
Write-Host "Готово! Исполняемый файл: dist\ChatList.exe" -ForegroundColor Green
