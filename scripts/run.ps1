Write-Host "==> Activating venv and starting Django on http://127.0.0.1:8000"
. .\.venv\Scripts\Activate.ps1
$env:DJANGO_SETTINGS_MODULE="shop.settings"
python manage.py runserver 0.0.0.0:8000
