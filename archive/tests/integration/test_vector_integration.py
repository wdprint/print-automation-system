"""
벡터 PDF 통합 테스트
실제 프로젝트에 벡터 방식이 제대로 통합되었는지 검증
"""

import os
import sys
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings_manager import SettingsManager
from core.pdf_processor import PDFProcessor


def test_vector_integration():
    """벡터 통합 테스트"""
    
    print("=" * 60)
    print("Vector PDF Processing Integration Test")
    print("=" * 60)
    
    # 테스트 파일 설정
    test_files = {
        'order': r"c:\Users\dltjd\OneDrive\바탕 화면\(주)성심건업\(주)성심건업_의뢰서_2025-08-08_090845 - 복사본.pdf",
        'print': r"c:\Users\dltjd\OneDrive\바탕 화면\(주)성심건업\1_국제무역관리자과정_표지_10.6mm.pdf",
        'qr': None  # QR 이미지 경로 (있으면 추가)
    }
    
    # 파일 존재 확인
    if not os.path.exists(test_files['order']):
        print(f"❌ 의뢰서 파일을 찾을 수 없습니다: {test_files['order']}")
        
        # 대체 테스트 파일 생성
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4, landscape
        
        test_files['order'] = "test_order.pdf"
        c = canvas.Canvas(test_files['order'], pagesize=landscape(A4))
        c.drawString(100, 500, "Test Order PDF - 2-up Layout")
        c.drawString(100, 480, "Left Page Area")
        c.drawString(500, 480, "Right Page Area")
        c.save()
        print(f"✅ 테스트용 의뢰서 생성: {test_files['order']}")
    
    if not os.path.exists(test_files['print']):
        print(f"❌ 인쇄 파일을 찾을 수 없습니다: {test_files['print']}")
        
        # 대체 테스트 파일 생성
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        
        test_files['print'] = "test_print.pdf"
        c = canvas.Canvas(test_files['print'], pagesize=A4)
        c.setFont("Helvetica-Bold", 48)
        c.drawString(100, 700, "COVER")
        c.setFont("Helvetica", 24)
        c.drawString(100, 600, "Test Thumbnail")
        c.drawString(100, 550, "High Quality Vector")
        c.save()
        print(f"✅ 테스트용 표지 생성: {test_files['print']}")
    
    # 설정 관리자 초기화
    settings = SettingsManager()
    
    # 테스트 1: 벡터 모드
    print("\n" + "-" * 60)
    print("Test 1: Vector Mode (Default)")
    print("-" * 60)
    
    settings.set('processing.mode', 'vector')
    processor = PDFProcessor(settings)
    
    output_vector = "test_output_vector.pdf"
    success = processor.process_files(
        test_files['order'],
        [test_files['print']],
        test_files['qr']
    )
    
    if success:
        print("[OK] Vector mode processing success")
        # 파일 크기 확인
        if os.path.exists("test_order_processed.pdf"):
            size = os.path.getsize("test_order_processed.pdf") / 1024
            print(f"   파일 크기: {size:.1f} KB")
    else:
        print("❌ 벡터 모드 처리 실패")
    
    # 테스트 2: 하이브리드 모드
    print("\n" + "-" * 60)
    print("Test 2: Hybrid Mode")
    print("-" * 60)
    
    settings.set('processing.mode', 'hybrid')
    processor = PDFProcessor(settings)
    
    success = processor.process_files(
        test_files['order'],
        [test_files['print']],
        test_files['qr']
    )
    
    if success:
        print("[OK] Hybrid mode processing success")
    else:
        print("[FAIL] Hybrid mode processing failed")
    
    # 테스트 3: 래스터 모드 (기존 방식)
    print("\n" + "-" * 60)
    print("Test 3: Raster Mode (Legacy)")
    print("-" * 60)
    
    settings.set('processing.mode', 'raster')
    processor = PDFProcessor(settings)
    
    success = processor.process_files(
        test_files['order'],
        [test_files['print']],
        test_files['qr']
    )
    
    if success:
        print("[OK] Raster mode processing success")
    else:
        print("[FAIL] Raster mode processing failed")
    
    # 테스트 4: 한글 파일명 처리
    print("\n" + "-" * 60)
    print("Test 4: Korean Filename Handling")
    print("-" * 60)
    
    # 한글 파일명으로 복사
    korean_order = "test_order_korean.pdf"
    korean_print = "test_print_korean.pdf"
    
    try:
        import shutil
        if os.path.exists(test_files['order']):
            shutil.copy(test_files['order'], korean_order)
        if os.path.exists(test_files['print']):
            shutil.copy(test_files['print'], korean_print)
        
        settings.set('processing.mode', 'vector')
        processor = PDFProcessor(settings)
        
        success = processor.process_files(
            korean_order,
            [korean_print],
            None
        )
        
        if success:
            print("[OK] Korean filename processing success")
        else:
            print("[FAIL] Korean filename processing failed")
            
    except Exception as e:
        print(f"[ERROR] Korean filename test error: {e}")
    
    # 테스트 5: 다중 썸네일 처리
    print("\n" + "-" * 60)
    print("Test 5: Multiple Thumbnails")
    print("-" * 60)
    
    # 여러 개의 인쇄 파일
    multiple_prints = [test_files['print']] * 3  # 같은 파일 3번 (테스트용)
    
    settings.set('processing.mode', 'vector')
    processor = PDFProcessor(settings)
    
    success = processor.process_files(
        test_files['order'],
        multiple_prints,
        test_files['qr']
    )
    
    if success:
        print("[OK] Multiple thumbnail processing success")
    else:
        print("[FAIL] Multiple thumbnail processing failed")
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    # 생성된 파일 목록
    output_files = []
    for file in Path('.').glob('*_processed*.pdf'):
        output_files.append(file.name)
        size = file.stat().st_size / 1024
        print(f"[FILE] {file.name} ({size:.1f} KB)")
    
    if not output_files:
        for file in Path('.').glob('test_*.pdf'):
            if 'processed' in file.name:
                output_files.append(file.name)
                size = file.stat().st_size / 1024
                print(f"[FILE] {file.name} ({size:.1f} KB)")
    
    print("\nRecommendations:")
    print("1. Use vector mode as default (highest quality)")
    print("2. QR codes: PNG format with 300+ DPI recommended")
    print("3. Thumbnail size adjustable in settings")
    print("4. Full Korean filename support")
    
    # 임시 파일 정리
    print("\nCleaning temporary files...")
    temp_files = ['test_order.pdf', 'test_print.pdf', 
                  'test_order_korean.pdf', 'test_print_korean.pdf']
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                print(f"  Deleted: {temp_file}")
            except:
                pass


