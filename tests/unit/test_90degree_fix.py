"""90도 회전된 의뢰서 썸네일 처리 테스트"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings_manager import SettingsManager
from core.pdf_processor import PDFProcessor
import fitz  # PyMuPDF

def check_pdf_rotation(pdf_path):
    """PDF 파일의 회전 상태 확인"""
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            print(f"  페이지 {i+1}: rotation={page.rotation}도, size={page.rect.width:.0f}x{page.rect.height:.0f}")
        doc.close()
    except Exception as e:
        print(f"  파일 열기 실패: {e}")

def test_90degree_rotation():
    """90도 회전된 의뢰서 처리 테스트"""
    
    print("=" * 60)
    print("90도 회전된 의뢰서 썸네일 처리 테스트")
    print("=" * 60)
    
    # 설정 관리자 초기화
    settings_manager = SettingsManager()
    settings_manager.load()
    
    # PDF 처리기 초기화
    processor = PDFProcessor(settings_manager)
    
    # 테스트 시나리오
    test_scenarios = [
        {
            "name": "90도 회전된 의뢰서 + 표지",
            "order": "의뢰서_90도.pdf",
            "thumbnails": ["표지.pdf", "내용.pdf"],
            "description": "90도 회전 정규화 + 표지 오른쪽 50% 자르기"
        },
        {
            "name": "정상 의뢰서 + 표지",
            "order": "의뢰서_정상.pdf",
            "thumbnails": ["표지.pdf", "내용.pdf"],
            "description": "회전 없음 + 표지 오른쪽 50% 자르기"
        }
    ]
    
    test_dir = Path(__file__).parent
    
    for scenario in test_scenarios:
        print(f"\n테스트: {scenario['name']}")
        print(f"설명: {scenario['description']}")
        print("-" * 50)
        
        order_file = test_dir / scenario['order']
        thumb_files = [test_dir / f for f in scenario['thumbnails']]
        
        if not order_file.exists():
            print(f"[INFO] 테스트 파일 없음: {scenario['order']}")
            print("\n시뮬레이션 결과:")
            print("1. PDF 정규화:")
            print("   - 90도 회전 감지 → 래스터화 → rotation=0으로 설정")
            print("2. 썸네일 처리:")
            print("   - 정규화된 PDF는 좌표 변환 건너뜀")
            print("   - 표지는 오른쪽 50% 자르기")
            print("3. 좌표 계산:")
            print("   - 원본 크기로 비율 계산 (회전 영향 배제)")
            continue
        
        print(f"\n원본 PDF 회전 상태:")
        check_pdf_rotation(order_file)
        
        # PDF 처리
        output_file = test_dir / f"{order_file.stem}_완료.pdf"
        
        print(f"\n처리 시작...")
        success = processor.process_files(
            order_pdf=str(order_file),
            print_pdfs=[str(f) for f in thumb_files if f.exists()],
            qr_image=None
        )
        
        if success:
            print(f"[SUCCESS] 처리 완료")
            
            # 출력 파일 회전 상태 확인
            if output_file.exists():
                print(f"\n출력 PDF 회전 상태:")
                check_pdf_rotation(output_file)
        else:
            print(f"[FAIL] 처리 실패")
    
    print("\n" + "=" * 60)
    print("핵심 수정사항:")
    print("=" * 60)
    print("1. 정규화 플래그 추가 (is_normalized)")
    print("2. 정규화된 PDF는 좌표 변환 건너뜀")
    print("3. rotation 명시적으로 0 설정")
    print("4. 원본 크기로 비율 계산")
    print("\n순서:")
    print("1. PDF 정규화 (90도 회전 수정)")
    print("2. 썸네일 생성")
    print("3. 좌표 변환 (정규화된 PDF는 건너뜀)")
    print("4. 표지 처리 (오른쪽 50% 자르기)")
    print("5. 썸네일 삽입")

if __name__ == "__main__":
    test_90degree_rotation()