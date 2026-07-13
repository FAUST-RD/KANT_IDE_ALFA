# Installs everything needed to run kant_editor.py (just Python 3 + PySide6, the rest is stdlib).
$ErrorActionPreference = 'Stop'

$python = $null
foreach ($candidate in @('python', 'py')) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $python = $candidate
        break
    }
}
if (-not $python) {
    Write-Error "Python non trovato. Installa Python 3 e riprova (https://www.python.org/downloads/)."
    exit 1
}

Write-Host "Uso $python ($(& $python --version))"
& $python -m pip install --upgrade pip
& $python -m pip install -r "$PSScriptRoot\requirements.txt"

Write-Host "Fatto. Avvia con: $python $PSScriptRoot\kant_editor.py"