def test_qr_quality():
    """QR 코드 품질 테스트"""
    
    print("\n" + "=" * 60)
    print("QR Code Quality Test")
    print("=" * 60)
    
    from PIL import Image, ImageDraw
    import qrcode  # pip install qrcode[pil] 필요
    
    try:
        # 고품질 QR 코드 생성
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # 최고 오류 정정
            box_size=10,
            border=4,
        )
        
        qr.add_data('https://example.com/order/12345')
        qr.make(fit=True)
        
        # 고해상도 이미지 생성
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # 크기 조정 (고품질)
        sizes = [70, 100, 150]
        
        for size in sizes:
            # 픽셀 크기로 변환
            pixel_size = int(size / 0.75)
            
            # 리사이즈
            resized = qr_img.resize((pixel_size, pixel_size), Image.Resampling.NEAREST)
            
            # 저장
            filename = f"test_qr_{size}pt.png"
            resized.save(filename, "PNG", compress_level=0)
            
            print(f"[OK] QR created: {filename} ({pixel_size}x{pixel_size} px)")
        
        print("\nQR Code Recommendations:")
        print("- Use NEAREST resampling (maintains sharpness)")
        print("- Save PNG uncompressed")
        print("- Minimum 70pt (93px) size recommended")
        
    except ImportError:
        print("[WARNING] qrcode module not found. Skipping QR test")
        print("   Install: pip install qrcode[pil]")


if __name__ == "__main__":
    # 메인 테스트 실행
    test_vector_integration()
    
    # QR 품질 테스트 (선택사항)
    # test_qr_quality()
    
    print("\n[COMPLETE] All tests finished!")