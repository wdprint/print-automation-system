"""현대적인 메인 드래그앤드롭 윈도우 - 다크 테마"""

import tkinter as tk
from tkinter import messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
from pathlib import Path
import os
from typing import Dict, Optional

from config.settings_manager import SettingsManager
from config.preset_manager import PresetManager
from core.pdf_processor import PDFProcessor
from utils.file_classifier import FileClassifier
from utils.logger import setup_logger
from .modern_settings import ModernSettingsWindow

class ModernMainWindow:
    """현대적인 드래그앤드롭 메인 윈도우"""
    
    def __init__(self):
        """메인 윈도우 초기화"""
        self.root = TkinterDnD.Tk()
        self.logger = setup_logger(self.__class__.__name__)
        self.settings_manager = SettingsManager()
        self.preset_manager = PresetManager()
        self.file_classifier = FileClassifier()
        
        # 세련된 라이트 테마
        self.colors = {
            'bg': '#fafafa',           # 배경 - 매우 연한 회색
            'card': '#ffffff',          # 카드 - 흰색
            'accent': '#2196F3',        # 강조 - 밝은 파란색
            'success': '#66BB6A',       # 성공 - 부드러운 녹색
            'warning': '#FFA726',       # 경고 - 부드러운 주황색
            'error': '#EF5350',         # 오류 - 부드러운 빨간색
            'text': '#424242',          # 텍스트 - 진한 회색
            'subtext': '#9E9E9E',       # 서브텍스트 - 중간 회색
            'border': '#E8E8E8',        # 테두리 - 매우 연한 회색
            'hover': '#F0F0F0',         # 호버 - 연한 회색
            'drop_zone': '#FAFAFA',     # 드롭존 - 매우 연한 배경
            'drop_zone_hover': '#E3F2FD'  # 드롭존 호버 - 연한 파랑
        }
        
        # 파일 정보
        self.files: Dict[str, Optional[str]] = {
            'order_pdf': None,
            'print_pdfs': [],  # 여러 PDF 파일 지원
            'qr_image': None
        }
        
        # 처리 상태
        self.processing = False
        self.progress_value = 0
        
        # 킬스위치 타이머 (6초)
        self.killswitch_timer = None
        self.killswitch_delay = 6000  # 6초 (밀리초)
        
        self.setup_ui()
        self.setup_drag_drop()
        self.animate_startup()
    
    def setup_ui(self):
        """UI 구성"""
        # 윈도우 설정
        self.root.title("PDF 인쇄 의뢰서 자동화 시스템")
        self.root.geometry("800x600")
        self.root.configure(bg=self.colors['bg'])
        
        # 윈도우 스타일
        self.root.resizable(True, True)
        self.root.minsize(700, 500)
        
        # 중앙 배치
        self.center_window()
        
        # 메인 컨테이너
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True)
        
        # 헤더
        self.create_header(main_container)
        
        # 드롭 영역
        self.create_drop_zone(main_container)
        
        # 파일 카드들
        self.create_file_cards(main_container)
        
        # 액션 버튼들
        self.create_action_buttons(main_container)
        
        # 상태 바
        self.create_status_bar(main_container)
    
    def create_header(self, parent):
        """헤더 생성"""
        header = tk.Frame(parent, bg=self.colors['bg'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        # 메인 헤더 컨테이너 (좌중우 레이아웃)
        header_container = tk.Frame(header, bg=self.colors['bg'])
        header_container.pack(fill='both', expand=True, padx=20)
        
        # 왼쪽: 로고/타이틀 영역
        title_frame = tk.Frame(header_container, bg=self.colors['bg'])
        title_frame.pack(side='left', fill='y')
        
        title_inner = tk.Frame(title_frame, bg=self.colors['bg'])
        title_inner.pack(expand=True)
        
        # 아이콘
        icon_label = tk.Label(
            title_inner,
            text="📄",
            font=('Segoe UI Emoji', 32),
            bg=self.colors['bg'],
            fg=self.colors['accent']
        )
        icon_label.pack(side='left', padx=(0, 15))
        
        # 타이틀
        title = tk.Label(
            title_inner,
            text="PDF 인쇄 의뢰서 자동화",
            font=('맑은 고딕', 18),  # 폰트 크기 줄임, 굵기 제거
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        title.pack(side='left')
        
        # 서브타이틀
        subtitle = tk.Label(
            title_inner,
            text="v2.0",
            font=('맑은 고딕', 10),
            bg=self.colors['bg'],
            fg=self.colors['subtext']
        )
        subtitle.pack(side='left', padx=(10, 0))
        
        # 오른쪽: 현재 프리셋 표시
        preset_frame = tk.Frame(header_container, bg=self.colors['bg'])
        preset_frame.pack(side='right', fill='y', padx=(20, 0))
        
        preset_inner = tk.Frame(preset_frame, bg=self.colors['card'], 
                                highlightthickness=1,
                                highlightbackground=self.colors['border'])
        preset_inner.pack(expand=True)
        
        # 프리셋 레이블
        preset_label = tk.Label(
            preset_inner,
            text="현재 프리셋",
            font=('맑은 고딕', 9),
            bg=self.colors['card'],
            fg=self.colors['subtext']
        )
        preset_label.pack(padx=15, pady=(8, 2))
        
        # 현재 프리셋 이름 표시
        current_preset = self.preset_manager.presets.get(self.preset_manager.current_preset, {})
        preset_name = current_preset.get('name', '기본')
        preset_hotkey = current_preset.get('hotkey', 'F1')
        
        self.preset_name_label = tk.Label(
            preset_inner,
            text=f"{preset_name}",
            font=('맑은 고딕', 12, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['accent']
        )
        self.preset_name_label.pack(padx=15, pady=(0, 2))
        
        # 프리셋 단축키 표시
        self.preset_hotkey_label = tk.Label(
            preset_inner,
            text=f"[{preset_hotkey}]",
            font=('맑은 고딕', 9),
            bg=self.colors['card'],
            fg=self.colors['subtext']
        )
        self.preset_hotkey_label.pack(padx=15, pady=(0, 8))
        
        # 프리셋 변경 버튼
        change_preset_btn = tk.Button(
            preset_inner,
            text="변경",
            font=('맑은 고딕', 9),
            bg=self.colors['accent'],
            fg='white',
            bd=0,
            padx=10,
            pady=3,
            cursor='hand2',
            command=self.open_preset_selector
        )
        change_preset_btn.pack(pady=(0, 8))
    
    def create_drop_zone(self, parent):
        """드롭 영역 생성"""
        # 드롭 영역 컨테이너
        drop_container = tk.Frame(parent, bg=self.colors['bg'])
        drop_container.pack(fill='both', expand=True, padx=40, pady=(0, 20))
        
        # 드롭 영역
        self.drop_frame = tk.Frame(
            drop_container,
            bg=self.colors['drop_zone'],
            highlightthickness=2,
            highlightbackground=self.colors['border'],
            highlightcolor=self.colors['accent']
        )
        self.drop_frame.pack(fill='both', expand=True)
        
        # 드롭 영역 콘텐츠
        drop_content = tk.Frame(self.drop_frame, bg=self.colors['drop_zone'])
        drop_content.place(relx=0.5, rely=0.5, anchor='center')
        
        # 드롭 아이콘
        self.drop_icon = tk.Label(
            drop_content,
            text="⬇",
            font=('Segoe UI Emoji', 48),
            bg=self.colors['drop_zone'],
            fg=self.colors['subtext']
        )
        self.drop_icon.pack()
        
        # 드롭 텍스트
        self.drop_text = tk.Label(
            drop_content,
            text="파일을 여기에 드래그하세요",
            font=('맑은 고딕', 12),
            bg=self.colors['drop_zone'],
            fg=self.colors['text']
        )
        self.drop_text.pack(pady=(10, 5))
        
        # 드롭 서브텍스트
        self.drop_subtext = tk.Label(
            drop_content,
            text="또는 클릭하여 파일 선택",
            font=('맑은 고딕', 10),
            bg=self.colors['drop_zone'],
            fg=self.colors['subtext'],
            cursor='hand2'
        )
        self.drop_subtext.pack()
        
        # 클릭 이벤트
        for widget in [self.drop_frame, drop_content, self.drop_icon, self.drop_text, self.drop_subtext]:
            widget.bind('<Button-1>', lambda e: self.select_files())
    
    def create_file_cards(self, parent):
        """파일 카드 생성"""
        cards_container = tk.Frame(parent, bg=self.colors['bg'])
        cards_container.pack(fill='x', padx=40, pady=(0, 20))
        
        # 카드 정보
        card_info = [
            ('📋', '의뢰서 PDF', 'order_pdf', '#4CAF50'),
            ('🖨️', '인쇄 데이터', 'print_pdf', '#2196F3'),
            ('📱', 'QR 이미지', 'qr_image', '#FF9800')
        ]
        
        self.file_cards = {}
        
        for icon, title, file_type, color in card_info:
            # 카드 프레임
            card = tk.Frame(
                cards_container,
                bg=self.colors['card'],
                highlightthickness=1,
                highlightbackground=self.colors['border']
            )
            card.pack(side='left', fill='both', expand=True, padx=5)
            
            # 카드 내용
            card_content = tk.Frame(card, bg=self.colors['card'])
            card_content.pack(padx=15, pady=15)
            
            # 아이콘
            icon_label = tk.Label(
                card_content,
                text=icon,
                font=('Segoe UI Emoji', 24),
                bg=self.colors['card'],
                fg=color
            )
            icon_label.pack()
            
            # 타이틀
            title_label = tk.Label(
                card_content,
                text=title,
                font=('맑은 고딕', 10),
                bg=self.colors['card'],
                fg=self.colors['text']
            )
            title_label.pack(pady=(5, 2))
            
            # 파일명
            file_label = tk.Label(
                card_content,
                text="선택 안됨",
                font=('맑은 고딕', 9),
                bg=self.colors['card'],
                fg=self.colors['subtext'],
                width=20,
                anchor='center'
            )
            file_label.pack()
            
            # 상태 인디케이터
            status_dot = tk.Label(
                card_content,
                text="●",
                font=('Segoe UI', 8),
                bg=self.colors['card'],
                fg=self.colors['border']
            )
            status_dot.pack(pady=(5, 0))
            
            self.file_cards[file_type] = {
                'card': card,
                'file_label': file_label,
                'status_dot': status_dot,
                'color': color
            }
    
    def create_action_buttons(self, parent):
        """액션 버튼 생성 - 처리 버튼 제거"""
        button_container = tk.Frame(parent, bg=self.colors['bg'])
        button_container.pack(pady=(0, 20))
        
        # 초기화 버튼
        self.clear_btn = self.create_button(
            button_container,
            "↺ 초기화",
            self.clear_files,
            self.colors['warning']
        )
        self.clear_btn.pack(side='left', padx=5)
        
        # 설정 버튼
        self.settings_btn = self.create_button(
            button_container,
            "⚙ 설정",
            self.open_settings,
            self.colors['accent']
        )
        self.settings_btn.pack(side='left', padx=5)
        
        # 정보 레이블 추가
        info_label = tk.Label(
            button_container,
            text="의뢰서 PDF가 들어오면 즉시 처리됩니다",
            font=('맑은 고딕', 9),
            bg=self.colors['bg'],
            fg=self.colors['subtext']
        )
        info_label.pack(side='left', padx=20)
    
    def create_button(self, parent, text, command, color, **kwargs):
        """스타일 버튼 생성"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg='white',
            font=('맑은 고딕', 10),  # 폰트 크기 줄임, 굵기 제거
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            activebackground=color,
            **kwargs
        )
        
        # 호버 효과
        def on_enter(e):
            if btn['state'] != 'disabled':
                btn.configure(bg=self.lighten_color(color))
        
        def on_leave(e):
            if btn['state'] != 'disabled':
                btn.configure(bg=color)
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        return btn
    
    def create_status_bar(self, parent):
        """상태 바 생성"""
        status_bar = tk.Frame(parent, bg=self.colors['card'], height=40)
        status_bar.pack(side='bottom', fill='x')
        status_bar.pack_propagate(False)
        
        # 상태 텍스트
        self.status_label = tk.Label(
            status_bar,
            text="준비됨",
            font=('맑은 고딕', 9),
            bg=self.colors['card'],
            fg=self.colors['text']
        )
        self.status_label.pack(side='left', padx=20, pady=10)
        
        # 프로그레스 바 (처리 중일 때만 표시)
        self.progress_frame = tk.Frame(status_bar, bg=self.colors['card'])
        self.progress_frame.pack(side='right', padx=20, pady=10)
        
        self.progress_bar = None
    
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
        
        # 드롭 애니메이션
        self.drop_frame.configure(bg=self.colors['drop_zone'])
        
        # 파일 경로 파싱
        files = self.parse_dropped_files(event.data)
        
        if files:
            self.logger.info(f"드롭된 파일: {files}")
            self.classify_and_display_files(files)
    
    def on_drag_enter(self, event):
        """드래그 진입 이벤트"""
        if not self.processing:
            self.drop_frame.configure(bg=self.colors['accent'], highlightcolor=self.colors['accent'])
            self.drop_icon.configure(fg=self.colors['accent'])
            self.drop_text.configure(text="놓아주세요!")
    
    def on_drag_leave(self, event):
        """드래그 이탈 이벤트"""
        self.drop_frame.configure(bg=self.colors['drop_zone'], highlightcolor=self.colors['accent'])
        self.drop_icon.configure(fg=self.colors['subtext'])
        self.drop_text.configure(text="파일을 여기에 드래그하세요")
    
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
        """파일 분류 및 표시 - 의뢰서 PDF가 있으면 즉시 처리"""
        # 파일 분류
        classified = self.file_classifier.classify(files)
        
        # 이전에 의뢰서 PDF가 있었는지 확인
        had_order_pdf = self.files.get('order_pdf') is not None
        
        # 파일 정보 업데이트
        if classified.order_pdf:
            self.files['order_pdf'] = classified.order_pdf
        if classified.print_pdfs:  # 여러 PDF 파일
            self.files['print_pdfs'].extend(classified.print_pdfs)
        if classified.qr_image:
            self.files['qr_image'] = classified.qr_image
        
        # UI 업데이트
        self.update_file_cards()
        
        # 킬스위치 타이머 관리
        if self.killswitch_timer:
            # 기존 타이머 취소
            self.root.after_cancel(self.killswitch_timer)
            self.killswitch_timer = None
        
        # 의뢰서 PDF가 새로 추가되었으면 즉시 처리
        if classified.order_pdf and not had_order_pdf:
            self.status_label.configure(text="⏳ 의뢰서 감지 - 1초 후 자동 처리...")
            # 1초 대기 후 처리 (다른 파일들이 들어올 시간을 줄임)
            self.root.after(1000, self.auto_process_files)
        elif self.files.get('order_pdf'):
            # 이미 의뢰서가 있고 추가 파일이 들어온 경우
            self.status_label.configure(text="✅ 의뢰서가 있습니다 - 자동 처리 준비")
            # 바로 처리
            self.root.after(500, self.auto_process_files)
        else:
            # 의뢰서 PDF가 없는 경우
            if self.files.get('print_pdfs') or self.files.get('qr_image'):
                self.status_label.configure(text="⚠ 의뢰서 PDF 대기중 (6초 후 초기화)")
                # 6초 후 리셋
                self.killswitch_timer = self.root.after(self.killswitch_delay, self.killswitch_reset)
            else:
                self.status_label.configure(text="파일을 드래그하세요")
        
        # 알 수 없는 파일 경고
        if classified.unknown_files:
            self.logger.warning(f"인식되지 않은 파일: {classified.unknown_files}")
    
    def killswitch_reset(self):
        """킬스위치 리셋 - 6초 후 의뢰서 PDF가 없으면 초기화"""
        self.killswitch_timer = None
        
        # 의뢰서 PDF가 여전히 없으면 초기화
        if not self.files.get('order_pdf'):
            self.clear_files()
            self.status_label.configure(text="⚠ 의뢰서 PDF가 없어 파일이 초기화되었습니다")
    
    def update_file_cards(self):
        """파일 카드 업데이트"""
        for file_type, card_info in self.file_cards.items():
            if file_type == 'print_pdf':
                # 여러 PDF 파일 처리
                print_pdfs = self.files.get('print_pdfs', [])
                if print_pdfs:
                    if len(print_pdfs) == 1:
                        filename = Path(print_pdfs[0]).name
                    else:
                        filename = f"{len(print_pdfs)}개 PDF 파일"
                    # 파일명이 길면 줄임
                    if len(filename) > 25:
                        filename = filename[:22] + "..."
                    card_info['file_label'].configure(text=filename, fg=self.colors['text'])
                    card_info['status_dot'].configure(fg=card_info['color'])
                    card_info['card'].configure(highlightbackground=card_info['color'])
                else:
                    card_info['file_label'].configure(text="선택 안됨", fg=self.colors['subtext'])
                    card_info['status_dot'].configure(fg=self.colors['border'])
                    card_info['card'].configure(highlightbackground=self.colors['border'])
            else:
                # order_pdf, qr_image 처리
                file_path = self.files.get(file_type)
                if file_path:
                    filename = Path(file_path).name
                    # 파일명이 길면 줄임
                    if len(filename) > 25:
                        filename = filename[:22] + "..."
                    card_info['file_label'].configure(text=filename, fg=self.colors['text'])
                    card_info['status_dot'].configure(fg=card_info['color'])
                    card_info['card'].configure(highlightbackground=card_info['color'])
                else:
                    card_info['file_label'].configure(text="선택 안됨", fg=self.colors['subtext'])
                    card_info['status_dot'].configure(fg=self.colors['border'])
                    card_info['card'].configure(highlightbackground=self.colors['border'])
    
    def select_files(self):
        """파일 선택 대화상자"""
        if self.processing:
            return
        
        files = filedialog.askopenfilenames(
            title="파일 선택",
            filetypes=[
                ("지원 파일", "*.pdf *.png *.jpg *.jpeg"),
                ("PDF 파일", "*.pdf"),
                ("이미지 파일", "*.png *.jpg *.jpeg"),
                ("모든 파일", "*.*")
            ]
        )
        
        if files:
            self.classify_and_display_files(list(files))
    
    def auto_process_files(self):
        """자동 파일 처리 - 의뢰서가 들어오면 바로 처리"""
        if self.processing:
            return
        
        # 최소 요구사항: 의뢰서 PDF만 확인
        if not self.files['order_pdf']:
            self.status_label.configure(text="❌ 의뢰서 PDF가 필요합니다")
            return
        
        # 바로 처리 시작
        self.process_files()
    
    def process_files(self):
        """파일 처리 시작 (내부용)"""
        if self.processing:
            return
        
        # 의뢰서 PDF만 있어도 처리 가능
        if not self.files['order_pdf']:
            return
        
        # 처리 시작
        self.processing = True
        self.clear_btn.configure(state='disabled')
        self.settings_btn.configure(state='disabled')
        
        # 프로그레스 바 표시
        self.show_progress()
        self.status_label.configure(text="⏳ PDF 처리 중...")
        
        # 별도 스레드에서 처리
        thread = threading.Thread(target=self._process_in_thread)
        thread.daemon = True
        thread.start()
    
    def _process_in_thread(self):
        """별도 스레드에서 PDF 처리"""
        try:
            # PDF 처리 (여러 PDF 파일 지원)
            processor = PDFProcessor(self.settings_manager)
            success = processor.process_files(
                self.files['order_pdf'],
                self.files['print_pdfs'],  # 여러 PDF 파일 리스트
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
        self.hide_progress()
        self.clear_btn.configure(state='normal')
        self.settings_btn.configure(state='normal')
        
        if success:
            self.status_label.configure(text="✅ 처리 완료!")
            self.show_success_animation()
            # 알람 제거 - 자동으로 기존 파일 덮어쓰기
            # messagebox.showinfo("완료", "PDF 처리가 완료되었습니다!")
            
            # 파일 초기화 (선택적)
            if self.settings_manager.get('ui.auto_clear_after_process', True):
                self.clear_files()
        else:
            error_msg = f"처리 실패: {error or '알 수 없는 오류'}"
            self.status_label.configure(text=f"❌ {error_msg}")
            messagebox.showerror("오류", error_msg)
    
    def clear_files(self):
        """파일 초기화"""
        self.files = {
            'order_pdf': None,
            'print_pdfs': [],  # 여러 PDF 파일
            'qr_image': None
        }
        self.update_file_cards()
        self.status_label.configure(text="파일을 드래그하세요")
    
    def open_settings(self):
        """설정 창 열기"""
        settings_window = ModernSettingsWindow(self.root)
        settings_window.run()
        
        # 설정 변경 후 재로드
        self.settings_manager.load()
    
    def show_progress(self):
        """프로그레스 바 표시"""
        if not self.progress_bar:
            self.progress_bar = tk.Frame(
                self.progress_frame,
                bg=self.colors['accent'],
                height=4,
                width=0
            )
            self.progress_bar.pack(side='left')
        
        self.animate_progress()
    
    def animate_progress(self):
        """프로그레스 애니메이션"""
        if self.processing:
            self.progress_value = (self.progress_value + 5) % 200
            width = self.progress_value if self.progress_value <= 100 else 200 - self.progress_value
            self.progress_bar.configure(width=width * 2)
            self.root.after(50, self.animate_progress)
    
    def hide_progress(self):
        """프로그레스 바 숨기기"""
        if self.progress_bar:
            self.progress_bar.destroy()
            self.progress_bar = None
        self.progress_value = 0
    
    def show_success_animation(self):
        """성공 애니메이션"""
        # 카드 하이라이트 애니메이션
        for card_info in self.file_cards.values():
            card_info['card'].configure(highlightbackground=self.colors['success'])
        
        self.root.after(2000, lambda: [
            card_info['card'].configure(highlightbackground=self.colors['border'])
            for card_info in self.file_cards.values()
        ])
    
    def animate_startup(self):
        """시작 애니메이션"""
        # 페이드인 효과
        self.root.attributes('-alpha', 0.0)
        self.fade_in()
    
    def fade_in(self, alpha=0.0):
        """페이드인 효과"""
        if alpha < 1.0:
            alpha += 0.05
            self.root.attributes('-alpha', alpha)
            self.root.after(10, lambda: self.fade_in(alpha))
    
    def lighten_color(self, color):
        """색상 밝게 하기"""
        # 간단한 색상 밝기 조정
        if color.startswith('#'):
            # Hex 색상을 밝게
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            
            # 20% 밝게
            r = min(255, int(r * 1.2))
            g = min(255, int(g * 1.2))
            b = min(255, int(b * 1.2))
            
            return f'#{r:02x}{g:02x}{b:02x}'
        return color
    
    def center_window(self):
        """윈도우를 화면 중앙에 배치"""
        self.root.update_idletasks()
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        window_width = 800
        window_height = 600
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def open_preset_selector(self):
        """프리셋 선택 다이얼로그 열기"""
        # 프리셋 선택 창
        dialog = tk.Toplevel(self.root)
        dialog.title("프리셋 선택")
        dialog.geometry("400x350")
        dialog.configure(bg=self.colors['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 중앙 배치
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (350 // 2)
        dialog.geometry(f"400x350+{x}+{y}")
        
        # 타이틀
        title = tk.Label(
            dialog,
            text="프리셋 선택",
            font=('맑은 고딕', 14, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        title.pack(pady=20)
        
        # 프리셋 목록
        presets_frame = tk.Frame(dialog, bg=self.colors['bg'])
        presets_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # 프리셋 버튼들
        for idx in ['1', '2', '3', '4']:
            preset = self.preset_manager.presets.get(idx, {})
            name = preset.get('name', f'프리셋 {idx}')
            hotkey = preset.get('hotkey', f'F{idx}')
            usage = preset.get('usage_count', 0)
            
            # 프리셋 버튼 프레임
            btn_frame = tk.Frame(presets_frame, bg=self.colors['card'], 
                                 highlightthickness=1,
                                 highlightbackground=self.colors['border'])
            btn_frame.pack(fill='x', pady=5)
            
            # 현재 선택된 프리셋이면 강조
            if idx == self.preset_manager.current_preset:
                btn_frame.configure(highlightbackground=self.colors['accent'],
                                   highlightthickness=2)
            
            # 버튼 내용
            btn_content = tk.Frame(btn_frame, bg=self.colors['card'])
            btn_content.pack(fill='x', padx=10, pady=8)
            
            # 왼쪽: 프리셋 정보
            info_frame = tk.Frame(btn_content, bg=self.colors['card'])
            info_frame.pack(side='left', fill='x', expand=True)
            
            name_label = tk.Label(
                info_frame,
                text=f"{name}",
                font=('맑은 고딕', 11, 'bold'),
                bg=self.colors['card'],
                fg=self.colors['text'],
                anchor='w'
            )
            name_label.pack(fill='x')
            
            detail_label = tk.Label(
                info_frame,
                text=f"{hotkey} | 사용: {usage}회",
                font=('맑은 고딕', 9),
                bg=self.colors['card'],
                fg=self.colors['subtext'],
                anchor='w'
            )
            detail_label.pack(fill='x')
            
            # 오른쪽: 선택 버튼
            select_btn = tk.Button(
                btn_content,
                text="선택",
                font=('맑은 고딕', 9),
                bg=self.colors['accent'],
                fg='white',
                bd=0,
                padx=15,
                pady=5,
                cursor='hand2',
                command=lambda p=idx: self.select_preset(p, dialog)
            )
            select_btn.pack(side='right')
        
        # 닫기 버튼
        close_btn = tk.Button(
            dialog,
            text="닫기",
            font=('맑은 고딕', 10),
            bg=self.colors['hover'],
            fg=self.colors['text'],
            bd=0,
            padx=20,
            pady=5,
            cursor='hand2',
            command=dialog.destroy
        )
        close_btn.pack(pady=(0, 20))
    
    def select_preset(self, preset_id, dialog):
        """프리셋 선택 및 적용"""
        try:
            # 프리셋 전환
            self.preset_manager.quick_switch(int(preset_id))
            
            # UI 업데이트
            self.update_preset_display()
            
            # 다이얼로그 닫기
            dialog.destroy()
            
            # 성공 메시지
            preset = self.preset_manager.presets.get(preset_id, {})
            name = preset.get('name', f'프리셋 {preset_id}')
            self.update_status(f"프리셋 '{name}' 적용됨", 'success')
            
        except Exception as e:
            self.logger.error(f"프리셋 선택 실패: {e}")
            messagebox.showerror("오류", f"프리셋 선택 실패: {e}")
    
    def update_preset_display(self):
        """현재 프리셋 표시 업데이트"""
        try:
            current_preset = self.preset_manager.presets.get(self.preset_manager.current_preset, {})
            preset_name = current_preset.get('name', '기본')
            preset_hotkey = current_preset.get('hotkey', 'F1')
            
            # 레이블 업데이트
            if hasattr(self, 'preset_name_label'):
                self.preset_name_label.config(text=preset_name)
            if hasattr(self, 'preset_hotkey_label'):
                self.preset_hotkey_label.config(text=f"[{preset_hotkey}]")
            
        except Exception as e:
            self.logger.error(f"프리셋 표시 업데이트 실패: {e}")
    
    def run(self):
        """메인 루프 실행"""
        self.logger.info("Modern GUI 시작")
        
        # 항상 위 설정
        if self.settings_manager.get('ui.window_always_on_top', False):
            self.root.attributes('-topmost', True)
        
        self.root.mainloop()