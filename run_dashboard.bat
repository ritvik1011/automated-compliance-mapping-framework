@echo off
setlocal EnableDelayedExpansion

:: Enable UTF-8 console output for emojis and special characters
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

title Compliance Monitoring Dashboard

:: Navigate to project root (directory where this batch file is located)
cd /d "%~dp0"

echo ======================================================================
echo    Automated Compliance Mapping ^& Gap Analysis Framework Dashboard
echo ======================================================================
echo [INFO] Working Directory: %CD%

:: Auto-detect and activate virtual environment if present
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment (venv)...
    call "venv\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment (.venv)...
    call ".venv\Scripts\activate.bat"
) else (
    echo [WARN] No local virtual environment found. Using system Python.
)

:: Verify python is reachable
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found in PATH or the virtual environment.
    echo Please ensure Python 3.10+ is installed and available in PATH.
    goto :error
)

:: Execute dashboard launcher
echo [INFO] Launching dashboard via run_dashboard.py...
python run_dashboard.py %*

if %ERRORLEVEL% neq 0 (
    goto :error
)

goto :end

:error
echo.
echo ======================================================================
echo [ERROR] The dashboard process terminated with error code %ERRORLEVEL%.
echo ======================================================================
pause
exit /b %ERRORLEVEL%

:end
exit /b 0
