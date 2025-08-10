#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""프리셋 미리보기 테스트 스크립트"""

import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent))

from gui.modern_settings import ModernSettingsWindow

def test_preset_preview():
    """프리셋 미리보기 테스트"""
    print("=" * 50)
    print("프리셋 시각적 미리보기 테스트")
    print("=" * 50)
    
    print("\n1. 설정 창 열기...")
    settings_window = ModernSettingsWindow()
    
    print("2. 프리셋 페이지로 이동...")
    # 프리셋 페이지 표시 (인덱스 4)
    settings_window.show_presets_page()
    
    print("\n테스트 내용:")
    print("- 각 프리셋 카드에 시각적 미리보기가 표시되는지 확인")
    print("- 미리보기에 썸네일 박스와 QR 박스가 올바르게 표시되는지 확인")
    print("- 각 프리셋별로 다른 좌표 설정이 반영되는지 확인")
    print("")
    print("✅ 설정 창이 열렸습니다.")
    print("프리셋 관리 메뉴를 확인하세요.")
    
    # 메인 루프 실행
    settings_window.run()
    
    print("\n" + "=" * 50)
    print("테스트 완료!")
    print("=" * 50)

if __name__ == "__main__":
    test_preset_preview()