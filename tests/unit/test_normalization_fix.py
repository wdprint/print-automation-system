"""정규화 수정 테스트"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.pdf_normalizer import PDFNormalizer
from utils.logger import setup_logger
import fitz
import tempfile

def test_normalization():
    """정규화 테스트"""
    logger = setup_logger("TestNormalization")
    
    # 테스트 파일 (90도 회전된 의뢰서)
    test_file = r"C:/Users/dltjd/OneDrive/바탕 화면/(주)성심건업/이진성-작업의뢰서(25년8월).pdf"
    
    if not os.path.exists(test_file):
        logger.error(f"테스트 파일이 없습니다: {test_file}")
        return False
    
    # 원본 파일 정보
    doc = fitz.open(test_file)
    page = doc[0]
    logger.info(f"원본 파일:")
    logger.info(f"  회전: {page.rotation}도")
    logger.info(f"  Rect: {page.rect} (실제 보이는 크기)")
    logger.info(f"  MediaBox: {page.mediabox} (물리적 크기)")
    doc.close()
    
    # 정규화 실행
    normalizer = PDFNormalizer()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        normalized_path = normalizer.normalize(test_file, temp_dir)
        
        if normalized_path != test_file:
            logger.info(f"\n정규화 완료: {normalized_path}")
            
            # 정규화된 파일 정보
            doc = fitz.open(normalized_path)
            page = doc[0]
            logger.info(f"정규화된 파일:")
            logger.info(f"  회전: {page.rotation}도")
            logger.info(f"  크기: {page.rect}")
            
            # 가로형인지 확인
            width = page.rect.width
            height = page.rect.height
            
            if width > height:
                logger.info(f"  ✅ 가로형 페이지 ({width:.1f} x {height:.1f})")
                result = True
            else:
                logger.error(f"  ❌ 세로형 페이지 ({width:.1f} x {height:.1f})")
                result = False
                
            doc.close()
            return result
        else:
            logger.warning("정규화가 필요하지 않거나 실패")
            return False
    
def test_full_processing():
    """전체 처리 테스트"""
    logger = setup_logger("TestFullProcessing")
    
    from config.settings_manager import SettingsManager
    from core.pdf_processor import PDFProcessor
    from utils.file_classifier import FileClassifier
    
    # 테스트 파일들
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
    
    # PDF 처리
    settings = SettingsManager()
    processor = PDFProcessor(settings)
    
    success = processor.process_files(
        classified.order_pdf,
        classified.print_pdfs,
        classified.qr_image
    )
    
    if success:
        # 결과 파일 확인
        output_path = classified.order_pdf.replace(".pdf", "_완료.pdf")
        if os.path.exists(output_path):
            doc = fitz.open(output_path)
            page = doc[0]
            width = page.rect.width
            height = page.rect.height
            
            logger.info(f"\n✅ 처리 완료:")
            logger.info(f"  출력 파일: {output_path}")
            logger.info(f"  페이지 크기: {width:.1f} x {height:.1f}")
            
            if width > height:
                logger.info(f"  ✅ 가로형 페이지 생성 성공!")
                doc.close()
                return True
            else:
                logger.error(f"  ❌ 세로형 페이지로 생성됨")
                doc.close()
                return False
        else:
            logger.error("출력 파일이 생성되지 않음")
            return False
    else:
        logger.error("처리 실패")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("정규화 수정 테스트")
    print("=" * 50)
    
    print("\n1. 정규화 테스트")
    if test_normalization():
        print("  ✅ 정규화 테스트 성공")
    else:
        print("  ❌ 정규화 테스트 실패")
    
    print("\n2. 전체 처리 테스트")
    if test_full_processing():
        print("  ✅ 전체 처리 테스트 성공")
    else:
        print("  ❌ 전체 처리 테스트 실패")