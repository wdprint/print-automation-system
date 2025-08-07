#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
인쇄 자동화 시스템 시작 스크립트
한글 인코딩 문제 방지 및 필요 모듈 확인
"""

import sys
import os
import subprocess

def check_and_install_packages():
    """필요한 패키지 확인 및 설치"""
    required_packages = {
        'tkinterdnd2': 'tkinterdnd2',
        'fitz': 'PyMuPDF',
        'PIL': 'Pillow'
    }
    
    missing_packages = []
    
    print("필요 패키지 확인 중...")
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"✓ {package} 설치됨")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} 미설치")
    
    if missing_packages:
        print(f"\n다음 패키지를 설치합니다: {', '.join(missing_packages)}")
        response = input("설치하시겠습니까? (y/n): ")
        
        if response.lower() == 'y':
            for package in missing_packages:
                print(f"\n{package} 설치 중...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print("\n설치 완료!")
            return True
        else:
            print("\n패키지가 설치되지 않았습니다. 프로그램을 종료합니다.")
            return False
    
    return True

def check_files():
    """필요한 파일 확인"""
    required_files = ['print_automation.py', 'settings_gui.py']
    missing_files = []
    
    print("\n필요 파일 확인 중...")
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} 존재")
        else:
            missing_files.append(file)
            print(f"✗ {file} 없음")
    
    if missing_files:
        print(f"\n오류: 다음 파일이 필요합니다: {', '.join(missing_files)}")
        print("모든 파일이 같은 폴더에 있는지 확인해주세요.")
        return False
    
    return True

def main():
    print("=" * 50)
    print("인쇄 의뢰서 자동화 시스템")
    print("=" * 50)
    
    # 패키지 확인 및 설치
    if not check_and_install_packages():
        input("\n엔터를 눌러 종료하세요...")
        return
    
    # 파일 확인
    if not check_files():
        input("\n엔터를 눌러 종료하세요...")
        return
    
    # 메인 프로그램 실행
    print("\n프로그램을 시작합니다...")
    print("-" * 50)
    
    try:
        import print_automation
        app = print_automation.PrintAutomationGUI()
        app.run()
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        input("\n엔터를 눌러 종료하세요...")

if __name__ == "__main__":
    main()
