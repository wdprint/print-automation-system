@echo off
chcp 65001 > nul
title 인쇄 자동화 시스템 EXE 빌드

echo ╔════════════════════════════════════════════╗
echo ║   인쇄 자동화 시스템 v2.0 EXE 빌드        ║
echo ╚════════════════════════════════════════════╝
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  관리자 권한이 필요할 수 있습니다.
    echo.
)

:: Python 버전 확인
echo [1/7] Python 확인 중...
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다!
    echo    https://www.python.org 에서 Python 3.8 이상을 설치하세요.
    pause
    exit /b 1
)
python --version

:: PyInstaller 설치 확인 및 설치
echo.
echo [2/7] PyInstaller 확인 중...
pip show pyinstaller > nul 2>&1
if errorlevel 1 (
    echo PyInstaller 설치 중...
    pip install --upgrade pyinstaller
    if errorlevel 1 (
        echo ❌ PyInstaller 설치 실패!
        pause
        exit /b 1
    )
) else (
    echo ✅ PyInstaller 이미 설치됨
)

:: 필수 패키지 설치
echo.
echo [3/7] 필수 패키지 설치 중...
pip install --upgrade tkinterdnd2 PyMuPDF Pillow numpy > nul 2>&1
if errorlevel 1 (
    echo ⚠️  일부 패키지 설치 실패 (계속 진행)
) else (
    echo ✅ 필수 패키지 설치 완료
)

:: 기존 빌드 정리
echo.
echo [4/7] 기존 빌드 정리 중...
if exist "build" (
    rmdir /s /q "build" 2>nul
    echo ✅ build 폴더 정리됨
)
if exist "dist\print_automation_enhanced.exe" (
    del "dist\print_automation_enhanced.exe" 2>nul
    echo ✅ 기존 EXE 파일 삭제됨
)

:: 필요한 파일 확인
echo.
echo [5/7] 필요 파일 확인 중...
set missing_files=0

if not exist "print_automation_enhanced.py" (
    echo ❌ print_automation_enhanced.py 파일이 없습니다!
    set missing_files=1
)
if not exist "enhanced_settings_gui.py" (
    echo ❌ enhanced_settings_gui.py 파일이 없습니다!
    set missing_files=1
)
if not exist "enhanced_print_processor.py" (
    echo ❌ enhanced_print_processor.py 파일이 없습니다!
    set missing_files=1
)

if %missing_files% equ 1 (
    echo.
    echo ❌ 필수 파일이 없습니다. 빌드를 중단합니다.
    pause
    exit /b 1
)
echo ✅ 모든 필수 파일 확인됨

:: 빌드 실행
echo.
echo [6/7] EXE 빌드 시작... (2-5분 소요)
echo ════════════════════════════════════════
pyinstaller print_automation_enhanced.spec --clean --noconfirm

:: 빌드 결과 확인
echo.
echo [7/7] 빌드 결과 확인 중...
if exist "dist\print_automation_enhanced.exe" (
    echo ✅ EXE 파일 생성 성공!
    
    :: 파일 크기 확인
    for %%A in ("dist\print_automation_enhanced.exe") do set size=%%~zA
    set /a size_mb=%size% / 1048576
    echo    파일 크기: 약 %size_mb% MB
    
    :: 필요 파일 복사
    echo.
    echo 📋 필요 파일 복사 중...
    
    :: 설정 파일들
    if exist "enhanced_settings.json" (
        copy /Y "enhanced_settings.json" "dist\" > nul 2>&1
        echo ✅ enhanced_settings.json 복사됨
    )
    if exist "settings.json" (
        copy /Y "settings.json" "dist\" > nul 2>&1
        echo ✅ settings.json 복사됨
    )
    if exist "coord_presets.json" (
        copy /Y "coord_presets.json" "dist\" > nul 2>&1
        echo ✅ coord_presets.json 복사됨
    )
    
    :: INI 파일
    if exist "설정파일.ini" (
        copy /Y "설정파일.ini" "dist\" > nul 2>&1
        echo ✅ 설정파일.ini 복사됨
    )
    
    :: AHK 파일 확인
    if exist "dist\의뢰서첨부_향상된버전.ahk" (
        echo ✅ 향상된 AHK 파일 준비됨
    )
    
    :: 실행 배치 파일 생성
    echo.
    echo 📝 실행 파일 생성 중...
    (
        echo @echo off
        echo chcp 65001 ^> nul
        echo title 인쇄 자동화 시스템 v2.0
        echo.
        echo if exist "print_automation_enhanced.exe" ^(
        echo     start "" "print_automation_enhanced.exe"
        echo ^) else ^(
        echo     echo 실행 파일을 찾을 수 없습니다!
        echo     pause
        echo ^)
    ) > "dist\실행.bat"
    echo ✅ 실행.bat 생성됨
    
    :: 자동화 실행 파일 생성
    (
        echo @echo off
        echo chcp 65001 ^> nul
        echo title 인쇄 자동화 시스템 - 자동화 모드
        echo.
        echo :: AutoHotkey 확인
        echo where AutoHotkey.exe ^> nul 2^>^&1
        echo if errorlevel 1 ^(
        echo     where AutoHotkey64.exe ^> nul 2^>^&1
        echo     if errorlevel 1 ^(
        echo         echo AutoHotkey가 설치되지 않았습니다.
        echo         echo https://www.autohotkey.com 에서 설치하세요.
        echo         pause
        echo         exit /b 1
        echo     ^) else ^(
        echo         set AHK_EXE=AutoHotkey64.exe
        echo     ^)
        echo ^) else ^(
        echo     set AHK_EXE=AutoHotkey.exe
        echo ^)
        echo.
        echo if exist "의뢰서첨부_향상된버전.ahk" ^(
        echo     echo 향상된 자동화 시스템을 시작합니다...
        echo     start "" "%%AHK_EXE%%" "의뢰서첨부_향상된버전.ahk"
        echo ^) else ^(
        echo     echo AHK 파일을 찾을 수 없습니다!
        echo     pause
        echo ^)
    ) > "dist\자동화_실행.bat"
    echo ✅ 자동화_실행.bat 생성됨
    
    echo.
    echo ════════════════════════════════════════
    echo 🎉 빌드 완료!
    echo ════════════════════════════════════════
    echo.
    echo 📁 생성된 파일 위치: dist\
    echo    • print_automation_enhanced.exe (메인 프로그램)
    echo    • 의뢰서첨부_향상된버전.ahk (자동화 스크립트)
    echo    • 실행.bat (GUI 모드 실행)
    echo    • 자동화_실행.bat (자동화 모드 실행)
    echo.
    echo 💡 사용 방법:
    echo    1. dist 폴더로 이동
    echo    2. "실행.bat" 더블클릭 (GUI 모드)
    echo    또는
    echo    3. "자동화_실행.bat" 더블클릭 (단축키 모드)
    echo.
    
) else (
    echo ❌ EXE 파일 생성 실패!
    echo.
    echo 가능한 원인:
    echo    1. 바이러스 백신이 차단했을 수 있습니다
    echo    2. 파일이 사용 중일 수 있습니다
    echo    3. 디스크 공간이 부족할 수 있습니다
    echo.
    echo 해결 방법:
    echo    1. 바이러스 백신 일시 중지 후 재시도
    echo    2. 모든 Python 프로그램 종료 후 재시도
    echo    3. 디스크 공간 확보 후 재시도
)

echo.
pause