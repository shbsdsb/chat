@echo off
title Chat Launcher
setlocal enabledelayedexpansion

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ============================================
echo          Chat (Vue3 + Flask)
echo ============================================
echo.
echo Root: %ROOT%
echo.

:: Check Python (python / python3 / py launcher)
set "PY_CMD="
python --version >nul 2>&1  && set "PY_CMD=python"  && goto :py_ok
python3 --version >nul 2>&1 && set "PY_CMD=python3" && goto :py_ok
py -3 --version >nul 2>&1    && set "PY_CMD=py -3"    && goto :py_ok
echo [ERR] Python not found. Install Python 3.x first.
pause
exit /b 1
:py_ok
%PY_CMD% --version

:: ---- Smart Node.js detection (NVM / FNM / Volta) ----
set "NODE_CMD="

:: 1) PATH
node --version >nul 2>&1 && set "NODE_CMD=node" && goto :node_ok

:: 2) NVM for Windows
if defined NVM_HOME if exist "%NVM_HOME%\*" (
    for /f "tokens=*" %%v in ('"%NVM_HOME%\nvm.exe" current 2^>nul') do set "NVM_VER=%%v"
    if defined NVM_VER (
        set "NP=%NVM_HOME%\%NVM_VER%"
        if exist "!NP!\node.exe" (
            set "NODE_CMD=!NP!\node.exe"
            set "PATH=!NP!;%PATH%"
            goto :node_ok
        )
    )
)
if exist "%ProgramFiles%\nodejs\node.exe" (
    set "NODE_CMD=%ProgramFiles%\nodejs\node.exe"
    set "PATH=%ProgramFiles%\nodejs;%PATH%"
    goto :node_ok
)

:: 3) FNM
set "FNM=%FNM_DIR%"
if not defined FNM set "FNM=%APPDATA%\fnm"
if not exist "%FNM%\*" set "FNM=%USERPROFILE%\.fnm"
if exist "%FNM%\fnm.exe" (
    for /f "tokens=*" %%v in ('"%FNM%\fnm.exe" env --shell cmd 2^>nul ^| findstr "PATH="') do (
        set "FL=%%v"
        set "FL=!FL:PATH=!"
        set "FL=!FL:~1!"
        if exist "!FL!\node.exe" (
            set "NODE_CMD=!FL!\node.exe"
            set "PATH=!FL!;%PATH%"
            goto :node_ok
        )
    )
)

:: 4) Volta
if exist "%LOCALAPPDATA%\Volta\node.exe" (
    set "NODE_CMD=%LOCALAPPDATA%\Volta\node.exe"
    set "PATH=%LOCALAPPDATA%\Volta;%PATH%"
    goto :node_ok
)

echo [ERR] Node.js not found. Please install:
echo       - Node.js, NVM for Windows, FNM, or Volta
pause
exit /b 1

:node_ok
echo Node:  %NODE_CMD%
%NODE_CMD% --version
echo.

echo [1/2] Starting Flask backend (port 5000) ...
start "Chat-Backend" cmd /k "cd /d %ROOT%\backend && %PY_CMD% -m pip install -r requirements.txt -q && %PY_CMD% run.py"

echo [2/2] Starting Electron app ...
start "Chat-Frontend" cmd /k "cd /d %ROOT%\frontend && npm install && npm run electron:dev"

echo.
echo ============================================
echo   Backend : http://127.0.0.1:5000
echo   Electron window will open automatically
echo ============================================
echo.
echo Both windows are running. Close this window to exit.
pause
