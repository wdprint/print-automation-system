#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
인쇄 자동화 시스템 - 향상된 버전
드래그 앤 드롭으로 파일을 받아 자동 처리
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import fitz
from PIL import Image
from pathlib import Path
import json
import os
import sys
from io import BytesIO

# 향상된 모듈들 임포트
from print_processor import EnhancedPrintProcessor
from settings_gui import EnhancedSettingsGUI

# 기존 설정도 호환성을 위해 유지
try:
    from config import *
except ImportError:
    # 기본값 설정
    PAGE_WIDTH = 842
    PAGE_HEIGHT = 595
    THUMBNAIL_CONFIG = {
        'max_width': 160,
        'max_height': 250,
        'positions': [
            {'x': 70, 'y': 180},
            {'x': 490, 'y': 180}
        ]
    }
    QR_CONFIG = {
        'max_width': 50,
        'max_height': 50,
        'positions': [
            {'x': 230, 'y': 470},
            {'x': 650, 'y': 470}
        ]
    }
    GUI_CONFIG = {
        'window_width': 500,
        'window_height': 400,
        'always_on_top': True,
        'resizable': False
    }
    DEBUG_MODE = False


class PrintAutomationGUI:
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("인쇄 의뢰서 자동화 시스템 v2.0")
        self.root.geometry(f"{GUI_CONFIG['window_width']}x{GUI_CONFIG['window_height']}")
        self.root.resizable(GUI_CONFIG['resizable'], GUI_CONFIG['resizable'])
        
        # 항상 최상단
        if GUI_CONFIG['always_on_top']:
            self.root.attributes("-topmost", True)
        
        # 드롭된 파일들
        self.dropped_files = {
            'order_pdf': None,
            'print_pdf': None,
            'qr_image': None
        }
        
        # 향상된 프로세서 사용
        self.processor = EnhancedPrintProcessor()
        
        # 설정 로드
        self.reload_settings()
        
        self.setup_ui()
    
    def reload_settings(self):
        """설정 다시 로드"""
        self.processor.settings = self.processor.load_enhanced_settings()
        print("설정이 다시 로드되었습니다.")
    
    def setup_ui(self):
        # 메인 프레임
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 제목 레이블
        title_label = tk.Label(
            main_frame, 
            text="PDF 2개 + 이미지 1개를\n드래그 앤 드롭 해주세요",
            font=("맑은 고딕", 16, "bold"),
            bg="#f0f0f0"
        )
        title_label.pack(pady=20)
        
        # 향상된 기능 표시
        feature_label = tk.Label(
            main_frame,
            text="✨ 백지 감지 | 다중 페이지 | 이미지 효과 | 자동 규칙",
            font=("맑은 고딕", 10),
            bg="#f0f0f0",
            fg="#0066cc"
        )
        feature_label.pack(pady=5)
        
        # 드롭 영역
        self.drop_frame = tk.Frame(
            main_frame, 
            bg="white", 
            relief=tk.GROOVE, 
            bd=2,
            height=200
        )
        self.drop_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 드롭 영역 안내 텍스트
        self.drop_label = tk.Label(
            self.drop_frame,
            text="파일을 여기에 드롭하세요",
            font=("맑은 고딕", 12),
            bg="white",
            fg="#999999"
        )
        self.drop_label.pack(expand=True)
        
        # 파일 목록 표시 영역
        self.file_list_frame = tk.Frame(main_frame, bg="#f0f0f0")
        self.file_list_frame.pack(fill=tk.X, pady=10)
        
        # 프로세싱 상태 표시
        self.progress_frame = tk.Frame(main_frame, bg="#f0f0f0")
        self.progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=("맑은 고딕", 9),
            bg="#f0f0f0",
            fg="#666666"
        )
        self.progress_label.pack(side=tk.LEFT)
        
        # 하단 프레임 (상태 레이블과 버튼들)
        bottom_frame = tk.Frame(main_frame, bg="#f0f0f0")
        bottom_frame.pack(fill=tk.X, pady=5)
        
        # 상태 레이블
        self.status_label = tk.Label(
            bottom_frame,
            text="대기 중...",
            font=("맑은 고딕", 10),
            bg="#f0f0f0",
            fg="#666666"
        )
        self.status_label.pack(side=tk.LEFT)
        
        # 버튼 컨테이너 (오른쪽 정렬)
        button_container = tk.Frame(bottom_frame, bg="#f0f0f0")
        button_container.pack(side=tk.RIGHT)
        
        # 고급 설정 버튼
        advanced_settings_btn = tk.Button(
            button_container,
            text="🎛 고급 설정",
            command=self.open_enhanced_settings,
            bg="#0066cc",
            fg="white",
            font=("맑은 고딕", 10, "bold"),
            padx=10,
            pady=5
        )
        advanced_settings_btn.pack(side=tk.LEFT, padx=5)
        
        # 기본 설정 버튼
        settings_btn = tk.Button(
            button_container,
            text="⚙ 위치 설정",
            command=self.open_basic_settings,
            bg="#666666",
            fg="white",
            font=("맑은 고딕", 10),
            padx=10,
            pady=5
        )
        settings_btn.pack(side=tk.LEFT, padx=5)
        
        # 초기화 버튼
        reset_btn = tk.Button(
            button_container,
            text="🔄 초기화",
            command=self.reset_files,
            bg="#999999",
            fg="white",
            font=("맑은 고딕", 10),
            padx=10,
            pady=5
        )
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        # 드래그 앤 드롭 설정
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        
        # 드래그 오버 효과
        self.drop_frame.dnd_bind('<<DragEnter>>', self.on_drag_enter)
        self.drop_frame.dnd_bind('<<DragLeave>>', self.on_drag_leave)
    
    def on_drag_enter(self, event):
        """드래그 진입 시 시각 효과"""
        self.drop_frame.config(bg="#e6f3ff")
        self.drop_label.config(bg="#e6f3ff", text="놓아주세요!", fg="#0066cc")
    
    def on_drag_leave(self, event):
        """드래그 떠날 때 원래대로"""
        self.drop_frame.config(bg="white")
        self.drop_label.config(bg="white", text="파일을 여기에 드롭하세요", fg="#999999")
    
    def on_drop(self, event):
        """파일 드롭 이벤트 처리"""
        # 드래그 효과 제거
        self.drop_frame.config(bg="white")
        self.drop_label.config(bg="white", fg="#999999")
        
        # 파일 경로 파싱
        files = self.parse_drop_data(event.data)
        
        # 파일 분류 및 표시
        self.classify_and_display_files(files)
        
        # 모든 파일이 준비되었는지 확인
        self.check_and_process()
    
    def parse_drop_data(self, data):
        """드롭 데이터 파싱"""
        files = []
        
        # 중괄호 처리
        if data.startswith('{') and data.endswith('}'):
            data = data[1:-1]
        
        # 공백이 포함된 경로 처리
        import re
        pattern = r'[{"]?([^{"}]+)[}"]?'
        matches = re.findall(pattern, data)
        
        for match in matches:
            if os.path.exists(match):
                files.append(match)
        
        # 그래도 못 찾으면 공백으로 분리
        if not files:
            parts = data.split()
            for part in parts:
                part = part.strip('{}')
                if os.path.exists(part):
                    files.append(part)
        
        return files
    
    def classify_and_display_files(self, files):
        """파일 분류 및 화면 표시"""
        for file_path in files:
            if not file_path:
                continue
            
            ext = Path(file_path).suffix.lower()
            filename = os.path.basename(file_path)
            
            # 처리 규칙 적용
            action = self.processor.apply_processing_rules(file_path)
            if action:
                self.progress_label.config(text=f"규칙 적용: {action}")
            
            # 파일 분류
            if ext == '.pdf':
                if '의뢰서' in filename:
                    self.dropped_files['order_pdf'] = file_path
                    self.processor.dropped_files['order_pdf'] = file_path
                else:
                    self.dropped_files['print_pdf'] = file_path
                    self.processor.dropped_files['print_pdf'] = file_path
            elif ext in ['.jpg', '.jpeg', '.png']:
                self.dropped_files['qr_image'] = file_path
                self.processor.dropped_files['qr_image'] = file_path
        
        # 파일 목록 업데이트
        self.update_file_list()
    
    def update_file_list(self):
        """파일 목록 표시 업데이트"""
        # 기존 위젯 제거
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()
        
        # 파일 정보 표시
        file_info = []
        
        if self.dropped_files['order_pdf']:
            file_info.append(f"📄 의뢰서: {os.path.basename(self.dropped_files['order_pdf'])}")
        
        if self.dropped_files['print_pdf']:
            file_info.append(f"📄 인쇄물: {os.path.basename(self.dropped_files['print_pdf'])}")
        
        if self.dropped_files['qr_image']:
            file_info.append(f"🖼 QR코드: {os.path.basename(self.dropped_files['qr_image'])}")
        
        # 라벨 생성
        for info in file_info:
            label = tk.Label(
                self.file_list_frame,
                text=info,
                font=("맑은 고딕", 9),
                bg="#f0f0f0",
                anchor="w"
            )
            label.pack(fill=tk.X, pady=2)
        
        # 상태 업데이트
        ready_count = sum(1 for v in self.dropped_files.values() if v)
        self.status_label.config(text=f"파일 {ready_count}/3개 준비됨")
    
    def check_and_process(self):
        """파일 준비 확인 및 자동 처리"""
        # 최소 2개 파일 필요 (의뢰서 + (인쇄물 또는 QR))
        if self.dropped_files['order_pdf'] and \
           (self.dropped_files['print_pdf'] or self.dropped_files['qr_image']):
            
            # 자동 처리 시작
            self.process_files()
    
    def process_files(self):
        """파일 처리"""
        try:
            self.status_label.config(text="처리 중...")
            self.progress_label.config(text="파일을 처리하고 있습니다...")
            self.root.update()
            
            # 향상된 처리 실행
            success = self.processor.process_files_enhanced()
            
            if success:
                self.status_label.config(text="✓ 완료되었습니다!", fg="green")
                self.progress_label.config(text="모든 처리가 성공적으로 완료되었습니다")
                messagebox.showinfo("완료", "파일 처리가 완료되었습니다!")
                
                # 자동 초기화 (선택적)
                if messagebox.askyesno("초기화", "파일 목록을 초기화하시겠습니까?"):
                    self.reset_files()
            else:
                self.status_label.config(text="✗ 처리 실패", fg="red")
                self.progress_label.config(text="오류가 발생했습니다")
                messagebox.showerror("오류", "파일 처리 중 오류가 발생했습니다.")
                
        except Exception as e:
            self.status_label.config(text="✗ 오류 발생", fg="red")
            self.progress_label.config(text=str(e))
            messagebox.showerror("오류", f"처리 중 오류가 발생했습니다:\n{str(e)}")
    
    def reset_files(self):
        """파일 목록 초기화"""
        self.dropped_files = {
            'order_pdf': None,
            'print_pdf': None,
            'qr_image': None
        }
        self.processor.dropped_files = {
            'order_pdf': None,
            'print_pdf': None,
            'qr_image': None
        }
        
        # 화면 초기화
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()
        
        self.status_label.config(text="대기 중...", fg="#666666")
        self.progress_label.config(text="")
        self.drop_label.config(text="파일을 여기에 드롭하세요")
        
        # 캐시 비우기 (선택적)
        if hasattr(self.processor, 'clear_cache'):
            self.processor.clear_cache()
    
    def open_enhanced_settings(self):
        """고급 설정 창 열기"""
        settings_window = EnhancedSettingsGUI(parent=self)
        self.root.wait_window(settings_window.window)
    
    def open_basic_settings(self):
        """기본 위치 설정 창 열기"""
        # 고급 설정과 동일한 창 사용 (통합됨)
        self.open_enhanced_settings()
    
    def reload_enhanced_settings(self):
        """향상된 설정 다시 로드"""
        self.processor.settings = self.processor.load_enhanced_settings()
        print("향상된 설정이 다시 로드되었습니다.")
        
        # 성능 설정 적용
        if self.processor.settings["performance"]["multithreading"]:
            from concurrent.futures import ThreadPoolExecutor
            self.processor.executor = ThreadPoolExecutor(
                max_workers=self.processor.settings["performance"]["max_concurrent_files"]
            )
    
    def run(self):
        """프로그램 실행"""
        self.root.mainloop()


