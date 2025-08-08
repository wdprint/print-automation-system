#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF 인쇄 의뢰서 자동화 시스템
메인 진입점 - 명령줄 인자 처리 및 모드 선택
"""

import argparse
import sys
import os
from pathlib import Path

# 프로젝트 루트 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent))

def process_cli(files: list, preset: str = None):
    """CLI 모드로 파일 처리"""
    from core.pdf_processor import PDFProcessor
    from config.settings_manager import SettingsManager
    from utils.file_classifier import FileClassifier
    from utils.logger import setup_logger
    
    logger = setup_logger('cli')
    logger.info(f"CLI 모드 시작 - 파일 수: {len(files)}, 프리셋: {preset or 'default'}")
    
    try:
        # 설정 로드
        settings_manager = SettingsManager()
        if preset:
            settings_manager.load_preset(preset)
        
        # 파일 분류
        classifier = FileClassifier()
        classified_files = classifier.classify(files)
        
        if not classified_files.is_valid():
            logger.error(f"파일 검증 실패: {classified_files.get_error()}")
            print(f"오류: {classified_files.get_error()}")
            return False
        
        # PDF 처리 (여러 PDF 파일 지원)
        processor = PDFProcessor(settings_manager)
        result = processor.process_files(
            classified_files.order_pdf,
            classified_files.print_pdfs,  # 여러 PDF 파일 리스트
            classified_files.qr_image
        )
        
        if result:
            logger.info("처리 완료")
            print("✅ PDF 처리가 완료되었습니다.")
        else:
            logger.error("처리 실패")
            print("❌ PDF 처리 중 오류가 발생했습니다.")
            
        return result
        
    except Exception as e:
        logger.critical(f"예상치 못한 오류: {e}")
        print(f"❌ 오류 발생: {e}")
        return False

def open_settings():
    """설정 창 열기"""
    from gui.modern_settings import ModernSettingsWindow
    import tkinter as tk
    
    root = tk.Tk()
    root.withdraw()  # 메인 윈도우 숨기기
    
    settings_window = ModernSettingsWindow(root)
    settings_window.run()

def open_gui():
    """GUI 모드 실행"""
    from gui.modern_main_window import ModernMainWindow
    
    app = ModernMainWindow()
    app.run()

def switch_preset(preset_index: str):
    """프리셋 전환"""
    from config.preset_manager import PresetManager
    from utils.logger import setup_logger
    
    logger = setup_logger('preset')
    
    try:
        preset_manager = PresetManager()
        preset_manager.quick_switch(int(preset_index))
        logger.info(f"프리셋 {preset_index}로 전환 완료")
        print(f"프리셋 F{preset_index}로 전환되었습니다.")
        return True
    except Exception as e:
        logger.error(f"프리셋 전환 실패: {e}")
        print(f"프리셋 전환 실패: {e}")
        return False

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='PDF 인쇄 의뢰서 자동화 시스템',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # GUI 모드 실행
  %(prog)s
  
  # CLI 모드로 파일 처리
  %(prog)s --cli "의뢰서.pdf" "인쇄데이터.pdf" "QR코드.png"
  
  # 설정 창 열기
  %(prog)s --settings
  
  # 프리셋 전환
  %(prog)s --preset 1
        """
    )
    
    parser.add_argument('--cli', action='store_true', 
                       help='CLI 모드 실행 (GUI 없이 처리)')
    parser.add_argument('--settings', action='store_true', 
                       help='설정 창만 열기')
    parser.add_argument('--preset', type=str, metavar='N',
                       help='프리셋 번호로 전환 (1-4)')
    parser.add_argument('--version', action='version', 
                       version='%(prog)s 2.0.0')
    parser.add_argument('files', nargs='*', 
                       help='처리할 파일들 (의뢰서 PDF, 인쇄 PDF, QR 이미지)')
    
    args = parser.parse_args()
    
    # 프리셋 전환 모드
    if args.preset:
        sys.exit(0 if switch_preset(args.preset) else 1)
    
    # CLI 모드
    if args.cli:
        if not args.files:
            parser.error("CLI 모드에서는 파일이 필요합니다.")
        sys.exit(0 if process_cli(args.files) else 1)
    
    # 설정 모드
    if args.settings:
        open_settings()
        sys.exit(0)
    
    # 파일이 제공된 경우 CLI 모드로 자동 실행
    if args.files:
        sys.exit(0 if process_cli(args.files) else 1)
    
    # 기본: GUI 모드
    open_gui()

if __name__ == '__main__':
    main()