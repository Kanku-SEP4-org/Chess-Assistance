$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VenvDir = Join-Path $ScriptDir ".venv"

Write-Host "=== Angriness Predictor - venv setup ==="

if (Test-Path $VenvDir) {
    Write-Host "Existing .venv found at $VenvDir"
    Write-Host "  Remove it first if you want a fresh install:"
    Write-Host "  Remove-Item -Recurse -Force $VenvDir"
    exit 1
}

python -m venv $VenvDir
Write-Host "Created venv at $VenvDir"

& "$VenvDir\Scripts\Activate.ps1"
python -m pip install --upgrade pip
python -m pip install -r (Join-Path $ScriptDir "requirements.txt")

Write-Host ""
Write-Host "Done. Activate with:"
Write-Host "  & $VenvDir\Scripts\Activate.ps1"
