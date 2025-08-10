"""썸네일 품질 개선 테스트 스크립트"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings_manager import SettingsManager
from core.pdf_processor import PDFProcessor

def test_thumbnail_quality():
    """썸네일 품질 테스트"""
    
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
    
    print("파일 확인 완료")
    print(f"의뢰서: {order_pdf}")
    print(f"인쇄 파일: {print_pdf}")
    
    # 설정 관리자 초기화
    settings_manager = SettingsManager()
    
    # 썸네일 품질 설정 확인 및 조정
    print("\n현재 썸네일 설정:")
    print(f"  - 렌더링 DPI: {settings_manager.get('thumbnail.render_dpi', 600)}")
    print(f"  - 대비: {settings_manager.get('thumbnail.contrast', 1.2)}")
    print(f"  - 크기: {settings_manager.get('thumbnail.max_width', 160)}x{settings_manager.get('thumbnail.max_height', 250)}")
    
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
        print("처리 완료!")
        print("생성된 파일을 확인해주세요.")
        
        # 출력 파일 경로
        output_path = Path(order_pdf).parent / f"{Path(order_pdf).stem}_완료.pdf"
        if output_path.exists():
            print(f"출력 파일: {output_path}")
        else:
            # 번호가 붙은 파일 찾기
            for i in range(1, 10):
                output_path = Path(order_pdf).parent / f"{Path(order_pdf).stem}_완료_{i}.pdf"
                if output_path.exists():
                    print(f"출력 파일: {output_path}")
                    break
    else:
        print("❌ 처리 실패")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("썸네일 품질 개선 테스트")
    print("=" * 50)
    
    # 개선 사항 설명
    print("\n적용된 개선 사항:")
    print("1. thumbnail() → resize() 메서드 변경")
    print("2. DPI 432 → 600으로 증가")
    print("3. 이중 리사이징 제거")
    print("4. 리사이징 후 샤프닝 적용")
    print("5. EDGE_ENHANCE_MORE 필터 추가")
    print("6. 대비 1.0 → 1.2로 기본값 증가")
    print("7. PNG 압축 최소화 (compress_level=1)")
    print("=" * 50)
    
    success = test_thumbnail_quality()
    
    if success:
        print("\n테스트 성공!")
        print("개선된 썸네일 품질을 확인해주세요.")
    else:
        print("\n테스트 실패. 오류를 확인해주세요.")