#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""실시간 좌표 업데이트 및 프리셋 UI 개선 테스트"""

import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent))

def test_realtime_update():
    """실시간 업데이트 테스트"""
    print("=" * 60)
    print("실시간 좌표 업데이트 및 UI 개선 테스트")
    print("=" * 60)
    
    print("\n✅ 개선된 기능:")
    print("\n1. 🔄 실시간 좌표 업데이트")
    print("   - 박스를 드래그하면 왼쪽 목록의 좌표가 즉시 변경됩니다")
    print("   - 박스 크기를 조절해도 실시간으로 반영됩니다")
    print("   - 저장하지 않아도 현재 상태를 바로 확인 가능")
    
    print("\n2. 📋 명확한 프리셋 버튼")
    print("   - 📥 불러오기: 프리셋의 설정을 현재 작업에 적용")
    print("   - 💾 여기에 저장: 현재 작업 중인 설정을 해당 프리셋에 저장")
    print("   - 더 이상 헷갈리지 않는 직관적인 표현")
    
    print("\n" + "=" * 60)
    print("테스트 방법:")
    print("\n📍 좌표 설정 페이지에서:")
    print("1. PDF를 불러온 후 박스를 드래그해보세요")
    print("2. 왼쪽 목록의 좌표값이 실시간으로 변경되는지 확인")
    print("3. 박스 모서리를 드래그하여 크기 조절")
    print("4. 크기값도 실시간으로 업데이트되는지 확인")
    
    print("\n🎯 프리셋 관리 페이지에서:")
    print("1. '📥 불러오기' 버튼 = 저장된 프리셋을 불러와서 사용")
    print("2. '💾 여기에 저장' 버튼 = 현재 설정을 이 프리셋에 저장")
    print("3. 각 버튼의 역할이 명확하게 구분됨")
    
    print("\n" + "=" * 60)
    
    from gui.modern_settings import ModernSettingsWindow
    
    print("\n설정 창을 열고 있습니다...")
    settings_window = ModernSettingsWindow()
    
    # 좌표 설정 페이지로 시작
    settings_window.show_coordinates_page()
    
    print("\n✅ 설정 창이 열렸습니다.")
    print("\n💡 테스트 순서:")
    print("1. 먼저 '📄 PDF 불러오기' 버튼으로 샘플 PDF를 로드하세요")
    print("2. 박스를 드래그하면서 왼쪽 좌표값이 실시간으로 변하는지 확인")
    print("3. 프리셋 관리로 이동하여 버튼 이름이 명확한지 확인")
    print("4. '여기에 저장' → '불러오기' 순서로 테스트")
    
    print("\n📌 중요:")
    print("- 이제 좌표를 조정하면서 바로 값을 확인할 수 있습니다")
    print("- 프리셋 버튼이 더 직관적으로 변경되었습니다")
    
    # 메인 루프 실행
    settings_window.run()
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    test_realtime_update()