@echo off
chcp 65001 > nul
title 포터블 버전 빌드

echo ╔════════════════════════════════════════════╗
echo ║   인쇄 자동화 시스템 - 포터블 버전 빌드    ║
echo ╚════════════════════════════════════════════╝
echo.
echo 단일 EXE 파일로 패키징합니다 (USB용)
echo.

:: PyInstaller 확인
pip show pyinstaller > nul 2>&1
if errorlevel 1 (
    echo PyInstaller 설치 중...
    pip install pyinstaller
)

:: 기존 파일 정리
if exist "dist\print_automation_portable.exe" del "dist\print_automation_portable.exe"

:: 단일 파일 빌드
echo.
echo 🔨 포터블 버전 빌드 중... (5-10분 소요)
echo ════════════════════════════════════════

pyinstaller --onefile ^
    --noconsole ^
    --name="print_automation_portable" ^
    --add-data="enhanced_settings_gui.py;." ^
    --add-data="enhanced_print_processor.py;." ^
    --add-data="settings_gui.py;." ^
    --add-data="config.py;." ^
    --hidden-import="tkinterdnd2" ^
    --hidden-import="PIL" ^
    --hidden-import="numpy" ^
    --hidden-import="fitz" ^
    print_automation_enhanced.py

:: 결과 확인
echo.
if exist "dist\print_automation_portable.exe" (
    echo ✅ 포터블 버전 생성 완료!
    
    for %%A in ("dist\print_automation_portable.exe") do set size=%%~zA
    set /a size_mb=%size% / 1048576
    echo    파일 크기: 약 %size_mb% MB
    echo.
    echo 📌 포터블 버전 특징:
    echo    • 단일 EXE 파일
    echo    • USB에서 실행 가능
    echo    • 설치 불필요
    echo    • 첫 실행시 속도가 느릴 수 있음
) else (
    echo ❌ 포터블 버전 생성 실패!
)

echo.
pause