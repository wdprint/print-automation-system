@echo off
REM PDF Automation System EXE Builder (Korean)
REM No special characters, simple commands only

echo ============================================
echo    PDF Automation System EXE Builder
echo ============================================
echo.

REM Check Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    echo Please install Python first
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Run Python build script
echo Starting build process...
echo.

python build_exe_simple.py

echo.
echo Press any key to exit...
pause > nul