"""표지 처리 및 회전 수정 테스트"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings_manager import SettingsManager
from core.pdf_processor import PDFProcessor
from utils.file_classifier import FileClassifier
from utils.logger import setup_logger

def test_cover_processing():
    """표지 처리 테스트"""
    logger = setup_logger("TestCoverFix")
    
    # 테스트 파일 경로 (실제 파일 경로로 변경 필요)
    test_files = [
        r"C:/Users/dltjd/OneDrive/바탕 화면/(주)성심건업/이진성-작업의뢰서(25년8월).pdf",
        r"C:/Users/dltjd/OneDrive/바탕 화면/(주)성심건업/1_국제무역관리자과정_내지_200p.pdf",
        r"C:/Users/dltjd/OneDrive/바탕 화면/(주)성심건업/1_국제무역관리자과정_표지_10.6mm.pdf"
    ]
    
    # 파일 존재 확인
    for file in test_files:
        if not os.path.exists(file):
            logger.error(f"테스트 파일이 없습니다: {file}")
            return False
    
    # 파일 분류
    classifier = FileClassifier()
    classified = classifier.classify(test_files)
    
    logger.info(f"분류 결과:")
    logger.info(f"  의뢰서: {classified.order_pdf}")
    logger.info(f"  인쇄 PDF: {classified.print_pdfs}")
    logger.info(f"  QR: {classified.qr_image}")
    
    # 설정 관리자
    settings = SettingsManager()
    
    # PDF 처리
    processor = PDFProcessor(settings)
    
    # 처리 실행
    success = processor.process_files(
        classified.order_pdf,
        classified.print_pdfs,
        classified.qr_image
    )
    
    if success:
        logger.info("✅ 처리 성공!")
        
        # 결과 확인
        output_path = classified.order_pdf.replace(".pdf", "_완료.pdf")
        if os.path.exists(output_path):
            logger.info(f"✅ 출력 파일 생성됨: {output_path}")
            
            # 파일 크기 확인
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"  파일 크기: {size_mb:.2f} MB")
        else:
            logger.error("❌ 출력 파일이 생성되지 않음")
            return False
    else:
        logger.error("❌ 처리 실패")
        return False
    
    return True

def test_cover_detection():
    """표지 감지 테스트"""
    logger = setup_logger("TestCoverDetection")
    
    test_filenames = [
        "1_국제무역관리자과정_표지_10.6mm.pdf",
        "표지.pdf",
        "cover.pdf",
        "COVER_PAGE.pdf",
        "내지.pdf",
        "content.pdf"
    ]
    
    import re
    for filename in test_filenames:
        is_cover = bool(re.search(r'표지|cover', filename, re.IGNORECASE))
        logger.info(f"{filename}: {'표지' if is_cover else '내지'}")
    
    return True

def test_rotation_normalization():
    """회전 정규화 테스트"""
    logger = setup_logger("TestRotation")
    
    from core.pdf_normalizer import PDFNormalizer
    
    normalizer = PDFNormalizer()
    
    # 테스트 파일 (90도 회전된 의뢰서)
    test_file = r"C:/Users/dltjd/OneDrive/바탕 화면/(주)성심건업/이진성-작업의뢰서(25년8월).pdf"
    
    if os.path.exists(test_file):
        # 회전 감지
        rotations = normalizer.detect_rotation(test_file)
        logger.info(f"회전 감지 결과: {rotations}")
        
        # 정규화 시도
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            normalized = normalizer.normalize(test_file, temp_dir)
            if normalized != test_file:
                logger.info(f"✅ 정규화 성공: {normalized}")
            else:
                logger.warning("⚠️ 정규화 불필요 또는 실패")
    else:
        logger.warning(f"테스트 파일 없음: {test_file}")
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("표지 처리 및 회전 수정 테스트")
    print("=" * 50)
    
    # 1. 표지 감지 테스트
    print("\n1. 표지 감지 테스트")
    test_cover_detection()
    
    # 2. 회전 정규화 테스트
    print("\n2. 회전 정규화 테스트")
    test_rotation_normalization()
    
    # 3. 전체 처리 테스트
    print("\n3. 전체 처리 테스트")
    if test_cover_processing():
        print("\n✅ 모든 테스트 성공!")
    else:
        print("\n❌ 테스트 실패")