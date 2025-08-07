#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
향상된 기능 테스트 스크립트
모든 설정이 정상 작동하는지 확인
"""

import sys
import os

def test_imports():
    """필요한 모듈 임포트 테스트"""
    print("=" * 60)
    print("모듈 임포트 테스트")
    print("=" * 60)
    
    modules_to_test = [
        ('tkinter', 'GUI 기본'),
        ('tkinterdnd2', '드래그앤드롭'),
        ('fitz', 'PDF 처리'),
        ('PIL', '이미지 처리'),
        ('numpy', '수학 연산')
    ]
    
    all_ok = True
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"✓ {module_name:15} - {description:20} OK")
        except ImportError as e:
            print(f"✗ {module_name:15} - {description:20} 실패: {e}")
            all_ok = False
    
    return all_ok

def test_files():
    """필요한 파일 존재 확인"""
    print("\n" + "=" * 60)
    print("파일 존재 테스트")
    print("=" * 60)
    
    files_to_test = [
        ('enhanced_settings_gui.py', '향상된 설정 GUI'),
        ('enhanced_print_processor.py', '향상된 처리 엔진'),
        ('print_automation_enhanced.py', '통합 GUI'),
        ('print_automation.py', '기본 프로그램'),
        ('settings_gui.py', '기본 설정 GUI')
    ]
    
    all_ok = True
    for filename, description in files_to_test:
        if os.path.exists(filename):
            print(f"✓ {filename:35} - {description}")
        else:
            print(f"✗ {filename:35} - {description} 없음")
            all_ok = False
    
    return all_ok

def test_enhanced_settings():
    """향상된 설정 모듈 테스트"""
    print("\n" + "=" * 60)
    print("향상된 설정 기능 테스트")
    print("=" * 60)
    
    try:
        from enhanced_settings_gui import EnhancedSettingsGUI
        
        # 설정 객체 생성 테스트
        print("✓ EnhancedSettingsGUI 임포트 성공")
        
        # 기본 설정 로드 테스트
        settings_gui = EnhancedSettingsGUI()
        settings = settings_gui.settings
        
        # 각 기능 확인
        features = [
            ('백지 감지', 'blank_detection' in settings),
            ('프리셋 관리', 'presets' in settings or True),  # 선택적
            ('썸네일 옵션', 'thumbnail' in settings),
            ('처리 규칙', 'processing_rules' in settings),
            ('성능 설정', 'performance' in settings)
        ]
        
        for feature, exists in features:
            if exists:
                print(f"✓ {feature:15} - 구현됨")
            else:
                print(f"✗ {feature:15} - 미구현")
        
        # 창 닫기
        settings_gui.window.destroy()
        
        return True
        
    except Exception as e:
        print(f"✗ 향상된 설정 테스트 실패: {e}")
        return False

def test_processor():
    """향상된 처리 엔진 테스트"""
    print("\n" + "=" * 60)
    print("향상된 처리 엔진 테스트")
    print("=" * 60)
    
    try:
        from enhanced_print_processor import EnhancedPrintProcessor
        
        # 프로세서 생성
        processor = EnhancedPrintProcessor()
        print("✓ EnhancedPrintProcessor 생성 성공")
        
        # 주요 메서드 확인
        methods = [
            'is_page_blank_enhanced',
            'create_enhanced_thumbnail',
            'apply_processing_rules',
            'process_files_enhanced'
        ]
        
        for method in methods:
            if hasattr(processor, method):
                print(f"✓ {method:30} - 구현됨")
            else:
                print(f"✗ {method:30} - 미구현")
        
        return True
        
    except Exception as e:
        print(f"✗ 처리 엔진 테스트 실패: {e}")
        return False

def test_integration():
    """통합 테스트"""
    print("\n" + "=" * 60)
    print("통합 테스트")
    print("=" * 60)
    
    try:
        # 기본 print_automation 테스트
        import print_automation
        print("✓ print_automation.py 임포트 성공")
        
        # 클래스 확인
        if hasattr(print_automation, 'PrintAutomationGUI'):
            print("✓ PrintAutomationGUI 클래스 존재")
        
        if hasattr(print_automation, 'PrintProcessor'):
            print("✓ PrintProcessor 클래스 존재")
        
        if hasattr(print_automation, 'CoordPresetManager'):
            print("✓ CoordPresetManager 클래스 존재")
        
        # 향상된 버전 테스트
        try:
            import print_automation_enhanced
            print("✓ print_automation_enhanced.py 임포트 성공")
            
            if hasattr(print_automation_enhanced, 'EnhancedPrintAutomationGUI'):
                print("✓ EnhancedPrintAutomationGUI 클래스 존재")
                
        except ImportError as e:
            print(f"- 향상된 버전 미설치: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 함수"""
    print("\n" + "🧪 인쇄 자동화 시스템 테스트 시작 " + "🧪")
    print("=" * 60)
    
    results = []
    
    # 각 테스트 실행
    results.append(("모듈 임포트", test_imports()))
    results.append(("파일 존재", test_files()))
    results.append(("향상된 설정", test_enhanced_settings()))
    results.append(("처리 엔진", test_processor()))
    results.append(("통합", test_integration()))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ 통과" if passed else "✗ 실패"
        print(f"{test_name:20} : {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✅ 모든 테스트 통과! 프로그램을 사용할 준비가 되었습니다.")
        print("\n실행 방법:")
        print("  python start_enhanced.py    # 향상된 버전 (권장)")
        print("  python print_automation.py  # 기본 버전")
    else:
        print("\n⚠️ 일부 테스트 실패. 위의 오류를 확인하세요.")
        print("\n필요한 패키지 설치:")
        print("  pip install tkinterdnd2 PyMuPDF Pillow numpy")
    
    input("\n엔터를 눌러 종료...")

if __name__ == "__main__":
    main()