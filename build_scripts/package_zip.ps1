# Package BuffetApp builds into ZIP files for distribution
# Usage examples:
#   powershell -ExecutionPolicy Bypass -File .\build_scripts\package_zip.ps1 -Source ".\dist\BuffetApp" -ZipName "BuffetApp-portable.zip" -OutDir "C:\Users\me\Google Drive\Releases"
#   powershell -ExecutionPolicy Bypass -File .\build_scripts\package_zip.ps1 -Source ".\installer\dist" -ZipName "BuffetApp-installer.zip"

param(
  [Parameter(Mandatory=$true)][string]$Source,
  [string]$ZipName = "BuffetApp.zip",
  [string]$OutDir = ".\releases"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Source)) {
  Write-Error "No existe la carpeta de origen: $Source"; exit 1
}

# Crear carpeta de salida si no existe
if (-not (Test-Path -LiteralPath $OutDir)) {
  New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
}

# Resolver ruta completa del ZIP
$zipPath = Join-Path $OutDir $ZipName

# Eliminar ZIP si existe
if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }

Write-Host "Comprimiendo '$Source' en '$zipPath' ..."
Add-Type -AssemblyName 'System.IO.Compression.FileSystem'
[System.IO.Compression.ZipFile]::CreateFromDirectory((Resolve-Path $Source), $zipPath)
Write-Host "Listo: $zipPath"
