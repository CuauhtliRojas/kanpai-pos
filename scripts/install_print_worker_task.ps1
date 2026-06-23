param(
    [string]$InstallDir = "C:\KanpaiPrintWorker",
    [string]$TaskName = "Kanpai Print Worker"
)

$ErrorActionPreference = "Stop"

$ExePath = Join-Path $InstallDir "KanpaiPrintWorker.exe"
$ConfigPath = Join-Path $InstallDir "print_worker_config.json"

if (-not (Test-Path $ExePath)) {
    throw "No existe EXE: $ExePath"
}

if (-not (Test-Path $ConfigPath)) {
    throw "No existe config: $ConfigPath"
}

$Action = New-ScheduledTaskAction -Execute $ExePath -Argument "--config `"$ConfigPath`"" -WorkingDirectory $InstallDir
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Settings $Settings `
    -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName

Write-Host "Instalado y arrancado: $TaskName"
Get-ScheduledTask -TaskName $TaskName | Format-List TaskName, State
