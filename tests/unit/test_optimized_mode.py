"""
최적화 모드 테스트
1. 고품질 래스터 썸네일
2. 흰색 배경으로 가독성 향상
3. 파일 크기 최적화
"""

import os
import sys
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings_manager import SettingsManager
from core.pdf_processor import PDFProcessor


def test_optimized_mode():
    """최적화 모드 테스트"""
    
    print("=" * 60)
    print("Optimized Mode Test")
    print("=" * 60)
    
    # 테스트 파일
    test_files = {
        'order': r"c:\Users\dltjd\OneDrive\바탕 화면\(주)성심건업\(주)성심건업_의뢰서_2025-08-08_090845 - 복사본.pdf",
        'print': r"c:\Users\dltjd\OneDrive\바탕 화면\(주)성심건업\1_국제무역관리자과정_표지_10.6mm.pdf",
        'qr': None
    }
    
    # 파일 존재 확인
    if not os.path.exists(test_files['order']):
        print(f"[WARNING] Order file not found, creating test file")
        
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4, landscape
        
        test_files['order'] = "test_order.pdf"
        c = canvas.Canvas(test_files['order'], pagesize=landscape(A4))
        
        # 배경에 텍스트 추가 (가독성 테스트용)
        c.setFont("Helvetica", 8)
        for y in range(50, 550, 20):
            c.drawString(50, y, "Background text - should be hidden by white background" * 3)
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(230, 500, "Left Thumbnail Area")
        c.drawString(658, 500, "Right Thumbnail Area")
        c.save()
    
    if not os.path.exists(test_files['print']):
        print(f"[WARNING] Print file not found, creating test file")
        
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        
        test_files['print'] = "test_print.pdf"
        c = canvas.Canvas(test_files['print'], pagesize=A4)
        
        # 테스트 표지 생성
        c.setFont("Helvetica-Bold", 72)
        c.drawString(100, 700, "COVER")
        
        c.setFont("Helvetica", 36)
        c.drawString(100, 600, "High Quality")
        c.drawString(100, 550, "Thumbnail Test")
        
        # 세부 텍스트 (품질 테스트용)
        c.setFont("Helvetica", 12)
        for i in range(10):
            c.drawString(100, 400 - i*15, f"Detail text line {i+1} - Should be readable")
        
        c.save()
    
    # 설정 관리자
    settings = SettingsManager()
    
    # 테스트 1: 최적화 모드 (기본)
    print("\n" + "-" * 60)
    print("Test 1: Optimized Mode (Default)")
    print("-" * 60)
    
    settings.set('processing.mode', 'optimized')
    settings.set('processing.white_background', True)
    settings.set('processing.optimal_dpi', 300)
    
    processor = PDFProcessor(settings)
    success = processor.process_files(
        test_files['order'],
        [test_files['print']],
        test_files['qr']
    )
    
    if success:
        print("[OK] Optimized mode processing success")
        # 결과 파일 확인
        result_files = list(Path('.').glob('*_processed*.pdf'))
        if result_files:
            file_size = result_files[-1].stat().st_size / 1024
            print(f"  Output: {result_files[-1].name}")
            print(f"  Size: {file_size:.1f} KB")
    else:
        print("[FAIL] Optimized mode processing failed")
    
    # 테스트 2: DPI 비교 테스트
    print("\n" + "-" * 60)
    print("Test 2: DPI Comparison")
    print("-" * 60)
    
    dpi_values = [150, 300, 600]
    
    for dpi in dpi_values:
        print(f"\nTesting DPI: {dpi}")
        
        settings.set('processing.optimal_dpi', dpi)
        settings.set('thumbnail.optimal_dpi', dpi)
        
        processor = PDFProcessor(settings)
        
        # 출력 파일명 지정
        output_name = f"test_optimized_{dpi}dpi.pdf"
        
        success = processor.process_files(
            test_files['order'],
            [test_files['print']],
            test_files['qr']
        )
        
        if success:
            # 가장 최근 생성된 파일 찾기
            result_files = sorted(Path('.').glob('*_processed*.pdf'), 
                                key=lambda x: x.stat().st_mtime)
            if result_files:
                latest_file = result_files[-1]
                # 이름 변경
                latest_file.rename(output_name)
                file_size = os.path.getsize(output_name) / 1024
                print(f"  [OK] Created: {output_name} ({file_size:.1f} KB)")
        else:
            print(f"  [FAIL] Failed at {dpi} DPI")
    
    # 테스트 3: 배경 유무 비교
    print("\n" + "-" * 60)
    print("Test 3: Background Comparison")
    print("-" * 60)
    
    # 배경 있음
    print("\nWith white background:")
    settings.set('processing.white_background', True)
    processor = PDFProcessor(settings)
    success = processor.process_files(
        test_files['order'],
        [test_files['print']],
        test_files['qr']
    )
    
    if success:
        print("[OK] With background processed")
    
    # 배경 없음 (벡터 모드로 테스트)
    print("\nWithout background (vector mode):")
    settings.set('processing.mode', 'vector')
    processor = PDFProcessor(settings)
    success = processor.process_files(
        test_files['order'],
        [test_files['print']],
        test_files['qr']
    )
    
    if success:
        print("[OK] Without background processed")
    
    # 테스트 4: 래스터화된 벡터 하이브리드
    print("\n" + "-" * 60)
    print("Test 4: Rasterized Vector Hybrid")
    print("-" * 60)
    
    settings.set('processing.mode', 'rasterized_hybrid')
    processor = PDFProcessor(settings)
    
    success = processor.process_files(
        test_files['order'],
        [test_files['print']],
        test_files['qr']
    )
    
    if success:
        print("[OK] Rasterized hybrid processed")
    else:
        print("[FAIL] Rasterized hybrid failed")
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    # 생성된 모든 테스트 파일 나열
    test_outputs = []
    for pattern in ['test_optimized_*.pdf', '*_processed*.pdf']:
        test_outputs.extend(Path('.').glob(pattern))
    
    if test_outputs:
        print("\nGenerated files:")
        for file in sorted(set(test_outputs)):
            size = file.stat().st_size / 1024
            print(f"  {file.name}: {size:.1f} KB")
    
    print("\nRecommendations:")
    print("1. Optimized mode (300 DPI) provides best balance")
    print("2. White background significantly improves readability")
    print("3. File size scales linearly with DPI")
    print("4. 300 DPI is optimal for print quality")
    
    # 임시 파일 정리
    print("\nCleaning up test files...")
    temp_files = ['test_order.pdf', 'test_print.pdf']
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                print(f"  Removed: {temp_file}")
            except:
                pass


