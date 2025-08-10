"""고품질 썸네일 생성 테스트 - 새로운 접근 방식"""

import fitz  # PyMuPDF
from PIL import Image, ImageFilter, ImageEnhance
from io import BytesIO
import os
from pathlib import Path

def create_high_quality_thumbnail():
    """고품질 썸네일 생성 - 다양한 방법 테스트"""
    
    pdf_path = r"c:\Users\dltjd\OneDrive\바탕 화면\(주)성심건업\1_국제무역관리자과정_표지_10.6mm.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"파일을 찾을 수 없습니다: {pdf_path}")
        return
    
    print("고품질 썸네일 생성 테스트")
    print("=" * 70)
    
    # PDF 열기
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    output_dir = Path("test_output_hq")
    output_dir.mkdir(exist_ok=True)
    
    # 방법 1: 매우 높은 DPI로 렌더링 후 고품질 리사이즈
    print("\n[방법 1] 초고해상도 렌더링 + 고품질 리사이즈")
    print("-" * 50)
    
    # 1200 DPI로 렌더링 (매우 높은 품질)
    dpi = 1200
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    
    # 이미지 크기 제한 우회
    Image.MAX_IMAGE_PIXELS = None  # 제한 해제
    
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_data = pix.pil_tobytes(format="PNG")
    img = Image.open(BytesIO(img_data))
    print(f"원본 렌더링: {img.width} x {img.height} pixels")
    
    # 실제 PDF 삽입 크기 (의뢰서 PDF에서 사용하는 크기)
    target_sizes = [
        (160, 250, "small"),   # 현재 기본값
        (320, 500, "medium"),  # 2배
        (480, 750, "large"),   # 3배
        (640, 1000, "xlarge")  # 4배
    ]
    
    for width, height, label in target_sizes:
        # 비율 유지하며 크기 계산
        img_ratio = img.width / img.height
        thumb_ratio = width / height
        
        if img_ratio > thumb_ratio:
            new_width = width
            new_height = int(width / img_ratio)
        else:
            new_height = height
            new_width = int(height * img_ratio)
        
        # 고품질 리사이즈
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 샤프닝 적용
        resized = resized.filter(ImageFilter.EDGE_ENHANCE_MORE)
        resized = resized.filter(ImageFilter.UnsharpMask(
            radius=1.5,
            percent=200,
            threshold=2
        ))
        
        # 대비 향상
        enhancer = ImageEnhance.Contrast(resized)
        resized = enhancer.enhance(1.3)
        
        # PNG로 저장 (무손실)
        output_png = output_dir / f"method1_{label}_{width}x{height}.png"
        resized.save(output_png, format="PNG", compress_level=0)
        
        # JPEG로도 저장 (비교용)
        output_jpg = output_dir / f"method1_{label}_{width}x{height}.jpg"
        resized.save(output_jpg, format="JPEG", quality=100, subsampling=0)
        
        print(f"  {label:8} ({new_width:4}x{new_height:4}): PNG={output_png.stat().st_size:,} bytes, JPG={output_jpg.stat().st_size:,} bytes")
    
    # 방법 2: 중간 해상도에서 단계적 리사이즈
    print("\n[방법 2] 단계적 리사이즈 (Super-sampling)")
    print("-" * 50)
    
    # 600 DPI로 렌더링
    dpi = 600
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_data = pix.pil_tobytes(format="PNG")
    img = Image.open(BytesIO(img_data))
    print(f"중간 해상도 렌더링: {img.width} x {img.height} pixels")
    
    for width, height, label in target_sizes:
        # 비율 계산
        img_ratio = img.width / img.height
        thumb_ratio = width / height
        
        if img_ratio > thumb_ratio:
            final_width = width
            final_height = int(width / img_ratio)
        else:
            final_height = height
            final_width = int(height * img_ratio)
        
        # 단계적 리사이즈 (2단계)
        # 1단계: 목표 크기의 2배로
        temp_width = final_width * 2
        temp_height = final_height * 2
        temp_img = img.resize((temp_width, temp_height), Image.Resampling.LANCZOS)
        
        # 샤프닝 적용
        temp_img = temp_img.filter(ImageFilter.SHARPEN)
        
        # 2단계: 최종 크기로
        final_img = temp_img.resize((final_width, final_height), Image.Resampling.LANCZOS)
        
        # 추가 샤프닝
        final_img = final_img.filter(ImageFilter.UnsharpMask(
            radius=0.8,
            percent=150,
            threshold=1
        ))
        
        # 저장
        output_png = output_dir / f"method2_{label}_{width}x{height}.png"
        final_img.save(output_png, format="PNG", compress_level=0)
        
        print(f"  {label:8} ({final_width:4}x{final_height:4}): {output_png.stat().st_size:,} bytes")
    
    # 방법 3: PyMuPDF의 get_pixmap에서 직접 크기 지정
    print("\n[방법 3] PyMuPDF 직접 크기 지정")
    print("-" * 50)
    
    for width, height, label in target_sizes:
        # 페이지 크기 대비 목표 크기 비율 계산
        page_width = page.rect.width
        page_height = page.rect.height
        
        # 적절한 zoom 계산
        zoom_x = width / page_width * 72 / 72.0
        zoom_y = height / page_height * 72 / 72.0
        zoom = max(zoom_x, zoom_y) * 3  # 3배 오버샘플링
        
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_data = pix.pil_tobytes(format="PNG")
        img = Image.open(BytesIO(img_data))
        
        # 정확한 크기로 리사이즈
        img_ratio = img.width / img.height
        thumb_ratio = width / height
        
        if img_ratio > thumb_ratio:
            final_width = width
            final_height = int(width / img_ratio)
        else:
            final_height = height
            final_width = int(height * img_ratio)
        
        final_img = img.resize((final_width, final_height), Image.Resampling.LANCZOS)
        
        # 품질 향상 처리
        final_img = final_img.filter(ImageFilter.EDGE_ENHANCE_MORE)
        enhancer = ImageEnhance.Sharpness(final_img)
        final_img = enhancer.enhance(2.0)
        
        output_png = output_dir / f"method3_{label}_{width}x{height}.png"
        final_img.save(output_png, format="PNG", compress_level=0)
        
        print(f"  {label:8} ({final_width:4}x{final_height:4}): {output_png.stat().st_size:,} bytes")
    
    doc.close()
    
    print("\n" + "=" * 70)
    print("테스트 완료!")
    print(f"생성된 썸네일은 '{output_dir}' 폴더에서 확인하세요.")
    print("\n권장사항:")
    print("1. 썸네일 크기를 현재 160x250에서 320x500 이상으로 증가")
    print("2. 1200 DPI로 렌더링 후 고품질 리사이즈")
    print("3. PNG 형식으로 무손실 저장")
    print("4. 다단계 샤프닝 적용")

if __name__ == "__main__":
    create_high_quality_thumbnail()