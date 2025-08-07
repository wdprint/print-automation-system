#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
간단한 Python 기반 빌드 스크립트
한글 인코딩 문제 해결
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header():
    """헤더 출력"""
    print("=" * 60)
    print("   인쇄 자동화 시스템 v2.0 - EXE 빌드")
    print("=" * 60)
    print()

def check_python():
    """Python 버전 확인"""
    print("[1/6] Python 버전 확인...")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7 이상이 필요합니다!")
        return False
    
    print("✅ Python 버전 OK")
    return True

def install_packages():
    """필요 패키지 설치"""
    print("\n[2/6] 필요 패키지 설치...")
    
    packages = [
        "pyinstaller",
        "tkinterdnd2",
        "PyMuPDF",
        "Pillow",
        "numpy"
    ]
    
    for package in packages:
        print(f"  설치 중: {package}")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", package], 
                         capture_output=True, text=True, check=True)
            print(f"  ✅ {package} 설치됨")
        except subprocess.CalledProcessError:
            print(f"  ⚠️ {package} 설치 실패 (계속 진행)")
    
    return True

def clean_build():
    """기존 빌드 정리"""
    print("\n[3/6] 기존 빌드 정리...")
    
    # build 폴더 삭제
    if Path("build").exists():
        shutil.rmtree("build", ignore_errors=True)
        print("  ✅ build 폴더 삭제됨")
    
    # 기존 exe 삭제
    exe_path = Path("dist/print_automation_enhanced.exe")
    if exe_path.exists():
        exe_path.unlink()
        print("  ✅ 기존 EXE 삭제됨")
    
    return True

def check_files():
    """필요 파일 확인"""
    print("\n[4/6] 필요 파일 확인...")
    
    required_files = [
        "print_automation_enhanced.py",
        "enhanced_settings_gui.py",
        "enhanced_print_processor.py"
    ]
    
    missing = []
    for file in required_files:
        if Path(file).exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - 없음")
            missing.append(file)
    
    if missing:
        print("\n❌ 필수 파일이 없습니다!")
        return False
    
    return True

def create_spec():
    """spec 파일 생성"""
    print("\n[4.5/6] spec 파일 생성...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['print_automation_enhanced.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('enhanced_settings_gui.py', '.'),
        ('enhanced_print_processor.py', '.'),
    ],
    hiddenimports=['tkinterdnd2', 'PIL', 'numpy', 'fitz'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'pandas', 'scipy'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='print_automation_enhanced',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open("print_automation_enhanced.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    print("  ✅ spec 파일 생성됨")
    return True

def build_exe():
    """EXE 빌드"""
    print("\n[5/6] EXE 빌드 중... (2-5분 소요)")
    print("=" * 60)
    
    try:
        # PyInstaller 실행
        result = subprocess.run(
            ["pyinstaller", "--clean", "--noconfirm", "print_automation_enhanced.spec"],
            capture_output=False,
            text=True
        )
        
        if result.returncode != 0:
            print("\n❌ 빌드 실패!")
            return False
            
    except Exception as e:
        print(f"\n❌ 빌드 오류: {e}")
        return False
    
    return True

def copy_files():
    """필요 파일 복사"""
    print("\n[6/6] 필요 파일 복사...")
    
    # dist 폴더 확인
    dist_path = Path("dist")
    if not dist_path.exists():
        dist_path.mkdir(parents=True)
    
    # 복사할 파일들
    files_to_copy = [
        "enhanced_settings.json",
        "settings.json",
        "coord_presets.json",
        "enhanced_settings_gui.py",
        "enhanced_print_processor.py"
    ]
    
    for file in files_to_copy:
        src = Path(file)
        if src.exists():
            dst = dist_path / file
            shutil.copy2(src, dst)
            print(f"  ✅ {file} 복사됨")
    
    # AHK 파일 복사
    ahk_src = Path("dist/의뢰서첨부_향상된버전.ahk")
    if not ahk_src.exists():
        ahk_alt = Path("의뢰서첨부_향상된버전.ahk")
        if ahk_alt.exists():
            shutil.copy2(ahk_alt, dist_path)
            print("  ✅ AHK 파일 복사됨")
    
    # 실행 파일 생성
    create_launchers(dist_path)
    
    return True

def create_launchers(dist_path):
    """실행 파일 생성"""
    
    # GUI 실행 파일
    gui_launcher = """@echo off
chcp 65001 > nul
title 인쇄 자동화 시스템 v2.0

if exist "print_automation_enhanced.exe" (
    start "" "print_automation_enhanced.exe"
) else (
    echo 실행 파일을 찾을 수 없습니다!
    pause
)
"""
    
    with open(dist_path / "실행_GUI.bat", "w", encoding="utf-8") as f:
        f.write(gui_launcher)
    
    print("  ✅ 실행_GUI.bat 생성됨")
    
    # 자동화 실행 파일
    ahk_launcher = """@echo off
chcp 65001 > nul
title 인쇄 자동화 - 자동화 모드

if exist "의뢰서첨부_향상된버전.ahk" (
    echo 자동화 시스템을 시작합니다...
    start "" "의뢰서첨부_향상된버전.ahk"
) else (
    echo AHK 파일을 찾을 수 없습니다!
    pause
)
"""
    
    with open(dist_path / "실행_자동화.bat", "w", encoding="utf-8") as f:
        f.write(ahk_launcher)
    
    print("  ✅ 실행_자동화.bat 생성됨")

def check_result():
    """빌드 결과 확인"""
    exe_path = Path("dist/print_automation_enhanced.exe")
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        
        print("\n" + "=" * 60)
        print("🎉 빌드 성공!")
        print("=" * 60)
        print(f"\n📁 위치: dist\\")
        print(f"📦 파일 크기: {size_mb:.1f} MB")
        print("\n실행 방법:")
        print("  1. dist 폴더로 이동")
        print("  2. '실행_GUI.bat' 더블클릭 (GUI 모드)")
        print("  또는")
        print("  3. '실행_자동화.bat' 더블클릭 (자동화 모드)")
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ 빌드 실패!")
        print("=" * 60)
        print("\n가능한 원인:")
        print("  1. 바이러스 백신이 차단")
        print("  2. 파일이 사용 중")
        print("  3. 디스크 공간 부족")
        return False

def main():
    """메인 함수"""
    try:
        # UTF-8 설정
        if sys.platform == "win32":
            os.system("chcp 65001 > nul")
        
        print_header()
        
        # 단계별 실행
        if not check_python():
            return 1
        
        if not install_packages():
            return 1
        
        if not clean_build():
            return 1
        
        if not check_files():
            return 1
        
        if not create_spec():
            return 1
        
        if not build_exe():
            return 1
        
        if not copy_files():
            return 1
        
        if not check_result():
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 취소되었습니다.")
        return 1
    except Exception as e:
        print(f"\n\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        input("\n엔터를 눌러 종료...")

if __name__ == "__main__":
    sys.exit(main())