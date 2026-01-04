# РЎРєСЂРёРїС‚ РґР»СЏ СЃР±РѕСЂРєРё РёСЃРїРѕР»РЅСЏРµРјРѕРіРѕ С„Р°Р№Р»Р° Рё СЃРѕР·РґР°РЅРёСЏ РёРЅСЃС‚Р°Р»Р»СЏС‚РѕСЂР°
# РџРѕР»СѓС‡Р°РµРј РІРµСЂСЃРёСЋ РёР· version.py
$version = python -c "import version; print(version.__version__)"
$appName = "ChatList"
$appNameWithVersion = "${appName}_v${version}"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "РЎР±РѕСЂРєР° ChatList v$version" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# РЁР°Рі 1: РЈСЃС‚Р°РЅРѕРІРєР° Р·Р°РІРёСЃРёРјРѕСЃС‚РµР№
Write-Host "РЁР°Рі 1: РЈСЃС‚Р°РЅРѕРІРєР° Р·Р°РІРёСЃРёРјРѕСЃС‚РµР№..." -ForegroundColor Green
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "РћС€РёР±РєР° РїСЂРё СѓСЃС‚Р°РЅРѕРІРєРµ Р·Р°РІРёСЃРёРјРѕСЃС‚РµР№!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# РЁР°Рі 2: РЎР±РѕСЂРєР° РёСЃРїРѕР»РЅСЏРµРјРѕРіРѕ С„Р°Р№Р»Р°
Write-Host "РЁР°Рі 2: РЎР±РѕСЂРєР° РёСЃРїРѕР»РЅСЏРµРјРѕРіРѕ С„Р°Р№Р»Р°..." -ForegroundColor Green
pyinstaller --onefile --windowed --name "$appNameWithVersion" --icon=app.ico main.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "РћС€РёР±РєР° РїСЂРё СЃР±РѕСЂРєРµ РёСЃРїРѕР»РЅСЏРµРјРѕРіРѕ С„Р°Р№Р»Р°!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# РЁР°Рі 3: РџСЂРѕРІРµСЂРєР° РЅР°Р»РёС‡РёСЏ Inno Setup
Write-Host "РЁР°Рі 3: РџСЂРѕРІРµСЂРєР° РЅР°Р»РёС‡РёСЏ Inno Setup..." -ForegroundColor Green
$innoSetupPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $innoSetupPath)) {
    $innoSetupPath = "C:\Program Files\Inno Setup 6\ISCC.exe"
}

if (-not (Test-Path $innoSetupPath)) {
    Write-Host "Inno Setup РЅРµ РЅР°Р№РґРµРЅ!" -ForegroundColor Yellow
    Write-Host "РЈСЃС‚Р°РЅРѕРІРёС‚Рµ Inno Setup 6 СЃ https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    Write-Host "РР»Рё СЃРѕР·РґР°Р№С‚Рµ РёРЅСЃС‚Р°Р»Р»СЏС‚РѕСЂ РІСЂСѓС‡РЅСѓСЋ, РѕС‚РєСЂС‹РІ setup.iss РІ Inno Setup Compiler" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "РСЃРїРѕР»РЅСЏРµРјС‹Р№ С„Р°Р№Р» РіРѕС‚РѕРІ: dist\$appNameWithVersion.exe" -ForegroundColor Cyan
    exit 0
}

# РЁР°Рі 4: РћР±РЅРѕРІР»РµРЅРёРµ setup.iss СЃ Р°РєС‚СѓР°Р»СЊРЅРѕР№ РІРµСЂСЃРёРµР№
Write-Host "РЁР°Рі 4: РћР±РЅРѕРІР»РµРЅРёРµ setup.iss..." -ForegroundColor Green
$setupContent = Get-Content "setup.iss" -Raw -Encoding UTF8
$setupContent = $setupContent -replace 'AppVersion ".*?"', "AppVersion `"$version`""
$setupContent = $setupContent -replace 'AppExeName ".*?"', "AppExeName `"$appNameWithVersion.exe`""
$setupContent = $setupContent -replace 'OutputBaseFilename=.*', "OutputBaseFilename=ChatList_Setup_v$version"
$setupContent | Set-Content "setup.iss" -Encoding UTF8

# РЁР°Рі 5: РЎРѕР·РґР°РЅРёРµ РёРЅСЃС‚Р°Р»Р»СЏС‚РѕСЂР°
Write-Host "РЁР°Рі 5: РЎРѕР·РґР°РЅРёРµ РёРЅСЃС‚Р°Р»Р»СЏС‚РѕСЂР°..." -ForegroundColor Green
& $innoSetupPath "setup.iss"

if ($LASTEXITCODE -ne 0) {
    Write-Host "РћС€РёР±РєР° РїСЂРё СЃРѕР·РґР°РЅРёРё РёРЅСЃС‚Р°Р»Р»СЏС‚РѕСЂР°!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "РЎР±РѕСЂРєР° Р·Р°РІРµСЂС€РµРЅР° СѓСЃРїРµС€РЅРѕ!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "РСЃРїРѕР»РЅСЏРµРјС‹Р№ С„Р°Р№Р»: dist\$appNameWithVersion.exe" -ForegroundColor Cyan
Write-Host "РРЅСЃС‚Р°Р»Р»СЏС‚РѕСЂ: installer\ChatList_Setup_v$version.exe" -ForegroundColor Cyan
Write-Host ""