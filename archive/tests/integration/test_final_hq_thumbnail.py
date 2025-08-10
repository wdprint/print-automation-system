"""최종 고품질 썸네일 테스트"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings_manager import SettingsManager
from core.pdf_processor import PDFProcessor

def test_final_quality():
    """최종 고품질 썸네일 테스트"""
    
    # 테스트 파일 경로
    order_pdf = r"c:\Users\dltjd\OneDrive\바탕 화면\(주)성심건업\(주)성심건업_의뢰서_2025-08-08_090845 - 복사본.pdf"
    print_pdf = r"c:\Users\dltjd\OneDrive\바탕 화면\(주)성심건업\1_국제무역관리자과정_표지_10.6mm.pdf"
    
    # 파일 존재 확인
    if not os.path.exists(order_pdf):
        print(f"의뢰서 파일을 찾을 수 없습니다: {order_pdf}")
        return False
    
    if not os.path.exists(print_pdf):
        print(f"인쇄 파일을 찾을 수 없습니다: {print_pdf}")
        return False
    
    print("고품질 썸네일 최종 테스트")
    print("=" * 70)
    print(f"의뢰서: {order_pdf}")
    print(f"인쇄 파일: {print_pdf}")
    
    # 설정 관리자 초기화
    settings_manager = SettingsManager()
    
    # 현재 설정 확인
    print("\n적용된 개선 사항:")
    print(f"  - 렌더링 DPI: {settings_manager.get('thumbnail.render_dpi', 900)} (900 DPI)")
    print(f"  - 대비: {settings_manager.get('thumbnail.contrast', 1.3)} (강화됨)")
    print(f"  - 샤프니스: {settings_manager.get('thumbnail.sharpness', 1.5)} (강화됨)")
    print(f"  - 내부 처리: 2배 크기로 처리 후 축소")
    print(f"  - 리사이징: resize() 메서드 사용 (고품질)")
    print(f"  - 엣지 강화: EDGE_ENHANCE_MORE 필터")
    print(f"  - 언샵 마스크: radius=1.5, percent=200")
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
        
        # 가능한 출력 파일명들
        possible_outputs = [
            output_base / f"{output_stem}_완료.pdf",
            output_base / f"{output_stem}_완료_1.pdf",
            output_base / f"{output_stem}_완료_2.pdf",
            output_base / f"{output_stem}_완료_3.pdf",
            output_base / f"{output_stem}_완료_4.pdf",
            output_base / f"{output_stem}_완료_5.pdf",
        ]
        
        for output_path in possible_outputs:
            if output_path.exists():
                print(f"출력 파일: {output_path}")
                print(f"파일 크기: {output_path.stat().st_size:,} bytes")
                break
        
        print("\n이제 생성된 PDF를 열어서 썸네일 품질을 확인하세요.")
        print("이전보다 훨씬 선명하고 깨끗한 썸네일을 볼 수 있을 것입니다!")
    else:
        print("\n처리 실패")
        return False
    
    return True

if __name__ == "__main__":
    success = test_final_quality()
    
    if not success:
        print("\n오류가 발생했습니다. 로그를 확인하세요.")