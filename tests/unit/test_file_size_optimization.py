"""파일 크기 최적화 테스트"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings_manager import SettingsManager
from core.pdf_processor import PDFProcessor
from utils.file_classifier import FileClassifier
from utils.logger import setup_logger
import fitz

def test_file_size():
    """파일 크기 최적화 테스트"""
    logger = setup_logger("TestFileSize")
    
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
    
    logger.info("파일 분류 완료:")
    logger.info(f"  의뢰서: {os.path.basename(classified.order_pdf)}")
    for pdf in classified.print_pdfs:
        logger.info(f"  인쇄 PDF: {os.path.basename(pdf)}")
    
    # PDF 처리
    settings = SettingsManager()
    processor = PDFProcessor(settings)
    
    # 처리 실행
    success = processor.process_files(
        classified.order_pdf,
        classified.print_pdfs,
        classified.qr_image
    )
    
    if success:
        # 결과 파일 확인
        output_path = classified.order_pdf.replace(".pdf", "_완료.pdf")
        
        # 여러 버전이 있을 수 있으므로 가장 최신 파일 찾기
        base_name = classified.order_pdf.replace(".pdf", "_완료")
        parent_dir = os.path.dirname(classified.order_pdf)
        
        # 가능한 파일들 찾기
        possible_files = []
        for i in range(10):
            if i == 0:
                path = f"{base_name}.pdf"
            else:
                path = f"{base_name}_{i}.pdf"
            if os.path.exists(path):
                possible_files.append(path)
        
        if possible_files:
            # 가장 최신 파일 선택
            output_path = max(possible_files, key=os.path.getmtime)
            
            # 파일 정보
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            
            doc = fitz.open(output_path)
            page_count = len(doc)
            
            # 이미지 수 계산
            total_images = 0
            for page in doc:
                total_images += len(page.get_images())
            
            logger.info(f"\n✅ 처리 완료:")
            logger.info(f"  출력 파일: {os.path.basename(output_path)}")
            logger.info(f"  파일 크기: {file_size:.2f} MB")
            logger.info(f"  페이지 수: {page_count}")
            logger.info(f"  총 이미지 수: {total_images}")
            
            # 크기 최적화 성공 판단
            if file_size < 8:  # 8MB 이하면 성공
                logger.info(f"  ✅ 파일 크기 최적화 성공! ({file_size:.2f} MB < 8 MB)")
                doc.close()
                return True
            else:
                logger.warning(f"  ⚠️ 파일 크기가 여전히 큽니다 ({file_size:.2f} MB)")
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
    print("파일 크기 최적화 테스트")
    print("=" * 50)
    
    if test_file_size():
        print("\n✅ 테스트 성공! 파일 크기가 최적화되었습니다.")
    else:
        print("\n❌ 테스트 실패")