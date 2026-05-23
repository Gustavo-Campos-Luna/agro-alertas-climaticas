@echo off
title Configurar Tarea Programada - Agro Alertas
echo.
echo ============================================================
echo   Configurando tarea automatica (7:00 AM todos los dias)
echo ============================================================
echo.

set SCRIPT_DIR=%~dp0
for %%I in ("%SCRIPT_DIR%..") do set PROJECT_DIR=%%~fI
set PYTHON_PATH=python
set TASK_NAME=AgroAlertasClimaticas
set "TASK_CMD=cmd /c ""cd /d "%PROJECT_DIR%" && set "PYTHONPATH=%PROJECT_DIR%\src" && %PYTHON_PATH% -X utf8 -m agro_alertas.main"""

:: Eliminar tarea anterior si existe
schtasks /delete /tn "%TASK_NAME%" /f > nul 2>&1

:: Crear nueva tarea: 7:00 AM, todos los dias
schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "%TASK_CMD%" ^
  /sc daily ^
  /st 07:00 ^
  /sd %date% ^
  /ru "%USERNAME%" ^
  /f

if %ERRORLEVEL% EQU 0 (
    echo [OK] Tarea programada creada exitosamente.
    echo.
    echo      Nombre: %TASK_NAME%
    echo      Hora: 7:00 AM todos los dias
    echo      Proyecto: %PROJECT_DIR%
    echo.
    echo      Para gestionar: Abre "Programador de tareas" de Windows
) else (
    echo [ERROR] No se pudo crear la tarea. Intenta ejecutar como Administrador.
)

echo.
pause
