"""메인 드래그앤드롭 윈도우"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
from pathlib import Path
import os

from config.constants import (
    WINDOW_TITLE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    DROP_ZONE_HEIGHT, COLORS, MESSAGES
)
from config.settings_manager import SettingsManager
from core.pdf_processor import PDFProcessor
from utils.file_classifier import FileClassifier
from utils.logger import setup_logger
from .settings_window import SettingsWindow

class MainWindow:
    """드래그앤드롭 메인 윈도우"""
    
    def __init__(self):
        """메인 윈도우 초기화"""
        self.root = TkinterDnD.Tk()
        self.logger = setup_logger(self.__class__.__name__)
        self.settings_manager = SettingsManager()
        self.file_classifier = FileClassifier()
        
        # 파일 정보
        self.files = {
            'order_pdf': None,
            'print_pdf': None,
            'qr_image': None
        }
        
        # 처리 상태
        self.processing = False
        
        self.setup_ui()
        self.setup_drag_drop()
    
    def setup_ui(self):
        """UI 구성"""
        # 윈도우 설정
        self.root.title(WINDOW_TITLE)
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # 윈도우 중앙 배치
        self.center_window()
        
        # 스타일 설정
        self.setup_styles()
        
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목
        title_label = ttk.Label(
            main_frame, 
            text="PDF 인쇄 의뢰서 자동화 시스템",
            font=('맑은 고딕', 16, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 드롭 영역
        self.drop_frame = tk.Frame(
            main_frame,
            bg=COLORS['background'],
            relief=tk.RIDGE,
            borderwidth=2,
            height=DROP_ZONE_HEIGHT
        )
        self.drop_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.drop_label = tk.Label(
            self.drop_frame,
            text=MESSAGES['drop_zone'],
            bg=COLORS['background'],
            fg=COLORS['text'],
            font=('맑은 고딕', 12),
            height=10
        )
        self.drop_label.pack(expand=True, fill='both')
        
        # 파일 목록 프레임
        files_frame = ttk.LabelFrame(main_frame, text="선택된 파일", padding="10")
        files_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # 파일 라벨들
        self.file_labels = {}
        file_types = [
            ('의뢰서 PDF:', 'order_pdf'),
            ('인쇄 PDF:', 'print_pdf'),
            ('QR 이미지:', 'qr_image')
        ]
        
        for i, (label_text, file_type) in enumerate(file_types):
            ttk.Label(files_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, pady=2)
            self.file_labels[file_type] = ttk.Label(files_frame, text="선택 안됨", foreground='gray')
            self.file_labels[file_type].grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        # 파일 선택 버튼
        self.select_btn = ttk.Button(
            button_frame,
            text="파일 선택",
            command=self.select_files,
            width=15
        )
        self.select_btn.grid(row=0, column=0, padx=5)
        
        # 처리 버튼
        self.process_btn = ttk.Button(
            button_frame,
            text="처리 시작",
            command=self.process_files,
            width=15,
            state='disabled'
        )
        self.process_btn.grid(row=0, column=1, padx=5)
        
        # 설정 버튼
        self.settings_btn = ttk.Button(
            button_frame,
            text="설정",
            command=self.open_settings,
            width=15
        )
        self.settings_btn.grid(row=0, column=2, padx=5)
        
        # 초기화 버튼
        self.clear_btn = ttk.Button(
            button_frame,
            text="초기화",
            command=self.clear_files,
            width=15
        )
        self.clear_btn.grid(row=0, column=3, padx=5)
        
        # 진행 표시줄
        self.progress = ttk.Progressbar(
            main_frame,
            mode='indeterminate',
            length=400
        )
        self.progress.grid(row=4, column=0, columnspan=2, pady=10)
        
        # 상태 라벨
        self.status_label = ttk.Label(
            main_frame,
            text="파일을 드래그하거나 선택하세요",
            font=('맑은 고딕', 10)
        )
        self.status_label.grid(row=5, column=0, columnspan=2)
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
    
    def setup_styles(self):
        """스타일 설정"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 버튼 스타일
        style.configure('TButton', font=('맑은 고딕', 10))
        style.map('TButton',
                 background=[('active', COLORS['primary'])])
        
        # 라벨 스타일
        style.configure('TLabel', font=('맑은 고딕', 10))
        style.configure('TLabelframe.Label', font=('맑은 고딕', 10, 'bold'))
    
    def setup_drag_drop(self):
        """드래그앤드롭 설정"""
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        self.drop_frame.dnd_bind('<<DragEnter>>', self.on_drag_enter)
        self.drop_frame.dnd_bind('<<DragLeave>>', self.on_drag_leave)
    
    def on_drop(self, event):
        """드래그앤드롭 이벤트 처리"""
        if self.processing:
            return
        
        # 파일 경로 파싱
        files = self.parse_dropped_files(event.data)
        
        if files:
            self.logger.info(f"드롭된 파일: {files}")
            self.classify_and_display_files(files)
        
        # 드롭 영역 스타일 복원
        self.drop_frame.configure(bg=COLORS['background'])
    
    def on_drag_enter(self, event):
        """드래그 진입 이벤트"""
        if not self.processing:
            self.drop_frame.configure(bg='#E0E0E0')
    
    def on_drag_leave(self, event):
        """드래그 이탈 이벤트"""
        self.drop_frame.configure(bg=COLORS['background'])
    
    def parse_dropped_files(self, data: str) -> list:
        """드롭된 파일 경로 파싱"""
        files = []
        
        # 중괄호로 묶인 경로 처리 (공백 포함 경로)
        if '{' in data:
            import re
            pattern = r'\{([^}]+)\}'
            matches = re.findall(pattern, data)
            files.extend(matches)
        
        # 일반 경로 처리
        for item in data.split():
            if item and '{' not in item:
                files.append(item)
        
        # 경로 정리
        cleaned_files = []
        for file in files:
            file = file.strip().strip('"').strip("'")
            if file and os.path.exists(file):
                cleaned_files.append(file)
        
        return cleaned_files
    
    def classify_and_display_files(self, files: list):
        """파일 분류 및 표시"""
        # 파일 분류
        classified = self.file_classifier.classify(files)
        
        # 파일 정보 업데이트
        self.files['order_pdf'] = classified.order_pdf
        self.files['print_pdf'] = classified.print_pdf
        self.files['qr_image'] = classified.qr_image
        
        # UI 업데이트
        self.update_file_labels()
        
        # 처리 버튼 활성화 여부
        if classified.is_valid():
            self.process_btn.configure(state='normal')
            self.status_label.configure(text="처리 준비 완료")
        else:
            self.process_btn.configure(state='disabled')
            error = classified.get_error()
            self.status_label.configure(text=error or "파일을 더 선택하세요")
        
        # 알 수 없는 파일 경고
        if classified.unknown_files:
            self.logger.warning(f"인식되지 않은 파일: {classified.unknown_files}")
    
    def update_file_labels(self):
        """파일 라벨 업데이트"""
        for file_type, label in self.file_labels.items():
            file_path = self.files.get(file_type)
            if file_path:
                filename = Path(file_path).name
                label.configure(text=filename, foreground='black')
            else:
                label.configure(text="선택 안됨", foreground='gray')
    
    def select_files(self):
        """파일 선택 대화상자"""
        if self.processing:
            return
        
        files = filedialog.askopenfilenames(
            title="파일 선택 (의뢰서 PDF, 인쇄 PDF, QR 이미지)",
            filetypes=[
                ("모든 파일", "*.*"),
                ("PDF 파일", "*.pdf"),
                ("이미지 파일", "*.png *.jpg *.jpeg *.bmp")
            ]
        )
        
        if files:
            self.classify_and_display_files(list(files))
    
    def process_files(self):
        """파일 처리 시작"""
        if self.processing:
            return
        
        # 파일 확인
        if not self.files['order_pdf'] or not self.files['print_pdf']:
            messagebox.showwarning("경고", "필수 파일을 모두 선택해주세요")
            return
        
        # 확인 대화상자 (설정에 따라)
        if self.settings_manager.get('ui.confirm_before_process', False):
            if not messagebox.askyesno("확인", "PDF 처리를 시작하시겠습니까?"):
                return
        
        # 처리 시작
        self.processing = True
        self.process_btn.configure(state='disabled')
        self.select_btn.configure(state='disabled')
        self.clear_btn.configure(state='disabled')
        self.progress.start(10)
        self.status_label.configure(text=MESSAGES['processing'])
        
        # 별도 스레드에서 처리
        thread = threading.Thread(target=self._process_in_thread)
        thread.daemon = True
        thread.start()
    
    def _process_in_thread(self):
        """별도 스레드에서 PDF 처리"""
        try:
            # PDF 처리
            processor = PDFProcessor(self.settings_manager)
            success = processor.process_files(
                self.files['order_pdf'],
                self.files['print_pdf'],
                self.files.get('qr_image')
            )
            
            # UI 업데이트 (메인 스레드에서)
            self.root.after(0, self._processing_complete, success)
            
        except Exception as e:
            self.logger.error(f"처리 중 오류: {e}", exc_info=True)
            self.root.after(0, self._processing_complete, False, str(e))
    
    def _processing_complete(self, success: bool, error: str = None):
        """처리 완료 처리"""
        self.processing = False
        self.progress.stop()
        self.process_btn.configure(state='normal')
        self.select_btn.configure(state='normal')
        self.clear_btn.configure(state='normal')
        
        if success:
            self.status_label.configure(text=MESSAGES['success'])
            messagebox.showinfo("완료", "PDF 처리가 완료되었습니다!")
            
            # 파일 초기화 (선택적)
            if self.settings_manager.get('ui.auto_clear_after_process', True):
                self.clear_files()
        else:
            error_msg = MESSAGES['error'].format(error=error or "알 수 없는 오류")
            self.status_label.configure(text=error_msg)
            messagebox.showerror("오류", error_msg)
    
    def clear_files(self):
        """파일 초기화"""
        self.files = {
            'order_pdf': None,
            'print_pdf': None,
            'qr_image': None
        }
        self.update_file_labels()
        self.process_btn.configure(state='disabled')
        self.status_label.configure(text="파일을 드래그하거나 선택하세요")
    
    def open_settings(self):
        """설정 창 열기"""
        settings_window = SettingsWindow(self.root)
        settings_window.run()
        
        # 설정 변경 후 재로드
        self.settings_manager.load()
    
    def center_window(self):
        """윈도우를 화면 중앙에 배치"""
        self.root.update_idletasks()
        
        # 화면 크기
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 윈도우 크기
        window_width = WINDOW_MIN_WIDTH
        window_height = WINDOW_MIN_HEIGHT
        
        # 중앙 위치 계산
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def run(self):
        """메인 루프 실행"""
        self.logger.info("GUI 시작")
        
        # 항상 위 설정
        if self.settings_manager.get('ui.window_always_on_top', True):
            self.root.attributes('-topmost', True)
        
        self.root.mainloop()