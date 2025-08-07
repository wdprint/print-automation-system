class PrintAutomationGUI:
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("인쇄 의뢰서 자동화 시스템")
        self.root.geometry(f"{GUI_CONFIG['window_width']}x{GUI_CONFIG['window_height']}")
        self.root.resizable(GUI_CONFIG['resizable'], GUI_CONFIG['resizable'])
        
        # 항상 최상단
        if GUI_CONFIG['always_on_top']:
            self.root.attributes("-topmost", True)
        
        # 드롭된 파일들
        self.dropped_files = {
            'order_pdf': None,      # 의뢰서 PDF
            'print_pdf': None,      # 인쇄데이터 PDF
            'qr_image': None        # QR 이미지
        }
        
        # temp_normalized_file 속성 초기화
        self.temp_normalized_file = None
        
        # PrintProcessor 인스턴스 (코드 재사용)
        self.processor = PrintProcessor()
        
        self.setup_ui()
    
    def reload_settings(self):
        """설정 다시 로드"""
        global settings, PAGE_WIDTH, PAGE_HEIGHT, THUMBNAIL_CONFIG, QR_CONFIG, DEBUG_MODE, PROCESSING_CONFIG, BLANK_DETECTION
        settings = load_settings()
        PAGE_WIDTH = settings['PAGE_WIDTH']
        PAGE_HEIGHT = settings['PAGE_HEIGHT']
        THUMBNAIL_CONFIG = settings['THUMBNAIL_CONFIG']
        QR_CONFIG = settings['QR_CONFIG']
        PROCESSING_CONFIG = settings['PROCESSING_CONFIG']
        BLANK_DETECTION = settings['BLANK_DETECTION']
        DEBUG_MODE = settings['DEBUG_MODE']
        
        if DEBUG_MODE:
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
        
        # 설정 버튼
        settings_btn = tk.Button(
            button_container,
            text="⚙ 설정",
            font=("맑은 고딕", 10),
            bg="#e0e0e0",
            activebackground="#d0d0d0",
            command=self.open_settings,
            cursor="hand2",
            padx=10
        )
        settings_btn.pack(side=tk.LEFT, padx=2)
        
        # 드래그 앤 드롭 설정
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
    
    def open_settings(self):
        """통합 설정 창 열기"""
        try:
            # 향상된 설정 GUI 우선 시도
            from enhanced_settings_gui import EnhancedSettingsGUI
            settings_window = EnhancedSettingsGUI(parent=self)
            self.root.wait_window(settings_window.window)
            print("향상된 설정 GUI를 사용합니다.")
            return
        except ImportError:
            print("향상된 설정 GUI를 찾을 수 없습니다. 기본 설정을 사용합니다.")
        except Exception as e:
            print(f"향상된 설정 GUI 오류: {e}")
        
        try:
            # 기본 설정 매니저 시도
            settings_window = CoordPresetManager(parent=self)
            self.root.wait_window(settings_window.root)
        except Exception as e:
            messagebox.showerror("오류", f"설정 창을 열 수 없습니다:\n{str(e)}\n\n향상된 버전을 사용해보세요:\npython start_enhanced.py")
            print(f"설정 창 오류: {e}")
            import traceback
            traceback.print_exc()
        
    def on_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        
        for file_path in files:
            self.classify_file(file_path)
        
        self.update_file_list()
        
        # 의뢰서 PDF가 있고, 인쇄데이터 PDF 또는 QR 이미지 중 하나라도 있으면 실행
        if self.dropped_files['order_pdf'] and (self.dropped_files['print_pdf'] or self.dropped_files['qr_image']):
            self.status_label.config(text="처리 중...", fg="#0066cc")
            # 별도 스레드에서 실행하여 GUI가 멈추지 않도록 함
            threading.Thread(target=self.process_files, daemon=True).start()
        elif self.dropped_files['order_pdf']:
            self.status_label.config(text="인쇄데이터 PDF 또는 QR 이미지를 추가하세요", fg="#ff6600")
            
    def classify_file(self, file_path):
        ext = Path(file_path).suffix.lower()
        filename = os.path.basename(file_path)
        
        if ext == '.pdf':
            # 파일명에 '의뢰서'가 포함되어 있으면 의뢰서로 분류
            if '의뢰서' in filename:
                self.dropped_files['order_pdf'] = file_path
            else:
                self.dropped_files['print_pdf'] = file_path
                
        elif ext in ['.jpg', '.jpeg', '.png']:
            self.dropped_files['qr_image'] = file_path
            
    def update_file_list(self):
        # 기존 위젯 삭제
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()
            
        # 파일 목록 표시
        files_info = [
            ("의뢰서 PDF", self.dropped_files['order_pdf']),
            ("인쇄데이터 PDF", self.dropped_files['print_pdf']),
            ("QR 이미지", self.dropped_files['qr_image'])
        ]
        
        for label, file_path in files_info:
            if file_path:
                file_name = os.path.basename(file_path)
                text = f"✓ {label}: {file_name}"
                color = "#006600"
            else:
                if label == "의뢰서 PDF":
                    text = f"✗ {label}: 필수"
                    color = "#cc0000"
                else:
                    text = f"✗ {label}: 선택"
                    color = "#999999"
                
            file_label = tk.Label(
                self.file_list_frame,
                text=text,
                font=("맑은 고딕", 9),
                bg="#f0f0f0",
                fg=color,
                anchor="w"
            )
            file_label.pack(fill=tk.X, padx=20)
            
    def process_files(self):
        """GUI에서 파일 처리"""
        try:
            # ProcessorPrintProcessor 사용
            self.processor.dropped_files = self.dropped_files.copy()
            self.processor.process_files()
            
            # 완료 메시지
            self.root.after(0, self.show_completion)
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.show_error(msg))
            
    def show_completion(self):
        self.status_label.config(text="✓ 완료되었습니다!", fg="#006600")
        self.drop_label.config(text="새로운 파일을 드롭하여 다시 시작할 수 있습니다")
        
        # 3초 후 초기화
        self.root.after(3000, self.reset_state)
        
    def show_error(self, error_msg):
        self.status_label.config(text=f"❌ 오류: {error_msg}", fg="#cc0000")
        
    def reset_state(self):
        self.dropped_files = {
            'order_pdf': None,
            'print_pdf': None,
            'qr_image': None
        }
        self.update_file_list()
        self.status_label.config(text="대기 중...", fg="#666666")
        self.drop_label.config(text="파일을 여기에 드롭하세요")
        
    def run(self):
        self.root.mainloop()


