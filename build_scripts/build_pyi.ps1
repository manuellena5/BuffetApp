# Build BuffetApp with PyInstaller (onedir) for fast startup
# Usage: run from repo root with PowerShell
# Requires: Python 3.11+ and pyinstaller installed in the target env

param(
    [string]$Python = "py",  # puedes pasar ruta completa a python.exe si querés
    [string]$Entry = "BuffetApp/main.py",
    [string]$Name = "BuffetApp",
    [string]$Icon = "assets/app.ico"
)

$ErrorActionPreference = "Stop"

function Resolve-Python {
    param([string]$Preferred)
    # Si pasaron una ruta válida, usarla
    if ($Preferred -and (Get-Command $Preferred -ErrorAction SilentlyContinue)) {
        return $Preferred
    }
    # Intentar 'py'
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { return $py.Name }
    # Intentar 'python'
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) { return $python.Name }
    throw "No se encontró Python en PATH. Pasá -Python con la ruta completa a python.exe (por ej.: -Python 'C:\\Users\\...\\python.exe')."
}

$PYEXE = Resolve-Python -Preferred $Python
Write-Host "Usando Python: $PYEXE"

# Ensure PyInstaller
Write-Host "Verificando PyInstaller en el intérprete seleccionado..."
try {
    & $PYEXE -m pyinstaller --version | Out-Null
} catch {
    Write-Host "Instalando PyInstaller en $PYEXE ..."
    & $PYEXE -m pip install --upgrade pip
    & $PYEXE -m pip install --upgrade pyinstaller
}

# Build
Write-Host "Compilando $Name (onedir) ..."
# Convert Windows-style add-data path: 'src;dest'
$addData = "BuffetApp;BuffetApp"

# Build args base
$args = @(
    '-m','PyInstaller', $Entry,
    '--noconfirm',
    '--clean',
    '--onedir',
    '--windowed',
    '--name', $Name,
    '--add-data', $addData
)

# Only add icon if file exists
if (Test-Path -LiteralPath $Icon) {
    Write-Host "Using icon: $Icon"
    $args += @('--icon', $Icon)
} else {
    Write-Warning "Icon not found: $Icon. Proceeding without --icon."
}

try {
    & $PYEXE @args
} catch {
    Write-Error "Falló PyInstaller. Si el error indica que no encuentra el módulo, asegurate de instalar dependencias en el mismo entorno de $PYEXE."; throw
}

Write-Host "Build completo. Salida: .\\dist\\$Name\\"