def main():
    """메인 함수"""
    import sys
    import argparse
    
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description='인쇄 자동화 시스템')
    parser.add_argument('--cli', action='store_true', help='CLI 모드로 실행')
    parser.add_argument('--settings', action='store_true', help='설정 창만 열기')
    parser.add_argument('files', nargs='*', help='처리할 파일들')
    
    args = parser.parse_args()
    
    # CLI 모드
    if args.cli:
        if len(args.files) < 2:
            print("오류: 최소 2개 파일이 필요합니다 (의뢰서 PDF + 썸네일/QR)")
            sys.exit(1)
        
        # 파일 분류
        order_pdf = None
        print_pdf = None
        qr_image = None
        
        for file_path in args.files:
            if file_path.lower().endswith('.pdf'):
                if '의뢰서' in file_path:
                    order_pdf = file_path
                else:
                    print_pdf = file_path
            elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                qr_image = file_path
        
        if not order_pdf:
            print("오류: 의뢰서 PDF가 없습니다")
            sys.exit(1)
        
        if not print_pdf and not qr_image:
            print("오류: 썸네일 PDF 또는 QR 이미지가 필요합니다")
            sys.exit(1)
        
        # 직접 처리 (GUI 없이)
        try:
            from print_processor import EnhancedPrintProcessor
            processor = EnhancedPrintProcessor()
            result = processor.process_files_direct(order_pdf, print_pdf, qr_image)
            if result:
                print("처리 완료")
                sys.exit(0)
            else:
                print("처리 실패")
                sys.exit(1)
        except Exception as e:
            print(f"오류: {e}")
            sys.exit(1)
    
    # 설정 모드
    elif args.settings:
        try:
            from settings_gui import EnhancedSettingsGUI
            settings_app = EnhancedSettingsGUI()
            settings_app.run()
        except ImportError as e:
            print(f"설정 모듈을 찾을 수 없습니다: {e}")
            sys.exit(1)
    
    # GUI 모드 (기본)
    else:
        # 의존성 확인
        try:
            import tkinterdnd2
            import fitz
            from PIL import Image
            import numpy
        except ImportError as e:
            print(f"필요한 패키지가 설치되지 않았습니다: {e}")
            print("\n다음 명령으로 설치하세요:")
            print("pip install tkinterdnd2 PyMuPDF Pillow numpy")
            input("\n엔터를 눌러 종료하세요...")
            return
        
        # GUI 실행
        app = PrintAutomationGUI()
        app.run()


if __name__ == "__main__":
    main()