@echo off
REM UTF-8 코드 페이지 설정
chcp 65001 > nul 2>&1

title Print Automation System v2.0 - EXE Build

echo ================================================
echo    Print Automation System v2.0 EXE Builder
echo ================================================
echo.

REM 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Administrator privileges may be required.
    echo.
)

REM Python 버전 확인
echo [1/7] Checking Python...
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)
python --version

REM PyInstaller 설치 확인 및 설치
echo.
echo [2/7] Checking PyInstaller...
pip show pyinstaller > nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install --upgrade pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller!
        pause
        exit /b 1
    )
) else (
    echo [OK] PyInstaller already installed
)

REM 필수 패키지 설치
echo.
echo [3/7] Installing required packages...
echo Installing: tkinterdnd2 PyMuPDF Pillow numpy
pip install --upgrade tkinterdnd2 PyMuPDF Pillow numpy
if errorlevel 1 (
    echo [WARNING] Some packages may have failed (continuing anyway)
) else (
    echo [OK] All packages installed
)

REM 기존 빌드 정리
echo.
echo [4/7] Cleaning previous build...
if exist "build" (
    rmdir /s /q "build" 2>nul
    echo [OK] build folder cleaned
)
if exist "dist\print_automation_enhanced.exe" (
    del "dist\print_automation_enhanced.exe" 2>nul
    echo [OK] Previous EXE deleted
)

REM 필요한 파일 확인
echo.
echo [5/7] Checking required files...
set missing_files=0

if not exist "print_automation_enhanced.py" (
    echo [ERROR] print_automation_enhanced.py not found!
    set missing_files=1
) else (
    echo [OK] print_automation_enhanced.py
)

if not exist "enhanced_settings_gui.py" (
    echo [ERROR] enhanced_settings_gui.py not found!
    set missing_files=1
) else (
    echo [OK] enhanced_settings_gui.py
)

if not exist "enhanced_print_processor.py" (
    echo [ERROR] enhanced_print_processor.py not found!
    set missing_files=1
) else (
    echo [OK] enhanced_print_processor.py
)

if %missing_files% equ 1 (
    echo.
    echo [ERROR] Required files are missing. Build cancelled.
    pause
    exit /b 1
)
echo [OK] All required files found

REM spec 파일 생성 (존재하지 않는 경우)
if not exist "print_automation_enhanced.spec" (
    echo.
    echo [5.5/7] Creating spec file...
    
    REM 간단한 spec 파일 생성
    pyi-makespec --onefile --noconsole --name print_automation_enhanced print_automation_enhanced.py
    
    if not exist "print_automation_enhanced.spec" (
        echo [ERROR] Failed to create spec file
        echo Creating basic spec file...
        
        REM 기본 spec 파일 직접 생성
        (
            echo # -*- mode: python ; coding: utf-8 -*-
            echo.
            echo a = Analysis(
            echo     ['print_automation_enhanced.py'],
            echo     pathex=[],
            echo     binaries=[],
            echo     datas=[],
            echo     hiddenimports=['tkinterdnd2', 'PIL', 'numpy', 'fitz'],
            echo     hookspath=[],
            echo     hooksconfig={},
            echo     runtime_hooks=[],
            echo     excludes=[],
            echo     noarchive=False,
            echo ^)
            echo.
            echo pyz = PYZ^(a.pure^)
            echo.
            echo exe = EXE(
            echo     pyz,
            echo     a.scripts,
            echo     a.binaries,
            echo     a.datas,
            echo     [],
            echo     name='print_automation_enhanced',
            echo     debug=False,
            echo     bootloader_ignore_signals=False,
            echo     strip=False,
            echo     upx=True,
            echo     upx_exclude=[],
            echo     runtime_tmpdir=None,
            echo     console=False,
            echo     disable_windowed_traceback=False,
            echo     argv_emulation=False,
            echo     target_arch=None,
            echo     codesign_identity=None,
            echo     entitlements_file=None,
            echo ^)
        ) > print_automation_enhanced.spec
    )
)

REM 빌드 실행
echo.
echo [6/7] Building EXE... (This may take 2-5 minutes)
echo ================================================

