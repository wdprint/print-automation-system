#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PDF 정규화 도구
세로형이지만 가로로 보이는 PDF를 실제 가로형으로 변환
"""

import fitz
import sys
from pathlib import Path

def normalize_pdf(input_path, output_path=None):
    """PDF를 정규화하여 실제 가로형으로 변환"""
    
    if output_path is None:
        p = Path(input_path)
        output_path = p.parent / f"{p.stem}_normalized{p.suffix}"
    
    print(f"입력 파일: {input_path}")
    print(f"출력 파일: {output_path}")
    
    # PDF 열기
    doc = fitz.open(input_path)
    new_doc = fitz.open()  # 새 문서
    
    for page_num, page in enumerate(doc):
        # 페이지 정보
        rect = page.rect
        rotation = page.rotation
        mediabox = page.mediabox
        
        print(f"\n페이지 {page_num + 1}:")
        print(f"  크기: {rect.width}x{rect.height}")
        print(f"  회전: {rotation}")
        print(f"  MediaBox: {mediabox}")
        
        # 페이지가 가로로 표시되어야 하는지 확인
        should_be_landscape = (rect.width > rect.height) or (rotation in [90, 270])
        
        if should_be_landscape:
            # 가로형 페이지 생성
            if rotation in [90, 270]:
                # 회전된 세로형을 가로형으로
                new_page = new_doc.new_page(width=rect.height, height=rect.width)
                
                # 페이지 내용을 PDF로 변환
                pix = page.get_pixmap(dpi=150)
                img_data = pix.pil_tobytes(format="PDF")
                
                # 새 페이지에 삽입
                img_rect = new_page.rect
                new_page.insert_image(img_rect, stream=img_data)
                
            else:
                # 이미 가로형인 경우
                new_page = new_doc.new_page(width=rect.width, height=rect.height)
                new_page.show_pdf_page(new_page.rect, doc, page_num)
        else:
            # 세로형 유지
            new_page = new_doc.new_page(width=rect.width, height=rect.height)
            new_page.show_pdf_page(new_page.rect, doc, page_num)
            
        print(f"  변환 후: {new_page.rect.width}x{new_page.rect.height}")
    
    # 저장
    new_doc.save(output_path)
    new_doc.close()
    doc.close()
    
    print(f"\n정규화 완료!")
    return output_path

def main():
    if len(sys.argv) < 2:
        print("사용법: python normalize_pdf.py [PDF파일경로]")
        input("파일을 드래그 앤 드롭하거나 경로를 입력하세요: ")
        return
    
    input_path = sys.argv[1]
    normalize_pdf(input_path)

if __name__ == "__main__":
    main()