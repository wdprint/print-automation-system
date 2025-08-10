"""
PDF를 벡터 형태로 유지하며 삽입하는 테스트
래스터화 없이 PDF를 PDF에 직접 삽입
"""

import os
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter, Transformation, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import fitz  # PyMuPDF for comparison
from PIL import Image
from io import BytesIO

# 테스트 파일 경로
TEST_PDF = r"c:\Users\dltjd\OneDrive\바탕 화면\(주)성심건업\1_국제무역관리자과정_표지_10.6mm.pdf"
OUTPUT_DIR = Path("test_vector_output")
OUTPUT_DIR.mkdir(exist_ok=True)

def method1_pypdf2_direct():
    """방법 1: PyPDF2로 PDF 직접 삽입 (벡터 유지)"""
    print("\n=== 방법 1: PyPDF2 직접 삽입 ===")
    
    try:
        # A4 백지 생성 (가로)
        writer = PdfWriter()
        page = PageObject.create_blank_page(width=A4[1], height=A4[0])  # 가로 A4
        
        # 표지 PDF 읽기
        reader = PdfReader(TEST_PDF)
        cover_page = reader.pages[0]
        
        # 원본 크기 확인
        orig_width = float(cover_page.mediabox.width)
        orig_height = float(cover_page.mediabox.height)
        print(f"원본 크기: {orig_width:.0f} x {orig_height:.0f} points")
        
        # 목표 크기 (points로 변환)
        target_width = 160 * 0.75  # 160 pixels to points
        target_height = 250 * 0.75  # 250 pixels to points
        
        # 스케일 계산
        scale_x = target_width / orig_width
        scale_y = target_height / orig_height
        scale = min(scale_x, scale_y)  # 비율 유지
        
        print(f"축소 비율: {scale:.3f} ({scale*100:.1f}%)")
        
        # 변환 매트릭스 생성 (크기 조정 + 위치 이동)
        x_pos = 100  # 왼쪽에서 100 포인트
        y_pos = 200  # 아래에서 200 포인트
        
        transformation = Transformation().scale(sx=scale, sy=scale).translate(tx=x_pos, ty=y_pos)
        
        # 표지를 백지에 추가
        cover_page.add_transformation(transformation)
        page.merge_page(cover_page)
        
        # Save
        writer.add_page(page)
        output_path = OUTPUT_DIR / "method1_pypdf2_vector.pdf"
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        print(f"[SUCCESS] Saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def method2_pypdf2_multiple():
    """방법 2: PyPDF2로 여러 크기 테스트 (2-up 레이아웃)"""
    print("\n=== 방법 2: 다양한 크기로 2-up 레이아웃 ===")
    
    try:
        # A4 가로 백지 생성
        writer = PdfWriter()
        page = PageObject.create_blank_page(width=A4[1], height=A4[0])
        
        # 표지 PDF 읽기
        reader = PdfReader(TEST_PDF)
        cover_page = reader.pages[0]
        
        # 원본 크기
        orig_width = float(cover_page.mediabox.width)
        orig_height = float(cover_page.mediabox.height)
        
        # 테스트할 크기들 (pixels -> points)
        test_sizes = [
            (160, 250, "160x250 (원본)"),
            (240, 375, "240x375 (1.5배)"),
            (320, 500, "320x500 (2배)")
        ]
        
        # 페이지 중앙에서 시작
        page_width = A4[1]
        page_height = A4[0]
        
        for idx, (width_px, height_px, label) in enumerate(test_sizes):
            print(f"\n크기 테스트: {label}")
            
            # 새 페이지 생성
            page = PageObject.create_blank_page(width=page_width, height=page_height)
            
            # 픽셀을 포인트로 변환
            target_width = width_px * 0.75
            target_height = height_px * 0.75
            
            # 스케일 계산
            scale = min(target_width / orig_width, target_height / orig_height)
            scaled_width = orig_width * scale
            scaled_height = orig_height * scale
            
            # 2-up 레이아웃 위치 계산
            spacing = 30  # 간격
            total_width = scaled_width * 2 + spacing
            
            # 중앙 정렬
            start_x = (page_width - total_width) / 2
            y_pos = (page_height - scaled_height) / 2
            
            # 왼쪽 페이지
            left_transform = Transformation().scale(sx=scale, sy=scale).translate(tx=start_x, ty=y_pos)
            left_page = PdfReader(TEST_PDF).pages[0]
            left_page.add_transformation(left_transform)
            page.merge_page(left_page)
            
            # 오른쪽 페이지
            right_x = start_x + scaled_width + spacing
            right_transform = Transformation().scale(sx=scale, sy=scale).translate(tx=right_x, ty=y_pos)
            right_page = PdfReader(TEST_PDF).pages[0]
            right_page.add_transformation(right_transform)
            page.merge_page(right_page)
            
            # 라벨 추가를 위한 reportlab 사용
            from reportlab.pdfgen import canvas
            from io import BytesIO
            
            packet = BytesIO()
            c = canvas.Canvas(packet, pagesize=(page_width, page_height))
            c.setFont("Helvetica", 12)
            c.drawString(50, page_height - 30, f"Test: {label} - Scale: {scale:.3f}")
            c.save()
            
            packet.seek(0)
            label_reader = PdfReader(packet)
            page.merge_page(label_reader.pages[0])
            
            writer.add_page(page)
            print(f"  축소율: {scale:.3f} ({scale*100:.1f}%)")
            print(f"  실제 크기: {scaled_width:.0f} x {scaled_height:.0f} points")
        
        # Save
        output_path = OUTPUT_DIR / "method2_size_comparison.pdf"
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        print(f"\n[SUCCESS] Saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def method3_fitz_comparison():
    """방법 3: 기존 래스터 방식과 비교 (PyMuPDF)"""
    print("\n=== 방법 3: 래스터 방식 비교 ===")
    
    try:
        # PDF 열기
        doc = fitz.open(TEST_PDF)
        page = doc[0]
        
        # 다양한 DPI로 테스트
        dpis = [72, 150, 300, 600]
        
        for dpi in dpis:
            # 렌더링
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # PIL 이미지로 변환
            img_data = pix.pil_tobytes(format="PNG")
            img = Image.open(BytesIO(img_data))
            
            # 160x250으로 리사이즈
            img.thumbnail((160, 250), Image.Resampling.LANCZOS)
            
            # Save
            output_path = OUTPUT_DIR / f"raster_{dpi}dpi.png"
            img.save(output_path, "PNG", optimize=False)
            
            print(f"Raster {dpi} DPI: {output_path}")
        
        doc.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def method4_reportlab_vector():
    """방법 4: ReportLab으로 PDF Form XObject 사용"""
    print("\n=== 방법 4: ReportLab Form XObject ===")
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4, landscape
        from PyPDF2 import PdfReader
        from pdfrw import PdfReader as PdfRwReader, PageMerge
        
        # pdfrw를 사용한 벡터 삽입
        output_path = OUTPUT_DIR / "method4_reportlab_vector.pdf"
        
        # A4 가로 캔버스 생성
        c = canvas.Canvas(str(output_path), pagesize=landscape(A4))
        page_width, page_height = landscape(A4)
        
        # 제목
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, page_height - 30, "PDF Vector Insertion Test")
        
        # 테스트 크기들
        positions = [
            (100, 300, 160, 250, "160x250"),
            (350, 300, 240, 375, "240x375"),
            (650, 200, 320, 500, "320x500")
        ]
        
        for x, y, width, height, label in positions:
            # 라벨
            c.setFont("Helvetica", 10)
            c.drawString(x, y - 15, label)
            
            # 테두리
            c.rect(x, y, width, height)
        
        c.save()
        print(f"[SUCCESS] ReportLab saved to: {output_path}")
        
        # PyPDF2로 PDF 합치기
        writer = PdfWriter()
        base_reader = PdfReader(output_path)
        cover_reader = PdfReader(TEST_PDF)
        
        base_page = base_reader.pages[0]
        
        for x, y, width, height, label in positions:
            cover_page = cover_reader.pages[0]
            
            # 크기 조정
            orig_width = float(cover_page.mediabox.width)
            orig_height = float(cover_page.mediabox.height)
            scale = min(width / orig_width, height / orig_height)
            
            transformation = Transformation().scale(sx=scale, sy=scale).translate(tx=x, ty=y)
            cover_page.add_transformation(transformation)
            base_page.merge_page(cover_page)
        
        writer.add_page(base_page)
        
        final_output = OUTPUT_DIR / "method4_final_vector.pdf"
        with open(final_output, 'wb') as f:
            writer.write(f)
        
        print(f"[SUCCESS] Final saved to: {final_output}")
        return True
        
    except ImportError as e:
        print(f"[WARNING] pdfrw not installed: pip install pdfrw")
        print(f"   Using PyPDF2 only...")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def main():
    """모든 방법 실행 및 비교"""
    print("=" * 60)
    print("PDF Vector Insertion Test")
    print("=" * 60)
    
    # 테스트 파일 확인
    if not os.path.exists(TEST_PDF):
        print(f"[ERROR] Test file not found: {TEST_PDF}")
        return
    
    print(f"Test file: {TEST_PDF}")
    
    # 각 방법 실행
    results = []
    
    # 방법 1: PyPDF2 직접 삽입
    if method1_pypdf2_direct():
        results.append("[OK] PyPDF2 direct insertion success")
    
    # 방법 2: 다양한 크기 테스트
    if method2_pypdf2_multiple():
        results.append("[OK] Size comparison test success")
    
    # 방법 3: 래스터 비교
    if method3_fitz_comparison():
        results.append("[OK] Raster comparison generated")
    
    # 방법 4: ReportLab
    if method4_reportlab_vector():
        results.append("[OK] ReportLab vector insertion success")
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    for result in results:
        print(result)
    
    print(f"\nOutput directory: {OUTPUT_DIR.absolute()}")
    print("\n[RECOMMENDATIONS]")
    print("1. Check method2_size_comparison.pdf to select optimal size")
    print("2. Compare vector method (PyPDF2) vs raster method (PNG) quality")
    print("3. Vector method maintains quality even when zoomed")

if __name__ == "__main__":
    main()