pyinstaller --clean --noconfirm print_automation_enhanced.spec

REM 빌드 결과 확인
echo.
echo [7/7] Checking build result...
if exist "dist\print_automation_enhanced.exe" (
    echo [SUCCESS] EXE file created!
    
    REM 파일 크기 확인
    for %%A in ("dist\print_automation_enhanced.exe") do set size=%%~zA
    set /a size_mb=%size% / 1048576
    echo File size: Approximately %size_mb% MB
    
    REM dist 폴더 확인 및 생성
    if not exist "dist" mkdir "dist"
    
    REM 필요 파일 복사
    echo.
    echo Copying required files...
    
    REM 설정 파일들
    if exist "enhanced_settings.json" (
        copy /Y "enhanced_settings.json" "dist\" > nul 2>&1
        echo [OK] enhanced_settings.json copied
    )
    if exist "settings.json" (
        copy /Y "settings.json" "dist\" > nul 2>&1
        echo [OK] settings.json copied
    )
    if exist "coord_presets.json" (
        copy /Y "coord_presets.json" "dist\" > nul 2>&1
        echo [OK] coord_presets.json copied
    )
    
    REM Python 모듈 복사 (필요한 경우)
    if exist "enhanced_settings_gui.py" (
        copy /Y "enhanced_settings_gui.py" "dist\" > nul 2>&1
        echo [OK] enhanced_settings_gui.py copied
    )
    if exist "enhanced_print_processor.py" (
        copy /Y "enhanced_print_processor.py" "dist\" > nul 2>&1
        echo [OK] enhanced_print_processor.py copied
    )
    
    REM AHK 파일 복사
    if exist "dist\의뢰서첨부_향상된버전.ahk" (
        echo [OK] Enhanced AHK file ready
    ) else (
        if exist "의뢰서첨부_향상된버전.ahk" (
            copy /Y "의뢰서첨부_향상된버전.ahk" "dist\" > nul 2>&1
            echo [OK] AHK file copied
        )
    )
    
    REM 실행 배치 파일 생성
    echo.
    echo Creating launch files...
    
    REM GUI 실행 파일
    (
        echo @echo off
        echo chcp 65001 ^> nul
        echo title Print Automation System v2.0
        echo.
        echo if exist "print_automation_enhanced.exe" ^(
        echo     start "" "print_automation_enhanced.exe"
        echo ^) else ^(
        echo     echo Executable not found!
        echo     pause
        echo ^)
    ) > "dist\Run_GUI.bat"
    echo [OK] Run_GUI.bat created
    
    REM 자동화 실행 파일
    (
        echo @echo off
        echo chcp 65001 ^> nul
        echo title Print Automation - AutoHotkey Mode
        echo.
        echo if exist "의뢰서첨부_향상된버전.ahk" ^(
        echo     echo Starting automation system...
        echo     start "" "의뢰서첨부_향상된버전.ahk"
        echo ^) else ^(
        echo     echo AHK file not found!
        echo     pause
        echo ^)
    ) > "dist\Run_AutoHotkey.bat"
    echo [OK] Run_AutoHotkey.bat created
    
    echo.
    echo ================================================
    echo BUILD COMPLETE!
    echo ================================================
    echo.
    echo Location: dist\
    echo Files:
    echo   - print_automation_enhanced.exe (Main program)
    echo   - Run_GUI.bat (GUI mode launcher)
    echo   - Run_AutoHotkey.bat (Automation mode)
    echo.
    echo How to use:
    echo   1. Go to dist folder
    echo   2. Double-click "Run_GUI.bat" for GUI mode
    echo   OR
    echo   3. Double-click "Run_AutoHotkey.bat" for automation
    echo.
    
) else (
    echo [ERROR] EXE build failed!
    echo.
    echo Possible causes:
    echo   1. Antivirus may be blocking
    echo   2. Files may be in use
    echo   3. Insufficient disk space
    echo.
    echo Solutions:
    echo   1. Temporarily disable antivirus
    echo   2. Close all Python programs
    echo   3. Free up disk space
)

echo.
pause