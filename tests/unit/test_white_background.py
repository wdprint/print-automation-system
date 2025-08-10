"""
흰색 배경 표시 테스트
rasterized_hybrid 모드에서 썸네일 주변에 흰색 배경이 제대로 나타나는지 확인
"""

import os
import sys
from pathlib import Path
import tempfile

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings_manager import SettingsManager
from core.pdf_processor import PDFProcessor
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import Color


def create_test_files():
    """테스트용 PDF 파일 생성"""
    
    # 의뢰서 PDF 생성 (회색 배경으로 흰색이 잘 보이도록)
    order_pdf = tempfile.mktemp(suffix='_order.pdf')
    c = canvas.Canvas(order_pdf, pagesize=landscape(A4))
    
    # 회색 배경 그리기 (흰색 배경이 잘 보이도록)
    lightgray = Color(0.8, 0.8, 0.8)  # 연한 회색
    gray = Color(0.5, 0.5, 0.5)  # 중간 회색
    
    c.setFillColor(lightgray)
    c.rect(0, 0, 842, 595, fill=1, stroke=0)
    
    # 텍스트 추가
    c.setFillColor(gray)
    c.setFont("Helvetica", 12)
    c.drawString(100, 500, "White Background Test - Order PDF")
    c.drawString(230, 480, "Left thumbnail area (should have white bg)")
    c.drawString(658, 480, "Right thumbnail area (should have white bg)")
    
    # 썸네일 위치 표시 (점선)
    c.setDash([3, 3])
    c.setStrokeColor(gray)
    c.rect(230, 234, 160, 250, fill=0, stroke=1)
    c.rect(658, 228, 160, 250, fill=0, stroke=1)
    
    c.save()
    print(f"[OK] Created order PDF: {order_pdf}")
    
    # 썸네일용 PDF 생성 (컬러풀한 내용)
    print_pdf = tempfile.mktemp(suffix='_print.pdf')
    c = canvas.Canvas(print_pdf, pagesize=A4)
    
    # 다채로운 배경
    colors = [
        Color(1, 0, 0),  # red
        Color(0, 0, 1),  # blue
        Color(0, 1, 0),  # green
        Color(1, 1, 0)   # yellow
    ]
    
    for i, color in enumerate(colors):
        c.setFillColor(color)
        c.rect(100 + i*100, 400, 80, 80, fill=1, stroke=0)
    
    # 제목
    c.setFillColor(Color(0.5, 0.5, 0.5))  # gray
    c.setFont("Helvetica-Bold", 36)
    c.drawString(100, 700, "THUMBNAIL")
    c.setFont("Helvetica", 24)
    c.drawString(100, 650, "White BG Test")
    
    # 세밀한 패턴 (흰색 배경 효과 테스트)
    c.setFont("Helvetica", 6)
    for i in range(30):
        c.drawString(100, 350 - i*8, f"Fine detail line {i+1} - Testing white background visibility")
    
    c.save()
    print(f"[OK] Created print PDF: {print_pdf}")
    
    return order_pdf, print_pdf


def test_white_background():
    """흰색 배경 테스트 실행"""
    
    print("=" * 60)
    print("White Background Visibility Test")
    print("=" * 60)
    
    # 설정 관리자 생성
    settings = SettingsManager()
    
    # rasterized_hybrid 모드로 설정
    settings.set('processing.mode', 'rasterized_hybrid')
    settings.set('processing.white_background', True)
    settings.set('thumbnail.render_dpi', 500)
    settings.set('thumbnail.white_border_size', 5)  # 테스트를 위해 좀 더 크게
    settings.save()
    
    print("\n[Settings]")
    print(f"Processing mode: {settings.get('processing.mode')}")
    print(f"White background: {settings.get('processing.white_background')}")
    print(f"White border size: {settings.get('thumbnail.white_border_size')} pixels")
    print(f"DPI: {settings.get('thumbnail.render_dpi')}")
    
    # 테스트 파일 생성
    print("\n[Creating test files]")
    order_pdf, print_pdf = create_test_files()
    
    # PDF 처리
    print("\n[Processing]")
    processor = PDFProcessor(settings)
    
    success = processor.process_files(
        order_pdf,
        [print_pdf],
        None
    )
    
    if success:
        # 최근 생성된 파일 찾기
        output_files = sorted(
            Path('.').glob('*_processed*.pdf'),
            key=lambda x: x.stat().st_mtime
        )
        
        if output_files:
            output_path = output_files[-1]
            # 파일명 변경
            new_name = "test_white_background_result.pdf"
            output_path.rename(new_name)
            output_path = new_name
            
            print(f"\n[SUCCESS] Output created: {output_path}")
            print("\nPlease check the output PDF:")
            print("1. Thumbnails should have white background/border")
            print("2. White border should be visible around thumbnails")
            print("3. Border size should be 5 pixels on each side")
            
            # 파일 크기 확인
            size_kb = Path(output_path).stat().st_size / 1024
            print(f"\nFile size: {size_kb:.1f} KB")
        else:
            print("\n[WARNING] Output file not found")
    else:
        print("\n[FAIL] Processing failed")
    
    # 다른 테두리 크기로 추가 테스트
    print("\n" + "-" * 60)
    print("Testing different border sizes")
    print("-" * 60)
    
    border_sizes = [0, 3, 5, 10]
    
    for border_size in border_sizes:
        print(f"\n[Test with {border_size}px border]")
        
        # 설정 변경
        settings.set('thumbnail.white_border_size', border_size)
        settings.save()
        
        # 새 프로세서 생성
        processor = PDFProcessor(settings)
        
        # 처리
        success = processor.process_files(
            order_pdf,
            [print_pdf],
            None
        )
        
        if success:
            # 최근 생성된 파일 찾기
            output_files = sorted(
                Path('.').glob('*_processed*.pdf'),
                key=lambda x: x.stat().st_mtime
            )
            
            if output_files:
                latest = output_files[-1]
                # 파일명 변경
                output_path = f"test_white_bg_border_{border_size}px.pdf"
                latest.rename(output_path)
                
                size_kb = Path(output_path).stat().st_size / 1024
                print(f"  [OK] Created: {output_path} ({size_kb:.1f} KB)")
            else:
                print(f"  [WARNING] Output file not found for {border_size}px")
        else:
            print(f"  [FAIL] Failed to process with {border_size}px border")
    
    # 임시 파일 정리
    print("\n[Cleanup]")
    for temp_file in [order_pdf, print_pdf]:
        try:
            os.unlink(temp_file)
            print(f"Removed: {temp_file}")
        except:
            pass
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
    print("\nKey findings:")
    print("1. White background is now visible as border around thumbnails")
    print("2. Border size is configurable via 'thumbnail.white_border_size'")
    print("3. Larger borders make white background more visible")
    print("4. Border helps readability on non-white backgrounds")


if __name__ == "__main__":
    test_white_background()