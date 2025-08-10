"""90도 회전 문제 수정 테스트"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings_manager import SettingsManager
from core.pdf_processor import PDFProcessor

def test_rotation_fix():
    """회전 수정 테스트"""
    
    print("=" * 50)
    print("90도 회전 PDF 처리 테스트")
    print("=" * 50)
    
    # 설정 관리자 초기화
    settings_manager = SettingsManager()
    settings_manager.load()
    
    # PDF 처리기 초기화
    processor = PDFProcessor(settings_manager)
    
    # 테스트 파일 경로 (사용자가 제공한 파일 사용)
    test_dir = Path(__file__).parent
    
    # 테스트할 PDF 파일들
    test_files = [
        ("의뢰서_90도회전.pdf", "회전된 의뢰서"),
        ("의뢰서_정상.pdf", "정상 의뢰서"),
    ]
    
    for filename, description in test_files:
        test_file = test_dir / filename
        if test_file.exists():
            print(f"\n테스트: {description}")
            print(f"파일: {test_file}")
            
            # PDF 처리
            output_file = test_dir / f"{filename.replace('.pdf', '_테스트완료.pdf')}"
            
            # 간단한 처리 (의뢰서만)
            success = processor.process_files(
                order_pdf=str(test_file),
                print_pdfs=[],
                qr_image=None
            )
            
            if success:
                print(f"[SUCCESS] 처리 성공!")
                print(f"   출력 파일을 확인하세요")
            else:
                print(f"[FAIL] 처리 실패")
        else:
            print(f"\n[WARNING] 테스트 파일 없음: {filename}")
            print(f"   테스트하려면 해당 이름의 PDF 파일을 준비하세요")
    
    print("\n" + "=" * 50)
    print("테스트 완료")
    print("=" * 50)
    print("\n주요 변경사항:")
    print("1. 회전 상태에 따라 좌표 변환 적용")
    print("2. 정규화된 PDF를 올바르게 사용")
    print("3. 디버깅 로그 추가로 회전 상태 추적")
    
if __name__ == "__main__":
    test_rotation_fix()