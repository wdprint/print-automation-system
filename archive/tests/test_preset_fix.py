#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""프리셋 문제 해결 테스트"""

import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent))

def test_preset_fix():
    """프리셋 문제 해결 테스트"""
    print("=" * 60)
    print("프리셋 적용 문제 해결")
    print("=" * 60)
    
    print("\n🔧 해결된 문제:")
    print("1. coord_vars 초기화 오류 수정")
    print("2. 위젯 경로 오류 처리")
    print("3. 프리셋 데이터 구조 개선")
    print("4. 안전한 UI 업데이트")
    
    print("\n📋 문제 해결 단계:")
    
    print("\n1. 먼저 프리셋을 초기화합니다:")
    print("   python reset_presets.py")
    
    import subprocess
    import os
    
    # 프리셋 초기화 실행
    try:
        result = subprocess.run([sys.executable, "reset_presets.py"], 
                              capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print("\n✅ 프리셋 초기화 성공!")
        else:
            print(f"\n⚠️ 프리셋 초기화 중 경고: {result.stderr}")
    except Exception as e:
        print(f"\n⚠️ 프리셋 초기화 실패: {e}")
        print("   수동으로 'python reset_presets.py'를 실행해주세요.")
    
    print("\n2. 설정 창을 열어 테스트합니다:")
    
    from gui.modern_settings import ModernSettingsWindow
    
    print("\n설정 창을 열고 있습니다...")
    settings_window = ModernSettingsWindow()
    
    # 프리셋 페이지로 이동
    settings_window.show_presets_page()
    
    print("\n✅ 설정 창이 열렸습니다.")
    print("\n테스트 순서:")
    print("1. 각 프리셋의 '현재 설정 저장' 버튼을 클릭하여 설정을 저장")
    print("2. 좌표 설정 페이지에서 박스 위치 변경")
    print("3. 다시 프리셋 관리로 돌아와서 특정 프리셋에 저장")
    print("4. 다른 프리셋 적용해보기")
    print("5. 이전 프리셋 다시 적용하여 설정이 독립적으로 유지되는지 확인")
    
    print("\n💡 팁:")
    print("- 프리셋을 처음 사용할 때는 '현재 설정 저장'을 먼저 해주세요")
    print("- 각 프리셋은 독립적으로 설정을 저장합니다")
    print("- F1~F4는 단축키로 사용할 수 있습니다")
    
    # 메인 루프 실행
    settings_window.run()
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    test_preset_fix()