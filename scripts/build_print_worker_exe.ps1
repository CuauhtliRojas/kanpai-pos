$ErrorActionPreference = "Stop"

$Repo = Split-Path -Parent $PSScriptRoot
Set-Location $Repo

Write-Host "`n=== LIMPIAR BUILD ANTERIOR ==="
Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "dist\KanpaiPrintWorker.exe" -Force -ErrorAction SilentlyContinue
Remove-Item "KanpaiPrintWorker.spec" -Force -ErrorAction SilentlyContinue

Write-Host "`n=== GENERAR EXE PRINT WORKER ==="
uv run pyinstaller `
  --clean `
  --onefile `
  --noconsole `
  --name KanpaiPrintWorker `
  "scripts\print_worker_windows.py"

Remove-Item "KanpaiPrintWorker.spec" -Force -ErrorAction SilentlyContinue

Write-Host "`n=== EXE GENERADO ==="
Get-Item "dist\KanpaiPrintWorker.exe" | Select-Object FullName, Length, LastWriteTime | Format-List
