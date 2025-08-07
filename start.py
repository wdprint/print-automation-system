#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
향상된 인쇄 자동화 시스템 시작 스크립트
의존성 확인 및 자동 설치
"""

import sys
import os
import subprocess
import platform

def check_and_install_packages():
    """필요한 패키지 확인 및 설치"""
    required_packages = {
        'tkinterdnd2': 'tkinterdnd2',
        'fitz': 'PyMuPDF',
        'PIL': 'Pillow',
        'numpy': 'numpy'
    }
    
    missing_packages = []
    
    print("=" * 60)
    print("향상된 인쇄 자동화 시스템 v2.0")
    print("=" * 60)
    print("\n필요 패키지 확인 중...")
    
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"✓ {package:20} 설치됨")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package:20} 미설치")
    
    if missing_packages:
        print(f"\n다음 패키지를 설치해야 합니다: {', '.join(missing_packages)}")
        response = input("자동으로 설치하시겠습니까? (y/n): ")
        
        if response.lower() == 'y':
            for package in missing_packages:
                print(f"\n{package} 설치 중...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    print(f"✓ {package} 설치 완료")
                except subprocess.CalledProcessError as e:
                    print(f"✗ {package} 설치 실패: {e}")
                    return False
            print("\n모든 패키지 설치 완료!")
            return True
        else:
            print("\n패키지가 설치되지 않았습니다.")
            print("수동으로 설치하려면:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
    
    return True

def check_files():
    """필요한 파일 확인"""
    required_files = [
        'print_automation.py',
        'print_processor.py', 
        'settings_gui.py'
    ]
    
    optional_files = [
        'enhanced_settings.json',
        'settings.json',
        'config.py'
    ]
    
    missing_files = []
    
    print("\n필요 파일 확인 중...")
    
    # 필수 파일 확인
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file:35} 존재")
        else:
            missing_files.append(file)
            print(f"✗ {file:35} 없음")
    
    # 선택적 파일 확인
    print("\n선택적 파일:")
    for file in optional_files:
        if os.path.exists(file):
            print(f"✓ {file:35} 존재")
        else:
            print(f"- {file:35} 없음 (자동 생성됨)")
    
    if missing_files:
        print(f"\n오류: 다음 파일이 필요합니다:")
        for file in missing_files:
            print(f"  - {file}")
        print("\n모든 파일이 같은 폴더에 있는지 확인해주세요.")
        return False
    
    return True

def create_default_config():
    """기본 설정 파일 생성"""
    if not os.path.exists('enhanced_settings.json'):
        default_settings = {
            "thumbnail": {
                "max_width": 160,
                "max_height": 250,
                "positions": [
                    {"x": 70, "y": 180},
                    {"x": 490, "y": 180}
                ],
                "multi_page": False,
                "page_selection": "1",
                "grayscale": False,
                "contrast": 1.0,
                "sharpness": 1.0
            },
            "qr": {
                "max_width": 50,
                "max_height": 50,
                "positions": [
                    {"x": 230, "y": 470},
                    {"x": 650, "y": 470}
                ]
            },
            "blank_detection": {
                "enabled": False,
                "threshold": 95,
                "algorithm": "simple",
                "exclude_areas": {
                    "header": 50,
                    "footer": 50,
                    "left_margin": 20,
                    "right_margin": 20
                },
                "cache_enabled": True
            },
            "processing_rules": {
                "enabled": False,
                "rules": []
            },
            "performance": {
                "multithreading": True,
                "max_concurrent_files": 3,
                "cache_size_mb": 100
            }
        }
        
        import json
        with open('enhanced_settings.json', 'w', encoding='utf-8') as f:
            json.dump(default_settings, f, indent=2, ensure_ascii=False)
        print("✓ 기본 설정 파일 생성됨: enhanced_settings.json")

def print_features():
    """주요 기능 소개"""
    print("\n" + "=" * 60)
    print("✨ 향상된 기능:")
    print("=" * 60)
    print("""
📌 백지 감지
  - 3가지 알고리즘 (단순/엔트로피/히스토그램)
  - 제외 영역 설정
  - 결과 캐싱

📌 프리셋 관리
  - 설정 저장/불러오기
  - 사용 통계
  - 단축키 지정

📌 썸네일 처리
  - 다중 페이지 지원
  - 흑백 변환
  - 대비/선명도 조정

📌 처리 규칙
  - 파일명 패턴 매칭
  - 자동 프리셋 적용
  - 조건부 처리

📌 성능 최적화
  - 멀티스레딩
  - 동시 처리
  - 캐시 관리
""")

def main():
    """메인 함수"""
    # OS 정보 출력
    print(f"운영체제: {platform.system()} {platform.release()}")
    print(f"Python 버전: {sys.version}")
    
    # 패키지 확인 및 설치
    if not check_and_install_packages():
        input("\n엔터를 눌러 종료하세요...")
        return
    
    # 파일 확인
    if not check_files():
        input("\n엔터를 눌러 종료하세요...")
        return
    
    # 기본 설정 생성
    create_default_config()
    
    # 기능 소개
    print_features()
    
    # 메인 프로그램 실행
    print("\n프로그램을 시작합니다...")
    print("-" * 60)
    
    try:
        # 메인 프로그램 실행
        import print_automation
        app = print_automation.PrintAutomationGUI()
        app.run()
        except Exception as e:
            print(f"\n오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            input("\n엔터를 눌러 종료하세요...")
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        input("\n엔터를 눌러 종료하세요...")

if __name__ == "__main__":
    main()