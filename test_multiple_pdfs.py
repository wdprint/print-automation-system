#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""여러 PDF 파일 처리 테스트 스크립트"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent))

from config.settings_manager import SettingsManager
from core.pdf_processor import PDFProcessor
from utils.file_classifier import FileClassifier
from utils.logger import setup_logger

def test_multiple_pdfs():
    """여러 PDF 파일 처리 테스트"""
    logger = setup_logger('test')
    
    print("=" * 50)
    print("여러 PDF 파일 처리 테스트")
    print("=" * 50)
    
    # 1. 설정 확인
    print("\n1. 설정 확인...")
    settings = SettingsManager()
    
    # 썸네일 박스 확인
    thumbnail_boxes = settings.get('coordinates.thumbnail_boxes', [])
    print(f"   - 썸네일 박스 수: {len(thumbnail_boxes)}")
    for idx, box in enumerate(thumbnail_boxes):
        print(f"     [{idx+1}] {box.get('name')} - 위치: ({box.get('x')}, {box.get('y')})")
    
    # 2. 파일 분류 테스트
    print("\n2. 파일 분류 테스트...")
    classifier = FileClassifier()
    
    # 테스트 파일 목록 (실제 파일 경로로 변경 필요)
    test_files = [
        "의뢰서.pdf",        # 의뢰서 PDF
        "인쇄데이터1.pdf",   # 첫 번째 인쇄 PDF
        "인쇄데이터2.pdf",   # 두 번째 인쇄 PDF
        "QR코드.png"         # QR 이미지
    ]
    
    # 테스트용 더미 파일 생성 (실제 테스트 시 제거)
    print("\n   테스트용 더미 파일 생성 중...")
    from PIL import Image
    import fitz
    
    # 의뢰서 PDF 생성
    if not os.path.exists("의뢰서.pdf"):
        doc = fitz.open()
        page = doc.new_page(width=842, height=595)  # A4 가로
        page.insert_text((100, 100), "테스트 의뢰서 PDF", fontsize=20)
        doc.save("의뢰서.pdf")
        doc.close()
        print("   - 의뢰서.pdf 생성 완료")
    
    # 인쇄 PDF 생성
    for i in [1, 2]:
        filename = f"인쇄데이터{i}.pdf"
        if not os.path.exists(filename):
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((100, 100), f"테스트 인쇄 데이터 {i}", fontsize=20)
            doc.save(filename)
            doc.close()
            print(f"   - {filename} 생성 완료")
    
    # QR 이미지 생성
    if not os.path.exists("QR코드.png"):
        img = Image.new('RGB', (100, 100), color='white')
        img.save("QR코드.png")
        print("   - QR코드.png 생성 완료")
    
    # 파일 분류
    classified = classifier.classify(test_files)
    print(f"\n   분류 결과:")
    print(f"   - 의뢰서 PDF: {classified.order_pdf}")
    print(f"   - 인쇄 PDF 수: {len(classified.print_pdfs)}")
    for idx, pdf in enumerate(classified.print_pdfs):
        print(f"     [{idx+1}] {pdf}")
    print(f"   - QR 이미지: {classified.qr_image}")
    
    # 3. PDF 처리 테스트
    print("\n3. PDF 처리 테스트...")
    
    if classified.is_valid():
        processor = PDFProcessor(settings)
        
        # 처리 실행
        result = processor.process_files(
            classified.order_pdf,
            classified.print_pdfs,
            classified.qr_image
        )
        
        if result:
            print("   ✅ PDF 처리 성공!")
            print("   - 출력 파일: 의뢰서_완료.pdf")
        else:
            print("   ❌ PDF 처리 실패")
    else:
        print(f"   ❌ 파일 검증 실패: {classified.get_error()}")
    
    # 4. 썸네일 박스 추가/삭제 테스트
    print("\n4. 썸네일 박스 관리 테스트...")
    
    # 새 박스 추가
    thumbnail_boxes = settings.get('coordinates.thumbnail_boxes', [])
    new_box = {
        "id": f"thumb_{len(thumbnail_boxes) + 1}",
        "name": f"테스트 썸네일 {len(thumbnail_boxes) + 1}",
        "x": 430,
        "y": 234,
        "width": 160,
        "height": 250,
        "rotation": 0,
        "opacity": 1.0
    }
    thumbnail_boxes.append(new_box)
    settings.set('coordinates.thumbnail_boxes', thumbnail_boxes)
    print(f"   - 새 썸네일 박스 추가: {new_box['name']}")
    
    # 설정 저장
    if settings.save():
        print("   - 설정 저장 완료")
    else:
        print("   - 설정 저장 실패")
    
    # 최종 상태 확인
    print("\n5. 최종 상태:")
    thumbnail_boxes = settings.get('coordinates.thumbnail_boxes', [])
    print(f"   - 총 썸네일 박스 수: {len(thumbnail_boxes)}")
    
    print("\n" + "=" * 50)
    print("테스트 완료!")
    print("=" * 50)

if __name__ == "__main__":
    test_multiple_pdfs()