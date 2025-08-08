"""설정 관리 윈도우"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
from pathlib import Path

from config.settings_manager import SettingsManager
from config.preset_manager import PresetManager
from config.constants import COLORS
from utils.logger import setup_logger

class SettingsWindow:
    """설정 관리 윈도우 - 탭 구조"""
    
    def __init__(self, parent=None):
        """설정 윈도우 초기화"""
        self.parent = parent
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.logger = setup_logger(self.__class__.__name__)
        self.settings_manager = SettingsManager()
        self.preset_manager = PresetManager()
        
        # 변경 사항 추적
        self.changes_made = False
        
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """UI 구성"""
        # 윈도우 설정
        self.window.title("설정")
        self.window.geometry("700x500")
        
        # 윈도우 중앙 배치
        self.center_window()
        
        # 메인 프레임
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # 탭 컨트롤
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # 탭 생성
        self.create_coordinates_tab()
        self.create_presets_tab()
        self.create_performance_tab()
        self.create_ui_tab()
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        # 저장 버튼
        self.save_btn = ttk.Button(
            button_frame,
            text="저장",
            command=self.save_settings,
            width=15
        )
        self.save_btn.pack(side='right', padx=5)
        
        # 취소 버튼
        self.cancel_btn = ttk.Button(
            button_frame,
            text="취소",
            command=self.close,
            width=15
        )
        self.cancel_btn.pack(side='right')
        
        # 초기화 버튼
        self.reset_btn = ttk.Button(
            button_frame,
            text="기본값으로 초기화",
            command=self.reset_to_defaults,
            width=20
        )
        self.reset_btn.pack(side='left')
    
    def create_coordinates_tab(self):
        """좌표 설정 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="좌표 설정")
        
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 좌표 입력 필드들
        self.coord_vars = {}
        
        # 썸네일 좌표 섹션
        thumb_frame = ttk.LabelFrame(scrollable_frame, text="썸네일 위치", padding="10")
        thumb_frame.pack(fill='x', padx=10, pady=5)
        
        positions = ['left', 'right']
        coords = ['x', 'y', 'width', 'height']
        
        for i, pos in enumerate(positions):
            pos_frame = ttk.LabelFrame(thumb_frame, text=f"{pos.upper()} 썸네일", padding="5")
            pos_frame.grid(row=0, column=i, padx=5, pady=5, sticky='ew')
            
            for j, coord in enumerate(coords):
                ttk.Label(pos_frame, text=f"{coord}:").grid(row=j, column=0, sticky='w', pady=2)
                
                var_key = f'thumbnail_{pos}_{coord}'
                self.coord_vars[var_key] = tk.StringVar()
                
                entry = ttk.Entry(pos_frame, textvariable=self.coord_vars[var_key], width=10)
                entry.grid(row=j, column=1, padx=(5, 0), pady=2)
                entry.bind('<KeyRelease>', lambda e: self.mark_changed())
        
        # QR 코드 좌표 섹션
        qr_frame = ttk.LabelFrame(scrollable_frame, text="QR 코드 위치", padding="10")
        qr_frame.pack(fill='x', padx=10, pady=5)
        
        qr_coords = ['x', 'y', 'size']
        
        for i, pos in enumerate(positions):
            pos_frame = ttk.LabelFrame(qr_frame, text=f"{pos.upper()} QR", padding="5")
            pos_frame.grid(row=0, column=i, padx=5, pady=5, sticky='ew')
            
            for j, coord in enumerate(qr_coords):
                ttk.Label(pos_frame, text=f"{coord}:").grid(row=j, column=0, sticky='w', pady=2)
                
                var_key = f'qr_{pos}_{coord}'
                self.coord_vars[var_key] = tk.StringVar()
                
                entry = ttk.Entry(pos_frame, textvariable=self.coord_vars[var_key], width=10)
                entry.grid(row=j, column=1, padx=(5, 0), pady=2)
                entry.bind('<KeyRelease>', lambda e: self.mark_changed())
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_presets_tab(self):
        """프리셋 관리 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="프리셋")
        
        # 프리셋 목록
        list_frame = ttk.LabelFrame(tab, text="프리셋 목록", padding="10")
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 트리뷰
        columns = ('name', 'hotkey', 'usage')
        self.preset_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=10)
        
        self.preset_tree.heading('#0', text='번호')
        self.preset_tree.heading('name', text='이름')
        self.preset_tree.heading('hotkey', text='단축키')
        self.preset_tree.heading('usage', text='사용 횟수')
        
        self.preset_tree.column('#0', width=50)
        self.preset_tree.column('name', width=200)
        self.preset_tree.column('hotkey', width=80)
        self.preset_tree.column('usage', width=100)
        
        self.preset_tree.pack(side='left', fill='both', expand=True)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.preset_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.preset_tree.configure(yscrollcommand=scrollbar.set)
        
        # 버튼 프레임
        preset_btn_frame = ttk.Frame(tab)
        preset_btn_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(preset_btn_frame, text="현재 설정을 프리셋으로 저장", 
                  command=self.save_preset).pack(side='left', padx=5)
        ttk.Button(preset_btn_frame, text="프리셋 불러오기", 
                  command=self.load_preset).pack(side='left', padx=5)
        ttk.Button(preset_btn_frame, text="프리셋 초기화", 
                  command=self.reset_preset).pack(side='left', padx=5)
        
        # 프리셋 목록 로드
        self.refresh_preset_list()
    
    def create_performance_tab(self):
        """성능 설정 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="성능")
        
        # 멀티스레딩 설정
        thread_frame = ttk.LabelFrame(tab, text="멀티스레딩", padding="10")
        thread_frame.pack(fill='x', padx=10, pady=10)
        
        self.multithread_var = tk.BooleanVar()
        ttk.Checkbutton(thread_frame, text="멀티스레딩 사용", 
                       variable=self.multithread_var,
                       command=self.mark_changed).pack(anchor='w')
        
        worker_frame = ttk.Frame(thread_frame)
        worker_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(worker_frame, text="최대 워커 수:").pack(side='left')
        self.max_workers_var = tk.StringVar()
        ttk.Spinbox(worker_frame, from_=1, to=8, width=10,
                   textvariable=self.max_workers_var,
                   command=self.mark_changed).pack(side='left', padx=(5, 0))
        
        # 캐시 설정
        cache_frame = ttk.LabelFrame(tab, text="캐시", padding="10")
        cache_frame.pack(fill='x', padx=10, pady=10)
        
        self.cache_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(cache_frame, text="캐시 사용", 
                       variable=self.cache_enabled_var,
                       command=self.mark_changed).pack(anchor='w')
        
        cache_size_frame = ttk.Frame(cache_frame)
        cache_size_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(cache_size_frame, text="캐시 크기 (MB):").pack(side='left')
        self.cache_size_var = tk.StringVar()
        ttk.Spinbox(cache_size_frame, from_=10, to=500, increment=10, width=10,
                   textvariable=self.cache_size_var,
                   command=self.mark_changed).pack(side='left', padx=(5, 0))
    
    def create_ui_tab(self):
        """UI 설정 탭"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="인터페이스")
        
        # 일반 설정
        general_frame = ttk.LabelFrame(tab, text="일반", padding="10")
        general_frame.pack(fill='x', padx=10, pady=10)
        
        self.always_on_top_var = tk.BooleanVar()
        ttk.Checkbutton(general_frame, text="항상 위에 표시", 
                       variable=self.always_on_top_var,
                       command=self.mark_changed).pack(anchor='w')
        
        self.show_tooltips_var = tk.BooleanVar()
        ttk.Checkbutton(general_frame, text="도구 설명 표시", 
                       variable=self.show_tooltips_var,
                       command=self.mark_changed).pack(anchor='w')
        
        self.confirm_process_var = tk.BooleanVar()
        ttk.Checkbutton(general_frame, text="처리 전 확인", 
                       variable=self.confirm_process_var,
                       command=self.mark_changed).pack(anchor='w')
        
        self.auto_clear_var = tk.BooleanVar()
        ttk.Checkbutton(general_frame, text="처리 후 자동 초기화", 
                       variable=self.auto_clear_var,
                       command=self.mark_changed).pack(anchor='w')
    
    def load_current_settings(self):
        """현재 설정 로드"""
        try:
            # 좌표 설정
            for pos in ['left', 'right']:
                for coord in ['x', 'y', 'width', 'height']:
                    key = f'thumbnail_{pos}_{coord}'
                    value = self.settings_manager.get(f'coordinates.thumbnail.{pos}.{coord}', '')
                    self.coord_vars[key].set(str(value))
                
                for coord in ['x', 'y', 'size']:
                    key = f'qr_{pos}_{coord}'
                    value = self.settings_manager.get(f'coordinates.qr.{pos}.{coord}', '')
                    self.coord_vars[key].set(str(value))
            
            # 성능 설정
            self.multithread_var.set(self.settings_manager.get('performance.multithreading', True))
            self.max_workers_var.set(str(self.settings_manager.get('performance.max_workers', 4)))
            self.cache_enabled_var.set(self.settings_manager.get('performance.cache_enabled', True))
            self.cache_size_var.set(str(self.settings_manager.get('performance.cache_size_mb', 100)))
            
            # UI 설정
            self.always_on_top_var.set(self.settings_manager.get('ui.window_always_on_top', True))
            self.show_tooltips_var.set(self.settings_manager.get('ui.show_tooltips', True))
            self.confirm_process_var.set(self.settings_manager.get('ui.confirm_before_process', False))
            self.auto_clear_var.set(self.settings_manager.get('ui.auto_clear_after_process', True))
            
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
                    value = self.coord_vars[key].get()
                    thumb_coords[coord] = int(value) if value else 0
                
                self.settings_manager.set(f'coordinates.thumbnail.{pos}', thumb_coords)
                
                qr_coords = {}
                for coord in ['x', 'y', 'size']:
                    key = f'qr_{pos}_{coord}'
                    value = self.coord_vars[key].get()
                    if coord == 'size':
                        qr_coords[coord] = int(value) if value else 70
                    else:
                        qr_coords[coord] = int(value) if value else 0
                
                self.settings_manager.set(f'coordinates.qr.{pos}', qr_coords)
            
            # 성능 설정 저장
            self.settings_manager.set('performance.multithreading', self.multithread_var.get())
            self.settings_manager.set('performance.max_workers', int(self.max_workers_var.get()))
            self.settings_manager.set('performance.cache_enabled', self.cache_enabled_var.get())
            self.settings_manager.set('performance.cache_size_mb', int(self.cache_size_var.get()))
            
            # UI 설정 저장
            self.settings_manager.set('ui.window_always_on_top', self.always_on_top_var.get())
            self.settings_manager.set('ui.show_tooltips', self.show_tooltips_var.get())
            self.settings_manager.set('ui.confirm_before_process', self.confirm_process_var.get())
            self.settings_manager.set('ui.auto_clear_after_process', self.auto_clear_var.get())
            
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
    
    def refresh_preset_list(self):
        """프리셋 목록 새로고침"""
        # 기존 항목 삭제
        for item in self.preset_tree.get_children():
            self.preset_tree.delete(item)
        
        # 프리셋 목록 로드
        preset_list = self.preset_manager.get_preset_list()
        
        for preset in preset_list:
            self.preset_tree.insert('', 'end', 
                                   text=preset['index'],
                                   values=(preset['name'], 
                                          preset['hotkey'],
                                          preset['usage_count']))
    
    def save_preset(self):
        """현재 설정을 프리셋으로 저장"""
        # 프리셋 선택 대화상자
        selected = self.preset_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "저장할 프리셋 슬롯을 선택하세요")
            return
        
        item = self.preset_tree.item(selected[0])
        preset_index = item['text']
        
        # 이름 입력
        name = simpledialog.askstring("프리셋 이름", 
                                      f"프리셋 {preset_index}의 이름을 입력하세요:",
                                      initialvalue=item['values'][0])
        if not name:
            return
        
        # 현재 설정 수집
        current_settings = {
            'coordinates': self.settings_manager.get('coordinates')
        }
        
        # 프리셋 저장
        if self.preset_manager.save_preset(preset_index, name, current_settings):
            messagebox.showinfo("성공", f"프리셋 {name}이(가) 저장되었습니다")
            self.refresh_preset_list()
        else:
            messagebox.showerror("오류", "프리셋 저장 실패")
    
    def load_preset(self):
        """프리셋 불러오기"""
        selected = self.preset_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "불러올 프리셋을 선택하세요")
            return
        
        item = self.preset_tree.item(selected[0])
        preset_index = item['text']
        
        # 프리셋 로드
        preset_data = self.preset_manager.load_preset(preset_index)
        if preset_data:
            # 좌표 설정 적용
            if 'coordinates' in preset_data:
                self.settings_manager.settings['coordinates'] = preset_data['coordinates']
                self.load_current_settings()
                self.mark_changed()
                messagebox.showinfo("성공", f"프리셋 {item['values'][0]}을(를) 불러왔습니다")
        else:
            messagebox.showerror("오류", "프리셋 불러오기 실패")
    
    def reset_preset(self):
        """프리셋 초기화"""
        selected = self.preset_tree.selection()
        if not selected:
            messagebox.showwarning("경고", "초기화할 프리셋을 선택하세요")
            return
        
        if not messagebox.askyesno("확인", "선택한 프리셋을 초기화하시겠습니까?"):
            return
        
        item = self.preset_tree.item(selected[0])
        preset_index = item['text']
        
        if self.preset_manager.reset_preset(preset_index):
            messagebox.showinfo("성공", "프리셋이 초기화되었습니다")
            self.refresh_preset_list()
        else:
            messagebox.showerror("오류", "프리셋 초기화 실패")
    
    def reset_to_defaults(self):
        """설정을 기본값으로 초기화"""
        if not messagebox.askyesno("확인", "모든 설정을 기본값으로 초기화하시겠습니까?"):
            return
        
        if self.settings_manager.reset_to_defaults():
            self.load_current_settings()
            messagebox.showinfo("성공", "설정이 초기화되었습니다")
        else:
            messagebox.showerror("오류", "초기화 실패")
    
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
    
    def center_window(self):
        """윈도우를 화면 중앙에 배치"""
        self.window.update_idletasks()
        
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        window_width = 700
        window_height = 500
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def run(self):
        """설정 창 실행"""
        self.window.grab_set()  # 모달 창으로 설정
        self.window.mainloop()