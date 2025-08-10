# -*- coding: utf-8 -*-
"""
최종 통합 테스트 - 회전 보정 후 좌표 시스템 검증
"""

import os
import sys
import fitz  # PyMuPDF
from PIL import Image, ImageDraw

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_thumbnail():
    """테스트용 썸네일 이미지 생성"""
    img = Image.new('RGB', (160, 250), color='lightblue')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 159, 249], outline='red', width=3)
    draw.text((50, 120), "THUMBNAIL", fill='black')
    img.save('test_thumbnail.png')
    return 'test_thumbnail.png'

def create_test_qr():
    """테스트용 QR 코드 이미지 생성"""
    img = Image.new('RGB', (70, 70), color='white')
    draw = ImageDraw.Draw(img)
    # QR 코드 패턴 시뮬레이션
    for i in range(0, 70, 10):
        for j in range(0, 70, 10):
            if (i + j) // 10 % 2 == 0:
                draw.rectangle([i, j, i+10, j+10], fill='black')
    draw.rectangle([0, 0, 69, 69], outline='red', width=2)
    img.save('test_qr.png')
    return 'test_qr.png'

def test_coordinate_mapping(pdf_path, output_name):
    """
    회전 보정 후 좌표 매핑 테스트
    의뢰서 PDF에 썸네일과 QR 코드를 삽입
    """
    print(f"\n{'='*60}")
    print(f"Testing: {os.path.basename(pdf_path)}")
    print(f"{'='*60}")
    
    # PDF 열기
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    print(f"Original rotation: {page.rotation}°")
    print(f"Original MediaBox: {page.mediabox}")
    
    # 회전 보정이 필요한지 확인
    needs_correction = page.rotation != 0
    
    if needs_correction:
        print("Applying rotation correction...")
        
        # 새 문서 생성
        new_doc = fitz.open()
        new_page = new_doc.new_page(width=842, height=595)
        
        # 회전 보정하여 내용 복사
        new_page.show_pdf_page(
            new_page.rect,
            doc,
            0,
            rotate=-page.rotation
        )
        
        doc.close()
        doc = new_doc
        page = doc[0]
        
        print(f"After correction: rotation={page.rotation}°")
    
    # 표준 좌표 (2-up 레이아웃)
    coordinates = {
        "thumbnail": {
            "left": {"x": 230, "y": 234, "width": 160, "height": 250},
            "right": {"x": 658, "y": 228, "width": 160, "height": 250}
        },
        "qr": {
            "left": {"x": 315, "y": 500, "size": 70},
            "right": {"x": 730, "y": 500, "size": 70}
        }
    }
    
    # 테스트 이미지 생성
    thumbnail_path = create_test_thumbnail()
    qr_path = create_test_qr()
    
    # 썸네일 삽입 (좌측)
    thumb_left = coordinates["thumbnail"]["left"]
    thumb_rect_left = fitz.Rect(
        thumb_left["x"],
        thumb_left["y"],
        thumb_left["x"] + thumb_left["width"],
        thumb_left["y"] + thumb_left["height"]
    )
    page.insert_image(thumb_rect_left, filename=thumbnail_path)
    print(f"Inserted left thumbnail at: {thumb_rect_left}")
    
    # 썸네일 삽입 (우측)
    thumb_right = coordinates["thumbnail"]["right"]
    thumb_rect_right = fitz.Rect(
        thumb_right["x"],
        thumb_right["y"],
        thumb_right["x"] + thumb_right["width"],
        thumb_right["y"] + thumb_right["height"]
    )
    page.insert_image(thumb_rect_right, filename=thumbnail_path)
    print(f"Inserted right thumbnail at: {thumb_rect_right}")
    
    # QR 코드 삽입 (좌측)
    qr_left = coordinates["qr"]["left"]
    qr_rect_left = fitz.Rect(
        qr_left["x"],
        qr_left["y"],
        qr_left["x"] + qr_left["size"],
        qr_left["y"] + qr_left["size"]
    )
    page.insert_image(qr_rect_left, filename=qr_path)
    print(f"Inserted left QR at: {qr_rect_left}")
    
    # QR 코드 삽입 (우측)
    qr_right = coordinates["qr"]["right"]
    qr_rect_right = fitz.Rect(
        qr_right["x"],
        qr_right["y"],
        qr_right["x"] + qr_right["size"],
        qr_right["y"] + qr_right["size"]
    )
    page.insert_image(qr_rect_right, filename=qr_path)
    print(f"Inserted right QR at: {qr_rect_right}")
    
    # 좌표 마커 추가 (디버깅용)
    # 페이지 중앙
    center_x = page.rect.width / 2
    page.draw_line(fitz.Point(center_x, 0), fitz.Point(center_x, page.rect.height), 
                   color=(1, 0, 0), width=1)
    
    # 저장
    doc.save(output_name)
    print(f"Saved: {output_name}")
    doc.close()
    
    # 정리
    os.remove(thumbnail_path)
    os.remove(qr_path)

def main():
    """메인 테스트 함수"""
    print("\n" + "="*60)
    print("FINAL INTEGRATION TEST")
    print("Testing coordinate system after rotation correction")
    print("="*60)
    
    # 테스트할 PDF 파일들
    test_files = [
        (r'C:\Users\wp\Desktop\(주)성심건업\(주)성심건업_의뢰서_2025-08-08_090845 - 복사본 (8).pdf', 
         'final_test_normal.pdf'),
        (r'C:\Users\wp\Desktop\(주)성심건업\이진성-작업의뢰서(25년8월) - 복사본 (3).pdf',
         'final_test_rotated.pdf')
    ]
    
    for pdf_path, output_name in test_files:
        if os.path.exists(pdf_path):
            test_coordinate_mapping(pdf_path, output_name)
        else:
            print(f"File not found: {pdf_path}")
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print("\nPlease check the output files:")
    print("1. final_test_normal.pdf - Should show thumbnails and QR codes in correct positions")
    print("2. final_test_rotated.pdf - Should also show thumbnails and QR codes in correct positions")
    print("\nBoth files should have:")
    print("- 2 thumbnails (left and right)")
    print("- 2 QR codes (left and right)")
    print("- Red center line for reference")
    print("\nIf positions are correct in both files, the rotation correction is working properly!")

if __name__ == "__main__":
    main()