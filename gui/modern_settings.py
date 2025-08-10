"""현대적인 설정 창 - 다크 테마 Material Design"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import copy
from pathlib import Path

from config.settings_manager import SettingsManager
from config.preset_manager import PresetManager
from config.constants import COLORS
from utils.logger import setup_logger
from .coordinate_preview import CoordinatePreview

class ModernSettingsWindow:
    """현대적인 설정 관리 윈도우"""
    
    def __init__(self, parent=None):
        """설정 윈도우 초기화"""
        self.parent = parent
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.logger = setup_logger(self.__class__.__name__)
        self.settings_manager = SettingsManager()
        self.preset_manager = PresetManager()
        
        # coord_vars 초기화 (좌표 입력 필드용)
        self.coord_vars = {}
        
        # 통일된 밝은 테마
        self.colors = {
            'bg': '#f5f5f5',           # 밝은 회색 배경
            'sidebar': '#ffffff',       # 흰색 사이드바
            'card': '#ffffff',          # 흰색 카드
            'accent': '#2196F3',        # 파란색 (coordinate_preview와 통일)
            'success': '#66BB6A',       # 녹색 (coordinate_preview와 통일)
            'warning': '#FFA726',       # 주황색 (coordinate_preview와 통일)
            'error': '#EF5350',         # 빨간색
            'text': '#424242',          # 어두운 회색 텍스트 (coordinate_preview와 통일)
            'subtext': '#9E9E9E',       # 중간 회색 (coordinate_preview와 통일)
            'border': '#E0E0E0',        # 연한 회색 테두리
            'hover': '#F5F5F5',         # 호버 색상
            'input_bg': '#ffffff',      # 입력 필드 배경
            'input_border': '#BDBDBD',  # 입력 필드 테두리
            'thumbnail': '#66BB6A',     # 썸네일 색상 (coordinate_preview와 통일)
            'qr': '#FFA726'            # QR 색상 (coordinate_preview와 통일)
        }
        
        # 변경 사항 추적
        self.changes_made = False
        
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """UI 구성"""
        # 윈도우 설정 - 크기 확대
        self.window.title("⚙️ 설정")
        self.window.geometry("1400x800")
        self.window.configure(bg=self.colors['bg'])
        
        # 윈도우 중앙 배치
        self.center_window()
        
        # 메인 컨테이너
        main_container = tk.Frame(self.window, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True)
        
        # 사이드바
        self.create_sidebar(main_container)
        
        # 컨텐츠 영역
        self.content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        self.content_frame.pack(side='right', fill='both', expand=True)
        
        # 기본 페이지 표시
        self.show_coordinates_page()
        
        # 하단 버튼 바
        self.create_bottom_bar()
    
    def create_sidebar(self, parent):
        """사이드바 생성 - 개선된 디자인"""
        sidebar = tk.Frame(parent, bg='#ffffff', width=280)  # 흰색 배경, 너비 증가
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        
        # 타이틀 섹션
        title_section = tk.Frame(sidebar, bg=self.colors['accent'], height=65)
        title_section.pack(fill='x')
        title_section.pack_propagate(False)
        
        title_container = tk.Frame(title_section, bg=self.colors['accent'])
        title_container.place(relx=0.5, rely=0.5, anchor='center')
        
        title = tk.Label(
            title_container,
            text="⚙  설정 메뉴",
            font=('맑은 고딕', 13),
            bg=self.colors['accent'],
            fg='white'
        )
        title.pack()
        
        # 구분선
        tk.Frame(sidebar, bg='#e0e0e0', height=1).pack(fill='x')
        
        # 메뉴 섹션
        menu_section = tk.Frame(sidebar, bg='#ffffff')
        menu_section.pack(fill='both', expand=True, pady=(15, 0))
        
        # 메뉴 아이템들 (설명 추가)
        menu_items = [
            ("📍  좌표 설정", self.show_coordinates_page, "썸네일과 QR 위치 조정"),
            ("🎨  이미지 효과", self.show_effects_page, "대비, 선명도, 밝기 조정"),
            ("📄  백지 감지", self.show_blank_detection_page, "빈 페이지 자동 건너뛰기"),
            ("⚡  성능 최적화", self.show_performance_page, "처리 속도 설정"),
            ("🎯  프리셋 관리", self.show_presets_page, "빠른 설정 저장"),
            ("🔧  고급 설정", self.show_advanced_page, "추가 옵션")
        ]
        
        self.menu_buttons = []
        self.menu_widgets = []  # 모든 메뉴 위젯 정보 저장
        
        for idx, (text, command, desc) in enumerate(menu_items):
            # 메뉴 항목 컨테이너 (Frame으로 클릭 가능하게)
            item_frame = tk.Frame(menu_section, bg='#ffffff', height=70)
            item_frame.pack(fill='x', pady=1)
            item_frame.pack_propagate(False)  # 크기 고정
            
            # 내부 컨테이너 (여백을 위해)
            inner_frame = tk.Frame(item_frame, bg='#ffffff')
            inner_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            
            # 텍스트 컨테이너
            text_container = tk.Frame(inner_frame, bg='#ffffff')
            text_container.pack(fill='both', expand=True, padx=20, pady=12)
            
            # 메인 텍스트
            main_text = tk.Label(
                text_container,
                text=text,
                font=('맑은 고딕', 11),
                bg='#ffffff',
                fg='#424242',
                anchor='w'
            )
            main_text.pack(fill='x')
            
            # 설명 텍스트
            desc_text = tk.Label(
                text_container,
                text=desc,
                font=('맑은 고딕', 8),
                bg='#ffffff',
                fg='#9E9E9E',
                anchor='w'
            )
            desc_text.pack(fill='x', pady=(2, 0))
            
            # 위젯 정보 저장
            widget_info = {
                'item_frame': item_frame,
                'inner_frame': inner_frame,
                'text_container': text_container,
                'main_text': main_text,
                'desc_text': desc_text,
                'command': command,
                'index': idx
            }
            
            # 클릭 및 호버 이벤트 바인딩
            def make_click_handler(cmd):
                return lambda e: cmd()
            
            def make_hover_handler(idx, hover):
                return lambda e: self._on_menu_hover(idx, hover)
            
            # 모든 위젯에 이벤트 바인딩
            widgets = [item_frame, inner_frame, text_container, main_text, desc_text]
            for widget in widgets:
                widget.bind('<Button-1>', make_click_handler(command))
                widget.bind('<Enter>', make_hover_handler(idx, True))
                widget.bind('<Leave>', make_hover_handler(idx, False))
                widget.configure(cursor='hand2')
            
            self.menu_buttons.append(item_frame)
            self.menu_widgets.append(widget_info)
    
    def _on_menu_hover(self, index, is_hover):
        """메뉴 호버 효과"""
        if index >= len(self.menu_widgets):
            return
            
        widget_info = self.menu_widgets[index]
        
        # 현재 활성 메뉴인지 확인
        is_active = hasattr(self, 'active_menu_index') and self.active_menu_index == index
        
        if is_active:
            # 활성 메뉴는 호버 효과 없음
            return
            
        # 호버 색상 설정
        if is_hover:
            bg_color = self.colors['hover']
        else:
            bg_color = '#ffffff'
        
        # 모든 관련 위젯의 배경색 변경
        try:
            widget_info['item_frame'].configure(bg=bg_color)
            widget_info['inner_frame'].configure(bg=bg_color)
            widget_info['text_container'].configure(bg=bg_color)
            widget_info['main_text'].configure(bg=bg_color)
            widget_info['desc_text'].configure(bg=bg_color)
        except:
            pass
    
    def show_coordinates_page(self):
        """좌표 설정 페이지"""
        self.clear_content()
        self.set_active_menu(0)
        
        # 페이지 타이틀
        title_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        title_frame.pack(fill='x', padx=30, pady=(20, 10))
        
        tk.Label(
            title_frame,
            text="좌표 설정",
            font=('Segoe UI', 16, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text']
        ).pack(side='left')
        
        tk.Label(
            title_frame,
            text="썸네일과 QR 코드의 위치를 설정합니다",
            font=('Segoe UI', 10),
            bg=self.colors['bg'],
            fg=self.colors['subtext']
        ).pack(side='left', padx=(20, 0))
        
        # PDF 로드 버튼 추가
        load_btn = tk.Button(
            title_frame,
            text="📄 PDF 불러오기",
            command=self.load_pdf_for_preview,
            bg=self.colors['accent'],
            fg='white',
            font=('맑은 고딕', 10),
            bd=0,
            padx=15,
            pady=5,
            cursor='hand2'
        )
        load_btn.pack(side='right', padx=(10, 0))
        
        # 메인 컨테이너 (좌우 분할)
        main_container = tk.Frame(self.content_frame, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True, padx=30, pady=10)
        
        # 왼쪽: 박스 목록
        self.left_frame = tk.Frame(main_container, bg=self.colors['card'], width=280)
        self.left_frame.pack(side='left', fill='y', padx=(0, 10))
        self.left_frame.pack_propagate(False)
        
        # 박스 목록 타이틀
        list_title = tk.Frame(self.left_frame, bg=self.colors['accent'], height=40)
        list_title.pack(fill='x')
        list_title.pack_propagate(False)
        
        tk.Label(
            list_title,
            text="📋 박스 목록",
            font=('맑은 고딕', 11, 'bold'),
            bg=self.colors['accent'],
            fg='white'
        ).place(relx=0.5, rely=0.5, anchor='center')
        
        # 박스 목록 스크롤 영역
        self.list_scroll = tk.Frame(self.left_frame, bg=self.colors['card'])
        self.list_scroll.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 박스 목록 업데이트
        self.update_box_list()
        
        
        # 오른쪽: 좌표 미리보기
        right_frame = tk.Frame(main_container, bg=self.colors['bg'])
        right_frame.pack(side='right', fill='both', expand=True)
        
        # 좌표 미리보기
        preview_frame = tk.Frame(right_frame, bg=self.colors['bg'])
        preview_frame.pack(fill='both', expand=True)
        
        self.coord_preview = CoordinatePreview(
            preview_frame, 
            self.settings_manager, 
            parent_window=self  # 생성자에서 직접 전달
        )
        self.coord_preview.pack(fill='both', expand=True)
    
    def create_coordinate_inputs(self, parent):
        """좌표 입력 필드 생성"""
        # 메인 컨테이너
        container = tk.Frame(parent, bg=self.colors['card'])
        container.pack(fill='both', padx=20, pady=20)
        
        # 썸네일 섹션
        thumb_label = tk.Label(
            container,
            text="썸네일 좌표",
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        )
        thumb_label.grid(row=0, column=0, columnspan=4, sticky='w', pady=(0, 10))
        
        # 컬럼 헤더
        headers = ['', 'X', 'Y', '너비', '높이']
        for i, header in enumerate(headers):
            tk.Label(
                container,
                text=header,
                font=('Segoe UI', 10),
                bg=self.colors['card'],
                fg=self.colors['subtext']
            ).grid(row=1, column=i, padx=5, pady=5)
        
        # 왼쪽/오른쪽 입력
        positions = [('왼쪽', 'left', 2), ('오른쪽', 'right', 3)]
        for label, pos, row in positions:
            tk.Label(
                container,
                text=label,
                font=('Segoe UI', 10),
                bg=self.colors['card'],
                fg=self.colors['text']
            ).grid(row=row, column=0, sticky='w', padx=(0, 10))
            
            # X, Y, Width, Height 입력 필드
            coords = ['x', 'y', 'width', 'height']
            for i, coord in enumerate(coords, 1):
                var_key = f'thumbnail_{pos}_{coord}'
                self.coord_vars[var_key] = tk.StringVar()
                
                entry = tk.Entry(
                    container,
                    textvariable=self.coord_vars[var_key],
                    width=8,
                    bg=self.colors['input_bg'],
                    fg=self.colors['text'],
                    insertbackground=self.colors['text'],
                    bd=1,
                    relief='flat'
                )
                entry.grid(row=row, column=i, padx=5, pady=5)
                entry.bind('<KeyRelease>', self.on_coordinate_change)
        
        # QR 섹션
        tk.Frame(container, bg=self.colors['border'], height=1).grid(
            row=4, column=0, columnspan=5, sticky='ew', pady=20
        )
        
        qr_label = tk.Label(
            container,
            text="QR 코드 좌표",
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        )
        qr_label.grid(row=5, column=0, columnspan=4, sticky='w', pady=(0, 10))
        
        # QR 헤더
        qr_headers = ['', 'X', 'Y', '크기']
        for i, header in enumerate(qr_headers):
            tk.Label(
                container,
                text=header,
                font=('Segoe UI', 10),
                bg=self.colors['card'],
                fg=self.colors['subtext']
            ).grid(row=6, column=i, padx=5, pady=5)
        
        # QR 왼쪽/오른쪽 입력
        qr_positions = [('왼쪽', 'left', 7), ('오른쪽', 'right', 8)]
        for label, pos, row in qr_positions:
            tk.Label(
                container,
                text=label,
                font=('Segoe UI', 10),
                bg=self.colors['card'],
                fg=self.colors['text']
            ).grid(row=row, column=0, sticky='w', padx=(0, 10))
            
            # X, Y, Size 입력 필드
            qr_coords = ['x', 'y', 'size']
            for i, coord in enumerate(qr_coords, 1):
                var_key = f'qr_{pos}_{coord}'
                self.coord_vars[var_key] = tk.StringVar()
                
                entry = tk.Entry(
                    container,
                    textvariable=self.coord_vars[var_key],
                    width=8,
                    bg=self.colors['input_bg'],
                    fg=self.colors['text'],
                    insertbackground=self.colors['text'],
                    bd=1,
                    relief='flat'
                )
                entry.grid(row=row, column=i, padx=5, pady=5)
                entry.bind('<KeyRelease>', self.on_coordinate_change)
    
    def on_coordinate_change(self, event=None):
        """좌표 변경 시 미리보기 업데이트"""
        self.mark_changed()
        # 임시로 설정 업데이트 (미리보기용)
        try:
            self.update_temp_settings()
            if hasattr(self, 'coord_preview'):
                self.coord_preview.refresh()
        except Exception as e:
            pass  # 입력 중 오류 무시
    
    def update_coordinate_fields(self):
        """좌표 입력 필드 업데이트 (드래그 앤 드롭 후)"""
        try:
            # 썸네일 좌표 업데이트
            for pos in ['left', 'right']:
                coords = self.settings_manager.get(f'coordinates.thumbnail.{pos}')
                if coords:
                    self.coord_vars[f'thumbnail_{pos}_x'].set(str(coords.get('x', 0)))
                    self.coord_vars[f'thumbnail_{pos}_y'].set(str(coords.get('y', 0)))
                    self.coord_vars[f'thumbnail_{pos}_width'].set(str(coords.get('width', 160)))
                    self.coord_vars[f'thumbnail_{pos}_height'].set(str(coords.get('height', 250)))
            
            # QR 좌표 업데이트
            for pos in ['left', 'right']:
                coords = self.settings_manager.get(f'coordinates.qr.{pos}')
                if coords:
                    self.coord_vars[f'qr_{pos}_x'].set(str(coords.get('x', 0)))
                    self.coord_vars[f'qr_{pos}_y'].set(str(coords.get('y', 0)))
                    self.coord_vars[f'qr_{pos}_size'].set(str(coords.get('size', 70)))
            
            self.mark_changed()
        except Exception as e:
            self.logger.error(f"좌표 필드 업데이트 실패: {e}")
    
    def update_temp_settings(self):
        """임시 설정 업데이트 (미리보기용)"""
        try:
            # 썸네일 좌표
            for pos in ['left', 'right']:
                for coord in ['x', 'y', 'width', 'height']:
                    key = f'thumbnail_{pos}_{coord}'
                    value = self.coord_vars[key].get()
                    if value:
                        self.settings_manager.settings['coordinates']['thumbnail'][pos][coord] = int(value)
            
            # QR 좌표
            for pos in ['left', 'right']:
                for coord in ['x', 'y', 'size']:
                    key = f'qr_{pos}_{coord}'
                    value = self.coord_vars[key].get()
                    if value:
                        if coord == 'size':
                            self.settings_manager.settings['coordinates']['qr'][pos]['size'] = int(value)
                        else:
                            self.settings_manager.settings['coordinates']['qr'][pos][coord] = int(value)
        except:
            pass  # 잘못된 입력 무시
    
    def load_pdf_for_preview(self):
        """PDF 파일 선택하여 미리보기에 로드"""
        if hasattr(self, 'coord_preview'):
            self.coord_preview.load_sample_pdf()
    
    def load_coordinate_values(self):
        """좌표 값을 입력 필드에 로드"""
        try:
            # 썸네일 좌표 로드
            for pos in ['left', 'right']:
                coords = self.settings_manager.get(f'coordinates.thumbnail.{pos}')
                if coords:
                    self.coord_vars[f'thumbnail_{pos}_x'].set(str(coords.get('x', 230 if pos == 'left' else 658)))
                    self.coord_vars[f'thumbnail_{pos}_y'].set(str(coords.get('y', 234 if pos == 'left' else 228)))
                    self.coord_vars[f'thumbnail_{pos}_width'].set(str(coords.get('width', 160)))
                    self.coord_vars[f'thumbnail_{pos}_height'].set(str(coords.get('height', 250)))
            
            # QR 좌표 로드
            for pos in ['left', 'right']:
                coords = self.settings_manager.get(f'coordinates.qr.{pos}')
                if coords:
                    self.coord_vars[f'qr_{pos}_x'].set(str(coords.get('x', 315 if pos == 'left' else 730)))
                    self.coord_vars[f'qr_{pos}_y'].set(str(coords.get('y', 500)))
                    self.coord_vars[f'qr_{pos}_size'].set(str(coords.get('size', 70)))
        except Exception as e:
            self.logger.error(f"좌표 값 로드 실패: {e}")
    
    def show_effects_page(self):
        """이미지 효과 페이지"""
        self.clear_content()
        self.set_active_menu(1)
        
        # 페이지 타이틀
        title_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        title_frame.pack(fill='x', padx=30, pady=(20, 10))
        
        tk.Label(
            title_frame,
            text="이미지 효과",
            font=('Segoe UI', 16, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text']
        ).pack(side='left')
        
        tk.Label(
            title_frame,
            text="썸네일 이미지에 적용할 효과를 설정합니다",
            font=('Segoe UI', 10),
            bg=self.colors['bg'],
            fg=self.colors['subtext']
        ).pack(side='left', padx=(20, 0))
        
        # 효과 설정 컨테이너
        effects_frame = tk.Frame(self.content_frame, bg=self.colors['card'])
        effects_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # 효과 슬라이더들
        self.effect_vars = {}
        
        # 해상도 DPI 슬라이더 (맨 위에 배치)
        self.create_dpi_control(effects_frame, 0)
        
        # 구분선
        separator = tk.Frame(effects_frame, bg=self.colors['border'], height=1)
        separator.grid(row=1, column=0, columnspan=3, sticky='ew', padx=20, pady=10)
        
        # 기타 효과 슬라이더들
        effects = [
            ('대비', 'contrast', 0.0, 2.0, 1.0),
            ('선명도', 'sharpness', 0.0, 2.0, 1.0),
            ('밝기', 'brightness', 0.0, 2.0, 1.0),
            ('채도', 'saturation', 0.0, 2.0, 1.0)
        ]
        
        for i, (label, key, min_val, max_val, default) in enumerate(effects):
            self.create_slider_control(effects_frame, label, key, min_val, max_val, default, i + 2)
        
        # 흑백 변환 체크박스
        grayscale_frame = tk.Frame(effects_frame, bg=self.colors['card'])
        grayscale_frame.grid(row=len(effects) + 2, column=0, columnspan=3, pady=20)
        
        self.grayscale_var = tk.BooleanVar(value=self.settings_manager.get('thumbnail.grayscale', False))
        grayscale_check = tk.Checkbutton(
            grayscale_frame,
            text="흑백 변환",
            variable=self.grayscale_var,
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 11),
            selectcolor=self.colors['card'],
            activebackground=self.colors['card']
        )
        grayscale_check.pack()
    
    def show_blank_detection_page(self):
        """백지 감지 페이지"""
        self.clear_content()
        self.set_active_menu(2)
        
        # 페이지 타이틀
        title_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        title_frame.pack(fill='x', padx=30, pady=(20, 10))
        
        tk.Label(
            title_frame,
            text="백지 감지",
            font=('Segoe UI', 16, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text']
        ).pack(side='left')
        
        tk.Label(
            title_frame,
            text="백지 페이지 자동 감지 설정",
            font=('Segoe UI', 10),
            bg=self.colors['bg'],
            fg=self.colors['subtext']
        ).pack(side='left', padx=(20, 0))
        
        # 백지 감지 설정
        blank_frame = tk.Frame(self.content_frame, bg=self.colors['card'])
        blank_frame.pack(fill='x', padx=30, pady=20)
        
        inner_frame = tk.Frame(blank_frame, bg=self.colors['card'])
        inner_frame.pack(padx=20, pady=20)
        
        # 백지 감지 활성화
        # 백지 감지 활성화 - 기본값 True로 설정
        self.blank_enabled_var = tk.BooleanVar(value=self.settings_manager.get('blank_detection.enabled', True))
        enable_check = tk.Checkbutton(
            inner_frame,
            text="백지 감지 활성화",
            variable=self.blank_enabled_var,
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 12, 'bold'),
            selectcolor=self.colors['card'],
            command=self.toggle_blank_settings
        )
        enable_check.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 20))
        
        # 감지 알고리즘 선택
        tk.Label(
            inner_frame,
            text="감지 알고리즘:",
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 11)
        ).grid(row=1, column=0, sticky='w', padx=(20, 10), pady=5)
        
        self.algorithm_var = tk.StringVar(value=self.settings_manager.get('blank_detection.algorithm', 'simple'))
        algorithms = [('단순 비교', 'simple'), ('엔트로피', 'entropy'), ('히스토그램', 'histogram')]
        
        for i, (text, value) in enumerate(algorithms):
            tk.Radiobutton(
                inner_frame,
                text=text,
                variable=self.algorithm_var,
                value=value,
                bg=self.colors['card'],
                fg=self.colors['text'],
                font=('Segoe UI', 10),
                selectcolor=self.colors['card']
            ).grid(row=2+i, column=0, sticky='w', padx=(40, 0), pady=2)
        
        # 임계값 설정
        tk.Label(
            inner_frame,
            text="감지 임계값:",
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 11)
        ).grid(row=5, column=0, sticky='w', padx=(20, 10), pady=(20, 5))
        
        self.threshold_var = tk.StringVar(value=str(self.settings_manager.get('blank_detection.threshold', 95)))
        threshold_frame = tk.Frame(inner_frame, bg=self.colors['card'])
        threshold_frame.grid(row=6, column=0, columnspan=2, sticky='w', padx=(40, 0))
        
        self.threshold_scale = tk.Scale(
            threshold_frame,
            from_=80,
            to=99,
            orient='horizontal',
            variable=self.threshold_var,
            bg=self.colors['card'],
            fg=self.colors['text'],
            length=300,
            highlightthickness=0
        )
        self.threshold_scale.pack(side='left')
        
        tk.Label(
            threshold_frame,
            textvariable=self.threshold_var,
            bg=self.colors['card'],
            fg=self.colors['accent'],
            font=('Segoe UI', 11, 'bold')
        ).pack(side='left', padx=(10, 0))
        
        tk.Label(
            threshold_frame,
            text="%",
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 11)
        ).pack(side='left')
    
    def show_performance_page(self):
        """성능 페이지"""
        self.clear_content()
        self.set_active_menu(3)
        
        # 페이지 타이틀
        title_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        title_frame.pack(fill='x', padx=30, pady=(20, 10))
        
        tk.Label(
            title_frame,
            text="성능 설정",
            font=('Segoe UI', 16, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text']
        ).pack(side='left')
        
        tk.Label(
            title_frame,
            text="처리 속도와 시스템 리소스 사용 설정",
            font=('Segoe UI', 10),
            bg=self.colors['bg'],
            fg=self.colors['subtext']
        ).pack(side='left', padx=(20, 0))
        
        # 성능 설정
        perf_frame = tk.Frame(self.content_frame, bg=self.colors['card'])
        perf_frame.pack(fill='x', padx=30, pady=20)
        
        inner_frame = tk.Frame(perf_frame, bg=self.colors['card'])
        inner_frame.pack(padx=20, pady=20)
        
        # 멀티스레딩
        self.multithread_var = tk.BooleanVar(value=self.settings_manager.get('performance.multithreading', True))
        multithread_check = tk.Checkbutton(
            inner_frame,
            text="멀티스레딩 사용 (빠른 처리)",
            variable=self.multithread_var,
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 11),
            selectcolor=self.colors['card']
        )
        multithread_check.grid(row=0, column=0, columnspan=2, sticky='w', pady=5)
        
        # 작업자 수
        tk.Label(
            inner_frame,
            text="최대 작업 스레드:",
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 11)
        ).grid(row=1, column=0, sticky='w', padx=(20, 10), pady=10)
        
        self.workers_var = tk.StringVar(value=str(self.settings_manager.get('performance.max_workers', 4)))
        workers_scale = tk.Scale(
            inner_frame,
            from_=1,
            to=8,
            orient='horizontal',
            variable=self.workers_var,
            bg=self.colors['card'],
            fg=self.colors['text'],
            length=200,
            highlightthickness=0
        )
        workers_scale.grid(row=1, column=1, sticky='w')
        
        # 캐시
        self.cache_var = tk.BooleanVar(value=self.settings_manager.get('performance.cache_enabled', True))
        cache_check = tk.Checkbutton(
            inner_frame,
            text="캐시 사용 (메모리 사용량 증가, 속도 향상)",
            variable=self.cache_var,
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 11),
            selectcolor=self.colors['card']
        )
        cache_check.grid(row=2, column=0, columnspan=2, sticky='w', pady=(20, 5))
        
        # 캐시 크기
        tk.Label(
            inner_frame,
            text="캐시 크기 (MB):",
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 11)
        ).grid(row=3, column=0, sticky='w', padx=(20, 10), pady=10)
        
        self.cache_size_var = tk.StringVar(value='100')
        cache_scale = tk.Scale(
            inner_frame,
            from_=50,
            to=500,
            orient='horizontal',
            variable=self.cache_size_var,
            bg=self.colors['card'],
            fg=self.colors['text'],
            length=200,
            highlightthickness=0,
            resolution=50
        )
        cache_scale.grid(row=3, column=1, sticky='w')
    
    def show_presets_page(self):
        """프리셋 페이지"""
        self.clear_content()
        self.set_active_menu(4)
        
        # 페이지 타이틀
        title_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        title_frame.pack(fill='x', padx=30, pady=(20, 10))
        
        tk.Label(
            title_frame,
            text="프리셋 관리",
            font=('맑은 고딕', 14),
            bg=self.colors['bg'],
            fg=self.colors['text']
        ).pack(side='left')
        
        tk.Label(
            title_frame,
            text="자주 사용하는 설정을 프리셋으로 저장",
            font=('맑은 고딕', 10),
            bg=self.colors['bg'],
            fg=self.colors['subtext']
        ).pack(side='left', padx=(20, 0))
        
        # 추천 핫키 설명
        info_frame = tk.Frame(self.content_frame, bg=self.colors['card'])
        info_frame.pack(fill='x', padx=30, pady=(0, 10))
        
        info_text = tk.Label(
            info_frame,
            text="💡 사용법: 📥 불러오기 = 프리셋 설정을 현재 작업에 적용 | 💾 여기에 저장 = 현재 작업을 프리셋에 저장 | 사용자 정의 단축키 설정 가능",
            font=('맑은 고딕', 9),
            bg=self.colors['card'],
            fg=self.colors['accent'],
            pady=10
        )
        info_text.pack(padx=15)
        
        # 프리셋 목록
        presets_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        presets_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # 프리셋 카드들
        self.preset_hotkeys = {
            'default': '',
            'preset_1': '',
            'preset_2': '',
            'preset_3': ''
        }
        
        # 프리셋 이름 가져오기
        preset_names = {}
        for pid in ['default', 'preset_1', 'preset_2', 'preset_3']:
            preset_data = self.preset_manager.get_preset_data(pid)
            if preset_data:
                preset_names[pid] = preset_data.get('name', f'프리셋 {pid.split("_")[-1]}')
            else:
                preset_names[pid] = '기본 설정' if pid == 'default' else f'프리셋 {pid.split("_")[-1]}'
        
        preset_cards = [
            (self.preset_hotkeys['default'], preset_names['default'], 'default', self.colors['success']),
            (self.preset_hotkeys['preset_1'], preset_names['preset_1'], 'preset_1', self.colors['accent']),
            (self.preset_hotkeys['preset_2'], preset_names['preset_2'], 'preset_2', self.colors['warning']),
            (self.preset_hotkeys['preset_3'], preset_names['preset_3'], 'preset_3', '#9C27B0')
        ]
        
        for i, (key, name, preset_id, color) in enumerate(preset_cards):
            card = tk.Frame(
                presets_frame,
                bg=self.colors['card'],
                highlightthickness=2,
                highlightbackground=color
            )
            card.grid(row=i//2, column=i%2, padx=10, pady=10, sticky='nsew')
            
            # 메인 컨테이너 (상하 분할)
            main_content = tk.Frame(card, bg=self.colors['card'])
            main_content.pack(fill='both', expand=True, padx=15, pady=15)
            
            # 상단: 기존 프리셋 정보
            content = tk.Frame(main_content, bg=self.colors['card'])
            content.pack(fill='x')
            
            # 단축키 프레임
            hotkey_frame = tk.Frame(content, bg=self.colors['card'])
            hotkey_frame.pack(side='left', padx=(0, 10))
            
            # 단축키 레이블
            hotkey_label = tk.Label(
                hotkey_frame,
                text=key,
                font=('맑은 고딕', 12, 'bold'),
                bg=self.colors['card'],
                fg=color,
                width=4
            )
            hotkey_label.pack()
            
            # 단축키 변경 버튼
            change_hotkey_btn = tk.Button(
                hotkey_frame,
                text="변경",
                font=('맑은 고딕', 8),
                bg=self.colors['hover'],
                fg=self.colors['text'],
                bd=0,
                padx=5,
                pady=2,
                cursor='hand2',
                command=lambda p=preset_id: self.change_hotkey(p)
            )
            change_hotkey_btn.pack(pady=(2, 0))
            
            # 이름 프레임
            name_frame = tk.Frame(content, bg=self.colors['card'])
            name_frame.pack(side='left', fill='x', expand=True)
            
            # 이름 입력 필드 (편집 가능)
            name_var = tk.StringVar(value=name)
            name_entry = tk.Entry(
                name_frame,
                textvariable=name_var,
                font=('맑은 고딕', 11),
                bg=self.colors['card'],
                fg=self.colors['text'],
                bd=1,
                relief='flat',
                width=15
            )
            name_entry.pack(anchor='w')
            
            # 이름 변경 시 자동 저장
            def save_name(event, pid=preset_id, var=name_var):
                new_name = var.get()
                if new_name:
                    self.preset_manager.update_preset_name(pid, new_name)
            
            name_entry.bind('<Return>', save_name)
            name_entry.bind('<FocusOut>', save_name)
            
            # 사용 횟수 표시
            preset_data = self.preset_manager.get_preset_data(preset_id) or {}
            usage_count = preset_data.get('usage_count', 0)
            usage_label = tk.Label(
                name_frame,
                text=f"사용: {usage_count}회",
                font=('맑은 고딕', 8),
                bg=self.colors['card'],
                fg=self.colors['subtext']
            )
            usage_label.pack(anchor='w')
            
            # 하단: 시각적 미리보기 추가
            preview_frame = tk.Frame(main_content, bg=self.colors['card'])
            preview_frame.pack(fill='both', expand=True, pady=(10, 0))
            
            # 미리보기 캔버스 생성
            self.create_preset_preview(preview_frame, preset_id)
            
            # 버튼들
            btn_frame = tk.Frame(content, bg=self.colors['card'])
            btn_frame.pack(side='right')
            
            # 불러오기 버튼 (프리셋 → 현재 설정)
            apply_btn = tk.Button(
                btn_frame,
                text="📥 불러오기",
                bg=color,
                fg='white',
                font=('맑은 고딕', 9),
                bd=0,
                padx=15,
                pady=5,
                cursor='hand2',
                command=lambda p=preset_id: self.apply_preset(p)
            )
            apply_btn.pack(side='left', padx=2)
            
            # 저장 버튼 (현재 설정 → 프리셋)
            save_btn = tk.Button(
                btn_frame,
                text="💾 여기에 저장",
                bg=self.colors['hover'],
                fg=self.colors['text'],
                font=('맑은 고딕', 9),
                bd=0,
                padx=15,
                pady=5,
                cursor='hand2',
                command=lambda p=preset_id: self.save_to_preset(p)
            )
            save_btn.pack(side='left', padx=2)
        
        # 그리드 가중치
        presets_frame.columnconfigure(0, weight=1)
        presets_frame.columnconfigure(1, weight=1)
        presets_frame.rowconfigure(0, weight=1)
        presets_frame.rowconfigure(1, weight=1)
    
    def update_box_list(self):
        """박스 목록 실시간 업데이트"""
        if not hasattr(self, 'list_scroll'):
            return
            
        # 기존 위젯 모두 제거
        for widget in self.list_scroll.winfo_children():
            widget.destroy()
        
        # 썸네일 박스 목록
        tk.Label(
            self.list_scroll,
            text="🖼️ 썸네일 박스",
            font=('맑은 고딕', 10, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(anchor='w', pady=(5, 5))
        
        thumbnail_boxes = self.settings_manager.get('coordinates.thumbnail_boxes', [])
        for idx, box in enumerate(thumbnail_boxes):
            box_frame = tk.Frame(self.list_scroll, bg=self.colors['hover'], relief='flat', bd=1)
            box_frame.pack(fill='x', pady=2)
            
            box_info = tk.Frame(box_frame, bg=self.colors['hover'])
            box_info.pack(fill='x', padx=8, pady=5)
            
            tk.Label(
                box_info,
                text=f"📌 {box.get('name', f'썸네일 {idx+1}')}",
                font=('맑은 고딕', 9, 'bold'),
                bg=self.colors['hover'],
                fg=self.colors['thumbnail']
            ).pack(anchor='w')
            
            tk.Label(
                box_info,
                text=f"위치: ({box.get('x', 0)}, {box.get('y', 0)})",
                font=('맑은 고딕', 8),
                bg=self.colors['hover'],
                fg=self.colors['subtext']
            ).pack(anchor='w')
            
            tk.Label(
                box_info,
                text=f"크기: {box.get('width', 160)} × {box.get('height', 250)}",
                font=('맑은 고딕', 8),
                bg=self.colors['hover'],
                fg=self.colors['subtext']
            ).pack(anchor='w')
        
        # 구분선
        tk.Frame(self.list_scroll, bg=self.colors['border'], height=1).pack(fill='x', pady=10)
        
        # QR 박스 목록
        tk.Label(
            self.list_scroll,
            text="📱 QR 박스",
            font=('맑은 고딕', 10, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(anchor='w', pady=(5, 5))
        
        qr_boxes = self.settings_manager.get('coordinates.qr_boxes', [])
        for idx, box in enumerate(qr_boxes):
            box_frame = tk.Frame(self.list_scroll, bg=self.colors['hover'], relief='flat', bd=1)
            box_frame.pack(fill='x', pady=2)
            
            box_info = tk.Frame(box_frame, bg=self.colors['hover'])
            box_info.pack(fill='x', padx=8, pady=5)
            
            tk.Label(
                box_info,
                text=f"📌 {box.get('name', f'QR {idx+1}')}",
                font=('맑은 고딕', 9, 'bold'),
                bg=self.colors['hover'],
                fg=self.colors['qr']
            ).pack(anchor='w')
            
            tk.Label(
                box_info,
                text=f"위치: ({box.get('x', 0)}, {box.get('y', 0)})",
                font=('맑은 고딕', 8),
                bg=self.colors['hover'],
                fg=self.colors['subtext']
            ).pack(anchor='w')
            
            tk.Label(
                box_info,
                text=f"크기: {box.get('size', 70)} × {box.get('size', 70)}",
                font=('맑은 고딕', 8),
                bg=self.colors['hover'],
                fg=self.colors['subtext']
            ).pack(anchor='w')
    
    def create_preset_preview(self, parent, preset_id):
        """프리셋 미리보기 캔버스 생성"""
        # 미리보기 캔버스
        canvas = tk.Canvas(
            parent,
            bg='#f8f8f8',
            width=280,
            height=150,
            highlightthickness=1,
            highlightbackground=self.colors['border']
        )
        canvas.pack(fill='both', expand=True)
        
        # 페이지 비율 (A4 가로)
        page_width = 842
        page_height = 595
        
        # 캔버스 크기에 맞게 스케일 계산
        scale = min(280 / page_width, 150 / page_height) * 0.9
        
        # 실제 그리기 영역
        draw_width = int(page_width * scale)
        draw_height = int(page_height * scale)
        
        # 중앙 정렬을 위한 오프셋
        offset_x = (280 - draw_width) // 2
        offset_y = (150 - draw_height) // 2
        
        # 페이지 배경 그리기
        canvas.create_rectangle(
            offset_x, offset_y,
            offset_x + draw_width, offset_y + draw_height,
            fill='white',
            outline=self.colors['border']
        )
        
        # 프리셋 데이터 가져오기
        preset_data = self.preset_manager.get_preset_data(preset_id) or {}
        
        # 좌표 데이터 가져오기 (프리셋에 저장된 설정 또는 현재 설정)
        if 'settings' in preset_data and 'coordinates' in preset_data['settings']:
            coordinates = preset_data['settings']['coordinates']
        else:
            coordinates = self.settings_manager.get('coordinates', {})
        
        # 썸네일 박스 그리기
        thumbnail_boxes = coordinates.get('thumbnail_boxes', [])
        for box in thumbnail_boxes:
            x = int(box.get('x', 0) * scale) + offset_x
            y = int(box.get('y', 0) * scale) + offset_y
            width = int(box.get('width', 160) * scale)
            height = int(box.get('height', 250) * scale)
            
            # 썸네일 박스 그리기
            canvas.create_rectangle(
                x, y, x + width, y + height,
                fill='#E8F5E9',
                outline=self.colors['thumbnail'],
                width=2
            )
            
            # 썸네일 레이블
            canvas.create_text(
                x + width // 2,
                y + height // 2,
                text="썸네일",
                fill=self.colors['thumbnail'],
                font=('맑은 고딕', 8)
            )
        
        # QR 박스 그리기
        qr_boxes = coordinates.get('qr_boxes', [])
        for box in qr_boxes:
            x = int(box.get('x', 0) * scale) + offset_x
            y = int(box.get('y', 0) * scale) + offset_y
            size = int(box.get('size', 70) * scale)
            
            # QR 박스 그리기
            canvas.create_rectangle(
                x, y, x + size, y + size,
                fill='#FFF3E0',
                outline=self.colors['qr'],
                width=2
            )
            
            # QR 레이블
            canvas.create_text(
                x + size // 2,
                y + size // 2,
                text="QR",
                fill=self.colors['qr'],
                font=('맑은 고딕', 8)
            )
        
        # 프리셋 정보 표시
        info_text = f"썸네일: {len(thumbnail_boxes)}개 | QR: {len(qr_boxes)}개"
        canvas.create_text(
            140, 140,
            text=info_text,
            fill=self.colors['subtext'],
            font=('맑은 고딕', 7),
            anchor='center'
        )
    
    def show_advanced_page(self):
        """고급 설정 페이지"""
        self.clear_content()
        self.set_active_menu(5)
        
        # 페이지 타이틀
        title_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        title_frame.pack(fill='x', padx=30, pady=(20, 10))
        
        tk.Label(
            title_frame,
            text="고급 설정",
            font=('Segoe UI', 16, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text']
        ).pack(side='left')
        
        tk.Label(
            title_frame,
            text="추가 옵션 및 처리 규칙",
            font=('Segoe UI', 10),
            bg=self.colors['bg'],
            fg=self.colors['subtext']
        ).pack(side='left', padx=(20, 0))
        
        # 고급 설정
        adv_frame = tk.Frame(self.content_frame, bg=self.colors['card'])
        adv_frame.pack(fill='x', padx=30, pady=20)
        
        inner_frame = tk.Frame(adv_frame, bg=self.colors['card'])
        inner_frame.pack(padx=20, pady=20)
        
        # UI 설정
        tk.Label(
            inner_frame,
            text="사용자 인터페이스",
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).grid(row=0, column=0, sticky='w', pady=(0, 10))
        
        self.always_on_top_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            inner_frame,
            text="창 항상 위에 표시",
            variable=self.always_on_top_var,
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 10),
            selectcolor=self.colors['card']
        ).grid(row=1, column=0, sticky='w', padx=(20, 0), pady=2)
        
        self.auto_clear_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            inner_frame,
            text="처리 완료 후 자동 초기화",
            variable=self.auto_clear_var,
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 10),
            selectcolor=self.colors['card']
        ).grid(row=2, column=0, sticky='w', padx=(20, 0), pady=2)
        
        self.confirm_process_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            inner_frame,
            text="처리 전 확인 대화상자 표시",
            variable=self.confirm_process_var,
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 10),
            selectcolor=self.colors['card']
        ).grid(row=3, column=0, sticky='w', padx=(20, 0), pady=2)
        
        # 로깅 설정
        tk.Label(
            inner_frame,
            text="로깅",
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).grid(row=4, column=0, sticky='w', pady=(20, 10))
        
        tk.Label(
            inner_frame,
            text="로그 레벨:",
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 10)
        ).grid(row=5, column=0, sticky='w', padx=(20, 0), pady=5)
        
        self.log_level_var = tk.StringVar(value='INFO')
        log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        
        log_menu = tk.OptionMenu(inner_frame, self.log_level_var, *log_levels)
        log_menu.config(
            bg=self.colors['input_bg'],
            fg=self.colors['text'],
            font=('Segoe UI', 10),
            bd=0,
            highlightthickness=0
        )
        log_menu.grid(row=5, column=1, sticky='w', padx=10)
        
        # 처리 규칙
        tk.Label(
            inner_frame,
            text="처리 규칙",
            font=('Segoe UI', 12, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).grid(row=6, column=0, sticky='w', pady=(20, 10))
        
        rules_text = tk.Text(
            inner_frame,
            height=5,
            width=50,
            bg=self.colors['input_bg'],
            fg=self.colors['text'],
            font=('Consolas', 9),
            insertbackground=self.colors['text']
        )
        rules_text.grid(row=7, column=0, columnspan=2, padx=(20, 0), pady=5)
        rules_text.insert('1.0', '# 파일명 패턴에 따른 처리 규칙\n# 예: "표지" 포함 시 QR 제외')
    
    def clear_content(self):
        """컨텐츠 영역 초기화"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def set_active_menu(self, index):
        """활성 메뉴 표시"""
        self.active_menu_index = index
        
        for i, widget_info in enumerate(self.menu_widgets):
            if i == index:
                # 활성 메뉴 스타일
                bg_color = self.colors['accent']
                text_color = 'white'
                desc_color = '#E0E0E0'
            else:
                # 비활성 메뉴 스타일
                bg_color = '#ffffff'
                text_color = '#424242'
                desc_color = '#9E9E9E'
            
            try:
                widget_info['item_frame'].configure(bg=bg_color)
                widget_info['inner_frame'].configure(bg=bg_color)
                widget_info['text_container'].configure(bg=bg_color)
                widget_info['main_text'].configure(bg=bg_color, fg=text_color)
                widget_info['desc_text'].configure(bg=bg_color, fg=desc_color)
            except:
                pass
    
    def create_bottom_bar(self):
        """하단 버튼 바"""
        bottom_bar = tk.Frame(self.window, bg=self.colors['card'], height=60)
        bottom_bar.pack(side='bottom', fill='x')
        bottom_bar.pack_propagate(False)
        
        # 버튼 컨테이너
        btn_container = tk.Frame(bottom_bar, bg=self.colors['card'])
        btn_container.pack(expand=True)
        
        # 저장 버튼
        save_btn = tk.Button(
            btn_container,
            text="✓ 저장",
            command=self.save_settings,
            bg=self.colors['success'],
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            bd=0,
            padx=30,
            pady=10,
            cursor='hand2'
        )
        save_btn.pack(side='left', padx=10, pady=15)
        
        # 취소 버튼
        cancel_btn = tk.Button(
            btn_container,
            text="✕ 취소",
            command=self.close,
            bg=self.colors['error'],
            fg='white',
            font=('Segoe UI', 11),
            bd=0,
            padx=30,
            pady=10,
            cursor='hand2'
        )
        cancel_btn.pack(side='left', padx=10, pady=15)
    
    def load_current_settings(self):
        """현재 설정 로드"""
        try:
            # 좌표 설정 - coord_vars가 초기화되어 있는 경우에만
            if self.coord_vars:
                for pos in ['left', 'right']:
                    for coord in ['x', 'y', 'width', 'height']:
                        key = f'thumbnail_{pos}_{coord}'
                        if key in self.coord_vars:
                            value = self.settings_manager.get(f'coordinates.thumbnail.{pos}.{coord}', '')
                            self.coord_vars[key].set(str(value))
                    
                    for coord in ['x', 'y', 'size']:
                        key = f'qr_{pos}_{coord}'
                        if key in self.coord_vars:
                            value = self.settings_manager.get(f'coordinates.qr.{pos}.{coord}', '')
                            self.coord_vars[key].set(str(value))
            
            # 백지 감지 설정 로드 (중요!)
            if hasattr(self, 'blank_enabled_var'):
                self.blank_enabled_var.set(self.settings_manager.get('blank_detection.enabled', True))
                self.threshold_var.set(self.settings_manager.get('blank_detection.threshold', 95))
            
            # 성능 설정 로드
            if hasattr(self, 'multithread_var'):
                self.multithread_var.set(self.settings_manager.get('performance.multithreading', True))
                self.workers_var.set(str(self.settings_manager.get('performance.max_workers', 4)))
                self.cache_var.set(self.settings_manager.get('performance.cache_enabled', True))
            
            # 이미지 효과 설정 로드
            if hasattr(self, 'effect_vars'):
                for key in self.effect_vars:
                    # render_dpi는 기본값이 다름
                    if key == 'render_dpi':
                        value = self.settings_manager.get(f'thumbnail.{key}', 432)
                    else:
                        value = self.settings_manager.get(f'thumbnail.{key}', 1.0)
                    self.effect_vars[key].set(value)
            if hasattr(self, 'grayscale_var'):
                self.grayscale_var.set(self.settings_manager.get('thumbnail.grayscale', False))
            
            self.changes_made = False
            
        except Exception as e:
            self.logger.error(f"설정 로드 실패: {e}")
    
    def save_settings(self):
        """설정 저장"""
        try:
            # 좌표 설정 저장
            for pos in ['left', 'right']:
                thumb_coords = {}
                for coord in ['x', 'y', 'width', 'height']:
                    key = f'thumbnail_{pos}_{coord}'
                    value = self.coord_vars.get(key)
                    if value:
                        thumb_coords[coord] = int(value.get()) if value.get() else 0
                
                self.settings_manager.set(f'coordinates.thumbnail.{pos}', thumb_coords)
                
                qr_coords = {}
                for coord in ['x', 'y', 'size']:
                    key = f'qr_{pos}_{coord}'
                    value = self.coord_vars.get(key)
                    if value:
                        if coord == 'size':
                            qr_coords[coord] = int(value.get()) if value.get() else 70
                        else:
                            qr_coords[coord] = int(value.get()) if value.get() else 0
                
                self.settings_manager.set(f'coordinates.qr.{pos}', qr_coords)
            
            # 백지 감지 설정 저장 (중요!)
            if hasattr(self, 'blank_enabled_var'):
                self.settings_manager.set('blank_detection.enabled', self.blank_enabled_var.get())
                self.settings_manager.set('blank_detection.threshold', self.threshold_var.get())
                self.settings_manager.set('blank_detection.algorithm', self.algorithm_var.get())
            
            # 이미지 효과 설정 저장
            if hasattr(self, 'effect_vars'):
                for key, var in self.effect_vars.items():
                    # render_dpi는 정수로 저장
                    if key == 'render_dpi':
                        self.settings_manager.set(f'thumbnail.{key}', int(var.get()))
                    else:
                        self.settings_manager.set(f'thumbnail.{key}', var.get())
                if hasattr(self, 'grayscale_var'):
                    self.settings_manager.set('thumbnail.grayscale', self.grayscale_var.get())
            
            # 성능 설정 저장
            if hasattr(self, 'multithread_var'):
                self.settings_manager.set('performance.multithreading', self.multithread_var.get())
                self.settings_manager.set('performance.max_workers', int(self.workers_var.get()))
                self.settings_manager.set('performance.cache_enabled', self.cache_var.get())
                self.settings_manager.set('performance.cache_size_mb', int(self.cache_size_var.get()))
            
            # 고급 설정 저장
            if hasattr(self, 'always_on_top_var'):
                self.settings_manager.set('ui.window_always_on_top', self.always_on_top_var.get())
                self.settings_manager.set('ui.auto_clear_after_process', self.auto_clear_var.get())
                self.settings_manager.set('ui.confirm_before_process', self.confirm_process_var.get())
                self.settings_manager.set('performance.log_level', self.log_level_var.get())
            
            # 파일에 저장
            if self.settings_manager.save():
                messagebox.showinfo("성공", "설정이 저장되었습니다")
                self.changes_made = False
                self.close()
            else:
                messagebox.showerror("오류", "설정 저장에 실패했습니다")
                
        except Exception as e:
            self.logger.error(f"설정 저장 실패: {e}")
            messagebox.showerror("오류", f"설정 저장 실패: {e}")
    
    def mark_changed(self):
        """변경사항 표시"""
        self.changes_made = True
    
    def close(self):
        """창 닫기"""
        if self.changes_made:
            if messagebox.askyesno("확인", "저장하지 않은 변경사항이 있습니다. 저장하시겠습니까?"):
                self.save_settings()
                return
        
        self.window.destroy()
    
    def create_dpi_control(self, parent, row):
        """DPI (해상도) 컨트롤 생성"""
        # 라벨 및 설명
        label_frame = tk.Frame(parent, bg=self.colors['card'])
        label_frame.grid(row=row, column=0, sticky='w', padx=20, pady=10)
        
        tk.Label(
            label_frame,
            text="🔍 해상도 (DPI):",
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 11, 'bold')
        ).pack(anchor='w')
        
        tk.Label(
            label_frame,
            text="높을수록 선명 (6배=432)",
            bg=self.colors['card'],
            fg=self.colors['subtext'],
            font=('Segoe UI', 8)
        ).pack(anchor='w')
        
        # DPI 슬라이더
        current_dpi = self.settings_manager.get('thumbnail.render_dpi', 500)
        self.dpi_var = tk.IntVar(value=current_dpi)
        self.effect_vars['render_dpi'] = self.dpi_var  # effect_vars에 추가
        
        # 슬라이더 프레임 (더 넓게)
        slider_frame = tk.Frame(parent, bg=self.colors['card'])
        slider_frame.grid(row=row, column=1, sticky='w', padx=10)
        
        dpi_slider = tk.Scale(
            slider_frame,
            from_=72,  # 1배 (최소)
            to=1200,   # 16.7배 (최대) - 자유도 높게
            orient='horizontal',
            variable=self.dpi_var,
            bg=self.colors['card'],
            fg=self.colors['text'],
            length=400,  # 더 긴 슬라이더
            highlightthickness=0,
            resolution=36,  # 0.5배 단위
            tickinterval=216  # 3배 단위로 눈금
        )
        dpi_slider.pack()
        
        # 값 표시 프레임
        value_frame = tk.Frame(parent, bg=self.colors['card'])
        value_frame.grid(row=row, column=2, sticky='w')
        
        # DPI 값과 배율 표시
        def update_dpi_label(*args):
            dpi = self.dpi_var.get()
            multiplier = dpi / 72
            label_text = f"{dpi} DPI\n({multiplier:.1f}배)"
            dpi_label.config(text=label_text)
        
        dpi_label = tk.Label(
            value_frame,
            text=f"{current_dpi} DPI\n({current_dpi/72:.1f}배)",
            bg=self.colors['card'],
            fg=self.colors['accent'],
            font=('Segoe UI', 10, 'bold'),
            width=10,
            justify='center'
        )
        dpi_label.pack()
        
        # 값 변경시 라벨 업데이트
        self.dpi_var.trace('w', update_dpi_label)
        
        # 추천값 버튼들
        preset_frame = tk.Frame(parent, bg=self.colors['card'])
        preset_frame.grid(row=row, column=3, sticky='w', padx=10)
        
        tk.Label(
            preset_frame,
            text="추천:",
            bg=self.colors['card'],
            fg=self.colors['subtext'],
            font=('Segoe UI', 9)
        ).pack(side='left', padx=(0, 5))
        
        dpi_presets = [
            ("저품질", 216),   # 3배
            ("표준", 432),     # 6배
            ("고품질", 648),   # 9배
            ("최고", 900)      # 12.5배
        ]
        
        for text, dpi in dpi_presets:
            btn = tk.Button(
                preset_frame,
                text=text,
                command=lambda d=dpi: self.dpi_var.set(d),
                bg=self.colors['accent'],
                fg='white',
                font=('Segoe UI', 8),
                relief='flat',
                padx=8,
                pady=3,
                cursor='hand2'
            )
            btn.pack(side='left', padx=2)
    
    def create_slider_control(self, parent, label, key, min_val, max_val, default, row):
        """슬라이더 컨트롤 생성"""
        # 라벨
        tk.Label(
            parent,
            text=label + ":",
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 11)
        ).grid(row=row, column=0, sticky='w', padx=20, pady=10)
        
        # 슬라이더
        var = tk.DoubleVar(value=default)
        self.effect_vars[key] = var
        
        slider = tk.Scale(
            parent,
            from_=min_val,
            to=max_val,
            orient='horizontal',
            variable=var,
            bg=self.colors['card'],
            fg=self.colors['text'],
            length=300,
            highlightthickness=0,
            resolution=0.1
        )
        slider.grid(row=row, column=1, sticky='w', padx=10)
        
        # 값 표시
        value_label = tk.Label(
            parent,
            textvariable=var,
            bg=self.colors['card'],
            fg=self.colors['accent'],
            font=('Segoe UI', 10),
            width=5
        )
        value_label.grid(row=row, column=2, sticky='w')
    
    def toggle_blank_settings(self):
        """백지 감지 설정 토글"""
        enabled = self.blank_enabled_var.get()
        # 하위 컨트롤들 활성/비활성화
        if hasattr(self, 'threshold_scale'):
            state = 'normal' if enabled else 'disabled'
            self.threshold_scale.configure(state=state)
    
    def apply_preset(self, preset_id):
        """프리셋 적용 - 프리셋의 독립적인 설정을 로드"""
        try:
            # 프리셋 키 결정
            preset_key = '1' if preset_id == 'default' else preset_id.split('_')[-1]
            
            self.logger.info(f"프리셋 적용 시작: {preset_id} (키: {preset_key})")
            
            # 프리셋 데이터 가져오기
            preset_data = self.preset_manager.get_preset_data(preset_id) or {}
            
            if preset_data and 'settings' in preset_data:
                # 프리셋의 설정을 현재 설정으로 적용 - 깊은 복사로 독립성 보장
                stored_settings = copy.deepcopy(preset_data['settings'])
                
                # 좌표 설정 적용
                if 'coordinates' in stored_settings:
                    self.settings_manager.set('coordinates', stored_settings['coordinates'])
                
                # 백지 감지 설정 적용
                if 'blank_detection' in stored_settings:
                    self.settings_manager.set('blank_detection', stored_settings['blank_detection'])
                
                # 썸네일 효과 설정 적용
                if 'thumbnail' in stored_settings:
                    self.settings_manager.set('thumbnail', stored_settings['thumbnail'])
                
                # 성능 설정 적용
                if 'performance' in stored_settings:
                    self.settings_manager.set('performance', stored_settings['performance'])
                
                # UI 업데이트 - 안전하게 처리
                try:
                    self.load_current_settings()
                except Exception as e:
                    self.logger.warning(f"설정 로드 중 경고: {e}")
                
                # 박스 목록 업데이트 - 위젯이 존재하는 경우만
                try:
                    if hasattr(self, 'list_scroll') and self.list_scroll.winfo_exists():
                        self.update_box_list()
                except Exception as e:
                    self.logger.warning(f"박스 목록 업데이트 중 경고: {e}")
                
                # 미리보기 업데이트 - 위젯이 존재하는 경우만
                try:
                    if hasattr(self, 'coord_preview') and hasattr(self.coord_preview, 'refresh'):
                        self.coord_preview.refresh()
                except Exception as e:
                    self.logger.warning(f"미리보기 업데이트 중 경고: {e}")
                
                messagebox.showinfo("불러오기 완료", f"프리셋 '{preset_data.get('name', preset_id)}'의 설정을 불러왔습니다.")
            else:
                # 프리셋에 설정이 없는 경우 현재 설정을 저장할지 묻기
                response = messagebox.askyesno(
                    "프리셋 설정 없음", 
                    f"프리셋 '{preset_data.get('name', preset_id)}'에 저장된 설정이 없습니다.\n현재 설정을 이 프리셋에 저장하시겠습니까?"
                )
                if response:
                    self.save_to_preset(preset_id)
        except Exception as e:
            self.logger.error(f"프리셋 적용 실패: {e}")
            messagebox.showerror("오류", f"프리셋 적용 실패: {e}")
    
    def save_to_preset(self, preset_id):
        """현재 설정을 프리셋으로 저장 - 독립적인 프리셋 설정"""
        try:
            # 프리셋 키 결정
            preset_key = '1' if preset_id == 'default' else preset_id.split('_')[-1]
            
            # 현재 설정 수집 - 깊은 복사로 독립적인 데이터 생성
            current_settings = {
                'coordinates': copy.deepcopy(self.settings_manager.get('coordinates')),
                'blank_detection': copy.deepcopy(self.settings_manager.get('blank_detection')),
                'thumbnail': copy.deepcopy(self.settings_manager.get('thumbnail')),
                'performance': copy.deepcopy(self.settings_manager.get('performance'))
            }
            
            # 프리셋에 설정 저장 (preset_manager의 메서드 사용)
            self.preset_manager.save_preset(preset_id, current_settings)
            
            # 프리셋 페이지 새로고침 - 안전하게 처리
            try:
                if hasattr(self, 'active_menu_index') and self.active_menu_index == 4:
                    self.show_presets_page()
            except Exception as e:
                self.logger.warning(f"프리셋 페이지 새로고침 중 경고: {e}")
            
            preset_data = self.preset_manager.get_preset_data(preset_id)
            preset_name = preset_data.get('name', preset_id) if preset_data else preset_id
            messagebox.showinfo("저장 완료", f"현재 작업 중인 설정을 프리셋 '{preset_name}'에 저장했습니다.")
        except Exception as e:
            self.logger.error(f"프리셋 저장 실패: {e}")
            messagebox.showerror("오류", f"프리셋 저장 실패: {e}")
    
    def change_hotkey(self, preset_id):
        """프리셋 핫키 변경 - 직접 입력 가능"""
        current_hotkey = self.preset_hotkeys.get(preset_id, '')
        
        # 핫키 입력 다이얼로그 - 크기 확대
        dialog = tk.Toplevel(self.window)
        dialog.title("핫키 변경")
        dialog.geometry("450x500")
        dialog.configure(bg=self.colors['bg'])
        
        # 중앙 배치
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 450) // 2
        y = (dialog.winfo_screenheight() - 500) // 2
        dialog.geometry(f"450x500+{x}+{y}")
        
        # 타이틀
        tk.Label(
            dialog,
            text="핫키 직접 입력",
            font=('맑은 고딕', 12, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text']
        ).pack(pady=15)
        
        # 현재 핫키
        tk.Label(
            dialog,
            text=f"현재: {current_hotkey}",
            font=('맑은 고딕', 10),
            bg=self.colors['bg'],
            fg=self.colors['subtext']
        ).pack(pady=5)
        
        # 입력 프레임
        input_frame = tk.Frame(dialog, bg=self.colors['card'])
        input_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 핫키 직접 입력 필드
        tk.Label(
            input_frame,
            text="새 핫키 입력:",
            font=('맑은 고딕', 11),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(pady=8)
        
        hotkey_var = tk.StringVar(value=current_hotkey)
        hotkey_entry = tk.Entry(
            input_frame,
            textvariable=hotkey_var,
            font=('맑은 고딕', 12),
            bg=self.colors['input_bg'],
            fg=self.colors['text'],
            justify='center',
            width=25
        )
        hotkey_entry.pack(pady=8)
        hotkey_entry.focus()
        
        # 예시 텍스트
        tk.Label(
            input_frame,
            text="예시: F1, F2, Ctrl+1, Shift+F1, Alt+A, Ctrl+Shift+S",
            font=('맑은 고딕', 9),
            bg=self.colors['card'],
            fg=self.colors['subtext']
        ).pack(pady=3)
        
        # 추천 핫키 리스트
        recommendations_frame = tk.Frame(input_frame, bg=self.colors['card'])
        recommendations_frame.pack(pady=10, fill='both', expand=True)
        
        tk.Label(
            recommendations_frame,
            text="추천 핫키:",
            font=('맑은 고딕', 10, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(pady=5)
        
        # 추천 버튼들 - 확장된 목록
        recommend_groups = [
            ("기본 Function 키", ['F1', 'F2', 'F3', 'F4', 'F5', 'F6']),
            ("Ctrl 조합", ['Ctrl+1', 'Ctrl+2', 'Ctrl+3', 'Ctrl+4', 'Ctrl+Q', 'Ctrl+W']),
            ("Alt 조합", ['Alt+1', 'Alt+2', 'Alt+Q', 'Alt+W', 'Alt+E', 'Alt+R']),
            ("Shift 조합", ['Shift+F1', 'Shift+F2', 'Shift+F3', 'Shift+F4']),
            ("복합 조합", ['Ctrl+Shift+1', 'Ctrl+Shift+2', 'Ctrl+Alt+1', 'Alt+Shift+Q'])
        ]
        
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(recommendations_frame, bg=self.colors['card'], height=200)
        scrollbar = tk.Scrollbar(recommendations_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['card'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for group_name, keys in recommend_groups:
            # 그룹 라벨
            group_label = tk.Label(
                scrollable_frame,
                text=group_name,
                font=('맑은 고딕', 9),
                bg=self.colors['card'],
                fg=self.colors['subtext']
            )
            group_label.pack(pady=(5, 2), anchor='w', padx=10)
            
            # 그룹 버튼 프레임
            group_frame = tk.Frame(scrollable_frame, bg=self.colors['card'])
            group_frame.pack(pady=2, padx=10, fill='x')
            
            for i, key in enumerate(keys):
                tk.Button(
                    group_frame,
                    text=key,
                    command=lambda k=key: hotkey_var.set(k),
                    bg=self.colors['hover'],
                    fg=self.colors['text'],
                    font=('맑은 고딕', 8),
                    bd=0,
                    padx=6,
                    pady=2,
                    cursor='hand2',
                    width=12
                ).grid(row=i//3, column=i%3, padx=2, pady=2, sticky='w')
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 버튼들
        btn_frame = tk.Frame(dialog, bg=self.colors['bg'])
        btn_frame.pack(pady=20)
        
        def apply_hotkey():
            new_hotkey = hotkey_var.get().strip()
            
            # 빈 값 체크
            if not new_hotkey:
                messagebox.showwarning("경고", "핫키를 입력해주세요.")
                return
            
            # 핫키 형식 검증 (기본적인 검증만)
            valid_modifiers = ['Ctrl', 'Alt', 'Shift', 'Win']
            parts = new_hotkey.split('+')
            
            # 최소한 하나의 키가 있어야 함
            if len(parts) == 0:
                messagebox.showwarning("경고", "올바른 핫키 형식이 아닙니다.")
                return
            
            # 중복 체크
            for pid, hkey in self.preset_hotkeys.items():
                if pid != preset_id and hkey.lower() == new_hotkey.lower():
                    response = messagebox.askyesno(
                        "중복 확인", 
                        f"{new_hotkey}는 이미 다른 프리셋에서 사용 중입니다.\n그래도 사용하시겠습니까?"
                    )
                    if not response:
                        return
            
            self.preset_hotkeys[preset_id] = new_hotkey
            # 프리셋 매니저에도 업데이트
            self.preset_manager.update_preset_hotkey(preset_id, new_hotkey)
            
            dialog.destroy()
            self.show_presets_page()  # 페이지 새로고침
        
        # Enter 키로도 적용 가능
        hotkey_entry.bind('<Return>', lambda e: apply_hotkey())
        
        tk.Button(
            btn_frame,
            text="적용",
            command=apply_hotkey,
            bg=self.colors['success'],
            fg='white',
            font=('맑은 고딕', 10),
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            btn_frame,
            text="취소",
            command=dialog.destroy,
            bg=self.colors['error'],
            fg='white',
            font=('맑은 고딕', 10),
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2'
        ).pack(side='left', padx=5)
    
    def center_window(self):
        """윈도우를 화면 중앙에 배치"""
        self.window.update_idletasks()
        
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        window_width = 1400
        window_height = 800
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def run(self):
        """설정 창 실행"""
        self.window.grab_set()  # 모달 창으로 설정
        self.window.mainloop()