# 필요한 패키지 설치 안내
def check_dependencies():
    required_packages = {
        'tkinterdnd2': 'tkinterdnd2',
        'fitz': 'PyMuPDF',
        'PIL': 'Pillow'
    }
    
    missing_packages = []
    
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("다음 패키지를 설치해주세요:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True


# 메인 실행 블록은 파일 끝에 있습니다

import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
import fitz  # PyMuPDF
from PIL import Image, ImageEnhance, ImageFilter
import os
from pathlib import Path
import threading
import shutil
import json
from io import BytesIO
import time  # 시간 측정용
import sys  # 명령줄 인자 처리용
from tkinter import ttk, filedialog, messagebox  # 프리셋 GUI용

# 설정 GUI 모듈 import
try:
    from settings_gui import SettingsGUI
    SETTINGS_GUI_AVAILABLE = True
except ImportError:
    SETTINGS_GUI_AVAILABLE = False
    print("settings_gui.py 파일이 없습니다. 설정 기능이 비활성화됩니다.")

# 정규화 모듈 import
try:
    from normalize_pdf import normalize_pdf as normalize_pdf_external
    NORMALIZE_AVAILABLE = True
except ImportError:
    NORMALIZE_AVAILABLE = False

# 설정 파일에서 로드 (settings.json 우선, 없으면 config.py, 그것도 없으면 기본값)
def load_settings():
    # 1. settings.json 확인
    settings_path = Path("settings.json")
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 기존 config.py 설정과 병합
                thumbnail_config = data.get('thumbnail', {})
                qr_config = data.get('qr', {})
                
                # config.py의 기본값 적용
                if 'white_background' not in thumbnail_config:
                    thumbnail_config['white_background'] = True
                if 'background_padding' not in thumbnail_config:
                    thumbnail_config['background_padding'] = 5
                
                # 백지 감지 설정 추가
                blank_detection = data.get('blank_detection', {
                    'enabled': True,
                    'threshold': 0.99,
                    'edge_margin': 20,
                    'max_pages': 10
                })
                
                return {
                    'PAGE_WIDTH': 842,
                    'PAGE_HEIGHT': 595,
                    'THUMBNAIL_CONFIG': thumbnail_config,
                    'QR_CONFIG': qr_config,
                    'GUI_CONFIG': data.get('gui', {
                        'window_width': 500, 'window_height': 400,
                        'always_on_top': True, 'resizable': False
                    }),
                    'PROCESSING_CONFIG': data.get('processing', {
                        'overwrite_original': True,
                        'backup_before_save': False,
                        'backup_suffix': '_backup',
                        'auto_normalize': True,
                        'rasterize_final': True
                    }),
                    'BLANK_DETECTION': blank_detection,
                    'DEBUG_MODE': data.get('debug', False)
                }
        except:
            pass
    
    # 2. config.py 확인
    try:
        import config
        thumbnail_config = getattr(config, 'THUMBNAIL_CONFIG', {
            'max_width': 160, 'max_height': 250,
            'positions': [{'x': 70, 'y': 180}, {'x': 490, 'y': 180}]
        })
        # 흰색 배경 옵션 추가 (기존 config.py와 호환성 유지)
        if 'white_background' not in thumbnail_config:
            thumbnail_config['white_background'] = True
        if 'background_padding' not in thumbnail_config:
            thumbnail_config['background_padding'] = 5
            
        return {
            'PAGE_WIDTH': getattr(config, 'PAGE_WIDTH', 842),
            'PAGE_HEIGHT': getattr(config, 'PAGE_HEIGHT', 595),
            'THUMBNAIL_CONFIG': thumbnail_config,
            'QR_CONFIG': getattr(config, 'QR_CONFIG', {
                'max_width': 50, 'max_height': 50,
                'positions': [{'x': 230, 'y': 470}, {'x': 650, 'y': 470}]
            }),
            'GUI_CONFIG': getattr(config, 'GUI_CONFIG', {
                'window_width': 500, 'window_height': 400,
                'always_on_top': True, 'resizable': False
            }),
            'PROCESSING_CONFIG': getattr(config, 'PROCESSING_CONFIG', {
                'overwrite_original': True,
                'backup_before_save': False,
                'backup_suffix': '_backup',
                'auto_normalize': True,
                'rasterize_final': True
            }),
            'BLANK_DETECTION': {
                'enabled': True,
                'threshold': 0.99,
                'edge_margin': 20,
                'max_pages': 10
            },
            'DEBUG_MODE': getattr(config, 'DEBUG_MODE', False)
        }
    except ImportError:
        pass
    
    # 3. 기본값 사용
    return {
        'PAGE_WIDTH': 842,
        'PAGE_HEIGHT': 595,
        'THUMBNAIL_CONFIG': {
            'max_width': 160, 'max_height': 250,
            'positions': [{'x': 70, 'y': 180}, {'x': 490, 'y': 180}],
            'white_background': True,  # 흰색 배경 기본값
            'background_padding': 5     # 배경 여백 기본값
        },
        'QR_CONFIG': {
            'max_width': 50, 'max_height': 50,
            'positions': [{'x': 230, 'y': 470}, {'x': 650, 'y': 470}]
        },
        'GUI_CONFIG': {
            'window_width': 500, 'window_height': 400,
            'always_on_top': True, 'resizable': False
        },
        'PROCESSING_CONFIG': {
            'overwrite_original': True,
            'backup_before_save': False,
            'backup_suffix': '_backup',
            'auto_normalize': True,
            'rasterize_final': True
        },
        'BLANK_DETECTION': {
            'enabled': True,
            'threshold': 0.99,
            'edge_margin': 20,
            'max_pages': 10
        },
        'DEBUG_MODE': False
    }

# 전역 설정 변수
settings = load_settings()
PAGE_WIDTH = settings['PAGE_WIDTH']
PAGE_HEIGHT = settings['PAGE_HEIGHT']
THUMBNAIL_CONFIG = settings['THUMBNAIL_CONFIG']
QR_CONFIG = settings['QR_CONFIG']
GUI_CONFIG = settings['GUI_CONFIG']
PROCESSING_CONFIG = settings['PROCESSING_CONFIG']
BLANK_DETECTION = settings['BLANK_DETECTION']
DEBUG_MODE = settings['DEBUG_MODE']

# 좌표 프리셋 관리 클래스
class CoordPresetManager:
    def __init__(self, parent=None):
        self.root = tk.Toplevel() if parent else tk.Tk()
        self.root.title("통합 설정 관리")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)
        
        # 부모 창 참조
        self.parent = parent
        
        # 스타일 설정
        style = ttk.Style()
        style.configure("Accent.TButton", foreground="blue")
        
        # 데이터 파일들
        self.coord_presets_file = Path("coord_presets.json")
        self.settings_file = Path("설정파일.ini")
        self.general_settings_file = Path("settings.json")
        
        # 데이터 로드
        self.coord_presets = self.load_coord_presets()
        self.hotkey_settings = self.load_hotkey_settings()
        self.general_settings = self.load_general_settings()
        
        # 현재 선택된 프리셋
        self.selected_preset = 1
        
        # sample PDF for preview
        self.sample_pdf = None
        self.preview_image = None
        self.canvas_scale = 1.0
        
        # 단축키 설명
        self.hotkey_descriptions = {
            "ProcessKey": "파일 처리",
            "SettingsKey": "설정 열기",
            "HelpKey": "도움말",
            "ResetKey": "초기화",
            "PresetManagerKey": "프리셋 관리"
        }
        
        # 단축키 변수들
        self.hotkey_vars = {}
        
        self.setup_ui()
        
    def load_coord_presets(self):
        """좌표 프리셋 로드"""
        if self.coord_presets_file.exists():
            try:
                with open(self.coord_presets_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 기본 프리셋
        default_presets = {}
        for i in range(1, 5):
            default_presets[str(i)] = {
                "name": f"프리셋 {i}",
                "hotkey": ["!q", "!w", "!e", "!r"][i-1],  # Alt+Q/W/E/R
                "thumbnail": {
                    "max_width": 160,
                    "max_height": 250,
                    "positions": [
                        {"x": 70, "y": 180},
                        {"x": 490, "y": 180}
                    ]
                },
                "qr": {
                    "max_width": 50,
                    "max_height": 50,
                    "positions": [
                        {"x": 230, "y": 470},
                        {"x": 650, "y": 470}
                    ]
                }
            }
        
        return default_presets
    
    def load_hotkey_settings(self):
        """전역 단축키 설정 로드"""
        settings = {
            "ProcessKey": "F3",
            "SettingsKey": "^F3",
            "HelpKey": "F1",
            "ResetKey": "^R",
            "PresetManagerKey": "^P"
        }
        
        if self.settings_file.exists():
            try:
                # INI 파일 읽기
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if '=' in line and not line.strip().startswith(';'):
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            if key in settings:
                                settings[key] = value
            except:
                pass
        
        return settings
    
    def load_general_settings(self):
        """일반 설정 로드"""
        if self.general_settings_file.exists():
            try:
                with open(self.general_settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        "show_tooltips": data.get("show_tooltips", True),
                        "play_sounds": data.get("play_sounds", True),
                        "tooltip_duration": data.get("tooltip_duration", 2000),
                        "blank_detection": data.get("blank_detection", {
                            "enabled": True,
                            "threshold": 0.99,
                            "edge_margin": 20,
                            "max_pages": 10
                        })
                    }
            except:
                pass
        
        # 기본값
        return {
            "show_tooltips": True,
            "play_sounds": True,
            "tooltip_duration": 2000,
            "blank_detection": {
                "enabled": True,
                "threshold": 0.99,
                "edge_margin": 20,
                "max_pages": 10
            }
        }
    
    def save_all_settings(self):
        """모든 설정 저장"""
        try:
            # 1. 좌표 프리셋 저장
            with open(self.coord_presets_file, 'w', encoding='utf-8') as f:
                json.dump(self.coord_presets, f, ensure_ascii=False, indent=2)
            
            # 2. 전역 단축키 저장 (INI 형식)
            ini_content = """; ========================================
;     인쇄 자동화 시스템 설정 파일
; ========================================

[Hotkeys]
; 파일 처리 단축키
ProcessKey={ProcessKey}

; 설정 프로그램 열기
SettingsKey={SettingsKey}

; 도움말 보기
HelpKey={HelpKey}

; 누적 파일 초기화
ResetKey={ResetKey}

; 프리셋 관리자 열기
PresetManagerKey={PresetManagerKey}

[General]
; 툴팁 표시 여부
ShowTooltips={show_tooltips}

; 처리 완료/실패 소리 재생 여부
PlaySounds={play_sounds}

; 툴팁 표시 시간 (밀리초)
TooltipDuration={tooltip_duration}
""".format(
                ProcessKey=self.hotkey_settings["ProcessKey"],
                SettingsKey=self.hotkey_settings["SettingsKey"],
                HelpKey=self.hotkey_settings["HelpKey"],
                ResetKey=self.hotkey_settings["ResetKey"],
                PresetManagerKey=self.hotkey_settings["PresetManagerKey"],
                show_tooltips="true" if self.general_settings["show_tooltips"] else "false",
                play_sounds="true" if self.general_settings["play_sounds"] else "false",
                tooltip_duration=self.general_settings["tooltip_duration"]
            )
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                f.write(ini_content)
            
            # 3. 일반 설정 + 백지 감지 설정 저장
            # 현재 settings.json 로드하여 업데이트
            current_settings = {}
            if self.general_settings_file.exists():
                try:
                    with open(self.general_settings_file, 'r', encoding='utf-8') as f:
                        current_settings = json.load(f)
                except:
                    pass
            
            # 백지 감지 설정 업데이트
            current_settings["blank_detection"] = self.general_settings["blank_detection"]
            current_settings["show_tooltips"] = self.general_settings["show_tooltips"]
            current_settings["play_sounds"] = self.general_settings["play_sounds"]
            current_settings["tooltip_duration"] = self.general_settings["tooltip_duration"]
            
            with open(self.general_settings_file, 'w', encoding='utf-8') as f:
                json.dump(current_settings, f, ensure_ascii=False, indent=2)
            
            # 4. AutoHotkey 리로드 플래그 생성
            reload_flag = Path("reload_settings.flag")
            reload_flag.touch()
            
            return True
            
        except Exception as e:
            messagebox.showerror("저장 실패", f"설정 저장 중 오류가 발생했습니다:\n{str(e)}")
            return False
    
    def setup_ui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 탭 컨트롤
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 탭 1: 좌표 프리셋
        self.setup_coord_preset_tab()
        
        # 탭 2: 전역 단축키
        self.setup_hotkey_tab()
        
        # 탭 3: 일반 설정
        self.setup_general_tab()
        
        # 하단 버튼
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="모두 저장", 
                  command=self.save_and_close,
                  style="Accent.TButton").pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="취소", 
                  command=self.root.destroy).pack(side=tk.RIGHT)
    
    def setup_coord_preset_tab(self):
        """좌표 프리셋 탭 설정"""
        preset_frame = ttk.Frame(self.notebook)
        self.notebook.add(preset_frame, text="좌표 프리셋")
        
        # 왼쪽: 프리셋 목록
        left_frame = ttk.Frame(preset_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(left_frame, text="프리셋 선택:", 
                 font=("맑은 고딕", 10, "bold")).pack(pady=(0, 10))
        
        self.preset_listbox = tk.Listbox(left_frame, width=20, height=10)
        self.preset_listbox.pack(fill=tk.BOTH, expand=True)
        self.preset_listbox.bind('<<ListboxSelect>>', self.on_preset_select)
        
        # 프리셋 목록 채우기
        for i in range(1, 5):
            preset = self.coord_presets[str(i)]
            self.preset_listbox.insert(tk.END, f"{preset['name']} ({preset['hotkey']})")
        
        self.preset_listbox.selection_set(0)
        
        # 오른쪽: 프리셋 편집
        right_frame = ttk.Frame(preset_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 프리셋 이름
        name_frame = ttk.Frame(right_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(name_frame, text="이름:").pack(side=tk.LEFT, padx=(0, 5))
        self.preset_name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.preset_name_var, width=30).pack(side=tk.LEFT)
        
        # 단축키
        hotkey_frame = ttk.Frame(right_frame)
        hotkey_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(hotkey_frame, text="단축키:").pack(side=tk.LEFT, padx=(0, 5))
        self.preset_hotkey_var = tk.StringVar()
        ttk.Entry(hotkey_frame, textvariable=self.preset_hotkey_var, width=20).pack(side=tk.LEFT)
        ttk.Label(hotkey_frame, text="(예: !q = Alt+Q)", 
                 foreground="gray").pack(side=tk.LEFT, padx=(10, 0))
        
        # 좌표 설정 프레임
        coord_frame = ttk.LabelFrame(right_frame, text="좌표 설정", padding="10")
        coord_frame.pack(fill=tk.BOTH, expand=True)
        
        # 미리보기와 좌표 편집
        preview_frame = ttk.Frame(coord_frame)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # PDF 로드 버튼
        ttk.Button(preview_frame, text="샘플 PDF 열기", 
                  command=self.load_sample_pdf).pack(pady=(0, 10))
        
        # Canvas for preview
        self.canvas = tk.Canvas(preview_frame, width=500, height=400, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # 좌표 편집 컨트롤
        control_frame = ttk.Frame(coord_frame)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))
        
        # 항목 선택
        ttk.Label(control_frame, text="편집 항목:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.edit_item_var = tk.StringVar(value="thumb_left")
        items = [
            ("썸네일 - 좌측", "thumb_left"),
            ("썸네일 - 우측", "thumb_right"),
            ("QR - 좌측", "qr_left"),
            ("QR - 우측", "qr_right")
        ]
        for i, (text, value) in enumerate(items):
            ttk.Radiobutton(control_frame, text=text, variable=self.edit_item_var,
                          value=value, command=self.update_coord_display).grid(
                              row=i+1, column=0, sticky=tk.W, padx=20)
        
        # 좌표 입력
        ttk.Separator(control_frame, orient='horizontal').grid(
            row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(control_frame, text="X:").grid(row=6, column=0, sticky=tk.W)
        self.x_var = tk.IntVar()
        ttk.Spinbox(control_frame, from_=0, to=842, width=10,
                    textvariable=self.x_var, command=self.update_preview).grid(
                        row=6, column=1, padx=5)
        
        ttk.Label(control_frame, text="Y:").grid(row=7, column=0, sticky=tk.W)
        self.y_var = tk.IntVar()
        ttk.Spinbox(control_frame, from_=0, to=595, width=10,
                    textvariable=self.y_var, command=self.update_preview).grid(
                        row=7, column=1, padx=5)
        
        # 크기 입력
        ttk.Label(control_frame, text="너비:").grid(row=8, column=0, sticky=tk.W, pady=(10, 0))
        self.width_var = tk.IntVar()
        ttk.Spinbox(control_frame, from_=10, to=300, width=10,
                    textvariable=self.width_var, command=self.update_preview).grid(
                        row=8, column=1, padx=5, pady=(10, 0))
        
        ttk.Label(control_frame, text="높이:").grid(row=9, column=0, sticky=tk.W)
        self.height_var = tk.IntVar()
        ttk.Spinbox(control_frame, from_=10, to=300, width=10,
                    textvariable=self.height_var, command=self.update_preview).grid(
                        row=9, column=1, padx=5)
        
        # 적용 버튼
        ttk.Button(control_frame, text="현재 좌표 저장",
                  command=self.save_current_coords).grid(
                      row=10, column=0, columnspan=2, pady=20)
    
    def setup_hotkey_tab(self):
        """전역 단축키 탭 설정"""
        hotkey_frame = ttk.Frame(self.notebook)
        self.notebook.add(hotkey_frame, text="전역 단축키")
        
        # 설명
        desc_label = ttk.Label(hotkey_frame, 
                             text="전역 단축키를 설정합니다. 수정자 키: ^ (Ctrl), ! (Alt), + (Shift), # (Win)",
                             wraplength=600)
        desc_label.pack(pady=(0, 20))
        
        # 단축키 설정 프레임
        settings_frame = ttk.LabelFrame(hotkey_frame, text="단축키 설정", padding="20")
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # 단축키 목록
        hotkey_items = [
            ("파일 처리", "ProcessKey", "선택한 파일들을 처리합니다"),
            ("설정 열기", "SettingsKey", "이 설정 창을 엽니다"),
            ("도움말", "HelpKey", "도움말을 표시합니다"),
            ("초기화", "ResetKey", "누적된 파일을 초기화합니다"),
            ("프리셋 관리", "PresetManagerKey", "프리셋 관리자를 엽니다")
        ]
        
        self.hotkey_vars = {}
        
        for i, (label, key, desc) in enumerate(hotkey_items):
            # 레이블
            ttk.Label(settings_frame, text=f"{label}:", 
                     font=("맑은 고딕", 10, "bold")).grid(
                         row=i*2, column=0, sticky=tk.W, pady=(10, 0))
            
            # 설명
            ttk.Label(settings_frame, text=desc, foreground="gray").grid(
                row=i*2, column=1, sticky=tk.W, padx=(20, 0), pady=(10, 0))
            
            # 입력 필드
            var = tk.StringVar(value=self.hotkey_settings[key])
            self.hotkey_vars[key] = var
            entry = ttk.Entry(settings_frame, textvariable=var, width=15)
            entry.grid(row=i*2+1, column=0, sticky=tk.W, pady=(5, 10))
            
            # 현재 설정 표시
            current_label = ttk.Label(settings_frame, 
                                    text=f"현재: {self.hotkey_settings[key]}",
                                    foreground="blue")
            current_label.grid(row=i*2+1, column=1, sticky=tk.W, padx=(20, 0), pady=(5, 10))
        
        # 기본값 복원 버튼
        ttk.Button(settings_frame, text="기본값 복원", 
                  command=self.restore_default_hotkeys).grid(row=len(self.hotkey_descriptions)*2, column=0, columnspan=2, pady=20)
    
    def setup_general_tab(self):
        """일반 설정 탭"""
        general_frame = ttk.Frame(self.notebook)
        self.notebook.add(general_frame, text="일반 설정")
        
        # 일반 설정
        general_settings = ttk.LabelFrame(general_frame, text="일반 설정", padding="20")
        general_settings.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # 툴팁 표시
        self.show_tooltips_var = tk.BooleanVar(value=self.general_settings["show_tooltips"])
        ttk.Checkbutton(general_settings, text="툴팁 표시", 
                       variable=self.show_tooltips_var).pack(anchor=tk.W, pady=5)
        
        # 소리 재생
        self.play_sounds_var = tk.BooleanVar(value=self.general_settings["play_sounds"])
        ttk.Checkbutton(general_settings, text="처리 완료/실패 소리 재생", 
                       variable=self.play_sounds_var).pack(anchor=tk.W, pady=5)
        
        # 툴팁 표시 시간
        tooltip_frame = ttk.Frame(general_settings)
        tooltip_frame.pack(anchor=tk.W, pady=5)
        
        ttk.Label(tooltip_frame, text="툴팁 표시 시간:").pack(side=tk.LEFT)
        self.tooltip_duration_var = tk.IntVar(value=self.general_settings["tooltip_duration"])
        ttk.Spinbox(tooltip_frame, from_=500, to=10000, increment=500, width=10,
                   textvariable=self.tooltip_duration_var).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(tooltip_frame, text="밀리초").pack(side=tk.LEFT, padx=(5, 0))
        
        # 백지 감지 설정
        blank_frame = ttk.LabelFrame(general_frame, text="백지 감지 설정", padding="20")
        blank_frame.pack(fill=tk.X, padx=20)
        
        # 백지 감지 활성화
        self.blank_detection_enabled_var = tk.BooleanVar(
            value=self.general_settings["blank_detection"]["enabled"])
        ttk.Checkbutton(blank_frame, text="백지 감지 활성화", 
                       variable=self.blank_detection_enabled_var,
                       command=self.toggle_blank_detection).pack(anchor=tk.W, pady=5)
        
        # 백지 감지 옵션들
        self.blank_options_frame = ttk.Frame(blank_frame)
        self.blank_options_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 백지 임계값
        threshold_frame = ttk.Frame(self.blank_options_frame)
        threshold_frame.pack(anchor=tk.W, pady=5)
        
        ttk.Label(threshold_frame, text="백지 임계값:").pack(side=tk.LEFT)
        self.blank_threshold_var = tk.DoubleVar(
            value=self.general_settings["blank_detection"]["threshold"])
        threshold_scale = ttk.Scale(threshold_frame, from_=0.9, to=1.0, 
                                   variable=self.blank_threshold_var,
                                   orient=tk.HORIZONTAL, length=200)
        threshold_scale.pack(side=tk.LEFT, padx=(5, 0))
        self.threshold_label = ttk.Label(threshold_frame, text="99%")
        self.threshold_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 임계값 변경 시 레이블 업데이트
        def update_threshold_label(*args):
            value = self.blank_threshold_var.get()
            self.threshold_label.config(text=f"{value*100:.0f}%")
        self.blank_threshold_var.trace('w', update_threshold_label)
        
        # 재단선 여백
        margin_frame = ttk.Frame(self.blank_options_frame)
        margin_frame.pack(anchor=tk.W, pady=5)
        
        ttk.Label(margin_frame, text="재단선 여백:").pack(side=tk.LEFT)
        self.edge_margin_var = tk.IntVar(
            value=self.general_settings["blank_detection"]["edge_margin"])
        ttk.Spinbox(margin_frame, from_=0, to=50, width=10,
                   textvariable=self.edge_margin_var).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(margin_frame, text="픽셀").pack(side=tk.LEFT, padx=(5, 0))
        
        # 최대 검색 페이지
        max_pages_frame = ttk.Frame(self.blank_options_frame)
        max_pages_frame.pack(anchor=tk.W, pady=5)
        
        ttk.Label(max_pages_frame, text="최대 검색 페이지:").pack(side=tk.LEFT)
        self.max_pages_var = tk.IntVar(
            value=self.general_settings["blank_detection"]["max_pages"])
        ttk.Spinbox(max_pages_frame, from_=1, to=20, width=10,
                   textvariable=self.max_pages_var).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(max_pages_frame, text="페이지").pack(side=tk.LEFT, padx=(5, 0))
        
        # 설명
        desc_text = """백지 감지 기능은 PDF의 첫 페이지가 백지인 경우 자동으로 다음 페이지를 찾아 썸네일로 사용합니다.
• 임계값: 페이지가 백지로 판단되는 기준 (99% = 거의 완전한 백지)
• 재단선 여백: 페이지 가장자리의 재단선을 무시할 픽셀 수
• 최대 검색: 백지가 아닌 페이지를 찾기 위해 검색할 최대 페이지 수"""
        
        ttk.Label(self.blank_options_frame, text=desc_text, 
                 foreground="gray", wraplength=500).pack(anchor=tk.W, pady=(20, 0))
        
        # 초기 상태 설정
        self.toggle_blank_detection()
    
    def toggle_blank_detection(self):
        """백지 감지 옵션 활성화/비활성화"""
        if self.blank_detection_enabled_var.get():
            for child in self.blank_options_frame.winfo_children():
                child.configure(state='normal')
        else:
            for child in self.blank_options_frame.winfo_children():
                child.configure(state='disabled')
    
    def on_preset_select(self, event):
        """프리셋 선택 시"""
        selection = self.preset_listbox.curselection()
        if selection:
            self.selected_preset = selection[0] + 1
            self.load_preset_data()
    
    def load_preset_data(self):
        """선택된 프리셋 데이터 로드"""
        preset = self.coord_presets[str(self.selected_preset)]
        self.preset_name_var.set(preset["name"])
        self.preset_hotkey_var.set(preset["hotkey"])
        
        # 좌표 표시 업데이트
        self.update_coord_display()
    
    def update_coord_display(self):
        """좌표 표시 업데이트"""
        preset = self.coord_presets[str(self.selected_preset)]
        item = self.edit_item_var.get()
        
        if item.startswith("thumb"):
            data = preset["thumbnail"]
            idx = 0 if item.endswith("left") else 1
        else:
            data = preset["qr"]
            idx = 0 if item.endswith("left") else 1
        
        pos = data["positions"][idx]
        self.x_var.set(pos["x"])
        self.y_var.set(pos["y"])
        self.width_var.set(data["max_width"])
        self.height_var.set(data["max_height"])
        
        self.update_preview()
    
    def save_current_coords(self):
        """현재 좌표 저장"""
        preset = self.coord_presets[str(self.selected_preset)]
        item = self.edit_item_var.get()
        
        # 이름과 단축키 업데이트
        preset["name"] = self.preset_name_var.get()
        preset["hotkey"] = self.preset_hotkey_var.get()
        
        # 좌표 업데이트
        if item.startswith("thumb"):
            idx = 0 if item.endswith("left") else 1
            preset["thumbnail"]["positions"][idx] = {
                "x": self.x_var.get(),
                "y": self.y_var.get()
            }
            preset["thumbnail"]["max_width"] = self.width_var.get()
            preset["thumbnail"]["max_height"] = self.height_var.get()
        else:
            idx = 0 if item.endswith("left") else 1
            preset["qr"]["positions"][idx] = {
                "x": self.x_var.get(),
                "y": self.y_var.get()
            }
            preset["qr"]["max_width"] = self.width_var.get()
            preset["qr"]["max_height"] = self.height_var.get()
        
        # 리스트박스 업데이트
        self.preset_listbox.delete(self.selected_preset - 1)
        self.preset_listbox.insert(self.selected_preset - 1, 
                                  f"{preset['name']} ({preset['hotkey']})")
        self.preset_listbox.selection_set(self.selected_preset - 1)
        
        messagebox.showinfo("저장", "현재 좌표가 저장되었습니다.")
    
    def load_sample_pdf(self):
        """샘플 PDF 로드"""
        file_path = filedialog.askopenfilename(
            title="샘플 PDF 선택",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                doc = fitz.open(file_path)
                page = doc[0]
                
                # 미리보기용 스케일 계산
                canvas_width = 500
                canvas_height = 400
                
                scale = min(canvas_width / page.rect.width, 
                           canvas_height / page.rect.height) * 0.9
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
                messagebox.showerror("오류", f"PDF 로드 중 오류 발생:\n{str(e)}")
    
    def update_preview(self):
        """미리보기 업데이트"""
        if not self.preview_image:
            return
        
        from PIL import ImageDraw, ImageTk
        
        # 이미지 복사
        img = self.preview_image.copy()
        draw = ImageDraw.Draw(img)
        
        preset = self.coord_presets[str(self.selected_preset)]
        
        # 모든 위치에 사각형 그리기
        # 썸네일
        for i, pos in enumerate(preset["thumbnail"]["positions"]):
            x = int(pos["x"] * self.canvas_scale)
            y = int(pos["y"] * self.canvas_scale)
            w = int(preset["thumbnail"]["max_width"] * self.canvas_scale)
            h = int(preset["thumbnail"]["max_height"] * self.canvas_scale)
            
            # 현재 편집 중인 항목 강조
            item = self.edit_item_var.get()
            is_current = (item == "thumb_left" and i == 0) or (item == "thumb_right" and i == 1)
            
            color = "red" if is_current else "blue"
            width = 3 if is_current else 1
            
            draw.rectangle([x, y, x+w, y+h], outline=color, width=width)
            draw.text((x+2, y+2), f"썸네일 {i+1}", fill=color)
        
        # QR
        for i, pos in enumerate(preset["qr"]["positions"]):
            x = int(pos["x"] * self.canvas_scale)
            y = int(pos["y"] * self.canvas_scale)
            w = int(preset["qr"]["max_width"] * self.canvas_scale)
            h = int(preset["qr"]["max_height"] * self.canvas_scale)
            
            # 현재 편집 중인 항목 강조
            item = self.edit_item_var.get()
            is_current = (item == "qr_left" and i == 0) or (item == "qr_right" and i == 1)
            
            color = "red" if is_current else "green"
            width = 3 if is_current else 1
            
            draw.rectangle([x, y, x+w, y+h], outline=color, width=width)
            draw.text((x+2, y+2), f"QR {i+1}", fill=color)
        
        # Canvas에 표시
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(250, 200, image=self.photo)
    
    def on_canvas_click(self, event):
        """캔버스 클릭 시"""
        if not self.preview_image:
            return
        
        # 클릭 위치를 실제 좌표로 변환
        x = int(event.x / self.canvas_scale)
        y = int(event.y / self.canvas_scale)
        
        # 범위 제한
        x = max(0, min(x, 842))
        y = max(0, min(y, 595))
        
        self.x_var.set(x)
        self.y_var.set(y)
        
        self.save_current_coords()
    
    def restore_default_hotkeys(self):
        """기본 단축키로 복원"""
        defaults = {
            "ProcessKey": "F3",
            "SettingsKey": "^F3",
            "HelpKey": "F1",
            "ResetKey": "^R",
            "PresetManagerKey": "^P"
        }
        
        for key, value in defaults.items():
            self.hotkey_vars[key].set(value)
        
        messagebox.showinfo("복원", "기본 단축키로 복원되었습니다.")
    
    def save_and_close(self):
        """저장하고 닫기"""
        # 현재 설정 수집
        for key, var in self.hotkey_vars.items():
            self.hotkey_settings[key] = var.get()
        
        self.general_settings["show_tooltips"] = self.show_tooltips_var.get()
        self.general_settings["play_sounds"] = self.play_sounds_var.get()
        self.general_settings["tooltip_duration"] = self.tooltip_duration_var.get()
        self.general_settings["blank_detection"] = {
            "enabled": self.blank_detection_enabled_var.get(),
            "threshold": self.blank_threshold_var.get(),
            "edge_margin": self.edge_margin_var.get(),
            "max_pages": self.max_pages_var.get()
        }
        
        # 모든 설정 저장
        if self.save_all_settings():
            messagebox.showinfo("저장 완료", "모든 설정이 저장되었습니다.")
            
            # 부모 프로그램에 설정 리로드 알림
            if self.parent and hasattr(self.parent, 'reload_settings'):
                self.parent.reload_settings()
            
            self.root.destroy()
    
    def run(self):
        """독립 실행"""
        if not self.parent:
            self.root.mainloop()


class PrintProcessor:
    """GUI 없이 파일 처리를 담당하는 클래스"""
    
    def __init__(self):
        self.dropped_files = {
            'order_pdf': None,
            'print_pdf': None,
            'qr_image': None
        }
        self.temp_normalized_file = None
    
    def classify_files(self, files):
        """파일 목록을 분류"""
        for file_path in files:
            if not file_path or file_path == '""':  # 빈 문자열 처리
                continue
                
            ext = Path(file_path).suffix.lower()
            filename = os.path.basename(file_path)
            
            if ext == '.pdf':
                if '의뢰서' in filename:
                    self.dropped_files['order_pdf'] = file_path
                else:
                    self.dropped_files['print_pdf'] = file_path
            elif ext in ['.jpg', '.jpeg', '.png']:
                self.dropped_files['qr_image'] = file_path
    
    def process_files_cli(self, files):
        """명령줄 모드에서 파일 처리"""
        self.classify_files(files)
        
        # 필수 파일 확인
        if not self.dropped_files['order_pdf']:
            print("오류: 의뢰서 PDF가 없습니다.")
            return False
        
        if not (self.dropped_files['print_pdf'] or self.dropped_files['qr_image']):
            print("오류: 인쇄데이터 PDF 또는 QR 이미지가 필요합니다.")
            return False
        
        # 파일 처리
        try:
            self.process_files()
            return True
        except Exception as e:
            print(f"처리 중 오류: {e}")
            if DEBUG_MODE:
                import traceback
                traceback.print_exc()
            return False
    
    def calculate_fit_size(self, original_width, original_height, max_width, max_height):
        """비율을 유지하면서 최대 크기 안에 맞는 크기 계산"""
        ratio = min(max_width / original_width, max_height / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        return new_width, new_height
    
    def is_blank_page(self, page, threshold=0.99, edge_margin=20):
        """페이지가 백지인지 확인"""
        if not BLANK_DETECTION.get('enabled', True):
            return False
            
        try:
            # 페이지를 이미지로 변환 (낮은 해상도로 빠르게 확인)
            mat = fitz.Matrix(0.5, 0.5)  # 50% 크기로 렌더링
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # PIL 이미지로 변환
            img_data = pix.pil_tobytes(format="PNG")
            img = Image.open(BytesIO(img_data))
            
            # 그레이스케일로 변환
            img_gray = img.convert('L')
            
            # 재단선 영역 제외하고 크롭
            width, height = img_gray.size
            if edge_margin > 0:
                crop_box = (edge_margin, edge_margin, 
                           width - edge_margin, height - edge_margin)
                img_cropped = img_gray.crop(crop_box)
            else:
                img_cropped = img_gray
            
            # 픽셀 값 분석
            pixels = list(img_cropped.getdata())
            total_pixels = len(pixels)
            
            # 흰색 픽셀 수 계산 (250 이상을 흰색으로 간주)
            white_pixels = sum(1 for pixel in pixels if pixel >= 250)
            white_ratio = white_pixels / total_pixels
            
            if DEBUG_MODE:
                print(f"  백지 검사: 흰색 픽셀 비율 {white_ratio:.2%}")
            
            return white_ratio >= threshold
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"  백지 검사 실패: {e}")
            return False
    
    def find_non_blank_page(self, pdf_path, max_pages=10):
        """백지가 아닌 첫 페이지 찾기"""
        if not BLANK_DETECTION.get('enabled', True):
            return 0
            
        try:
            doc = fitz.open(pdf_path)
            threshold = BLANK_DETECTION.get('threshold', 0.99)
            edge_margin = BLANK_DETECTION.get('edge_margin', 20)
            max_search = min(BLANK_DETECTION.get('max_pages', 10), len(doc))
            
            for page_num in range(max_search):
                page = doc[page_num]
                
                if DEBUG_MODE:
                    print(f"\n  페이지 {page_num + 1} 검사 중...")
                
                if not self.is_blank_page(page, threshold, edge_margin):
                    if DEBUG_MODE and page_num > 0:
                        print(f"  -> 백지가 아닌 페이지 발견! (페이지 {page_num + 1})")
                    doc.close()
                    return page_num
            
            doc.close()
            
            # 모든 페이지가 백지인 경우
            if DEBUG_MODE:
                print(f"  -> 처음 {max_search}페이지가 모두 백지입니다. 첫 페이지 사용.")
            return 0
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"백지 검사 중 오류: {e}")
            return 0
    
    def normalize_pdf_to_landscape(self, input_path):
        """PDF를 아크로뱃에서 보이는 그대로 가로형으로 재생성 (렌더링 방식)"""
        # 외부 normalize_pdf 모듈이 있으면 우선 사용
        if NORMALIZE_AVAILABLE:
            try:
                if DEBUG_MODE:
                    print("외부 normalize_pdf 모듈을 사용합니다.")
                temp_path = Path(input_path).parent / f"temp_normalized_{Path(input_path).name}"
                result = normalize_pdf_external(input_path, str(temp_path))
                self.temp_normalized_file = str(temp_path)
                return str(temp_path)
            except Exception as e:
                if DEBUG_MODE:
                    print(f"외부 모듈 실패, 내장 방식 사용: {e}")
        
        # 내장 정규화 방식
        try:
            doc = fitz.open(input_path)
            
            # 표준 A4 가로형 크기
            A4_LANDSCAPE_WIDTH = 842
            A4_LANDSCAPE_HEIGHT = 595
            
            # 임시 파일로 정규화
            temp_path = Path(input_path).parent / f"temp_normalized_{Path(input_path).name}"
            new_doc = fitz.open()
            
            for page_num, page in enumerate(doc):
                # 원본 페이지 정보
                rect = page.rect
                rotation = page.rotation
                
                if DEBUG_MODE:
                    print(f"\n원본 페이지 {page_num + 1}:")
                    print(f"  - 크기: {rect.width:.1f}x{rect.height:.1f}")
                    print(f"  - 회전: {rotation}도")
                
                # 페이지를 아크로뱃에서 보이는 그대로 렌더링
                # get_pixmap()은 회전이 적용된 상태로 렌더링함
                mat = fitz.Matrix(6.0, 6.0)  # 6배 해상도로 렌더링 (고품질)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # 렌더링된 이미지의 실제 크기
                img_width = pix.width / 6.0  # 6배로 렌더링했으므로 원래 크기로 환산
                img_height = pix.height / 6.0
                
                if DEBUG_MODE:
                    print(f"  - 렌더링된 크기: {img_width:.1f}x{img_height:.1f}")
                    print(f"  - 6배 고해상도 렌더링")
                
                # 가로형인지 확인
                is_landscape = img_width > img_height
                
                # 새 가로형 페이지 생성
                new_page = new_doc.new_page(width=A4_LANDSCAPE_WIDTH, height=A4_LANDSCAPE_HEIGHT)
                
                # 최종 크기와 위치 변수 초기화
                final_width = 0
                final_height = 0
                x_offset = 0
                y_offset = 0
                
                if is_landscape:
                    # 이미 가로형인 경우
                    # A4 가로형에 맞게 크기 조정
                    scale_x = A4_LANDSCAPE_WIDTH / img_width
                    scale_y = A4_LANDSCAPE_HEIGHT / img_height
                    scale = min(scale_x, scale_y)
                    
                    # 중앙 정렬을 위한 위치 계산
                    final_width = img_width * scale
                    final_height = img_height * scale
                    x_offset = (A4_LANDSCAPE_WIDTH - final_width) / 2
                    y_offset = (A4_LANDSCAPE_HEIGHT - final_height) / 2
                    
                    # 대상 영역
                    target_rect = fitz.Rect(x_offset, y_offset, 
                                           x_offset + final_width, 
                                           y_offset + final_height)
                    
                    # 가로형은 렌더링된 픽스맵을 직접 삽입
                    new_page.insert_image(target_rect, pixmap=pix)
                else:
                    # 세로형인 경우 - 90도 회전하여 가로로 만들기
                    # 회전 후 크기로 계산
                    scale_x = A4_LANDSCAPE_WIDTH / img_height
                    scale_y = A4_LANDSCAPE_HEIGHT / img_width
                    scale = min(scale_x, scale_y)
                    
                    # 중앙 정렬을 위한 위치 계산
                    final_width = img_height * scale
                    final_height = img_width * scale
                    x_offset = (A4_LANDSCAPE_WIDTH - final_width) / 2
                    y_offset = (A4_LANDSCAPE_HEIGHT - final_height) / 2
                    
                    # 픽스맵을 PIL 이미지로 변환
                    img_data = pix.pil_tobytes(format="PNG")
                    img = Image.open(BytesIO(img_data))
                    
                    # 90도 회전
                    img = img.rotate(-90, expand=True)
                    
                    # 다시 바이트로 변환
                    img_buffer = BytesIO()
                    img.save(img_buffer, format="PNG", optimize=True)
                    img_bytes = img_buffer.getvalue()
                    
                    # 대상 영역
                    target_rect = fitz.Rect(x_offset, y_offset, 
                                           x_offset + final_width, 
                                           y_offset + final_height)
                    
                    # 회전된 이미지 삽입
                    new_page.insert_image(target_rect, stream=img_bytes)
                    
                    if DEBUG_MODE:
                        print(f"  - 세로형 → 가로형 변환 완료")
                
                if DEBUG_MODE:
                    print(f"  - 최종 크기: {final_width:.1f}x{final_height:.1f}")
                    print(f"  - 위치: ({x_offset:.1f}, {y_offset:.1f})")
            
            # 저장
            new_doc.save(str(temp_path))
            new_doc.close()
            doc.close()
            
            self.temp_normalized_file = str(temp_path)
            
            if DEBUG_MODE:
                print(f"\nPDF 정규화 완료: {temp_path}")
            
            return str(temp_path)
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"PDF 정규화 실패: {e}")
                import traceback
                traceback.print_exc()
            return input_path
    
    def create_pdf_thumbnail(self, pdf_path, page_num=0, crop_right_half=False):
        """PDF 페이지를 직접 사용하여 고품질 삽입용 데이터 생성"""
        try:
            # 백지가 아닌 페이지 찾기
            if BLANK_DETECTION.get('enabled', True) and page_num == 0:
                non_blank_page = self.find_non_blank_page(pdf_path)
                if non_blank_page > 0:
                    print(f"  - 백지 감지: 페이지 {non_blank_page + 1}을 썸네일로 사용")
                    page_num = non_blank_page
            
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            
            # 표지 크롭 처리를 위한 임시 PDF 생성
            if crop_right_half:
                # 오른쪽 50%만 사용하는 임시 PDF 생성
                temp_doc = fitz.open()
                # 페이지 크기의 절반으로 새 페이지 생성
                new_width = page.rect.width / 2
                new_height = page.rect.height
                temp_page = temp_doc.new_page(width=new_width, height=new_height)
                
                # 오른쪽 절반만 복사
                source_rect = fitz.Rect(page.rect.width/2, 0, page.rect.width, page.rect.height)
                temp_page.show_pdf_page(temp_page.rect, doc, page_num, clip=source_rect)
                
                # 임시 PDF를 메모리에 저장
                pdf_bytes = temp_doc.tobytes()
                
                # 크기 정보 저장
                width = new_width
                height = new_height
                
                temp_doc.close()
                doc.close()
                
                return pdf_bytes, width, height
            else:
                # 전체 페이지 사용
                # 단일 페이지 PDF를 메모리에 저장
                temp_doc = fitz.open()
                temp_page = temp_doc.new_page(width=page.rect.width, height=page.rect.height)
                temp_page.show_pdf_page(temp_page.rect, doc, page_num)
                
                pdf_bytes = temp_doc.tobytes()
                
                # 크기 정보 저장
                width = page.rect.width
                height = page.rect.height
                
                temp_doc.close()
                doc.close()
                
                return pdf_bytes, width, height
                
        except Exception as e:
            if DEBUG_MODE:
                print(f"PDF 썸네일 생성 실패: {e}")
                import traceback
                traceback.print_exc()
            raise e
    
    def get_normalized_rect(self, x, y, width, height, page):
        """정규화된 가로형 PDF에서는 좌표 변환이 필요 없음"""
        return fitz.Rect(x, y, x + width, y + height)
    
    def draw_white_background(self, page, x, y, width, height, padding=0):
        """썸네일 뒤에 흰색 배경 그리기"""
        # 패딩을 포함한 사각형 좌표
        rect = fitz.Rect(
            x - padding,
            y - padding,
            x + width + padding,
            y + height + padding
        )
        
        # 흰색 배경 그리기
        shape = page.new_shape()
        shape.draw_rect(rect)
        shape.finish(
            fill=(1, 1, 1),  # 흰색 (RGB: 1, 1, 1)
            stroke_opacity=0  # 테두리 없음
        )
        shape.commit()
        
        if DEBUG_MODE:
            print(f"    - 흰색 배경 추가: {rect.width:.1f}x{rect.height:.1f} (패딩: {padding})")
    
    def process_files(self):
        """파일 처리 메인 로직"""
        try:
            start_time = time.time()
            
            print("\n" + "="*60)
            print("인쇄 의뢰서 자동화 처리 시작")
            print("="*60)
            
            if DEBUG_MODE:
                print("\n[디버그 모드 활성화]")
                print(f"의뢰서 PDF: {self.dropped_files['order_pdf']}")
                print(f"인쇄데이터 PDF: {self.dropped_files['print_pdf']}")
                print(f"QR 이미지: {self.dropped_files['qr_image']}")
            
            # PDF 썸네일과 QR 데이터 초기화
            pdf_thumb_data = None
            thumb_pdf_w = thumb_pdf_h = 0
            thumbnail_data = None  # 대체 이미지 방식용
            thumb_w = thumb_h = 0
            qr_data = None
            qr_w = qr_h = 0
            
            # 1. 인쇄데이터 PDF가 있으면 PDF 직접 삽입용 데이터 생성
            if self.dropped_files['print_pdf']:
                print("\n1. 인쇄 데이터 PDF 처리 중...")
                
                try:
                    # 파일명에 '표지' 포함 여부 확인
                    filename = os.path.basename(self.dropped_files['print_pdf'])
                    crop_right_half = '표지' in filename
                    
                    if crop_right_half:
                        print("  - 표지 파일 감지: 오른쪽 50%만 사용")
                    
                    # PDF 파일 확인
                    if not os.path.exists(self.dropped_files['print_pdf']):
                        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {self.dropped_files['print_pdf']}")
                    
                    # PDF 직접 삽입용 데이터 생성
                    pdf_thumb_data, thumb_pdf_w, thumb_pdf_h = self.create_pdf_thumbnail(
                        self.dropped_files['print_pdf'],
                        page_num=0,
                        crop_right_half=crop_right_half
                    )
                    
                    print(f"  - PDF 썸네일 준비 완료: {thumb_pdf_w:.1f}x{thumb_pdf_h:.1f}")
                    print(f"  - 벡터 형식 유지 (품질 손실 없음)")
                    
                except Exception as e:
                    print(f"  - PDF 처리 실패: {e}")
                    print("  - 대체 방법: 이미지로 변환하여 처리합니다.")
                    
                    # 실패 시 기존 이미지 방식으로 대체
                    try:
                        # 백지가 아닌 페이지 찾기
                        page_num = 0
                        if BLANK_DETECTION.get('enabled', True):
                            page_num = self.find_non_blank_page(self.dropped_files['print_pdf'])
                        
                        print_doc = fitz.open(self.dropped_files['print_pdf'])
                        first_page = print_doc[page_num]
                        
                        # 이미지로 변환
                        mat = fitz.Matrix(2, 2)  # 2배 스케일
                        pix = first_page.get_pixmap(matrix=mat, alpha=False)
                        img = Image.open(BytesIO(pix.pil_tobytes(format="PNG")))
                        
                        # 표지 크롭 처리
                        if crop_right_half:
                            crop_left = img.width // 2
                            img = img.crop((crop_left, 0, img.width, img.height))
                        
                        # 최종 크기 계산
                        thumb_w, thumb_h = self.calculate_fit_size(
                            img.width, img.height,
                            THUMBNAIL_CONFIG['max_width'],
                            THUMBNAIL_CONFIG['max_height']
                        )
                        
                        # 리사이즈
                        img = img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                        
                        # PNG로 저장
                        thumb_buffer = BytesIO()
                        img.save(thumb_buffer, format='PNG')
                        thumbnail_data = thumb_buffer.getvalue()
                        
                        print_doc.close()
                        
                        print(f"  - 대체 이미지 썸네일 생성 완료: {thumb_w}x{thumb_h}")
                        
                    except Exception as e2:
                        print(f"  - 대체 방법도 실패: {e2}")
                        thumbnail_data = None
            
            # 2. QR 이미지가 있으면 로드 및 리사이즈 (개선된 방식)
            if self.dropped_files['qr_image']:
                print("\n2. QR 이미지 처리 중...")
                qr_img = Image.open(self.dropped_files['qr_image'])
                print(f"  - 원본 QR 크기: {qr_img.width}x{qr_img.height}")
                
                qr_max_w = QR_CONFIG['max_width']
                qr_max_h = QR_CONFIG['max_height']
                qr_w, qr_h = self.calculate_fit_size(
                    qr_img.width, qr_img.height, qr_max_w, qr_max_h
                )
                
                print(f"  - 목표 QR 크기: {qr_max_w}x{qr_max_h}")
                print(f"  - 조정된 크기: {qr_w}x{qr_h}")
                
                # QR 코드에 최적화된 리사이즈 (NEAREST + 샤프닝)
                qr_img = qr_img.resize((qr_w, qr_h), Image.Resampling.NEAREST)
                
                # 샤프닝 필터 적용으로 경계선 강화
                enhancer = ImageEnhance.Sharpness(qr_img)
                qr_img = enhancer.enhance(2.0)  # 샤프니스 2배 증가
                
                print("  - QR 코드 최적화: NEAREST 리샘플링 + 샤프닝 적용")
                
                # PIL 이미지를 바이트로 변환
                qr_buffer = BytesIO()
                qr_img.save(qr_buffer, format='PNG')
                qr_data = qr_buffer.getvalue()
            
            # 3. 백업 생성 (설정된 경우)
            if PROCESSING_CONFIG['backup_before_save']:
                backup_path = Path(self.dropped_files['order_pdf'])
                backup_name = backup_path.stem + PROCESSING_CONFIG['backup_suffix'] + backup_path.suffix
                backup_full_path = backup_path.parent / backup_name
                shutil.copy2(self.dropped_files['order_pdf'], backup_full_path)
                if DEBUG_MODE:
                    print(f"\n백업 생성: {backup_full_path}")
            
            # 4. 의뢰서 PDF 정규화 (자동 정규화 설정된 경우)
            order_pdf_path = self.dropped_files['order_pdf']
            is_normalized = False
            
            # 파일명으로 정규화 필요 여부 추가 체크
            filename = os.path.basename(order_pdf_path)
            skip_normalize = 'skip_norm' in filename.lower()
            
            if PROCESSING_CONFIG.get('auto_normalize', True) and not skip_normalize:
                print("\n3. PDF 정규화 중...")
                print("  - 벡터 방식으로 페이지 재구성")
                normalized_path = self.normalize_pdf_to_landscape(order_pdf_path)
                if normalized_path != order_pdf_path:
                    order_pdf_path = normalized_path
                    is_normalized = True
                    print("  - PDF 정규화 완료!")
            elif skip_normalize:
                print("\n파일명에 'skip_norm'이 포함되어 정규화를 건너뜁니다.")
            
            # 5. 의뢰서 PDF 열기 및 수정
            print("\n4. 의뢰서 PDF 처리 중...")
            order_doc = fitz.open(order_pdf_path)
            
            # 흰색 배경 설정 확인
            use_white_bg = THUMBNAIL_CONFIG.get('white_background', True)
            bg_padding = THUMBNAIL_CONFIG.get('background_padding', 5)
            
            if use_white_bg and DEBUG_MODE:
                print(f"  - 썸네일 흰색 배경 활성화 (패딩: {bg_padding}px)")
            
            for page_num in range(len(order_doc)):
                page = order_doc[page_num]
                
                print(f"\n  페이지 {page_num + 1}/{len(order_doc)}:")
                print(f"    - 크기: {page.rect.width:.1f}x{page.rect.height:.1f}")
                print(f"    - 회전: {page.rotation}도")
                
                # 썸네일 삽입 (PDF 또는 이미지)
                if pdf_thumb_data:
                    # PDF 직접 삽입
                    inserted_count = 0
                    
                    try:
                        # 임시 PDF 문서 생성
                        thumb_doc = fitz.open(stream=pdf_thumb_data, filetype="pdf")
                        thumb_page = thumb_doc[0]
                        
                        for pos in THUMBNAIL_CONFIG['positions']:
                            # 목표 크기 계산
                            thumb_w, thumb_h = self.calculate_fit_size(
                                thumb_pdf_w, thumb_pdf_h,
                                THUMBNAIL_CONFIG['max_width'],
                                THUMBNAIL_CONFIG['max_height']
                            )
                            
                            # 중앙 정렬을 위한 오프셋 계산
                            x_offset = (THUMBNAIL_CONFIG['max_width'] - thumb_w) // 2
                            y_offset = (THUMBNAIL_CONFIG['max_height'] - thumb_h) // 2
                            
                            # 실제 위치
                            actual_x = pos['x'] + x_offset
                            actual_y = pos['y'] + y_offset
                            
                            # 흰색 배경 그리기 (설정된 경우)
                            if use_white_bg:
                                self.draw_white_background(
                                    page, actual_x, actual_y, 
                                    thumb_w, thumb_h, bg_padding
                                )
                            
                            # 대상 위치와 크기
                            target_rect = fitz.Rect(
                                actual_x, actual_y,
                                actual_x + thumb_w,
                                actual_y + thumb_h
                            )
                            
                            # PDF 페이지 직접 삽입 (벡터 유지)
                            page.show_pdf_page(target_rect, thumb_doc, 0)
                            inserted_count += 1
                        
                        thumb_doc.close()
                        print(f"    - PDF 썸네일 {inserted_count}개 삽입 (벡터 품질)")
                        
                    except Exception as e:
                        print(f"    - PDF 삽입 실패: {e}")
                        print(f"    - 이미지 방식으로 재시도합니다.")
                        # 이미지 방식으로 대체
                        if thumbnail_data:
                            inserted_count = 0
                            for pos in THUMBNAIL_CONFIG['positions']:
                                x_offset = (THUMBNAIL_CONFIG['max_width'] - thumb_w) // 2
                                y_offset = (THUMBNAIL_CONFIG['max_height'] - thumb_h) // 2
                                
                                actual_x = pos['x'] + x_offset
                                actual_y = pos['y'] + y_offset
                                
                                # 흰색 배경 그리기 (설정된 경우)
                                if use_white_bg:
                                    self.draw_white_background(
                                        page, actual_x, actual_y,
                                        thumb_w, thumb_h, bg_padding
                                    )
                                
                                rect = self.get_normalized_rect(
                                    actual_x, actual_y,
                                    thumb_w, thumb_h,
                                    page
                                )
                                page.insert_image(rect, stream=thumbnail_data)
                                inserted_count += 1
                            print(f"    - 이미지 썸네일 {inserted_count}개 삽입")
                
                elif thumbnail_data:
                    # 이미지 방식 (대체)
                    inserted_count = 0
                    for pos in THUMBNAIL_CONFIG['positions']:
                        x_offset = (THUMBNAIL_CONFIG['max_width'] - thumb_w) // 2
                        y_offset = (THUMBNAIL_CONFIG['max_height'] - thumb_h) // 2
                        
                        actual_x = pos['x'] + x_offset
                        actual_y = pos['y'] + y_offset
                        
                        # 흰색 배경 그리기 (설정된 경우)
                        if use_white_bg:
                            self.draw_white_background(
                                page, actual_x, actual_y,
                                thumb_w, thumb_h, bg_padding
                            )
                        
                        rect = self.get_normalized_rect(
                            actual_x, actual_y,
                            thumb_w, thumb_h,
                            page
                        )
                        page.insert_image(rect, stream=thumbnail_data)
                        inserted_count += 1
                    print(f"    - 이미지 썸네일 {inserted_count}개 삽입")
                
                # QR 코드 삽입 (QR 이미지가 있는 경우)
                if qr_data:
                    inserted_count = 0
                    for pos in QR_CONFIG['positions']:
                        # 중앙 정렬을 위한 오프셋 계산
                        x_offset = (QR_CONFIG['max_width'] - qr_w) // 2
                        y_offset = (QR_CONFIG['max_height'] - qr_h) // 2
                        
                        # 정규화된 PDF는 좌표 변환 불필요
                        rect = self.get_normalized_rect(
                            pos['x'] + x_offset,
                            pos['y'] + y_offset,
                            qr_w,
                            qr_h,
                            page
                        )
                        page.insert_image(rect, stream=qr_data)
                        inserted_count += 1
                    print(f"    - QR 코드 {inserted_count}개 삽입")
            
            # 6. 저장
            print("\n5. 저장 중...")
            
            # 래스터화 옵션 확인
            should_rasterize = PROCESSING_CONFIG.get('rasterize_final', True)
            
            if should_rasterize:
                print("  - 최종 PDF 래스터화 활성화 (품질 유지 + 용량 최적화)")
                # 래스터화된 새 문서 생성
                raster_doc = fitz.open()
                
                for page_num in range(len(order_doc)):
                    page = order_doc[page_num]
                    
                    # 페이지를 고해상도로 래스터화
                    pix = page.get_pixmap(dpi=200, alpha=False)  # 200 DPI로 래스터화
                    
                    # 새 페이지 생성
                    new_page = raster_doc.new_page(width=page.rect.width, height=page.rect.height)
                    
                    # 래스터화된 이미지 삽입
                    new_page.insert_image(new_page.rect, pixmap=pix)
                
                # 래스터화된 문서로 교체
                order_doc.close()
                order_doc = raster_doc
                print("  - 래스터화 완료")
            
            if PROCESSING_CONFIG['overwrite_original']:
                # 정규화된 파일인 경우 특별 처리
                if is_normalized and self.temp_normalized_file:
                    # 수정된 내용을 임시 파일에 저장
                    temp_save_path = str(Path(self.temp_normalized_file).parent / f"save_{Path(self.temp_normalized_file).name}")
                    order_doc.save(temp_save_path, garbage=4, deflate=True)
                    order_doc.close()
                    
                    # 임시 저장 파일을 원본으로 이동
                    shutil.move(temp_save_path, self.dropped_files['order_pdf'])
                    
                    # 정규화 임시 파일 삭제
                    try:
                        if os.path.exists(self.temp_normalized_file):
                            os.remove(self.temp_normalized_file)
                    except:
                        pass
                    self.temp_normalized_file = None
                else:
                    # 정규화되지 않은 원본 파일인 경우
                    order_doc.save(self.dropped_files['order_pdf'], garbage=4, deflate=True)
                    order_doc.close()
                
                print(f"  - 원본 파일 덮어쓰기 완료: {os.path.basename(self.dropped_files['order_pdf'])}")
            else:
                # 새 파일로 저장
                save_path = Path(self.dropped_files['order_pdf'])
                new_name = save_path.stem + '_processed' + save_path.suffix
                new_path = save_path.parent / new_name
                order_doc.save(str(new_path), garbage=4, deflate=True)
                order_doc.close()
                
                # 정규화 임시 파일 삭제 (있는 경우)
                if self.temp_normalized_file and os.path.exists(self.temp_normalized_file):
                    try:
                        os.remove(self.temp_normalized_file)
                    except:
                        pass
                    self.temp_normalized_file = None
                
                print(f"  - 새 파일로 저장: {new_name}")
            
            print("\n✅ 모든 처리가 완료되었습니다!")
            
            # 처리 시간 계산
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"⏱️  처리 시간: {processing_time:.2f}초")
            
            # 파일 크기 정보 출력
            if os.path.exists(self.dropped_files['order_pdf']):
                file_size = os.path.getsize(self.dropped_files['order_pdf']) / 1024 / 1024  # MB
                print(f"📄 최종 파일 크기: {file_size:.2f} MB")
            
            print("="*60 + "\n")
            
        except Exception as e:
            error_msg = str(e)
            print("\n" + "="*60)
            print("❌ 오류 발생!")
            print("="*60)
            print(f"오류 내용: {error_msg}")
            
            if DEBUG_MODE:
                import traceback
                print("\n[상세 오류 정보]")
                traceback.print_exc()
            
            print("="*60 + "\n")
            raise e


# 메인 실행 블록
if __name__ == "__main__":
    # 명령줄 인자 확인
    if len(sys.argv) > 1 and "--cli" in sys.argv:
        # CLI 모드 실행
        if not check_dependencies():
            sys.exit(1)
            
        # --cli를 제외한 파일 경로들 추출
        files = [arg for arg in sys.argv[1:] if arg != "--cli" and os.path.exists(arg)]
        
        if not files:
            print("오류: 처리할 파일이 없습니다.")
            sys.exit(1)
        
        # 파일 처리
        processor = PrintProcessor()
        success = processor.process_files_cli(files)
        sys.exit(0 if success else 1)
    
    elif len(sys.argv) > 1 and "--coord-presets" in sys.argv:
        # 좌표 프리셋 관리 모드
        if check_dependencies():
            manager = CoordPresetManager()
            manager.run()
        else:
            input("\n엔터를 눌러 종료하세요...")
        
    else:
        # GUI 모드 실행
        if check_dependencies():
            app = PrintAutomationGUI()
            app.run()
        else:
            input("\n엔터를 눌러 종료하세요...")