@echo off
title Agro Alertas Climaticas - Setup
color 0A
echo.
echo ============================================================
echo   Sistema Agro Alertas Climaticas - Instalacion
echo   Santiago, Chile
echo ============================================================
echo.

set SCRIPT_DIR=%~dp0
for %%I in ("%SCRIPT_DIR%..") do set PROJECT_DIR=%%~fI
set PYTHONPATH=%PROJECT_DIR%\src;%PYTHONPATH%
cd /d "%PROJECT_DIR%"

:: Verificar Python
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no encontrado. Descarga desde https://python.org
    pause
    exit /b 1
)

echo [1/3] Instalando dependencias Python...
pip install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)
echo       OK - requests, groq, matplotlib, python-dotenv, numpy

echo.
echo [2/3] Verificando archivo .env...
if not exist ".env" (
    echo [WARN] Archivo .env no encontrado.
    echo        Copia .env.example a .env y completa tus credenciales.
) else (
    echo       OK - .env encontrado
)

echo.
echo [3/3] Probando el sistema (modo test, sin email)...
python -X utf8 -m agro_alertas.main --test
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] El sistema encontro un error. Revisa la configuracion.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Instalacion completada.
echo.
echo   Comandos disponibles:
echo     set PYTHONPATH=src
echo     python -m agro_alertas.main            -> Ejecuta y envia email
echo     python -m agro_alertas.main --preview  -> Genera preview HTML local
echo     python -m agro_alertas.main --test     -> Solo muestra resumen en consola
echo.
echo   Para automatizar (cada manana):
echo     Ejecuta: scripts\configurar_tarea.bat
echo ============================================================
echo.
pause
