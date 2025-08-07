@echo off
chcp 65001 > nul
echo ========================================
echo   향상된 인쇄 자동화 시스템 빌드
echo ========================================
echo.

:: Python 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    echo    https://www.python.org 에서 설치하세요.
    pause
    exit /b 1
)

:: PyInstaller 설치 확인
echo 📦 PyInstaller 확인 중...
pip show pyinstaller > nul 2>&1
if errorlevel 1 (
    echo PyInstaller 설치 중...
    pip install pyinstaller
)

:: 필요 패키지 설치
echo.
echo 📦 필요 패키지 설치 중...
pip install tkinterdnd2 PyMuPDF Pillow numpy

:: 기존 빌드 정리
echo.
echo 🧹 기존 빌드 정리 중...
if exist "dist\print_automation_enhanced.exe" del "dist\print_automation_enhanced.exe"
if exist "build" rmdir /s /q "build"

:: PyInstaller spec 파일 생성
echo.
echo 📝 spec 파일 생성 중...
(
echo # -*- mode: python ; coding: utf-8 -*-
echo.
echo a = Analysis(
echo     ['print_automation_enhanced.py'],
echo     pathex=[],
echo     binaries=[],
echo     datas=[
echo         ^('enhanced_settings_gui.py', '.'^^),
echo         ^('enhanced_print_processor.py', '.'^^),
echo         ^('enhanced_settings.json', '.'^^),
echo         ^('settings.json', '.'^^),
echo         ^('config.py', '.'^^)
echo     ],
echo     hiddenimports=['tkinterdnd2', 'PIL', 'numpy'],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=[],
echo     noarchive=False,
echo     optimize=0,
echo ^)
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
echo     icon='icon.ico'
echo ^)
) > print_automation_enhanced.spec

:: 빌드 실행
echo.
echo 🔨 EXE 빌드 중... (시간이 걸릴 수 있습니다)
pyinstaller print_automation_enhanced.spec --clean

:: 결과 확인
echo.
if exist "dist\print_automation_enhanced.exe" (
    echo ✅ 빌드 성공!
    echo.
    echo 📁 생성된 파일: dist\print_automation_enhanced.exe
    echo.
    
    :: dist 폴더로 필요 파일 복사
    echo 📋 필요 파일 복사 중...
    if not exist "dist\enhanced_settings.json" copy "enhanced_settings.json" "dist\" > nul 2>&1
    if not exist "dist\settings.json" copy "settings.json" "dist\" > nul 2>&1
    if not exist "dist\설정파일.ini" copy "설정파일.ini" "dist\" > nul 2>&1
    
    :: 향상된 AHK 파일도 복사
    if exist "dist\의뢰서첨부_향상된버전.ahk" (
        echo ✅ 향상된 AHK 파일 준비됨
    ) else (
        copy "dist\의뢰서첨부_향상된버전.ahk" "dist\" > nul 2>&1
    )
    
    echo.
    echo 🎉 모든 준비 완료!
    echo.
    echo 실행 방법:
    echo   1. dist 폴더로 이동
    echo   2. 의뢰서첨부_향상된버전.ahk 실행 (AutoHotkey 필요)
    echo   또는
    echo   3. print_automation_enhanced.exe 직접 실행 (GUI 모드)
) else (
    echo ❌ 빌드 실패!
    echo    오류 메시지를 확인하세요.
)

echo.
pause