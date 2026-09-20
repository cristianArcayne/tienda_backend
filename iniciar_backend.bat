@echo off
title Backend FashionStore API - Neon DB
echo ========================================================
echo Iniciando FashionStore Backend con Base de Datos Neon...
echo ========================================================
cd /d "%~dp0"

if not exist ".env" (
    if exist "venv\.env" (
        copy venv\.env .env
    )
)

echo.
echo Servidor iniciando en http://localhost:8000 (y accesible en red local 192.168.1.6:8000)
echo Documentacion API en http://localhost:8000/docs
echo Presiona Ctrl+C para detener el servidor.
echo.

venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --reload --port 8000
pause