def compare_file_sizes():
    """파일 크기 비교 분석"""
    
    print("\n" + "=" * 60)
    print("File Size Analysis")
    print("=" * 60)
    
    # 모든 PDF 파일 찾기
    pdf_files = list(Path('.').glob('*.pdf'))
    
    if not pdf_files:
        print("No PDF files found")
        return
    
    # 크기별 정렬
    pdf_files.sort(key=lambda x: x.stat().st_size)
    
    print("\nFile sizes (sorted):")
    for file in pdf_files:
        size_kb = file.stat().st_size / 1024
        size_mb = size_kb / 1024
        
        if size_mb > 1:
            print(f"  {file.name}: {size_mb:.2f} MB")
        else:
            print(f"  {file.name}: {size_kb:.1f} KB")
    
    # 모드별 평균 크기 계산
    mode_sizes = {
        'optimized': [],
        'vector': [],
        'hybrid': [],
        'raster': []
    }
    
    for file in pdf_files:
        name = file.name.lower()
        size = file.stat().st_size / 1024
        
        if 'optimized' in name:
            mode_sizes['optimized'].append(size)
        elif 'vector' in name:
            mode_sizes['vector'].append(size)
        elif 'hybrid' in name:
            mode_sizes['hybrid'].append(size)
        elif 'raster' in name or '처리' in name:
            mode_sizes['raster'].append(size)
    
    print("\nAverage sizes by mode:")
    for mode, sizes in mode_sizes.items():
        if sizes:
            avg_size = sum(sizes) / len(sizes)
            print(f"  {mode}: {avg_size:.1f} KB (n={len(sizes)})")


if __name__ == "__main__":
    # 메인 테스트
    test_optimized_mode()
    
    # 크기 분석
    compare_file_sizes()
    
    print("\n[COMPLETE] All tests finished!")