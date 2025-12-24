# Bootstrap script for Windows (PowerShell)
Write-Output "Bootstrapping project environment..."

# Install Python using winget if not present
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Output "Installing Python via winget..."
    winget install --id Python.Python.3 -e --silent
  } else {
    Write-Output "winget not available. Please install Python 3.11+ manually and re-run this script."
    exit 1
  }
}

# Create venv and install requirements
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Output "Bootstrap complete. Run 'python -m pytest -q' to run tests or 'python scripts/demo_local_run.py' to run demo."