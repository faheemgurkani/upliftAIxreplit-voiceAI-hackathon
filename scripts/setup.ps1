# Thin wrapper → scripts/setup.py (Windows PowerShell)
# Usage:  .\scripts\setup.ps1 install
#         .\scripts\setup.ps1 dev
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$script = Join-Path $Root "scripts\setup.py"

if (Get-Command py -ErrorAction SilentlyContinue) {
  & py -3 $script @args
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  & python $script @args
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
  & python3 $script @args
} else {
  Write-Error "Python 3.10+ is required. Install from https://www.python.org/downloads/ and ensure Add to PATH is checked."
  exit 1
}
exit $LASTEXITCODE
