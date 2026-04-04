$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

$Python = Join-Path $RootDir ".venv\Scripts\python.exe"
$Pip = Join-Path $RootDir ".venv\Scripts\pip.exe"

& $Python -m pip install --upgrade pip
& $Pip install -e ".\apps\backend[dev]"

Push-Location ".\apps\backend"
& (Join-Path $RootDir ".venv\Scripts\alembic.exe") upgrade head
Pop-Location

& $Python ".\scripts\init_data.py" --demo

npm install

$BackendProcess = Start-Process -FilePath $Python -ArgumentList "-m", "uvicorn", "app.main:app", "--app-dir", "apps/backend", "--host", "127.0.0.1", "--port", "8000" -PassThru

try {
  npm run frontend:dev
} finally {
  if ($BackendProcess -and -not $BackendProcess.HasExited) {
    Stop-Process -Id $BackendProcess.Id -Force
  }
}

