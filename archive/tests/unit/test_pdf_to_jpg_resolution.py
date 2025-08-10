"""PDF를 JPG로 변환하여 해상도 테스트"""

import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
import os
from pathlib import Path

def test_pdf_to_jpg_resolutions():
    """다양한 DPI로 PDF를 JPG로 변환하고 해상도 확인"""
    
    pdf_path = r"c:\Users\dltjd\OneDrive\바탕 화면\(주)성심건업\1_국제무역관리자과정_표지_10.6mm.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"파일을 찾을 수 없습니다: {pdf_path}")
        return
    
    print(f"PDF 파일: {pdf_path}")
    print("=" * 70)
    
    # PDF 열기
    doc = fitz.open(pdf_path)
    page = doc[0]  # 첫 페이지
    
    # 페이지 원본 크기
    page_rect = page.rect
    print(f"원본 PDF 페이지 크기: {page_rect.width:.0f} x {page_rect.height:.0f} points")
    print(f"(1 point = 1/72 inch)")
    print("=" * 70)
    
    # 다양한 DPI로 테스트
    dpi_values = [72, 150, 300, 450, 600, 900, 1200]
    
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    for dpi in dpi_values:
        print(f"\n[DPI: {dpi}]")
        
        # DPI에 따른 zoom 계산
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        
        # 페이지를 pixmap으로 변환
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        # PIL 이미지로 변환
        img_data = pix.pil_tobytes(format="PNG")
        img = Image.open(BytesIO(img_data))
        
        # 이미지 정보 출력
        print(f"  - 이미지 크기: {img.width} x {img.height} pixels")
        print(f"  - 실제 해상도: {img.width/page_rect.width*72:.0f} x {img.height/page_rect.height*72:.0f} DPI")
        print(f"  - 파일 크기 (메모리): {len(img_data):,} bytes ({len(img_data)/1024/1024:.2f} MB)")
        
        # 썸네일 크기로 리사이징 테스트
        thumb_sizes = [(160, 250), (200, 300), (240, 360)]
        
        for thumb_width, thumb_height in thumb_sizes:
            # 비율 유지하며 리사이즈
            img_copy = img.copy()
            img_ratio = img_copy.width / img_copy.height
            thumb_ratio = thumb_width / thumb_height
            
            if img_ratio > thumb_ratio:
                new_width = thumb_width
                new_height = int(thumb_width / img_ratio)
            else:
                new_height = thumb_height
                new_width = int(thumb_height * img_ratio)
            
            # resize 메서드 사용
            resized = img_copy.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 저장
            output_path = output_dir / f"dpi_{dpi}_thumb_{thumb_width}x{thumb_height}.jpg"
            resized.save(output_path, format="JPEG", quality=95)
            
            file_size = output_path.stat().st_size
            print(f"    → 썸네일 {thumb_width}x{thumb_height}: {resized.width}x{resized.height} px, {file_size:,} bytes")
        
        # 전체 이미지도 저장 (비교용)
        full_output = output_dir / f"dpi_{dpi}_full.jpg"
        img.save(full_output, format="JPEG", quality=95)
        print(f"  - 전체 이미지 저장: {full_output.name}")
    
    doc.close()
    
    print("\n" + "=" * 70)
    print("권장 사항:")
    print("1. 텍스트가 많은 문서: 최소 300 DPI")
    print("2. 고품질 인쇄물: 600 DPI 이상")
    print("3. 썸네일 생성: 원본을 높은 DPI(600-900)로 렌더링 후 리사이즈")
    print(f"\n생성된 이미지는 '{output_dir}' 폴더에서 확인하세요.")

if __name__ == "__main__":
    test_pdf_to_jpg_resolutions()