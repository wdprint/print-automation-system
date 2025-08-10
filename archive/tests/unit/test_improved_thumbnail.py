"""개선된 썸네일 품질 최종 테스트"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings_manager import SettingsManager
from core.pdf_processor import PDFProcessor

def test_improved_thumbnail():
    """개선된 썸네일 품질 테스트"""
    
    # 테스트 파일 경로
    order_pdf = r"c:\Users\dltjd\OneDrive\바탕 화면\(주)성심건업\이진성-작업의뢰서(25년8월) - 복사본 (2).pdf"
    print_pdf = r"c:\Users\dltjd\OneDrive\바탕 화면\(주)성심건업\1_국제무역관리자과정_표지_10.6mm.pdf"
    
    # 파일 존재 확인
    if not os.path.exists(order_pdf):
        print(f"의뢰서 파일을 찾을 수 없습니다: {order_pdf}")
        return False
    
    if not os.path.exists(print_pdf):
        print(f"표지 파일을 찾을 수 없습니다: {print_pdf}")
        return False
    
    print("개선된 썸네일 품질 테스트")
    print("=" * 70)
    print(f"의뢰서: {Path(order_pdf).name}")
    print(f"표지: {Path(print_pdf).name}")
    
    # 설정 관리자 초기화
    settings_manager = SettingsManager()
    
    # 현재 설정 확인
    print("\n적용된 개선 사항:")
    print("  [의뢰서 처리]")
    print("  - 변경 없음 (용량 낭비 방지)")
    print()
    print("  [썸네일 생성]")
    print(f"  - 렌더링 DPI: {settings_manager.get('thumbnail.render_dpi', 1200)} (표지용 초고해상도)")
    print(f"  - 대비: {settings_manager.get('thumbnail.contrast', 1.3)}")
    print(f"  - 샤프니스: {settings_manager.get('thumbnail.sharpness', 1.5)}")
    print(f"  - 리사이징: resize() 메서드 사용")
    print(f"  - 필터: EDGE_ENHANCE_MORE + UnsharpMask")
    print("=" * 70)
    
    # PDF 처리기 초기화
    processor = PDFProcessor(settings_manager)
    
    # 처리 실행
    print("\n처리 시작...")
    success = processor.process_files(
        order_pdf=order_pdf,
        print_pdfs=[print_pdf],
        qr_image=None
    )
    
    if success:
        print("\n처리 완료!")
        
        # 출력 파일 찾기
        output_base = Path(order_pdf).parent
        output_stem = Path(order_pdf).stem
        
        # 생성된 파일 찾기
        for i in range(10):
            if i == 0:
                output_path = output_base / f"{output_stem}_완료.pdf"
            else:
                output_path = output_base / f"{output_stem}_완료_{i}.pdf"
            
            if output_path.exists():
                print(f"\n생성된 파일: {output_path.name}")
                print(f"파일 크기: {output_path.stat().st_size:,} bytes")
                print(f"전체 경로: {output_path}")
                break
        
        print("\n" + "=" * 70)
        print("결과:")
        print("- 의뢰서 페이지: 원본 유지 (용량 절약)")
        print("- 썸네일: 1200 DPI 고품질 렌더링")
        print("\n생성된 PDF를 열어서 썸네일 품질을 확인하세요!")
    else:
        print("\n처리 실패")
        return False
    
    return True

if __name__ == "__main__":
    success = test_improved_thumbnail()
    
    if not success:
        print("\n오류가 발생했습니다. 로그를 확인하세요.")