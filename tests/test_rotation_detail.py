# -*- coding: utf-8 -*-
"""
PDF 회전 문제 상세 분석 스크립트
"""

import os
import sys
import fitz  # PyMuPDF

def analyze_pdf_rotation(pdf_path):
    """PDF 회전 상태 상세 분석"""
    
    print(f"\n{'='*60}")
    print(f"Analyzing: {os.path.basename(pdf_path)}")
    print(f"{'='*60}")
    
    doc = fitz.open(pdf_path)
    
    for page_num, page in enumerate(doc):
        print(f"\n[Page {page_num + 1}]")
        
        # 기본 정보
        rotation = page.rotation
        rect = page.rect
        mediabox = page.mediabox
        cropbox = page.cropbox
        
        print(f"  Rotation: {rotation}°")
        print(f"  Page.rect: {rect.width:.0f} x {rect.height:.0f}")
        print(f"  MediaBox: {mediabox.width:.0f} x {mediabox.height:.0f}")
        print(f"  CropBox: {cropbox.width:.0f} x {cropbox.height:.0f}")
        
        # 변환 매트릭스
        mat = page.transformation_matrix
        print(f"  Transform Matrix: {mat}")
        
        # 실제 렌더링 크기
        pix = page.get_pixmap(dpi=72)  # 72 DPI = 1:1 scale
        print(f"  Rendered size: {pix.width} x {pix.height}")
        
        # 콘텐츠 방향 판단
        if rotation in [90, 270]:
            actual_width = rect.height
            actual_height = rect.width
        else:
            actual_width = rect.width
            actual_height = rect.height
            
        if actual_width > actual_height:
            orientation = "Landscape"
        else:
            orientation = "Portrait"
            
        print(f"  Actual orientation: {orientation}")
        
        # 텍스트 방향 테스트 (텍스트가 있는 경우)
        text_blocks = page.get_text("blocks")
        if text_blocks:
            print(f"  Text blocks found: {len(text_blocks)}")
            # 첫 번째 텍스트 블록의 위치로 방향 추정
            first_block = text_blocks[0]
            print(f"  First text block position: x={first_block[0]:.0f}, y={first_block[1]:.0f}")
    
    doc.close()
    return True

def test_rotation_fix():
    """회전 수정 방법 테스트"""
    
    test_pdf = r'C:\Users\wp\Desktop\(주)성심건업\이진성-작업의뢰서(25년8월) - 복사본 (3).pdf'
    
    if not os.path.exists(test_pdf):
        print(f"Test file not found: {test_pdf}")
        return
    
    print("\n" + "="*60)
    print("Testing rotation fix methods")
    print("="*60)
    
    doc = fitz.open(test_pdf)
    page = doc[0]  # 첫 페이지만 테스트
    
    # 방법 1: set_rotation 사용
    print("\n[Method 1] Using set_rotation(0)")
    original_rotation = page.rotation
    print(f"  Original rotation: {original_rotation}°")
    
    page.set_rotation(0)
    print(f"  After set_rotation(0): {page.rotation}°")
    print(f"  Rect after: {page.rect.width:.0f} x {page.rect.height:.0f}")
    
    # 방법 2: 새 페이지에 변환 매트릭스 적용
    print("\n[Method 2] Using transformation matrix")
    new_doc = fitz.open()
    
    # 원본 페이지의 실제 크기 계산
    if original_rotation in [90, 270]:
        target_width = page.rect.height
        target_height = page.rect.width
    else:
        target_width = page.rect.width
        target_height = page.rect.height
    
    # A4 가로 표준 크기
    if target_width < target_height:  # 세로인 경우
        target_width, target_height = 842, 595
    else:
        target_width, target_height = 842, 595
    
    new_page = new_doc.new_page(width=target_width, height=target_height)
    
    # 회전을 보정하는 변환 매트릭스 생성
    if original_rotation == 90:
        # 90도 시계반대방향 회전 = 270도 시계방향 회전으로 보정
        rotate_matrix = fitz.Matrix(0, 1, -1, 0, target_width, 0)
    elif original_rotation == 180:
        rotate_matrix = fitz.Matrix(-1, 0, 0, -1, target_width, target_height)
    elif original_rotation == 270:
        # 270도 시계반대방향 회전 = 90도 시계방향 회전으로 보정
        rotate_matrix = fitz.Matrix(0, -1, 1, 0, 0, target_height)
    else:
        rotate_matrix = fitz.Matrix(1, 0, 0, 1, 0, 0)  # 단위 행렬
    
    # 페이지 내용 복사 with 변환
    new_page.show_pdf_page(new_page.rect, doc, 0, rotate=original_rotation)
    
    print(f"  New page size: {new_page.rect.width:.0f} x {new_page.rect.height:.0f}")
    print(f"  New page rotation: {new_page.rotation}°")
    
    # 테스트 파일 저장
    test_output = "test_rotation_fixed.pdf"
    new_doc.save(test_output)
    print(f"  Saved test file: {test_output}")
    
    new_doc.close()
    doc.close()
    
    # 결과 파일 분석
    print("\n[Verifying fixed PDF]")
    analyze_pdf_rotation(test_output)

if __name__ == "__main__":
    # 원본 파일들 분석
    files = [
        r'C:\Users\wp\Desktop\(주)성심건업\(주)성심건업_의뢰서_2025-08-08_090845 - 복사본 (8).pdf',
        r'C:\Users\wp\Desktop\(주)성심건업\이진성-작업의뢰서(25년8월) - 복사본 (3).pdf'
    ]
    
    for pdf_file in files:
        if os.path.exists(pdf_file):
            analyze_pdf_rotation(pdf_file)
    
    # 회전 수정 테스트
    test_rotation_fix()