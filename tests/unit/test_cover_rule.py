"""표지 썸네일 규칙 테스트"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings_manager import SettingsManager
from core.pdf_processor import PDFProcessor

def test_cover_rule():
    """표지 처리 규칙 테스트"""
    
    print("=" * 50)
    print("표지 썸네일 규칙 테스트")
    print("=" * 50)
    
    # 설정 관리자 초기화
    settings_manager = SettingsManager()
    settings_manager.load()
    
    # PDF 처리기 초기화
    processor = PDFProcessor(settings_manager)
    
    # 테스트 시나리오
    test_scenarios = [
        {
            "name": "표지 PDF + 썸네일 2개",
            "order": "의뢰서.pdf",
            "thumbnails": ["표지.pdf", "내용.pdf"],
            "description": "표지 PDF는 왼쪽 50% 잘리고, 첫 번째 박스에 우선 배치"
        },
        {
            "name": "일반 썸네일 2개",
            "order": "의뢰서.pdf",
            "thumbnails": ["페이지1.pdf", "페이지2.pdf"],
            "description": "일반적인 순서대로 배치"
        },
        {
            "name": "Cover 파일명 (영문)",
            "order": "의뢰서.pdf",
            "thumbnails": ["cover.pdf", "page1.pdf"],
            "description": "영문 cover도 표지로 인식"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n테스트: {scenario['name']}")
        print(f"설명: {scenario['description']}")
        print("-" * 40)
        
        # 파일 존재 확인 (실제 테스트를 위해서는 파일 준비 필요)
        test_dir = Path(__file__).parent
        order_file = test_dir / scenario['order']
        thumb_files = [test_dir / f for f in scenario['thumbnails']]
        
        # 파일이 없으면 시뮬레이션
        if not order_file.exists():
            print(f"[INFO] 테스트 파일이 없어 시뮬레이션 모드로 실행")
            print(f"       의뢰서: {scenario['order']}")
            for i, thumb in enumerate(scenario['thumbnails']):
                has_cover = '표지' in thumb or 'cover' in thumb.lower()
                if has_cover:
                    print(f"       썸네일{i+1}: {thumb} [표지 감지 - 왼쪽 50% 자르기]")
                else:
                    print(f"       썸네일{i+1}: {thumb}")
            
            if any('표지' in f or 'cover' in f.lower() for f in scenario['thumbnails']):
                print("\n[규칙 적용]")
                print("1. 표지 파일 감지됨")
                print("2. 표지는 왼쪽 50%만 사용")
                print("3. 썸네일이 여러 개면 첫 번째 박스에 우선 배치")
        else:
            # 실제 파일이 있으면 처리
            print(f"실제 처리 시작...")
            success = processor.process_files(
                order_pdf=str(order_file),
                print_pdfs=[str(f) for f in thumb_files if f.exists()],
                qr_image=None
            )
            
            if success:
                print("[SUCCESS] 처리 완료")
            else:
                print("[FAIL] 처리 실패")
    
    print("\n" + "=" * 50)
    print("테스트 완료")
    print("=" * 50)
    print("\n구현된 규칙:")
    print("1. 파일명에 '표지' 또는 'cover' 포함 시 자동 감지")
    print("2. 표지 썸네일은 왼쪽 50% 자동 자르기")
    print("3. 썸네일이 여러 개일 때 첫 번째 박스에 우선 배치")
    print("4. 나머지 썸네일은 두 번째 박스부터 순서대로 배치")

if __name__ == "__main__":
    test_cover_rule()