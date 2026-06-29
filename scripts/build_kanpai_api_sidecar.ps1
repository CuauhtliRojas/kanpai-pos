Set-Location (Resolve-Path "$PSScriptRoot\..")
$ErrorActionPreference = "Stop"

Write-Host "`n=== BUILD KANPAI API SIDECAR ==="

$sidecarDir = "frontend\src-tauri\binaries"
$sidecarPath = Join-Path $sidecarDir "kanpai-api.exe"
$legacyAuditPath = Join-Path $sidecarDir "kanpai-api-x86_64-pc-windows-msvc.exe"

New-Item -ItemType Directory -Force $sidecarDir | Out-Null

uv run pyinstaller `
  --noconfirm `
  --clean `
  --onefile `
  --noconsole `
  --name kanpai-api `
  --paths "." `
  --paths "airtable\scripts" `
  --collect-submodules "app" `
  --collect-submodules "airtable" `
  --add-data "airtable;airtable" `
  --add-data "alembic;alembic" `
  --add-data "alembic.ini;." `
  --add-data "config;config" `
  --hidden-import "app.main" `
  --hidden-import "app.models" `
  --hidden-import "airtable.scripts.pull_airtable_to_sqlite" `
  --hidden-import "airtable.scripts.push_sqlite_to_airtable" `
  scripts\kanpai_api_entrypoint.py

if (!(Test-Path "dist\kanpai-api.exe")) {
  throw "PyInstaller no genero dist\kanpai-api.exe"
}

Copy-Item "dist\kanpai-api.exe" $sidecarPath -Force
Copy-Item "dist\kanpai-api.exe" $legacyAuditPath -Force

$item = Get-Item $sidecarPath
Write-Host "OK sidecar runtime:"
Write-Host ("  {0}" -f $item.FullName)
Write-Host ("  bytes={0}" -f $item.Length)
Write-Host ("  modified={0}" -f $item.LastWriteTime)

$audit = Get-Item $legacyAuditPath
Write-Host "OK sidecar audit copy:"
Write-Host ("  {0}" -f $audit.FullName)
Write-Host ("  bytes={0}" -f $audit.Length)
Write-Host ("  modified={0}" -f $audit.LastWriteTime)
