<#
.SYNOPSIS
    Automated Compliance Mapping Framework - Dashboard Launcher (PowerShell)
.DESCRIPTION
    Launches the Streamlit compliance monitoring dashboard using the project's
    virtual environment with proper UTF-8 character encoding and error trapping.
#>

# 1. Set terminal encoding to UTF-8 for emoji support
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# 2. Set window title
$host.UI.RawUI.WindowTitle = "Compliance Monitoring Dashboard Launcher (PowerShell)"

# 3. Explicitly navigate to the folder containing this script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ScriptDir) {
    $ScriptDir = Get-Location
}
Set-Location $ScriptDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   Automated Compliance Mapping & Gap Analysis Dashboard (PowerShell)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "[DIAGNOSTIC] Working Directory: $ScriptDir" -ForegroundColor DarkGray

# 4. Detect and activate virtual environment
$VenvActivate = Join-Path $ScriptDir "venv\Scripts\Activate.ps1"
$VenvPython = Join-Path $ScriptDir "venv\Scripts\python.exe"
$DotVenvActivate = Join-Path $ScriptDir ".venv\Scripts\Activate.ps1"
$DotVenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"

$PythonExe = $null

if (Test-Path $VenvActivate) {
    Write-Host "[INFO] Activating virtual environment: venv" -ForegroundColor Green
    try {
        & $VenvActivate
    } catch {
        Write-Host "[WARN] Could not run Activate.ps1 directly (possibly execution policy)." -ForegroundColor Yellow
    }
    if (Test-Path $VenvPython) {
        $PythonExe = $VenvPython
    }
} elseif (Test-Path $DotVenvActivate) {
    Write-Host "[INFO] Activating virtual environment: .venv" -ForegroundColor Green
    try {
        & $DotVenvActivate
    } catch {
        Write-Host "[WARN] Could not run Activate.ps1 directly." -ForegroundColor Yellow
    }
    if (Test-Path $DotVenvPython) {
        $PythonExe = $DotVenvPython
    }
} else {
    Write-Host "[WARN] No virtual environment folder ('venv') found in project root." -ForegroundColor Yellow
}

# Fall back to system python if venv python not found
if (-not $PythonExe) {
    $PythonExe = "python"
}

# 5. Verify Python executable
Write-Host "[DIAGNOSTIC] Testing Python executable: $PythonExe" -ForegroundColor DarkGray
try {
    $PyVersion = & $PythonExe --version 2>&1
    Write-Host "[INFO] Python Detected: $PyVersion" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "======================================================================" -ForegroundColor Red
    Write-Host "[ERROR] Failed to execute Python: $_" -ForegroundColor Red
    Write-Host "Please ensure Python is installed and 'venv' exists in $ScriptDir" -ForegroundColor Red
    Write-Host "======================================================================" -ForegroundColor Red
    Read-Host "Press Enter to close this window..."
    exit 1
}

# 6. Verify run_dashboard.py exists
$LauncherScript = Join-Path $ScriptDir "run_dashboard.py"
if (-not (Test-Path $LauncherScript)) {
    Write-Host ""
    Write-Host "======================================================================" -ForegroundColor Red
    Write-Host "[ERROR] Launcher script 'run_dashboard.py' was not found in $ScriptDir" -ForegroundColor Red
    Write-Host "======================================================================" -ForegroundColor Red
    Read-Host "Press Enter to close this window..."
    exit 1
}

# 7. Execute the launcher script
Write-Host ""
Write-Host "[INFO] Launching dashboard... (Press Ctrl+C to terminate)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

& $PythonExe $LauncherScript $args
$ExitCode = $LASTEXITCODE

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
if ($ExitCode -eq 0) {
    Write-Host "[INFO] Dashboard process terminated cleanly." -ForegroundColor Green
} else {
    Write-Host "[ERROR] Dashboard exited with code $ExitCode." -ForegroundColor Red
}
Write-Host "======================================================================" -ForegroundColor Cyan

# 8. Crucial Pause to prevent window from disappearing
Write-Host ""
Read-Host "Press Enter to close this window..."
exit $ExitCode
