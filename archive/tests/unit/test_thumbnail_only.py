"""표지 PDF를 고품질 썸네일로 만드는 테스트"""

import fitz  # PyMuPDF
from PIL import Image, ImageFilter, ImageEnhance
from io import BytesIO
import os
from pathlib import Path

def test_thumbnail_quality():
    """표지 PDF를 다양한 설정으로 썸네일 생성 테스트"""
    
    # 표지 PDF 경로
    pdf_path = r"c:\Users\dltjd\OneDrive\바탕 화면\(주)성심건업\1_국제무역관리자과정_표지_10.6mm.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"파일을 찾을 수 없습니다: {pdf_path}")
        return
    
    print("표지 PDF → 썸네일 품질 테스트")
    print("=" * 70)
    
    # PDF 열기
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    # 출력 디렉토리
    output_dir = Path("thumbnail_test_output")
    output_dir.mkdir(exist_ok=True)
    
    # 실제 의뢰서에 삽입되는 썸네일 크기
    target_width = 160
    target_height = 250
    
    # 테스트할 DPI 설정들
    test_configs = [
        {"dpi": 600, "label": "600dpi_standard"},
        {"dpi": 900, "label": "900dpi_high"},
        {"dpi": 1200, "label": "1200dpi_ultra"},
        {"dpi": 1500, "label": "1500dpi_max"},
    ]
    
    # 이미지 크기 제한 해제
    Image.MAX_IMAGE_PIXELS = None
    
    for config in test_configs:
        dpi = config["dpi"]
        label = config["label"]
        
        print(f"\n[{label}] DPI: {dpi}")
        print("-" * 50)
        
        # DPI에 따른 zoom 계산
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        
        # 페이지를 pixmap으로 변환
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_data = pix.pil_tobytes(format="PNG")
        img = Image.open(BytesIO(img_data))
        
        print(f"  원본 렌더링: {img.width} x {img.height} pixels")
        
        # 방법 1: 직접 resize (기본)
        img_copy = img.copy()
        img_ratio = img_copy.width / img_copy.height
        thumb_ratio = target_width / target_height
        
        if img_ratio > thumb_ratio:
            new_width = target_width
            new_height = int(target_width / img_ratio)
        else:
            new_height = target_height
            new_width = int(target_height * img_ratio)
        
        resized = img_copy.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 기본 저장
        basic_path = output_dir / f"{label}_basic.png"
        resized.save(basic_path, format="PNG", compress_level=0)
        print(f"  기본: {new_width}x{new_height} → {basic_path.stat().st_size:,} bytes")
        
        # 방법 2: 샤프닝 적용
        sharpened = resized.copy()
        sharpened = sharpened.filter(ImageFilter.EDGE_ENHANCE_MORE)
        sharpened = sharpened.filter(ImageFilter.UnsharpMask(
            radius=1.5,
            percent=200,
            threshold=1
        ))
        
        sharp_path = output_dir / f"{label}_sharp.png"
        sharpened.save(sharp_path, format="PNG", compress_level=0)
        print(f"  샤프닝: {sharp_path.stat().st_size:,} bytes")
        
        # 방법 3: 대비 향상 + 샤프닝
        enhanced = resized.copy()
        
        # 대비 향상
        contrast = ImageEnhance.Contrast(enhanced)
        enhanced = contrast.enhance(1.3)
        
        # 샤프닝
        enhanced = enhanced.filter(ImageFilter.EDGE_ENHANCE_MORE)
        enhanced = enhanced.filter(ImageFilter.UnsharpMask(
            radius=1.5,
            percent=200,
            threshold=1
        ))
        
        enhanced_path = output_dir / f"{label}_enhanced.png"
        enhanced.save(enhanced_path, format="PNG", compress_level=0)
        print(f"  강화: {enhanced_path.stat().st_size:,} bytes")
        
        # 방법 4: 2단계 리사이징 (오버샘플링)
        # 먼저 2배 크기로
        temp_width = new_width * 2
        temp_height = new_height * 2
        temp_img = img.resize((temp_width, temp_height), Image.Resampling.LANCZOS)
        
        # 샤프닝
        temp_img = temp_img.filter(ImageFilter.SHARPEN)
        
        # 최종 크기로
        final_img = temp_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 추가 샤프닝
        final_img = final_img.filter(ImageFilter.UnsharpMask(
            radius=1.0,
            percent=150,
            threshold=2
        ))
        
        oversample_path = output_dir / f"{label}_oversample.png"
        final_img.save(oversample_path, format="PNG", compress_level=0)
        print(f"  오버샘플링: {oversample_path.stat().st_size:,} bytes")
        
        # JPEG 버전도 저장 (비교용)
        enhanced_jpg = output_dir / f"{label}_enhanced.jpg"
        enhanced.save(enhanced_jpg, format="JPEG", quality=100, subsampling=0)
        print(f"  JPEG (100%): {enhanced_jpg.stat().st_size:,} bytes")
    
    doc.close()
    
    print("\n" + "=" * 70)
    print("권장 설정:")
    print("1. DPI: 1200 (품질과 속도의 균형)")
    print("2. 처리: EDGE_ENHANCE_MORE + UnsharpMask(1.5, 200, 1)")
    print("3. 대비: 1.3배 향상")
    print("4. 저장: PNG 무손실 (compress_level=0)")
    print(f"\n생성된 썸네일은 '{output_dir}' 폴더에서 확인하세요.")
    print("각 파일을 비교하여 최적의 설정을 선택하세요.")

if __name__ == "__main__":
    test_thumbnail_quality()