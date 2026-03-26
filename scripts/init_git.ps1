Param(
    [string]$RepoUrl = ""
)

if (-Not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git не установлен. Установите: https://git-scm.com/download/win"
    exit 1
}

if ($RepoUrl -eq "") {
    Write-Host "⚠ Укажите URL репозитория: .\scripts\init_git.ps1 -RepoUrl 'https://github.com/USER/wbtech_shop.git'"
    exit 1
}

Write-Host "==> Инициализация Git репозитория..."
git init

Write-Host "==> Добавляем файлы..."
git add .

Write-Host "==> Создаем первый коммит..."
git commit -m "Initial commit: Django DRF shop (Windows)"

Write-Host "==> Создаем ветку main..."
git branch -M main

Write-Host "==> Привязываем удаленный репозиторий..."
git remote add origin $RepoUrl

Write-Host "==> Отправляем код на GitHub..."
git push -u origin main

Write-Host "✅ Готово! Проверьте репозиторий на GitHub."
