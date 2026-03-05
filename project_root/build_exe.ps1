Param(
    [switch]$OneFile = $true,
    [string]$IconPath = ".\assets\sorth.ico"
)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$pythonCandidates = @(
    ".\venv\Scripts\python.exe",
    "..\venv\Scripts\python.exe",
    "python"
)

$pythonExe = $null
foreach ($candidate in $pythonCandidates) {
    if ($candidate -eq "python" -or (Test-Path $candidate)) {
        $pythonExe = $candidate
        break
    }
}

if (-not $pythonExe) {
    throw "No se encontró un ejecutable de Python para compilar."
}

Write-Host "Usando Python: $pythonExe"

# Validate critical dependency before build
& $pythonExe -c "import PyQt6; print('PyQt6 OK')"

Write-Host "Instalando PyInstaller..."
& $pythonExe -m pip install --upgrade pyinstaller

$baseArgs = @(
    '--noconfirm',
    '--clean',
    '--name', 'SORTH',
    '--hidden-import', 'PyQt6',
    '--add-data', 'data/input;data/input',
    '--add-data', 'assets;assets',
    '--add-data', 'README.md;.',
    '--add-data', '../CREDITS.md;.',
    'gui_app.py'
)

if ($IconPath -and (Test-Path $IconPath)) {
    $resolvedIcon = (Resolve-Path $IconPath).Path
    $baseArgs = @('--icon', $resolvedIcon) + $baseArgs
    Write-Host "Usando icono: $resolvedIcon"
} elseif ($IconPath -and $PSBoundParameters.ContainsKey('IconPath')) {
    throw "No se encontró el archivo de icono: $IconPath"
} elseif (Test-Path ".\assets\sorth.ico") {
    $defaultIcon = (Resolve-Path ".\assets\sorth.ico").Path
    $baseArgs = @('--icon', $defaultIcon) + $baseArgs
    Write-Host "Usando icono por defecto: $defaultIcon"
}

if ($OneFile) {
    $args = @('--onefile', '--windowed') + $baseArgs
} else {
    $args = @('--windowed') + $baseArgs
}

Write-Host "Compilando ejecutable..."
& $pythonExe -m PyInstaller @args

if ($OneFile) {
    Write-Host "Listo: dist/SORTH.exe"
} else {
    Write-Host "Listo: dist/SORTH/SORTH.exe"
}
