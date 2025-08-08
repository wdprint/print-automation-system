# -*- coding: utf-8 -*-
"""
PDF 정규화 테스트 스크립트
회전된 PDF 파일을 정규화하고 결과를 확인
"""

import os
import sys
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.pdf_normalizer import PDFNormalizer

def test_normalization():
    """PDF 정규화 테스트"""
    
    # 테스트할 PDF 파일들
    test_files = [
        r'C:\Users\wp\Desktop\(주)성심건업\(주)성심건업_의뢰서_2025-08-08_090845 - 복사본 (8).pdf',
        r'C:\Users\wp\Desktop\(주)성심건업\이진성-작업의뢰서(25년8월) - 복사본 (3).pdf'
    ]
    
    normalizer = PDFNormalizer()
    
    print("=" * 50)
    print("PDF Normalization Test")
    print("=" * 50)
    
    for pdf_path in test_files:
        if not os.path.exists(pdf_path):
            print(f"\nFile not found: {pdf_path}")
            continue
            
        filename = os.path.basename(pdf_path)
        print(f"\n[Testing] {filename}")
        
        # 회전 감지
        rotation_info = normalizer.detect_rotation(pdf_path)
        print(f"  Rotation detected: {rotation_info}")
        
        # 정규화 필요 여부 확인
        needs_normalization = any(
            page_info.get('needs_correction', False) 
            for page_info in rotation_info.values()
        )
        
        if needs_normalization:
            print("  => Normalization needed!")
            
            # 출력 디렉토리 설정
            output_dir = os.path.dirname(pdf_path)
            
            # 정규화 실행
            normalized_path = normalizer.normalize(pdf_path, output_dir)
            
            if normalized_path != pdf_path:
                print(f"  => Normalized file: {normalized_path}")
                
                # 정규화 후 다시 확인
                new_rotation_info = normalizer.detect_rotation(normalized_path)
                print(f"  => After normalization: {new_rotation_info}")
            else:
                print("  => No changes made")
        else:
            print("  => No normalization needed")
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_normalization()