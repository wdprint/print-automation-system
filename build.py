#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF 인쇄 의뢰서 자동화 시스템 빌드 스크립트
Windows EXE 파일 생성용
"""

import os
import sys
import shutil
import PyInstaller.__main__
from pathlib import Path

def clean_build():
    """기존 빌드 파일 정리"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"정리 중: {dir_name}")
            shutil.rmtree(dir_name)
    
    for pattern in files_to_clean:
        for file in Path('.').glob(pattern):
            print(f"삭제 중: {file}")
            file.unlink()

def build_exe():
    """PyInstaller로 EXE 빌드"""
    
    # 아이콘 파일 경로 (있는 경우)
    icon_path = 'resources/icons/app.ico' if os.path.exists('resources/icons/app.ico') else None
    
    # PyInstaller 인자
    args = [
        'main.py',
        '--name=print_automation',
        '--onefile',
        '--windowed',
        '--clean',
        '--noconfirm',
        
        # 데이터 파일 포함
        '--add-data=settings.example.json;.',
        '--add-data=samples;samples',
        '--add-data=CLAUDE.md;.',
        '--add-data=README.md;.',
        
        # 숨겨진 import
        '--hidden-import=tkinterdnd2',
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=customtkinter',
        '--hidden-import=numpy',
        '--hidden-import=fitz',
        '--hidden-import=PyMuPDF',
        '--hidden-import=pdf2image',
        '--hidden-import=pypdfium2',
        
        # 경로 설정
        '--distpath=dist',
        '--workpath=build',
        '--specpath=.',
        
        # 최적화
        '--optimize=2',
    ]
    
    # 아이콘이 있으면 추가
    if icon_path:
        args.append(f'--icon={icon_path}')
    
    print("=" * 60)
    print("PDF 인쇄 의뢰서 자동화 시스템 빌드 시작")
    print("=" * 60)
    
    # PyInstaller 실행
    PyInstaller.__main__.run(args)
    
    print("\n" + "=" * 60)
    print("빌드 완료!")
    print("=" * 60)
    
    # 빌드 결과 확인
    exe_path = Path('dist/print_automation.exe')
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n✅ 생성된 파일: {exe_path}")
        print(f"📦 파일 크기: {size_mb:.2f} MB")
        
        # 추가 파일 복사
        print("\n📋 추가 파일 복사 중...")
        
        # settings.example.json을 dist로 복사
        if os.path.exists('settings.example.json'):
            shutil.copy('settings.example.json', 'dist/settings.example.json')
            print("  - settings.example.json 복사 완료")
        
        # README 복사
        if os.path.exists('README.md'):
            shutil.copy('README.md', 'dist/README.md')
            print("  - README.md 복사 완료")
        
        print("\n🎉 모든 작업 완료!")
        print(f"📂 배포 디렉토리: {Path('dist').absolute()}")
        
        # 사용법 안내
        print("\n" + "=" * 60)
        print("사용법:")
        print("1. dist 폴더로 이동")
        print("2. print_automation.exe 실행")
        print("3. 첫 실행 시 settings.example.json을 settings.json으로 복사")
        print("=" * 60)
        
    else:
        print("\n❌ 빌드 실패: EXE 파일이 생성되지 않았습니다.")
        sys.exit(1)

def create_installer():
    """NSIS 설치 프로그램 스크립트 생성 (선택사항)"""
    nsis_script = """
; PDF 인쇄 의뢰서 자동화 시스템 설치 스크립트
!define PRODUCT_NAME "PDF Print Automation"
!define PRODUCT_VERSION "2.0.0"
!define PRODUCT_PUBLISHER "wdprint"

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "print_automation_setup.exe"
InstallDir "$PROGRAMFILES\\${PRODUCT_NAME}"
RequestExecutionLevel admin

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  File "dist\\print_automation.exe"
  File "dist\\settings.example.json"
  File "dist\\README.md"
  
  CreateDirectory "$SMPROGRAMS\\${PRODUCT_NAME}"
  CreateShortcut "$SMPROGRAMS\\${PRODUCT_NAME}\\${PRODUCT_NAME}.lnk" "$INSTDIR\\print_automation.exe"
  CreateShortcut "$DESKTOP\\${PRODUCT_NAME}.lnk" "$INSTDIR\\print_automation.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\\*.*"
  RMDir "$INSTDIR"
  Delete "$SMPROGRAMS\\${PRODUCT_NAME}\\*.*"
  RMDir "$SMPROGRAMS\\${PRODUCT_NAME}"
  Delete "$DESKTOP\\${PRODUCT_NAME}.lnk"
SectionEnd
"""
    
    with open('installer.nsi', 'w', encoding='utf-8') as f:
        f.write(nsis_script)
    
    print("\n📝 NSIS 설치 스크립트 생성됨: installer.nsi")
    print("   NSIS가 설치되어 있다면 다음 명령으로 설치 프로그램을 만들 수 있습니다:")
    print("   makensis installer.nsi")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='빌드 스크립트')
    parser.add_argument('--clean', action='store_true', help='빌드 전 정리')
    parser.add_argument('--installer', action='store_true', help='설치 프로그램 스크립트 생성')
    
    args = parser.parse_args()
    
    if args.clean:
        clean_build()
    
    # 메인 빌드
    build_exe()
    
    if args.installer:
        create_installer()