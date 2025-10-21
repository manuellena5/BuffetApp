# Sign all binaries in a folder using a PFX certificate
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\build_scripts\sign.ps1 -PfxPath "C:\path\cert.pfx" -PfxPassword "SECRET" -Folder ".\dist\BuffetApp"
# Requires: signtool (Windows SDK) in PATH

param(
  [Parameter(Mandatory=$true)] [string]$PfxPath,
  [Parameter(Mandatory=$true)] [string]$PfxPassword,
  [string]$Folder = ".\dist\BuffetApp",
  [string]$TimestampUrl = "http://timestamp.digicert.com",
  [string]$SigntoolPath
)

$ErrorActionPreference = "Stop"

function Find-SignTool {
  param([string]$Override)
  if ($Override -and (Test-Path -LiteralPath $Override)) { return $Override }
  # Try PATH
  $cmd = Get-Command signtool -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Path }
  # Try common Windows Kits locations (prefer x64 and highest version)
  $candidates = @()
  $roots = @(
    "C:\\Program Files (x86)\\Windows Kits\\10\\bin",
    "C:\\Program Files (x86)\\Windows Kits\\8.1\\bin"
  )
  foreach ($root in $roots) {
    if (Test-Path -LiteralPath $root) {
      $candidates += Get-ChildItem -Path $root -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue
    }
  }
  if ($candidates.Count -gt 0) {
    $best = $candidates | Sort-Object FullName -Descending | Select-Object -First 1
    return $best.FullName
  }
  return $null
}

if (-not (Test-Path -LiteralPath $Folder)) {
  Write-Error "Carpeta no encontrada: $Folder. Generá primero el build (PyInstaller onedir)."; exit 1
}
if (-not (Test-Path -LiteralPath $PfxPath)) {
  Write-Error "Certificado PFX no encontrado: $PfxPath"; exit 1
}

$signtool = Find-SignTool -Override $SigntoolPath
if (-not $signtool) {
  Write-Error "No se encontró 'signtool'. Instalá Windows 10/11 SDK o agregá la ruta con -SigntoolPath"; exit 1
}

$binFiles = Get-ChildItem -Path $Folder -Recurse -Include *.exe,*.dll,*.pyd -ErrorAction SilentlyContinue
if (-not $binFiles -or $binFiles.Count -eq 0) {
  Write-Warning "No se encontraron binarios para firmar en $Folder"; exit 0
}

Write-Host "Usando signtool: $signtool"
Write-Host "Firmando $($binFiles.Count) archivos en $Folder..."
foreach ($f in $binFiles) {
  Write-Host "Firmando: $($f.FullName)"
  & $signtool sign /fd SHA256 /td SHA256 /tr $TimestampUrl /f $PfxPath /p $PfxPassword "$($f.FullName)"
  if ($LASTEXITCODE -ne 0) { throw "Falló firma: $($f.FullName)" }
}

# Verificación (opcional)
Write-Host "Verificando firmas..."
foreach ($f in $binFiles) {
  & $signtool verify /pa "$($f.FullName)" | Out-Null
}
Write-Host "Firma completada."
