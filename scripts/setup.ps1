
Param([string]$PythonExe = "python")

Write-Host "==> Creating virtual environment (.venv)"
& $PythonExe -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Failed to create venv" }

Write-Host "==> Activating venv"
. .\.venv\Scripts\Activate.ps1

Write-Host "==> Upgrading pip"
python -m pip install --upgrade pip

Write-Host "==> Installing requirements"
pip install -r requirements-win.txt

if (-Not (Test-Path ".env")) {
    Write-Host "==> Creating .env"
    Set-Content -Path ".env" -Value ("DEBUG=1`nSECRET_KEY=dev-secret-key-change-me`nALLOWED_HOSTS=*`nDB_ENGINE=sqlite`nDJANGO_SUPERUSER_USERNAME=admin`nDJANGO_SUPERUSER_PASSWORD=admin`nDJANGO_SUPERUSER_EMAIL=admin@example.com")
}

Write-Host "==> Applying migrations"
python manage.py migrate

Write-Host "==> Creating superuser (admin/admin) if missing"
$code = @"
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','shop.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
u = os.getenv('DJANGO_SUPERUSER_USERNAME','admin')
e = os.getenv('DJANGO_SUPERUSER_EMAIL','admin@example.com')
p = os.getenv('DJANGO_SUPERUSER_PASSWORD','admin')
if not User.objects.filter(username=u).exists():
    User.objects.create_superuser(username=u, email=e, password=p)
    print('Created admin user')
else:
    print('Admin user already exists')
"@
# Write to a temp file to avoid quoting issues
$tmp = Join-Path $PSScriptRoot "_create_superuser.py"
Set-Content -Path $tmp -Value $code -Encoding UTF8
python $tmp
Remove-Item $tmp -Force -ErrorAction SilentlyContinue

Write-Host "==> Setup complete"
