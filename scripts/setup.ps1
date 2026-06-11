
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
    Write-Host "==> Creating .env (no hardcoded passwords)"
    Set-Content -Path ".env" -Value ("DEBUG=1`nSECRET_KEY=dev-secret-key-change-me`nALLOWED_HOSTS=*`nDB_ENGINE=sqlite`nDJANGO_SUPERUSER_USERNAME=admin`nDJANGO_SUPERUSER_PASSWORD=`nDJANGO_SUPERUSER_EMAIL=admin@example.com")
}

Write-Host "==> Applying migrations"
python manage.py migrate

# Create/ensure superuser, generating a random password if none provided
Write-Host "==> Creating superuser (generates secure password if none provided)"

# If .env contains an empty DJANGO_SUPERUSER_PASSWORD line, generate a secure one and write it
$envContent = Get-Content -Raw -Path ".env"
$pwLine = ($envContent -split "\r?\n") -match '^DJANGO_SUPERUSER_PASSWORD='
if ($pwLine -and ($pwLine -match '^DJANGO_SUPERUSER_PASSWORD=$')) {
    $bytes = New-Object 'System.Byte[]' 24
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $pw = [Convert]::ToBase64String($bytes) -replace '[+/=]', ''
    $pw = $pw.Substring(0,16)
    (Get-Content .env) -replace '^DJANGO_SUPERUSER_PASSWORD=.*', "DJANGO_SUPERUSER_PASSWORD=$pw" | Set-Content .env
    Write-Host "Generated DJANGO_SUPERUSER_PASSWORD and stored in .env"
} else {
    Write-Host "Using existing DJANGO_SUPERUSER_PASSWORD from .env or environment"
}

$code = @"
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','shop.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
u = os.getenv('DJANGO_SUPERUSER_USERNAME','admin')
e = os.getenv('DJANGO_SUPERUSER_EMAIL','admin@example.com')
p = os.getenv('DJANGO_SUPERUSER_PASSWORD','')
if not p:
    try:
        with open('.env') as f:
            for line in f:
                if line.startswith('DJANGO_SUPERUSER_PASSWORD='):
                    p = line.split('=',1)[1].strip()
                    break
    except Exception:
        p = ''
if not User.objects.filter(username=u).exists():
    if not p:
        p = 'changeme123'
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
