# ReviewBot AI — React dashboard (dev)
$Root = Split-Path -Parent $PSScriptRoot
Set-Location "$Root\frontend"

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..."
    npm install
}

Write-Host "Dashboard: http://localhost:5173"
Write-Host "Backend API proxied from :8000 — keep run_server.ps1 running"
npm run dev
