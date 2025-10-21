# BuffetApp - Build y Instalador

Este repo incluye tareas para generar el ejecutable (PyInstaller, onedir) y el instalador (Inno Setup) con foco en arranque rápido.

## 1) Requisitos
- Windows 10/11
- Python 3.11 (mismo entorno que usás para desarrollar)
- PyInstaller (`pip install pyinstaller`)
- Inno Setup (opcional, para generar .exe instalador) – agrega `iscc` al PATH o ajusta la tarea de VS Code.

## 2) Ejecutable portable (onedir)
Desde VS Code:
- Task: "Build EXE (PyInstaller onedir)". Genera `dist/BuffetApp/BuffetApp.exe`.

Desde PowerShell (manual):
```powershell
powershell -ExecutionPolicy Bypass -File .\build_scripts\build_pyi.ps1
```

Notas:
- onedir arranca más rápido que onefile en PCs viejas.
- Incluye la carpeta `BuffetApp` como datos (`--add-data`).

## 3) Instalador (Inno Setup)
1. Primero corré el build de PyInstaller (paso 2).
2. Luego ejecutá la tarea: "Build Installer (Inno Setup)".
   - Genera el instalador en `installer\dist`.

## 4) Optimización de arranque aplicada
- Carga perezosa (lazy) de vistas pesadas.
- `init_db` en background si la DB ya existe.
- Preferencia de icono `.ico` (más liviano) con fallback a PNG.

## 5) Antivirus y falsos positivos
- Preferí distribuir el ejecutable firmado digitalmente.
- Firmá todo `dist/BuffetApp` con `build_scripts/sign.ps1` (requiere `signtool` y un .pfx válido):
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\build_scripts\sign.ps1 -PfxPath "C:\ruta\cert.pfx" -PfxPassword "TU_PASSWORD" -Folder ".\dist\BuffetApp"
   ```
- Alternativa de build con menos detecciones: Nuitka (tarea "Build EXE (Nuitka onedir)").
- Evitá ejecutar desde Descargas/Temp; instalá en `C:\Program Files\BuffetApp`.

## 6) Probar en otra PC
- Copiá `dist/BuffetApp/` y ejecutá `BuffetApp.exe`, o instalá con el `.exe` de Inno Setup.
- Si el antivirus inspecciona la primera corrida, la segunda debería ser más rápida.

## 7) Troubleshooting
- Si `iscc` no se encuentra, agregá la ruta de Inno Setup al PATH o edita `.vscode/tasks.json` (options.env.Path).
- Si faltan recursos, verificá que la carpeta `BuffetApp` esté incluida (add-data) y que `utils_paths.resource_path` resuelva bien.
