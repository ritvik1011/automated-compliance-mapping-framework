@echo off
setlocal

:: Set console encoding to UTF-8 for emoji support and clean rendering
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

title Compliance Monitoring Dashboard Launcher

:: Navigate directly to the directory where this script resides
cd /d "%~dp0"

echo ======================================================================
echo    Automated Compliance Mapping ^& Gap Analysis Dashboard
echo ======================================================================
echo [DIAGNOSTIC] Current Directory : %CD%
echo [DIAGNOSTIC] Script Directory  : %~dp0

:: Check and activate virtual environment (venv)
if not exist "%~dp0venv\Scripts\activate.bat" goto :check_dot_venv

echo [INFO] Activating virtual environment: venv
call "%~dp0venv\Scripts\activate.bat"
goto :check_python

:check_dot_venv
if not exist "%~dp0.venv\Scripts\activate.bat" goto :no_venv_found
echo [INFO] Activating virtual environment: .venv
call "%~dp0.venv\Scripts\activate.bat"
goto :check_python

:no_venv_found
echo [WARN] No local virtual environment found at "%~dp0venv".
echo [WARN] Attempting to fall back to system Python...

:check_python
echo [DIAGNOSTIC] Testing Python executable...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo ======================================================================
    echo [ERROR] 'python' was not found in PATH or in the virtual environment.
    echo.
    echo Possible causes:
    echo  1. Virtual environment 'venv' has not been created in this folder.
    echo  2. Python is not installed or not added to system PATH.
    echo ======================================================================
    goto :finish_error
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
for /f "tokens=*" %%i in ('where python') do (
    if not defined PYTHON_PATH set PYTHON_PATH=%%i
)
echo [INFO] Detected Python : %PYTHON_VERSION%
echo [INFO] Python Location : %PYTHON_PATH%

:: Verify run_dashboard.py exists
if not exist "%~dp0run_dashboard.py" (
    echo.
    echo ======================================================================
    echo [ERROR] Launcher file 'run_dashboard.py' not found in %CD%
    echo ======================================================================
    goto :finish_error
)

:: Launch the Streamlit dashboard via run_dashboard.py
echo.
echo [INFO] Launching dashboard... (Press Ctrl+C in this window to stop)
echo ======================================================================
echo.

python "%~dp0run_dashboard.py" %*
set SCRIPT_EXIT_CODE=%ERRORLEVEL%

echo.
echo ======================================================================
if %SCRIPT_EXIT_CODE% equ 0 (
    echo [INFO] Dashboard process finished successfully.
) else (
    echo [ERROR] Dashboard exited with error code: %SCRIPT_EXIT_CODE%
)
echo ======================================================================
goto :finish

:finish_error
set SCRIPT_EXIT_CODE=1

:finish
echo.
echo [DIAGNOSTIC] Process completed. Press any key to close this window...
pause
exit /b %SCRIPT_EXIT_CODE%
