# Build BuffetApp with Nuitka (standalone, onedir)
# Produces: .\build_nuitka\main.dist\main.exe

param(
  [string]$Python = "py",
  [string]$Entry = "BuffetApp/main.py",
  [string]$OutputDir = "build_nuitka",
  [string]$Icon = "assets/app.ico"
)

$ErrorActionPreference = "Stop"

Write-Host "Instalando Nuitka y dependencias mínimas..."
& $Python -m pip install --upgrade nuitka orderedset zstandard  # zstandard para compresión opcional

Write-Host "Compilando con Nuitka..."
$args = @(
  '-m','nuitka', $Entry,
  '--standalone',
  '--enable-plugin=tk-inter',
  '--windows-console=no',
  '--output-dir', $OutputDir,
  '--include-data-dir=BuffetApp=BuffetApp'
)

if (Test-Path -LiteralPath $Icon) {
  $args += @('--windows-icon-from-ico', $Icon)
}

& $Python @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Listo: $OutputDir\main.dist\main.exe"
