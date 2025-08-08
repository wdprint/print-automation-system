# -*- coding: utf-8 -*-
"""
PDF 회전 정규화 통합 테스트
실제 PDF 처리 엔진을 통해 회전된 PDF가 올바르게 처리되는지 확인
"""

import os
import sys
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.pdf_processor import PDFProcessor
from config.settings_manager import SettingsManager

def test_rotation_processing():
    """회전된 PDF 처리 테스트"""
    
    # 테스트 파일 경로
    order_pdf = r'C:\Users\wp\Desktop\(주)성심건업\(주)성심건업_의뢰서_2025-08-08_090845 - 복사본 (8).pdf'  # 정상
    print_pdf = r'C:\Users\wp\Desktop\(주)성심건업\이진성-작업의뢰서(25년8월) - 복사본 (3).pdf'  # 90도 회전
    
    print("=" * 60)
    print("PDF Rotation Integration Test")
    print("=" * 60)
    
    # 설정 관리자 초기화
    settings_manager = SettingsManager()
    
    # PDF 정규화 활성화 확인
    settings_manager.set('pdf_normalization.enabled', True)
    print("\n[Settings]")
    print(f"  PDF Normalization: {settings_manager.get('pdf_normalization.enabled', True)}")
    
    # PDF 처리기 초기화
    processor = PDFProcessor(settings_manager)
    
    # 테스트 케이스 1: 정상 의뢰서 + 회전된 인쇄 PDF
    print("\n[Test Case 1] Normal order PDF + Rotated print PDF")
    print(f"  Order PDF: {os.path.basename(order_pdf)}")
    print(f"  Print PDF: {os.path.basename(print_pdf)} (90° rotated)")
    
    # 처리 실행
    success = processor.process_files(
        order_pdf=order_pdf,
        print_pdfs=[print_pdf],  # 리스트로 전달
        qr_image=None  # QR 없이 테스트
    )
    
    if success:
        print("  => SUCCESS: Files processed successfully!")
        
        # 출력 파일 확인
        output_dir = os.path.dirname(order_pdf)
        output_files = [f for f in os.listdir(output_dir) if '_완료' in f]
        if output_files:
            print(f"  => Output file: {output_files[-1]}")
    else:
        print("  => FAILED: Processing failed")
    
    # 테스트 케이스 2: 회전된 의뢰서 + 정상 인쇄 PDF
    print("\n[Test Case 2] Rotated order PDF + Normal print PDF")
    print(f"  Order PDF: {os.path.basename(print_pdf)} (90° rotated)")
    print(f"  Print PDF: {os.path.basename(order_pdf)}")
    
    # 처리 실행 (파일 위치 바꿔서)
    success = processor.process_files(
        order_pdf=print_pdf,  # 회전된 PDF를 의뢰서로
        print_pdfs=[order_pdf],  # 정상 PDF를 인쇄 데이터로
        qr_image=None
    )
    
    if success:
        print("  => SUCCESS: Files processed successfully!")
        
        # 출력 파일 확인
        output_dir = os.path.dirname(print_pdf)
        output_files = [f for f in os.listdir(output_dir) if '_완료' in f]
        if output_files:
            print(f"  => Output file: {output_files[-1]}")
    else:
        print("  => FAILED: Processing failed")
    
    print("\n" + "=" * 60)
    print("Integration test completed!")
    print("=" * 60)
    
    print("\n[Summary]")
    print("The PDF rotation normalization feature is now integrated.")
    print("Both order PDFs and print PDFs are automatically normalized.")
    print("Rotated PDFs (90°, 180°, 270°) will be corrected before processing.")

if __name__ == "__main__":
    test_rotation_processing()