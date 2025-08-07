@echo off
chcp 65001 > nul
title 빌드 정리

echo ╔════════════════════════════════════════════╗
echo ║         빌드 파일 정리 도구                ║
echo ╚════════════════════════════════════════════╝
echo.

echo 다음 항목들을 삭제합니다:
echo • build 폴더
echo • __pycache__ 폴더들
echo • *.pyc 파일들
echo • *.spec 파일 (선택)
echo.

set /p confirm="계속하시겠습니까? (Y/N): "
if /i "%confirm%" neq "Y" (
    echo 취소되었습니다.
    pause
    exit /b 0
)

echo.
echo 정리 중...

:: build 폴더 삭제
if exist "build" (
    rmdir /s /q "build"
    echo ✅ build 폴더 삭제됨
)

:: __pycache__ 폴더들 삭제
for /d /r %%d in (__pycache__) do (
    if exist "%%d" (
        rmdir /s /q "%%d"
        echo ✅ %%d 삭제됨
    )
)

:: *.pyc 파일 삭제
del /s /q *.pyc 2>nul
echo ✅ *.pyc 파일들 삭제됨

:: spec 파일 삭제 여부 확인
set /p del_spec="spec 파일도 삭제하시겠습니까? (Y/N): "
if /i "%del_spec%" equ "Y" (
    del /q *.spec 2>nul
    echo ✅ *.spec 파일들 삭제됨
)

echo.
echo ✨ 정리 완료!
echo.
pause