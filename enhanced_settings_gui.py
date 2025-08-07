import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import fitz
from PIL import Image, ImageTk, ImageDraw, ImageEnhance, ImageOps
import json
import os
from pathlib import Path
from datetime import datetime
import numpy as np
from collections import defaultdict
import threading
import queue

class EnhancedSettingsGUI:
    def __init__(self, parent=None):
        self.parent = parent
        self.window = tk.Toplevel() if parent else tk.Tk()
        self.window.title("인쇄 자동화 - 고급 설정")
        self.window.geometry("1200x800")
        
        # 설정값 초기화
        self.settings = self.load_settings()
        self.sample_pdf = None
        self.preview_image = None
        self.canvas_scale = 1.0
        
        # 현재 선택된 항목
        self.selected_item = None
        self.selected_index = 0
        
        # 백지 감지 캐시
        self.blank_detection_cache = {}
        
        # 처리 큐
        self.processing_queue = queue.Queue()
        
        self.setup_ui()
        
    def load_settings(self):
        """저장된 설정 로드 또는 기본값 사용"""
        settings_path = Path("enhanced_settings.json")
        
        if settings_path.exists():
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 확장된 기본값
        return {
            "thumbnail": {
                "max_width": 160,
                "max_height": 250,
                "positions": [
                    {"x": 70, "y": 180},
                    {"x": 490, "y": 180}
                ],
                "multi_page": False,
                "page_selection": "1",  # "1", "1-3", "1,3,5" 등
                "grayscale": False,
                "contrast": 1.0,  # 0.5 ~ 2.0
                "sharpness": 1.0  # 0.5 ~ 2.0
            },
            "qr": {
                "max_width": 50,
                "max_height": 50,
                "positions": [
                    {"x": 230, "y": 470},
                    {"x": 650, "y": 470}
                ]
            },
            "blank_detection": {
                "enabled": False,
                "threshold": 95,  # 80~100%
                "algorithm": "simple",  # simple, entropy, histogram
                "exclude_areas": {
                    "header": 50,  # 상단 제외 픽셀
                    "footer": 50,  # 하단 제외 픽셀
                    "left_margin": 20,  # 좌측 제외 픽셀
                    "right_margin": 20  # 우측 제외 픽셀
                },
                "cache_enabled": True
            },
            "presets": {
                "default": {
                    "name": "기본",
                    "description": "표준 설정",
                    "last_used": None,
                    "use_count": 0,
                    "hotkey": "F3",
                    "settings": {}  # 현재 설정의 복사본
                }
            },
            "processing_rules": {
                "enabled": False,
                "rules": [
                    {
                        "name": "표지 자동 크롭",
                        "pattern": "표지|cover",
                        "action": "crop_right_half",
                        "preset": None
                    }
                ]
            },
            "performance": {
                "multithreading": True,
                "max_concurrent_files": 3,
                "cache_size_mb": 100
            }
        }
    
    def save_settings(self):
        """설정을 JSON 파일로 저장"""
        try:
            with open("enhanced_settings.json", 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("저장 완료", "설정이 저장되었습니다.")
            return True
        except Exception as e:
            messagebox.showerror("저장 실패", f"설정 저장 중 오류가 발생했습니다:\n{str(e)}")
            return False
    
    def setup_ui(self):
        # 노트북 (탭) 위젯 생성
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 각 탭 생성
        self.create_position_tab()
        self.create_blank_detection_tab()
        self.create_preset_tab()
        self.create_thumbnail_options_tab()
        self.create_processing_rules_tab()
        self.create_performance_tab()
        
        # 하단 버튼 프레임
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="저장", command=self.save_and_close).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="취소", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="적용", command=self.apply_settings).pack(side=tk.RIGHT, padx=5)
    
    def create_position_tab(self):
        """위치 설정 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="위치 설정")
        
        # 기존 위치 설정 UI를 여기에 구현
        main_frame = ttk.Frame(tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 왼쪽: 미리보기 영역
        preview_frame = ttk.LabelFrame(main_frame, text="미리보기", padding="10")
        preview_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # PDF 로드 버튼
        load_btn = ttk.Button(preview_frame, text="샘플 PDF 열기", command=self.load_sample_pdf)
        load_btn.pack(pady=(0, 10))
        
        # Canvas for preview
        self.canvas = tk.Canvas(preview_frame, width=600, height=500, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # 오른쪽: 설정 컨트롤
        control_frame = ttk.LabelFrame(main_frame, text="위치 및 크기 설정", padding="10")
        control_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 항목 선택
        ttk.Label(control_frame, text="설정 항목:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.item_var = tk.StringVar(value="thumbnail_left")
        items = [
            ("썸네일 - 좌측", "thumbnail_left"),
            ("썸네일 - 우측", "thumbnail_right"),
            ("QR 코드 - 좌측", "qr_left"),
            ("QR 코드 - 우측", "qr_right")
        ]
        for i, (text, value) in enumerate(items):
            ttk.Radiobutton(control_frame, text=text, variable=self.item_var, 
                          value=value, command=self.update_selection).grid(row=i+1, column=0, sticky=tk.W, padx=20)
        
        # 위치 설정
        ttk.Label(control_frame, text="위치 (X, Y):").grid(row=6, column=0, sticky=tk.W, pady=5)
        
        pos_frame = ttk.Frame(control_frame)
        pos_frame.grid(row=7, column=0, sticky=tk.W, padx=20)
        
        ttk.Label(pos_frame, text="X:").pack(side=tk.LEFT)
        self.x_var = tk.IntVar(value=0)
        self.x_spinbox = ttk.Spinbox(pos_frame, from_=0, to=842, width=10, 
                                    textvariable=self.x_var, command=self.update_preview)
        self.x_spinbox.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(pos_frame, text="Y:").pack(side=tk.LEFT, padx=(10, 0))
        self.y_var = tk.IntVar(value=0)
        self.y_spinbox = ttk.Spinbox(pos_frame, from_=0, to=595, width=10, 
                                    textvariable=self.y_var, command=self.update_preview)
        self.y_spinbox.pack(side=tk.LEFT, padx=5)
        
        # 크기 설정
        ttk.Label(control_frame, text="최대 크기:").grid(row=8, column=0, sticky=tk.W, pady=(10, 5))
        
        size_frame = ttk.Frame(control_frame)
        size_frame.grid(row=9, column=0, sticky=tk.W, padx=20)
        
        ttk.Label(size_frame, text="너비:").pack(side=tk.LEFT)
        self.width_var = tk.IntVar(value=0)
        self.width_spinbox = ttk.Spinbox(size_frame, from_=10, to=300, width=10,
                                        textvariable=self.width_var, command=self.update_preview)
        self.width_spinbox.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(size_frame, text="높이:").pack(side=tk.LEFT, padx=(10, 0))
        self.height_var = tk.IntVar(value=0)
        self.height_spinbox = ttk.Spinbox(size_frame, from_=10, to=300, width=10,
                                         textvariable=self.height_var, command=self.update_preview)
        self.height_spinbox.pack(side=tk.LEFT, padx=5)
        
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
    
    def create_blank_detection_tab(self):
        """백지 감지 설정 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="백지 감지")
        
        main_frame = ttk.Frame(tab, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 백지 감지 활성화
        self.blank_detection_enabled = tk.BooleanVar(value=self.settings["blank_detection"]["enabled"])
        ttk.Checkbutton(main_frame, text="백지 감지 활성화", 
                       variable=self.blank_detection_enabled,
                       command=self.toggle_blank_detection).grid(row=0, column=0, sticky=tk.W, pady=10)
        
        # 설정 프레임
        settings_frame = ttk.LabelFrame(main_frame, text="감지 설정", padding="10")
        settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # 임계값 슬라이더
        ttk.Label(settings_frame, text="백지 임계값:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.threshold_var = tk.IntVar(value=self.settings["blank_detection"]["threshold"])
        self.threshold_slider = ttk.Scale(settings_frame, from_=80, to=100, 
                                         variable=self.threshold_var,
                                         orient=tk.HORIZONTAL, length=300)
        self.threshold_slider.grid(row=0, column=1, padx=10)
        self.threshold_label = ttk.Label(settings_frame, text=f"{self.threshold_var.get()}%")
        self.threshold_label.grid(row=0, column=2)
        
        self.threshold_slider.configure(command=lambda v: self.threshold_label.config(text=f"{int(float(v))}%"))
        
        # 알고리즘 선택
        ttk.Label(settings_frame, text="감지 알고리즘:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.algorithm_var = tk.StringVar(value=self.settings["blank_detection"]["algorithm"])
        algorithm_frame = ttk.Frame(settings_frame)
        algorithm_frame.grid(row=1, column=1, sticky=tk.W)
        
        algorithms = [
            ("단순 (빠름)", "simple"),
            ("엔트로피 (정확)", "entropy"),
            ("히스토그램 (균형)", "histogram")
        ]
        for text, value in algorithms:
            ttk.Radiobutton(algorithm_frame, text=text, variable=self.algorithm_var,
                          value=value).pack(side=tk.LEFT, padx=5)
        
        # 제외 영역 설정
        exclude_frame = ttk.LabelFrame(main_frame, text="제외 영역 (픽셀)", padding="10")
        exclude_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # 헤더/푸터
        ttk.Label(exclude_frame, text="상단:").grid(row=0, column=0, sticky=tk.W)
        self.header_exclude = tk.IntVar(value=self.settings["blank_detection"]["exclude_areas"]["header"])
        ttk.Spinbox(exclude_frame, from_=0, to=200, textvariable=self.header_exclude,
                   width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(exclude_frame, text="하단:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.footer_exclude = tk.IntVar(value=self.settings["blank_detection"]["exclude_areas"]["footer"])
        ttk.Spinbox(exclude_frame, from_=0, to=200, textvariable=self.footer_exclude,
                   width=10).grid(row=0, column=3, padx=5)
        
        # 좌우 여백
        ttk.Label(exclude_frame, text="좌측:").grid(row=1, column=0, sticky=tk.W)
        self.left_exclude = tk.IntVar(value=self.settings["blank_detection"]["exclude_areas"]["left_margin"])
        ttk.Spinbox(exclude_frame, from_=0, to=200, textvariable=self.left_exclude,
                   width=10).grid(row=1, column=1, padx=5)
        
        ttk.Label(exclude_frame, text="우측:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0))
        self.right_exclude = tk.IntVar(value=self.settings["blank_detection"]["exclude_areas"]["right_margin"])
        ttk.Spinbox(exclude_frame, from_=0, to=200, textvariable=self.right_exclude,
                   width=10).grid(row=1, column=3, padx=5)
        
        # 테스트 프레임
        test_frame = ttk.LabelFrame(main_frame, text="실시간 테스트", padding="10")
        test_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(test_frame, text="PDF 테스트", command=self.test_blank_detection).pack(side=tk.LEFT, padx=5)
        self.test_result_label = ttk.Label(test_frame, text="테스트 결과가 여기에 표시됩니다")
        self.test_result_label.pack(side=tk.LEFT, padx=20)
        
        # 캐싱 옵션
        self.cache_enabled = tk.BooleanVar(value=self.settings["blank_detection"]["cache_enabled"])
        ttk.Checkbutton(main_frame, text="감지 결과 캐싱 사용", 
                       variable=self.cache_enabled).grid(row=4, column=0, sticky=tk.W, pady=10)
    
    def create_preset_tab(self):
        """프리셋 관리 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="프리셋 관리")
        
        main_frame = ttk.Frame(tab, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 프리셋 목록
        list_frame = ttk.LabelFrame(main_frame, text="프리셋 목록", padding="10")
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 트리뷰로 프리셋 표시
        columns = ("name", "description", "last_used", "use_count", "hotkey")
        self.preset_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=15)
        
        self.preset_tree.heading("#0", text="ID")
        self.preset_tree.heading("name", text="이름")
        self.preset_tree.heading("description", text="설명")
        self.preset_tree.heading("last_used", text="마지막 사용")
        self.preset_tree.heading("use_count", text="사용 횟수")
        self.preset_tree.heading("hotkey", text="단축키")
        
        self.preset_tree.column("#0", width=50)
        self.preset_tree.column("name", width=100)
        self.preset_tree.column("description", width=200)
        self.preset_tree.column("last_used", width=150)
        self.preset_tree.column("use_count", width=80)
        self.preset_tree.column("hotkey", width=80)
        
        self.preset_tree.pack(fill=tk.BOTH, expand=True)
        
        # 프리셋 로드
        self.load_presets()
        
        # 프리셋 상세 설정
        detail_frame = ttk.LabelFrame(main_frame, text="프리셋 상세", padding="10")
        detail_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 이름
        ttk.Label(detail_frame, text="이름:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.preset_name_var = tk.StringVar()
        ttk.Entry(detail_frame, textvariable=self.preset_name_var, width=30).grid(row=0, column=1, padx=5)
        
        # 설명
        ttk.Label(detail_frame, text="설명:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.preset_desc_text = tk.Text(detail_frame, width=30, height=3)
        self.preset_desc_text.grid(row=1, column=1, padx=5)
        
        # 단축키
        ttk.Label(detail_frame, text="단축키:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.preset_hotkey_var = tk.StringVar()
        hotkey_frame = ttk.Frame(detail_frame)
        hotkey_frame.grid(row=2, column=1, sticky=tk.W)
        
        ttk.Entry(hotkey_frame, textvariable=self.preset_hotkey_var, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(hotkey_frame, text="녹화", command=self.record_hotkey).pack(side=tk.LEFT)
        
        # 버튼들
        button_frame = ttk.Frame(detail_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="새 프리셋", command=self.new_preset).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="현재 설정 저장", command=self.save_current_as_preset).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="적용", command=self.apply_preset).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="삭제", command=self.delete_preset).pack(side=tk.LEFT, padx=5)
        
        # 통계 정보
        stats_frame = ttk.LabelFrame(detail_frame, text="사용 통계", padding="10")
        stats_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.stats_label = ttk.Label(stats_frame, text="프리셋을 선택하세요")
        self.stats_label.pack()
        
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
    
    def create_thumbnail_options_tab(self):
        """썸네일 처리 옵션 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="썸네일 옵션")
        
        main_frame = ttk.Frame(tab, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 페이지 선택
        page_frame = ttk.LabelFrame(main_frame, text="페이지 선택", padding="10")
        page_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=10)
        
        self.multi_page_var = tk.BooleanVar(value=self.settings["thumbnail"].get("multi_page", False))
        ttk.Checkbutton(page_frame, text="다중 페이지 썸네일 사용",
                       variable=self.multi_page_var,
                       command=self.toggle_multi_page).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(page_frame, text="페이지 선택:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.page_selection_var = tk.StringVar(value=self.settings["thumbnail"].get("page_selection", "1"))
        page_entry = ttk.Entry(page_frame, textvariable=self.page_selection_var, width=30)
        page_entry.grid(row=1, column=1, padx=10)
        
        ttk.Label(page_frame, text="예: 1 (첫 페이지), 1-3 (1~3페이지), 1,3,5 (선택 페이지)").grid(row=2, column=0, columnspan=2, sticky=tk.W)
        
        # 이미지 처리 옵션
        image_frame = ttk.LabelFrame(main_frame, text="이미지 처리", padding="10")
        image_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # 흑백 변환
        self.grayscale_var = tk.BooleanVar(value=self.settings["thumbnail"].get("grayscale", False))
        ttk.Checkbutton(image_frame, text="흑백 변환",
                       variable=self.grayscale_var).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # 대비 조정
        ttk.Label(image_frame, text="대비:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.contrast_var = tk.DoubleVar(value=self.settings["thumbnail"].get("contrast", 1.0))
        contrast_scale = ttk.Scale(image_frame, from_=0.5, to=2.0,
                                  variable=self.contrast_var,
                                  orient=tk.HORIZONTAL, length=300)
        contrast_scale.grid(row=1, column=1, padx=10)
        self.contrast_label = ttk.Label(image_frame, text=f"{self.contrast_var.get():.1f}")
        self.contrast_label.grid(row=1, column=2)
        
        contrast_scale.configure(command=lambda v: self.contrast_label.config(text=f"{float(v):.1f}"))
        
        # 선명도 조정
        ttk.Label(image_frame, text="선명도:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.sharpness_var = tk.DoubleVar(value=self.settings["thumbnail"].get("sharpness", 1.0))
        sharpness_scale = ttk.Scale(image_frame, from_=0.5, to=2.0,
                                   variable=self.sharpness_var,
                                   orient=tk.HORIZONTAL, length=300)
        sharpness_scale.grid(row=2, column=1, padx=10)
        self.sharpness_label = ttk.Label(image_frame, text=f"{self.sharpness_var.get():.1f}")
        self.sharpness_label.grid(row=2, column=2)
        
        sharpness_scale.configure(command=lambda v: self.sharpness_label.config(text=f"{float(v):.1f}"))
        
        # 미리보기
        preview_frame = ttk.LabelFrame(main_frame, text="효과 미리보기", padding="10")
        preview_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(preview_frame, text="샘플 이미지 로드", command=self.load_sample_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(preview_frame, text="효과 적용 미리보기", command=self.preview_image_effects).pack(side=tk.LEFT, padx=5)
        
        self.preview_canvas = tk.Canvas(preview_frame, width=400, height=300, bg="gray")
        self.preview_canvas.pack(pady=10)
    
    def create_processing_rules_tab(self):
        """처리 규칙 엔진 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="처리 규칙")
        
        main_frame = ttk.Frame(tab, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 규칙 엔진 활성화
        self.rules_enabled = tk.BooleanVar(value=self.settings["processing_rules"]["enabled"])
        ttk.Checkbutton(main_frame, text="자동 처리 규칙 활성화",
                       variable=self.rules_enabled).grid(row=0, column=0, sticky=tk.W, pady=10)
        
        # 규칙 목록
        rules_frame = ttk.LabelFrame(main_frame, text="처리 규칙", padding="10")
        rules_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # 규칙 트리뷰
        columns = ("pattern", "action", "preset")
        self.rules_tree = ttk.Treeview(rules_frame, columns=columns, show="tree headings", height=10)
        
        self.rules_tree.heading("#0", text="규칙 이름")
        self.rules_tree.heading("pattern", text="파일명 패턴")
        self.rules_tree.heading("action", text="동작")
        self.rules_tree.heading("preset", text="적용 프리셋")
        
        self.rules_tree.column("#0", width=150)
        self.rules_tree.column("pattern", width=200)
        self.rules_tree.column("action", width=150)
        self.rules_tree.column("preset", width=150)
        
        self.rules_tree.pack(fill=tk.BOTH, expand=True)
        
        # 규칙 로드
        self.load_rules()
        
        # 규칙 편집
        edit_frame = ttk.LabelFrame(main_frame, text="규칙 편집", padding="10")
        edit_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # 규칙 이름
        ttk.Label(edit_frame, text="규칙 이름:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.rule_name_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.rule_name_var, width=30).grid(row=0, column=1, padx=5)
        
        # 파일명 패턴
        ttk.Label(edit_frame, text="파일명 패턴:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.rule_pattern_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.rule_pattern_var, width=30).grid(row=1, column=1, padx=5)
        ttk.Label(edit_frame, text="(정규식 또는 단순 텍스트)").grid(row=1, column=2, sticky=tk.W)
        
        # 동작 선택
        ttk.Label(edit_frame, text="동작:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.rule_action_var = tk.StringVar()
        actions = ["없음", "crop_right_half", "skip_blank_pages", "force_grayscale", "auto_rotate"]
        ttk.Combobox(edit_frame, textvariable=self.rule_action_var,
                    values=actions, width=28).grid(row=2, column=1, padx=5)
        
        # 프리셋 적용
        ttk.Label(edit_frame, text="프리셋:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.rule_preset_var = tk.StringVar()
        preset_names = list(self.settings["presets"].keys())
        ttk.Combobox(edit_frame, textvariable=self.rule_preset_var,
                    values=preset_names, width=28).grid(row=3, column=1, padx=5)
        
        # 버튼들
        button_frame = ttk.Frame(edit_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="규칙 추가", command=self.add_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="규칙 수정", command=self.update_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="규칙 삭제", command=self.delete_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="테스트", command=self.test_rule).pack(side=tk.LEFT, padx=5)
        
        main_frame.rowconfigure(1, weight=1)
    
    def create_performance_tab(self):
        """성능 옵션 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="성능 옵션")
        
        main_frame = ttk.Frame(tab, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 멀티스레딩
        threading_frame = ttk.LabelFrame(main_frame, text="멀티스레딩", padding="10")
        threading_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=10)
        
        self.multithreading_var = tk.BooleanVar(value=self.settings["performance"]["multithreading"])
        ttk.Checkbutton(threading_frame, text="멀티스레딩 사용",
                       variable=self.multithreading_var).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(threading_frame, text="동시 처리 파일 수:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.concurrent_files_var = tk.IntVar(value=self.settings["performance"]["max_concurrent_files"])
        ttk.Spinbox(threading_frame, from_=1, to=10, textvariable=self.concurrent_files_var,
                   width=10).grid(row=1, column=1, padx=10)
        
        # 캐싱
        cache_frame = ttk.LabelFrame(main_frame, text="캐싱", padding="10")
        cache_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(cache_frame, text="캐시 크기 (MB):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.cache_size_var = tk.IntVar(value=self.settings["performance"]["cache_size_mb"])
        ttk.Spinbox(cache_frame, from_=10, to=500, textvariable=self.cache_size_var,
                   increment=10, width=10).grid(row=0, column=1, padx=10)
        
        ttk.Button(cache_frame, text="캐시 비우기", command=self.clear_cache).grid(row=0, column=2, padx=10)
        
        # 성능 모니터
        monitor_frame = ttk.LabelFrame(main_frame, text="성능 모니터", padding="10")
        monitor_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        
        self.monitor_text = tk.Text(monitor_frame, width=60, height=10)
        self.monitor_text.pack()
        
        ttk.Button(monitor_frame, text="성능 테스트", command=self.run_performance_test).pack(pady=10)
    
    # 헬퍼 메서드들
    def load_sample_pdf(self):
        """샘플 PDF 파일 로드"""
        file_path = filedialog.askopenfilename(
            title="샘플 PDF 선택",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                doc = fitz.open(file_path)
                page = doc[0]
                
                # 미리보기용 스케일 계산
                canvas_width = 600
                canvas_height = 500
                
                scale = min(canvas_width / page.rect.width, canvas_height / page.rect.height) * 0.9
                self.canvas_scale = scale
                
                # 이미지 생성
                mat = fitz.Matrix(scale, scale)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_data = pix.pil_tobytes(format="PNG")
                
                from io import BytesIO
                img = Image.open(BytesIO(img_data))
                
                self.preview_image = img
                doc.close()
                
                self.update_preview()
                
            except Exception as e:
                messagebox.showerror("오류", f"PDF 로드 중 오류가 발생했습니다:\n{str(e)}")
    
    def update_selection(self):
        """선택된 항목에 따라 값 업데이트"""
        selected = self.item_var.get()
        
        if selected.startswith("thumbnail"):
            settings = self.settings["thumbnail"]
            self.selected_item = "thumbnail"
            self.selected_index = 0 if selected.endswith("left") else 1
        else:
            settings = self.settings["qr"]
            self.selected_item = "qr"
            self.selected_index = 0 if selected.endswith("left") else 1
        
        pos = settings["positions"][self.selected_index]
        self.x_var.set(pos["x"])
        self.y_var.set(pos["y"])
        self.width_var.set(settings["max_width"])
        self.height_var.set(settings["max_height"])
        
        self.update_preview()
    
    def update_preview(self):
        """미리보기 업데이트"""
        if not self.preview_image:
            return
        
        # 현재 설정값 저장
        if self.selected_item:
            settings = self.settings[self.selected_item]
            settings["positions"][self.selected_index]["x"] = self.x_var.get()
            settings["positions"][self.selected_index]["y"] = self.y_var.get()
            settings["max_width"] = self.width_var.get()
            settings["max_height"] = self.height_var.get()
        
        # 이미지 복사
        img = self.preview_image.copy()
        draw = ImageDraw.Draw(img)
        
        # 모든 위치에 사각형 그리기
        for i, pos in enumerate(self.settings["thumbnail"]["positions"]):
            x = int(pos["x"] * self.canvas_scale)
            y = int(pos["y"] * self.canvas_scale)
            w = int(self.settings["thumbnail"]["max_width"] * self.canvas_scale)
            h = int(self.settings["thumbnail"]["max_height"] * self.canvas_scale)
            
            color = "red" if self.selected_item == "thumbnail" and self.selected_index == i else "blue"
            width = 3 if self.selected_item == "thumbnail" and self.selected_index == i else 1
            
            draw.rectangle([x, y, x+w, y+h], outline=color, width=width)
            draw.text((x+2, y+2), f"썸네일 {i+1}", fill=color)
        
        # QR 위치
        for i, pos in enumerate(self.settings["qr"]["positions"]):
            x = int(pos["x"] * self.canvas_scale)
            y = int(pos["y"] * self.canvas_scale)
            w = int(self.settings["qr"]["max_width"] * self.canvas_scale)
            h = int(self.settings["qr"]["max_height"] * self.canvas_scale)
            
            color = "red" if self.selected_item == "qr" and self.selected_index == i else "green"
            width = 3 if self.selected_item == "qr" and self.selected_index == i else 1
            
            draw.rectangle([x, y, x+w, y+h], outline=color, width=width)
            draw.text((x+2, y+2), f"QR {i+1}", fill=color)
        
        # Canvas에 표시
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(300, 250, image=self.photo)
    
    def on_canvas_click(self, event):
        """캔버스 클릭시 위치 설정"""
        if not self.preview_image or not self.selected_item:
            return
        
        x = int(event.x / self.canvas_scale)
        y = int(event.y / self.canvas_scale)
        
        x = max(0, min(x, 842))
        y = max(0, min(y, 595))
        
        self.x_var.set(x)
        self.y_var.set(y)
        
        self.update_preview()
    
    def toggle_blank_detection(self):
        """백지 감지 토글"""
        enabled = self.blank_detection_enabled.get()
        self.settings["blank_detection"]["enabled"] = enabled
    
    def test_blank_detection(self):
        """백지 감지 테스트"""
        file_path = filedialog.askopenfilename(
            title="테스트할 PDF 선택",
            filetypes=[("PDF files", "*.pdf")]
        )
        
        if file_path:
            try:
                doc = fitz.open(file_path)
                blank_pages = []
                
                for i, page in enumerate(doc):
                    if self.is_page_blank(page):
                        blank_pages.append(i + 1)
                
                doc.close()
                
                if blank_pages:
                    self.test_result_label.config(text=f"백지 페이지: {blank_pages}")
                else:
                    self.test_result_label.config(text="백지 페이지가 없습니다")
                    
            except Exception as e:
                self.test_result_label.config(text=f"오류: {str(e)}")
    
    def is_page_blank(self, page):
        """페이지가 백지인지 확인"""
        algorithm = self.algorithm_var.get()
        threshold = self.threshold_var.get()
        
        # 페이지를 이미지로 변환
        pix = page.get_pixmap(dpi=150)
        img_data = pix.pil_tobytes(format="PNG")
        
        from io import BytesIO
        img = Image.open(BytesIO(img_data))
        
        # 제외 영역 적용
        exclude = self.settings["blank_detection"]["exclude_areas"]
        width, height = img.size
        crop_box = (
            exclude["left_margin"],
            exclude["header"],
            width - exclude["right_margin"],
            height - exclude["footer"]
        )
        img = img.crop(crop_box)
        
        # 알고리즘별 처리
        if algorithm == "simple":
            return self._simple_blank_detection(img, threshold)
        elif algorithm == "entropy":
            return self._entropy_blank_detection(img, threshold)
        else:  # histogram
            return self._histogram_blank_detection(img, threshold)
    
    def _simple_blank_detection(self, img, threshold):
        """단순 백지 감지"""
        gray = img.convert('L')
        pixels = np.array(gray)
        white_ratio = np.sum(pixels > 250) / pixels.size * 100
        return white_ratio > threshold
    
    def _entropy_blank_detection(self, img, threshold):
        """엔트로피 기반 백지 감지"""
        gray = img.convert('L')
        histogram = gray.histogram()
        histogram = [h for h in histogram if h > 0]
        
        if not histogram:
            return True
        
        total = sum(histogram)
        entropy = -sum((h/total) * np.log2(h/total) for h in histogram if h > 0)
        
        # 낮은 엔트로피는 백지를 의미
        return entropy < (100 - threshold) / 10
    
    def _histogram_blank_detection(self, img, threshold):
        """히스토그램 기반 백지 감지"""
        gray = img.convert('L')
        histogram = gray.histogram()
        
        # 백색 영역의 비율 계산
        white_pixels = sum(histogram[250:])
        total_pixels = sum(histogram)
        
        if total_pixels == 0:
            return True
        
        white_ratio = white_pixels / total_pixels * 100
        return white_ratio > threshold
    
    def load_presets(self):
        """프리셋 목록 로드"""
        self.preset_tree.delete(*self.preset_tree.get_children())
        
        for preset_id, preset_data in self.settings["presets"].items():
            last_used = preset_data.get("last_used", "없음")
            if last_used and last_used != "없음":
                last_used = datetime.fromisoformat(last_used).strftime("%Y-%m-%d %H:%M")
            
            self.preset_tree.insert("", "end", text=preset_id,
                                   values=(preset_data["name"],
                                          preset_data["description"],
                                          last_used,
                                          preset_data["use_count"],
                                          preset_data.get("hotkey", "")))
    
    def new_preset(self):
        """새 프리셋 생성"""
        preset_id = f"preset_{len(self.settings['presets'])}"
        self.settings["presets"][preset_id] = {
            "name": "새 프리셋",
            "description": "설명을 입력하세요",
            "last_used": None,
            "use_count": 0,
            "hotkey": "",
            "settings": {}
        }
        self.load_presets()
    
    def save_current_as_preset(self):
        """현재 설정을 프리셋으로 저장"""
        selected = self.preset_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "프리셋을 선택하세요")
            return
        
        preset_id = self.preset_tree.item(selected[0])["text"]
        
        # 현재 설정 복사
        current_settings = {
            "thumbnail": self.settings["thumbnail"].copy(),
            "qr": self.settings["qr"].copy(),
            "blank_detection": self.settings["blank_detection"].copy(),
            "processing_rules": self.settings["processing_rules"].copy(),
            "performance": self.settings["performance"].copy()
        }
        
        self.settings["presets"][preset_id]["settings"] = current_settings
        self.settings["presets"][preset_id]["name"] = self.preset_name_var.get()
        self.settings["presets"][preset_id]["description"] = self.preset_desc_text.get("1.0", "end-1c")
        self.settings["presets"][preset_id]["hotkey"] = self.preset_hotkey_var.get()
        
        messagebox.showinfo("저장", "프리셋이 저장되었습니다")
        self.load_presets()
    
    def apply_preset(self):
        """선택된 프리셋 적용"""
        selected = self.preset_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "프리셋을 선택하세요")
            return
        
        preset_id = self.preset_tree.item(selected[0])["text"]
        preset_settings = self.settings["presets"][preset_id].get("settings", {})
        
        if preset_settings:
            # 프리셋 설정 적용
            for key, value in preset_settings.items():
                self.settings[key] = value.copy()
            
            # 사용 통계 업데이트
            self.settings["presets"][preset_id]["last_used"] = datetime.now().isoformat()
            self.settings["presets"][preset_id]["use_count"] += 1
            
            messagebox.showinfo("적용", f"'{self.settings['presets'][preset_id]['name']}' 프리셋이 적용되었습니다")
            self.load_presets()
    
    def delete_preset(self):
        """프리셋 삭제"""
        selected = self.preset_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "프리셋을 선택하세요")
            return
        
        preset_id = self.preset_tree.item(selected[0])["text"]
        
        if preset_id == "default":
            messagebox.showwarning("경고", "기본 프리셋은 삭제할 수 없습니다")
            return
        
        if messagebox.askyesno("확인", "정말 삭제하시겠습니까?"):
            del self.settings["presets"][preset_id]
            self.load_presets()
    
    def record_hotkey(self):
        """단축키 녹화"""
        messagebox.showinfo("단축키 녹화", "단축키를 누르세요 (ESC로 취소)")
        # 실제 구현은 키보드 이벤트 처리 필요
    
    def toggle_multi_page(self):
        """다중 페이지 토글"""
        self.settings["thumbnail"]["multi_page"] = self.multi_page_var.get()
    
    def load_sample_image(self):
        """샘플 이미지 로드"""
        file_path = filedialog.askopenfilename(
            title="샘플 이미지 선택",
            filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*")]
        )
        
        if file_path:
            self.sample_image = Image.open(file_path)
            self.preview_image_effects()
    
    def preview_image_effects(self):
        """이미지 효과 미리보기"""
        if not hasattr(self, 'sample_image'):
            messagebox.showwarning("경고", "먼저 샘플 이미지를 로드하세요")
            return
        
        img = self.sample_image.copy()
        
        # 흑백 변환
        if self.grayscale_var.get():
            img = ImageOps.grayscale(img)
        
        # 대비 조정
        if self.contrast_var.get() != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(self.contrast_var.get())
        
        # 선명도 조정
        if self.sharpness_var.get() != 1.0:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(self.sharpness_var.get())
        
        # 캔버스에 표시
        img.thumbnail((400, 300), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(img)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(200, 150, image=self.preview_photo)
    
    def load_rules(self):
        """처리 규칙 로드"""
        self.rules_tree.delete(*self.rules_tree.get_children())
        
        for rule in self.settings["processing_rules"]["rules"]:
            self.rules_tree.insert("", "end", text=rule["name"],
                                  values=(rule["pattern"],
                                         rule["action"],
                                         rule.get("preset", "없음")))
    
    def add_rule(self):
        """규칙 추가"""
        new_rule = {
            "name": self.rule_name_var.get(),
            "pattern": self.rule_pattern_var.get(),
            "action": self.rule_action_var.get(),
            "preset": self.rule_preset_var.get() if self.rule_preset_var.get() else None
        }
        
        self.settings["processing_rules"]["rules"].append(new_rule)
        self.load_rules()
    
    def update_rule(self):
        """규칙 수정"""
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "수정할 규칙을 선택하세요")
            return
        
        rule_name = self.rules_tree.item(selected[0])["text"]
        
        for rule in self.settings["processing_rules"]["rules"]:
            if rule["name"] == rule_name:
                rule["name"] = self.rule_name_var.get()
                rule["pattern"] = self.rule_pattern_var.get()
                rule["action"] = self.rule_action_var.get()
                rule["preset"] = self.rule_preset_var.get() if self.rule_preset_var.get() else None
                break
        
        self.load_rules()
    
    def delete_rule(self):
        """규칙 삭제"""
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "삭제할 규칙을 선택하세요")
            return
        
        rule_name = self.rules_tree.item(selected[0])["text"]
        
        self.settings["processing_rules"]["rules"] = [
            r for r in self.settings["processing_rules"]["rules"]
            if r["name"] != rule_name
        ]
        
        self.load_rules()
    
    def test_rule(self):
        """규칙 테스트"""
        test_filename = tk.simpledialog.askstring("테스트", "테스트할 파일명을 입력하세요:")
        
        if test_filename:
            import re
            matched_rules = []
            
            for rule in self.settings["processing_rules"]["rules"]:
                if re.search(rule["pattern"], test_filename, re.IGNORECASE):
                    matched_rules.append(rule["name"])
            
            if matched_rules:
                messagebox.showinfo("매칭 결과", f"매칭된 규칙: {', '.join(matched_rules)}")
            else:
                messagebox.showinfo("매칭 결과", "매칭된 규칙이 없습니다")
    
    def clear_cache(self):
        """캐시 비우기"""
        self.blank_detection_cache.clear()
        messagebox.showinfo("완료", "캐시가 비워졌습니다")
    
    def run_performance_test(self):
        """성능 테스트"""
        import time
        
        self.monitor_text.delete("1.0", tk.END)
        self.monitor_text.insert("1.0", "성능 테스트 시작...\n")
        
        # 테스트 실행 (실제로는 별도 스레드에서 실행해야 함)
        def test():
            start_time = time.time()
            
            # 여기에 실제 테스트 코드
            self.monitor_text.insert(tk.END, f"멀티스레딩: {self.multithreading_var.get()}\n")
            self.monitor_text.insert(tk.END, f"동시 처리 파일: {self.concurrent_files_var.get()}\n")
            self.monitor_text.insert(tk.END, f"캐시 크기: {self.cache_size_var.get()}MB\n")
            
            time.sleep(1)  # 시뮬레이션
            
            elapsed = time.time() - start_time
            self.monitor_text.insert(tk.END, f"\n테스트 완료: {elapsed:.2f}초\n")
        
        threading.Thread(target=test, daemon=True).start()
    
    def apply_settings(self):
        """설정 적용"""
        # 백지 감지 설정 업데이트
        self.settings["blank_detection"]["enabled"] = self.blank_detection_enabled.get()
        self.settings["blank_detection"]["threshold"] = self.threshold_var.get()
        self.settings["blank_detection"]["algorithm"] = self.algorithm_var.get()
        self.settings["blank_detection"]["exclude_areas"]["header"] = self.header_exclude.get()
        self.settings["blank_detection"]["exclude_areas"]["footer"] = self.footer_exclude.get()
        self.settings["blank_detection"]["exclude_areas"]["left_margin"] = self.left_exclude.get()
        self.settings["blank_detection"]["exclude_areas"]["right_margin"] = self.right_exclude.get()
        self.settings["blank_detection"]["cache_enabled"] = self.cache_enabled.get()
        
        # 썸네일 옵션 업데이트
        self.settings["thumbnail"]["multi_page"] = self.multi_page_var.get()
        self.settings["thumbnail"]["page_selection"] = self.page_selection_var.get()
        self.settings["thumbnail"]["grayscale"] = self.grayscale_var.get()
        self.settings["thumbnail"]["contrast"] = self.contrast_var.get()
        self.settings["thumbnail"]["sharpness"] = self.sharpness_var.get()
        
        # 처리 규칙 업데이트
        self.settings["processing_rules"]["enabled"] = self.rules_enabled.get()
        
        # 성능 옵션 업데이트
        self.settings["performance"]["multithreading"] = self.multithreading_var.get()
        self.settings["performance"]["max_concurrent_files"] = self.concurrent_files_var.get()
        self.settings["performance"]["cache_size_mb"] = self.cache_size_var.get()
        
        messagebox.showinfo("적용", "설정이 적용되었습니다")
    
    def save_and_close(self):
        """저장하고 닫기"""
        self.apply_settings()
        if self.save_settings():
            if self.parent:
                # 메인 프로그램에 설정 변경 알림
                self.parent.reload_enhanced_settings()
            self.window.destroy()
    
    def run(self):
        """독립 실행시"""
        if not self.parent:
            self.window.mainloop()


if __name__ == "__main__":
    # 독립 실행 테스트
    app = EnhancedSettingsGUI()
    app.run()