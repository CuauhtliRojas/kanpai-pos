param(
    [string]$Config = "$PSScriptRoot\print_worker_config.json",
    [switch]$DryRun,
    [switch]$Once
)

$arguments = @("run", "python", "$PSScriptRoot\print_worker_windows.py", "--config", $Config)
if ($DryRun) { $arguments += "--dry-run" }
if ($Once) { $arguments += "--once" }
& uv @arguments
