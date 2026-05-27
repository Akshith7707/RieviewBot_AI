# ReviewBot AI — start backend (Windows)
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
    Write-Host "Copy .env.example to .env and add your API keys first." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -q
$env:PYTHONPATH = $Root
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
