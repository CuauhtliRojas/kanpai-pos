$ErrorActionPreference = "Stop"
$env:DEBUG = "false"
$BaseUrl = "http://127.0.0.1:8011"

function Invoke-Api {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Path,
        [hashtable]$Body
    )
    $arguments = @{
        Method = $Method
        Uri = "$BaseUrl$Path"
        ContentType = "application/json"
    }
    if ($null -ne $Body) {
        $arguments.Body = $Body | ConvertTo-Json -Depth 8
    }
    Invoke-RestMethod @arguments
}

Write-Host "1/17 health"
Invoke-Api -Method Get -Path "/health"

Write-Host "2/17 pytest"
$originalDatabaseUrl = $env:DATABASE_URL
$temporaryDatabase = "data/smoke_pytest_$PID.db"
try {
    $env:DATABASE_URL = "sqlite:///./$temporaryDatabase"
    uv run alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw "temporary test database migration failed" }
    uv run python -m app.db.seed
    if ($LASTEXITCODE -ne 0) { throw "temporary test database seed failed" }
    uv run pytest
    if ($LASTEXITCODE -ne 0) { throw "pytest failed" }
}
finally {
    if ($null -eq $originalDatabaseUrl) {
        Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
    }
    else {
        $env:DATABASE_URL = $originalDatabaseUrl
    }
    Remove-Item -LiteralPath $temporaryDatabase -Force -ErrorAction SilentlyContinue
}

Write-Host "3/17 ruff"
uv run ruff check .
if ($LASTEXITCODE -ne 0) { throw "ruff failed" }

Write-Host "4/17 git diff check"
git diff --check
if ($LASTEXITCODE -ne 0) { throw "git diff --check failed" }

Write-Host "5/17 seed"
uv run python -m app.db.seed
if ($LASTEXITCODE -ne 0) { throw "seed failed" }

$employee = Invoke-Api -Method Get -Path "/api/v1/operations/employees" |
    Where-Object { $_.active -and $_.employee_code -eq "EMP-0001" } |
    Select-Object -First 1
$table = Invoke-Api -Method Get -Path "/api/v1/operations/tables" |
    Where-Object { $_.active -and $_.status -eq "FREE" } |
    Select-Object -First 1
$product = Invoke-Api -Method Get -Path "/api/v1/catalog/products" |
    Where-Object { $_.sku -eq "DEV-CHELA" } |
    Select-Object -First 1
$cashMethod = Invoke-Api -Method Get -Path "/api/v1/catalog/payment-methods" |
    Where-Object { $_.active -and $_.method_key -eq "CASH" } |
    Select-Object -First 1
if (-not $employee -or -not $table -or -not $product -or -not $cashMethod) {
    throw "Required seeded catalog data is unavailable"
}

Write-Host "6/17 open cash shift"
$shift = Invoke-Api -Method Post -Path "/api/v1/pos/cash-shifts/open" -Body @{
    employee_id = $employee.id
    opening_cash_cents = 0
}

Write-Host "7/17 open ticket"
$ticket = Invoke-Api -Method Post -Path "/api/v1/pos/tables/$($table.id)/open-ticket" -Body @{
    employee_id = $employee.id
    guest_count = 1
    note = "Smoke local backend"
}

Write-Host "8/17 add product"
$lineResult = Invoke-Api -Method Post -Path "/api/v1/pos/tickets/$($ticket.id)/lines" -Body @{
    product_id = $product.id
    employee_id = $employee.id
    quantity = 1
}

Write-Host "9/17 send round"
Invoke-Api -Method Post -Path "/api/v1/pos/tickets/$($ticket.id)/send-round" -Body @{
    employee_id = $employee.id
}

Write-Host "10/17 start payment"
Invoke-Api -Method Post -Path "/api/v1/pos/tickets/$($ticket.id)/start-payment" -Body @{
    employee_id = $employee.id
}

Write-Host "11/17 pay"
$total = $lineResult.ticket_totals.total_cents
$paymentResult = Invoke-Api -Method Post -Path "/api/v1/pos/tickets/$($ticket.id)/payments" -Body @{
    employee_id = $employee.id
    payment_method_id = $cashMethod.id
    amount_cents = $total
    received_cents = $total
}
if (-not $paymentResult.closed) { throw "Smoke ticket did not close as PAID" }

Write-Host "12/17 inventory consumption"
$movements = Invoke-Api -Method Get -Path "/api/v1/pos/tickets/$($ticket.id)/inventory-movements"
if (@($movements).Count -eq 0) { throw "No inventory consumption was generated" }

Write-Host "13/17 print jobs"
Invoke-Api -Method Get -Path "/api/v1/printing/jobs/pending"

Write-Host "14/17 reports"
Invoke-Api -Method Get -Path "/api/v1/reports/operational-summary"
Invoke-Api -Method Get -Path "/api/v1/reports/inventory-consumption"

Write-Host "15/17 ticket audit"
Invoke-Api -Method Get -Path "/api/v1/audit/tickets/$($ticket.id)"

Write-Host "16/17 preflight"
$preflight = Invoke-Api -Method Get -Path "/api/v1/preflight/local-backend"
if ($preflight.status -eq "ERROR") { throw "Preflight returned ERROR" }

Write-Host "17/17 complete"
Write-Host "SMOKE OK"
