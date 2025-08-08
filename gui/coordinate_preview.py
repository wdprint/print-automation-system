"""좌표 미리보기 위젯 - 현대적인 디자인"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.messagebox
from PIL import Image, ImageTk, ImageDraw
import fitz  # PyMuPDF
from pathlib import Path
import io

class CoordinatePreview(tk.Frame):
    """좌표 미리보기 위젯"""
    
    def __init__(self, parent, settings_manager, parent_window=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.settings = settings_manager
        self.parent_window = parent_window  # 부모 창 참조 직접 설정
        self.sample_image = None
        self.photo_image = None
        self.scale_factor = 1.0
        self.original_size = (842, 595)  # A4 가로
        
        # 드래그 앤 드롭 관련 변수
        self.dragging = False
        self.resizing = False
        self.selected_box = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.resize_handle = None
        
        # 썸네일 박스 관리
        self.thumbnail_boxes = []  # 동적 썸네일 박스 리스트
        self.qr_boxes = []  # 동적 QR 박스 리스트
        
        # 통일된 밝은 테마 (modern_settings와 동일)
        self.colors = {
            'bg': '#f5f5f5',
            'card': '#ffffff',
            'accent': '#2196F3',
            'text': '#424242',
            'subtext': '#9E9E9E',
            'border': '#E0E0E0',
            'thumbnail': '#66BB6A',
            'qr': '#FFA726'
        }
        
        self.configure(bg=self.colors['bg'])
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        # 메인 컨테이너
        main_container = tk.Frame(self, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 상단 툴바
        toolbar = tk.Frame(main_container, bg=self.colors['card'], height=50)
        toolbar.pack(fill='x', pady=(0, 10))
        toolbar.pack_propagate(False)
        
        # 샘플 PDF 로드 버튼
        self.load_btn = tk.Button(
            toolbar,
            text="📄 샘플 PDF 불러오기",
            command=self.load_sample_pdf,
            bg=self.colors['accent'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        self.load_btn.pack(side='left', padx=10, pady=10)
        
        # 리셋 버튼
        self.reset_btn = tk.Button(
            toolbar,
            text="↺ 초기화",
            command=self.reset_coordinates,
            bg='#f44336',
            fg='white',
            font=('Segoe UI', 10),
            bd=0,
            padx=15,
            pady=10,
            cursor='hand2'
        )
        self.reset_btn.pack(side='left', padx=5, pady=10)
        
        # 구분선
        tk.Frame(toolbar, width=2, bg=self.colors['border']).pack(side='left', fill='y', padx=10)
        
        # 썸네일 박스 추가 버튼
        self.add_thumb_btn = tk.Button(
            toolbar,
            text="➕ 썸네일 박스 추가",
            command=self.add_thumbnail_box,
            bg=self.colors['thumbnail'],
            fg='white',
            font=('Segoe UI', 10),
            bd=0,
            padx=15,
            pady=10,
            cursor='hand2'
        )
        self.add_thumb_btn.pack(side='left', padx=5, pady=10)
        
        # 썸네일 박스 삭제 버튼
        self.del_thumb_btn = tk.Button(
            toolbar,
            text="➖ 썸네일 박스 삭제",
            command=self.delete_thumbnail_box,
            bg='#FF7043',
            fg='white',
            font=('Segoe UI', 10),
            bd=0,
            padx=15,
            pady=10,
            cursor='hand2'
        )
        self.del_thumb_btn.pack(side='left', padx=5, pady=10)
        
        # 구분선
        tk.Frame(toolbar, width=2, bg=self.colors['border']).pack(side='left', fill='y', padx=10)
        
        # QR 박스 추가 버튼
        self.add_qr_btn = tk.Button(
            toolbar,
            text="➕ QR 박스 추가",
            command=self.add_qr_box,
            bg=self.colors['qr'],
            fg='white',
            font=('Segoe UI', 10),
            bd=0,
            padx=15,
            pady=10,
            cursor='hand2'
        )
        self.add_qr_btn.pack(side='left', padx=5, pady=10)
        
        # QR 박스 삭제 버튼
        self.del_qr_btn = tk.Button(
            toolbar,
            text="➖ QR 박스 삭제",
            command=self.delete_qr_box,
            bg='#FF7043',
            fg='white',
            font=('Segoe UI', 10),
            bd=0,
            padx=15,
            pady=10,
            cursor='hand2'
        )
        self.del_qr_btn.pack(side='left', padx=5, pady=10)
        
        # 정보 레이블
        self.info_label = tk.Label(
            toolbar,
            text="PDF를 불러와서 좌표를 확인하세요",
            bg=self.colors['card'],
            fg=self.colors['subtext'],
            font=('Segoe UI', 10)
        )
        self.info_label.pack(side='left', padx=20)
        
        # 미리보기 영역 - 크기 확대
        preview_frame = tk.Frame(main_container, bg=self.colors['card'])
        preview_frame.pack(fill='both', expand=True)
        
        # 최소 크기 설정
        preview_frame.configure(height=500)
        
        # 캔버스 - 크기 확대
        self.canvas = tk.Canvas(
            preview_frame,
            bg=self.colors['bg'],
            highlightthickness=1,
            highlightbackground=self.colors['border'],
            width=800,
            height=450
        )
        self.canvas.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 캔버스 이벤트 바인딩
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        self.canvas.bind('<Motion>', self.on_canvas_motion)
        
        # 좌표 정보 패널 및 저장 버튼
        info_panel = tk.Frame(main_container, bg=self.colors['card'], height=100)
        info_panel.pack(fill='x', pady=(10, 0))
        info_panel.pack_propagate(False)
        
        # 저장 버튼 추가
        save_btn = tk.Button(
            info_panel,
            text="💾 좌표 설정 저장",
            command=self.save_coordinates,
            bg=self.colors['accent'],
            fg='white',
            font=('맑은 고딕', 10, 'bold'),
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        save_btn.pack(side='top', pady=10)
        
        # 좌표 표시
        coord_frame = tk.Frame(info_panel, bg=self.colors['card'])
        coord_frame.pack(expand=True)
        
        self.coord_label = tk.Label(
            coord_frame,
            text="마우스 위치: X: --- , Y: ---",
            bg=self.colors['card'],
            fg=self.colors['text'],
            font=('Segoe UI', 11)
        )
        self.coord_label.pack(pady=5)
        
        self.selection_label = tk.Label(
            coord_frame,
            text="클릭하여 좌표 선택",
            bg=self.colors['card'],
            fg=self.colors['subtext'],
            font=('Segoe UI', 10)
        )
        self.selection_label.pack(pady=5)
        
        # 범례
        legend_frame = tk.Frame(info_panel, bg=self.colors['card'])
        legend_frame.pack(side='bottom', pady=10)
        
        # 썸네일 범례
        thumb_indicator = tk.Frame(legend_frame, bg=self.colors['thumbnail'], width=20, height=20)
        thumb_indicator.grid(row=0, column=0, padx=5)
        tk.Label(legend_frame, text="썸네일 위치", bg=self.colors['card'], 
                fg=self.colors['text'], font=('Segoe UI', 9)).grid(row=0, column=1, padx=(0, 20))
        
        # QR 범례
        qr_indicator = tk.Frame(legend_frame, bg=self.colors['qr'], width=20, height=20)
        qr_indicator.grid(row=0, column=2, padx=5)
        tk.Label(legend_frame, text="QR 위치", bg=self.colors['card'], 
                fg=self.colors['text'], font=('Segoe UI', 9)).grid(row=0, column=3)
        
    def load_sample_pdf(self):
        """샘플 PDF 로드"""
        file_path = filedialog.askopenfilename(
            title="샘플 PDF 선택",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # PDF 첫 페이지를 이미지로 변환
                doc = fitz.open(file_path)
                page = doc[0]
                
                # 페이지를 이미지로 변환
                mat = fitz.Matrix(1.5, 1.5)  # 150% 스케일
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_data = pix.tobytes("png")
                
                # PIL 이미지로 변환
                self.sample_image = Image.open(io.BytesIO(img_data))
                self.original_size = (page.rect.width, page.rect.height)
                
                doc.close()
                
                # 캔버스에 표시
                self.display_preview()
                
                self.info_label.config(text=f"✓ {Path(file_path).name} 로드됨")
                
            except Exception as e:
                messagebox.showerror("오류", f"PDF 로드 실패: {str(e)}")
    
    def display_preview(self):
        """미리보기 표시"""
        if not self.sample_image:
            return
        
        # 캔버스 크기에 맞게 리사이즈
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            self.after(100, self.display_preview)
            return
        
        # 이미지 비율 유지하며 리사이즈
        img_width, img_height = self.sample_image.size
        scale = min(canvas_width / img_width, canvas_height / img_height) * 0.9
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # 스케일 팩터 저장
        self.scale_factor = new_width / self.original_size[0]
        
        # 이미지 리사이즈
        display_image = self.sample_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 좌표 박스 그리기
        self.draw_coordinate_boxes(display_image)
        
        # PhotoImage로 변환
        self.photo_image = ImageTk.PhotoImage(display_image)
        
        # 캔버스에 표시
        self.canvas.delete("all")
        self.canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self.photo_image,
            anchor='center'
        )
    
    def draw_coordinate_boxes(self, image):
        """좌표 박스 그리기"""
        draw = ImageDraw.Draw(image, 'RGBA')
        
        # 썸네일 박스들 그리기 (새로운 배열 구조)
        thumbnail_boxes = self.settings.get('coordinates.thumbnail_boxes', [])
        for idx, box in enumerate(thumbnail_boxes):
            x = int(box.get('x', 0) * self.scale_factor)
            y = int(box.get('y', 0) * self.scale_factor)
            width = int(box.get('width', 160) * self.scale_factor)
            height = int(box.get('height', 250) * self.scale_factor)
            
            # 반투명 박스
            draw.rectangle(
                [x, y, x + width, y + height],
                outline=self.colors['thumbnail'],
                width=3
            )
            # 채우기
            draw.rectangle(
                [x, y, x + width, y + height],
                fill=(76, 175, 80, 50)  # 반투명 녹색
            )
            
            # 레이블
            draw.text(
                (x + 5, y + 5),
                box.get('name', f'썸네일 {idx + 1}'),
                fill=self.colors['thumbnail']
            )
        
        # QR 박스들 그리기 (새로운 배열 구조)
        qr_boxes = self.settings.get('coordinates.qr_boxes', [])
        for idx, box in enumerate(qr_boxes):
            x = int(box.get('x', 0) * self.scale_factor)
            y = int(box.get('y', 0) * self.scale_factor)
            size = int(box.get('size', 70) * self.scale_factor)
            
            # 반투명 박스
            draw.rectangle(
                [x, y, x + size, y + size],
                outline=self.colors['qr'],
                width=3
            )
            # 채우기
            draw.rectangle(
                [x, y, x + size, y + size],
                fill=(255, 152, 0, 50)  # 반투명 주황색
            )
            
            # 레이블
            draw.text(
                (x + 5, y + 5),
                box.get('name', f'QR {idx + 1}'),
                fill=self.colors['qr']
            )
        
        # 박스 수 업데이트
        self.update_box_count()
    
    def on_canvas_click(self, event):
        """캔버스 클릭 이벤트"""
        if not self.sample_image:
            messagebox.showinfo("알림", "먼저 샘플 PDF를 불러오세요")
            return
        
        # 캔버스 중심과 이미지 크기 계산
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width = int(self.original_size[0] * self.scale_factor)
        img_height = int(self.original_size[1] * self.scale_factor)
        
        # 이미지 시작 위치
        img_x = (canvas_width - img_width) // 2
        img_y = (canvas_height - img_height) // 2
        
        # 클릭 위치를 이미지 좌표로 변환
        rel_x = event.x - img_x
        rel_y = event.y - img_y
        
        # 원본 좌표로 변환
        if 0 <= rel_x <= img_width and 0 <= rel_y <= img_height:
            orig_x = int(rel_x / self.scale_factor)
            orig_y = int(rel_y / self.scale_factor)
            
            # 클릭한 위치가 어느 박스 안인지 확인
            clicked_box = self.get_box_at_position(orig_x, orig_y)
            
            if clicked_box:
                self.selected_box = clicked_box
                self.drag_start_x = orig_x
                self.drag_start_y = orig_y
                
                # 리사이즈 핸들 체크
                handle = self.get_resize_handle(orig_x, orig_y, clicked_box)
                if handle:
                    self.resizing = True
                    self.resize_handle = handle
                else:
                    self.dragging = True
                
                # 박스 이름 표시
                box_name = clicked_box['box'].get('name', f"{clicked_box['type']} {clicked_box['index']+1}")
                self.selection_label.config(
                    text=f"선택: {box_name}",
                    fg=self.colors['accent']
                )
            else:
                self.selection_label.config(
                    text=f"선택된 좌표: X: {orig_x}, Y: {orig_y}",
                    fg=self.colors['accent']
                )
                
                # 클립보드에 복사
                self.clipboard_clear()
                self.clipboard_append(f"{orig_x},{orig_y}")
    
    def on_canvas_motion(self, event):
        """캔버스 마우스 이동 이벤트"""
        if not self.sample_image:
            return
        
        # 캔버스 중심과 이미지 크기 계산
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width = int(self.original_size[0] * self.scale_factor)
        img_height = int(self.original_size[1] * self.scale_factor)
        
        # 이미지 시작 위치
        img_x = (canvas_width - img_width) // 2
        img_y = (canvas_height - img_height) // 2
        
        # 마우스 위치를 이미지 좌표로 변환
        rel_x = event.x - img_x
        rel_y = event.y - img_y
        
        # 원본 좌표로 변환
        if 0 <= rel_x <= img_width and 0 <= rel_y <= img_height:
            orig_x = int(rel_x / self.scale_factor)
            orig_y = int(rel_y / self.scale_factor)
            
            self.coord_label.config(text=f"마우스 위치: X: {orig_x}, Y: {orig_y}")
        else:
            self.coord_label.config(text="마우스 위치: X: ---, Y: ---")
    
    def reset_coordinates(self):
        """좌표 초기화"""
        if messagebox.askyesno("확인", "모든 좌표를 기본값으로 초기화하시겠습니까?"):
            # 기본값으로 리셋
            self.settings.reset_to_defaults()
            
            # 미리보기 다시 그리기
            if self.sample_image:
                self.display_preview()
            
            messagebox.showinfo("완료", "좌표가 초기화되었습니다")
    
    def refresh(self):
        """미리보기 새로고침"""
        if self.sample_image:
            self.display_preview()
    
    def get_box_at_position(self, x, y):
        """주어진 위치에 있는 박스 찾기"""
        # 썸네일 박스 확인 (새로운 배열 구조)
        thumbnail_boxes = self.settings.get('coordinates.thumbnail_boxes', [])
        for idx, box in enumerate(thumbnail_boxes):
            box_x = box.get('x', 0)
            box_y = box.get('y', 0)
            width = box.get('width', 160)
            height = box.get('height', 250)
            
            if box_x <= x <= box_x + width and box_y <= y <= box_y + height:
                return {
                    'type': 'thumbnail',
                    'index': idx,
                    'box': box,
                    'coords': box  # 호환성을 위해 coords도 유지
                }
        
        # QR 박스 확인 (새로운 배열 구조)
        qr_boxes = self.settings.get('coordinates.qr_boxes', [])
        for idx, box in enumerate(qr_boxes):
            box_x = box.get('x', 0)
            box_y = box.get('y', 0)
            size = box.get('size', 70)
            
            if box_x <= x <= box_x + size and box_y <= y <= box_y + size:
                return {
                    'type': 'qr',
                    'index': idx,
                    'box': box,
                    'coords': box  # 호환성을 위해 coords도 유지
                }
        
        return None
    
    def get_resize_handle(self, x, y, box):
        """리사이즈 핸들 위치 확인"""
        margin = 10  # 핸들 감지 여백
        
        if box['type'] == 'thumbnail':
            coords = box['coords']
            box_x = coords.get('x', 0)
            box_y = coords.get('y', 0)
            width = coords.get('width', 160)
            height = coords.get('height', 250)
            
            # 오른쪽 하단 모서리
            if abs(x - (box_x + width)) < margin and abs(y - (box_y + height)) < margin:
                return 'bottom-right'
            # 오른쪽 상단 모서리
            elif abs(x - (box_x + width)) < margin and abs(y - box_y) < margin:
                return 'top-right'
            # 왼쪽 하단 모서리
            elif abs(x - box_x) < margin and abs(y - (box_y + height)) < margin:
                return 'bottom-left'
            # 왼쪽 상단 모서리
            elif abs(x - box_x) < margin and abs(y - box_y) < margin:
                return 'top-left'
        
        elif box['type'] == 'qr':
            coords = box['coords']
            box_x = coords.get('x', 0)
            box_y = coords.get('y', 0)
            size = coords.get('size', 70)
            
            # 오른쪽 하단 모서리
            if abs(x - (box_x + size)) < margin and abs(y - (box_y + size)) < margin:
                return 'bottom-right'
            # 오른쪽 상단 모서리
            elif abs(x - (box_x + size)) < margin and abs(y - box_y) < margin:
                return 'top-right'
            # 왼쪽 하단 모서리
            elif abs(x - box_x) < margin and abs(y - (box_y + size)) < margin:
                return 'bottom-left'
            # 왼쪽 상단 모서리
            elif abs(x - box_x) < margin and abs(y - box_y) < margin:
                return 'top-left'
        
        return None
    
    def on_canvas_drag(self, event):
        """캔버스 드래그 이벤트"""
        if not self.selected_box:
            return
        
        # 캔버스 중심과 이미지 크기 계산
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width = int(self.original_size[0] * self.scale_factor)
        img_height = int(self.original_size[1] * self.scale_factor)
        
        # 이미지 시작 위치
        img_x = (canvas_width - img_width) // 2
        img_y = (canvas_height - img_height) // 2
        
        # 드래그 위치를 이미지 좌표로 변환
        rel_x = event.x - img_x
        rel_y = event.y - img_y
        
        # 원본 좌표로 변환
        if 0 <= rel_x <= img_width and 0 <= rel_y <= img_height:
            orig_x = int(rel_x / self.scale_factor)
            orig_y = int(rel_y / self.scale_factor)
            
            if self.dragging:
                # 박스 이동
                dx = orig_x - self.drag_start_x
                dy = orig_y - self.drag_start_y
                
                if self.selected_box['type'] == 'thumbnail':
                    # 썸네일 박스 배열 업데이트
                    thumbnail_boxes = self.settings.get('coordinates.thumbnail_boxes', [])
                    if self.selected_box['index'] < len(thumbnail_boxes):
                        box = thumbnail_boxes[self.selected_box['index']]
                        box['x'] = max(0, min(self.original_size[0] - box['width'], box['x'] + dx))
                        box['y'] = max(0, min(self.original_size[1] - box['height'], box['y'] + dy))
                        self.settings.set('coordinates.thumbnail_boxes', thumbnail_boxes)
                
                elif self.selected_box['type'] == 'qr':
                    # QR 박스 배열 업데이트
                    qr_boxes = self.settings.get('coordinates.qr_boxes', [])
                    if self.selected_box['index'] < len(qr_boxes):
                        box = qr_boxes[self.selected_box['index']]
                        box['x'] = max(0, min(self.original_size[0] - box['size'], box['x'] + dx))
                        box['y'] = max(0, min(self.original_size[1] - box['size'], box['y'] + dy))
                        self.settings.set('coordinates.qr_boxes', qr_boxes)
                
                self.drag_start_x = orig_x
                self.drag_start_y = orig_y
                
                # 드래그 중 실시간 업데이트
                self._update_parent_window()
                
            elif self.resizing:
                # 박스 크기 조정 - 개선된 버전
                if self.selected_box['type'] == 'thumbnail':
                    # 썸네일 박스 배열 업데이트
                    thumbnail_boxes = self.settings.get('coordinates.thumbnail_boxes', [])
                    if self.selected_box['index'] < len(thumbnail_boxes):
                        box = thumbnail_boxes[self.selected_box['index']]
                        
                        # 각 모서리별 크기 조정
                        if self.resize_handle == 'bottom-right':
                            box['width'] = max(50, orig_x - box['x'])
                            box['height'] = max(50, orig_y - box['y'])
                        elif self.resize_handle == 'bottom-left':
                            new_width = max(50, box['x'] + box['width'] - orig_x)
                            box['x'] = box['x'] + box['width'] - new_width
                            box['width'] = new_width
                            box['height'] = max(50, orig_y - box['y'])
                        elif self.resize_handle == 'top-right':
                            box['width'] = max(50, orig_x - box['x'])
                            new_height = max(50, box['y'] + box['height'] - orig_y)
                            box['y'] = box['y'] + box['height'] - new_height
                            box['height'] = new_height
                        elif self.resize_handle == 'top-left':
                            new_width = max(50, box['x'] + box['width'] - orig_x)
                            new_height = max(50, box['y'] + box['height'] - orig_y)
                            box['x'] = box['x'] + box['width'] - new_width
                            box['y'] = box['y'] + box['height'] - new_height
                            box['width'] = new_width
                            box['height'] = new_height
                        
                        self.settings.set('coordinates.thumbnail_boxes', thumbnail_boxes)
                
                elif self.selected_box['type'] == 'qr':
                    # QR 박스 배열 업데이트
                    qr_boxes = self.settings.get('coordinates.qr_boxes', [])
                    if self.selected_box['index'] < len(qr_boxes):
                        box = qr_boxes[self.selected_box['index']]
                        
                        # QR 코드는 정사각형 유지하며 크기 조정
                        if self.resize_handle == 'bottom-right':
                            dx = orig_x - box['x']
                            dy = orig_y - box['y']
                            new_size = max(30, min(200, max(dx, dy)))  # 30~200 픽셀 범위
                            box['size'] = new_size
                        elif self.resize_handle == 'bottom-left':
                            dx = box['x'] + box['size'] - orig_x
                            dy = orig_y - box['y']
                            new_size = max(30, min(200, max(dx, dy)))
                            box['x'] = box['x'] + box['size'] - new_size
                            box['size'] = new_size
                        elif self.resize_handle == 'top-right':
                            dx = orig_x - box['x']
                            dy = box['y'] + box['size'] - orig_y
                            new_size = max(30, min(200, max(dx, dy)))
                            box['y'] = box['y'] + box['size'] - new_size
                            box['size'] = new_size
                        elif self.resize_handle == 'top-left':
                            dx = box['x'] + box['size'] - orig_x
                            dy = box['y'] + box['size'] - orig_y
                            new_size = max(30, min(200, max(dx, dy)))
                            box['x'] = box['x'] + box['size'] - new_size
                            box['y'] = box['y'] + box['size'] - new_size
                            box['size'] = new_size
                        
                        self.settings.set('coordinates.qr_boxes', qr_boxes)
                
                # 리사이징 중 실시간 업데이트
                self._update_parent_window()
            
            # 미리보기 업데이트
            self.display_preview()
            
            # 부모 창의 좌표 입력 필드 업데이트
            if hasattr(self.master.master, 'update_coordinate_fields'):
                self.master.master.update_coordinate_fields()
            
            # 부모 창의 박스 목록 실시간 업데이트 - 드래그 중에도 계속 업데이트
            self._update_parent_window()
    
    def on_canvas_release(self, event):
        """캔버스 마우스 버튼 릴리즈 이벤트"""
        self.dragging = False
        self.resizing = False
        self.selected_box = None
        self.resize_handle = None
    
    def add_thumbnail_box(self):
        """썸네일 박스 추가"""
        try:
            # 현재 썸네일 박스 가져오기
            thumbnail_boxes = self.settings.get('coordinates.thumbnail_boxes', [])
            
            # 새 박스 ID 생성
            new_id = f"thumb_{len(thumbnail_boxes) + 1}"
            
            # 기본 위치 계산 (기존 박스와 겹치지 않게)
            base_x = 230 + (len(thumbnail_boxes) % 3) * 200
            base_y = 234 + (len(thumbnail_boxes) // 3) * 280
            
            # 새 박스 추가
            new_box = {
                "id": new_id,
                "name": f"썸네일 {len(thumbnail_boxes) + 1}",
                "x": base_x,
                "y": base_y,
                "width": 160,
                "height": 250,
                "rotation": 0,
                "opacity": 1.0
            }
            
            thumbnail_boxes.append(new_box)
            self.settings.set('coordinates.thumbnail_boxes', thumbnail_boxes)
            
            # 화면 업데이트
            self.display_preview()  # update_preview가 아니라 display_preview 사용
            self.update_box_count()
            
            # 부모 창의 박스 목록 업데이트
            if hasattr(self.master.master, 'update_box_list'):
                self.master.master.update_box_list()
            
            tk.messagebox.showinfo("추가 완료", f"썸네일 박스 '{new_box['name']}'가 추가되었습니다.")
            
        except Exception as e:
            tk.messagebox.showerror("오류", f"썸네일 박스 추가 실패: {str(e)}")
    
    def delete_thumbnail_box(self):
        """썸네일 박스 삭제"""
        try:
            # 현재 썸네일 박스 가져오기
            thumbnail_boxes = self.settings.get('coordinates.thumbnail_boxes', [])
            
            if len(thumbnail_boxes) <= 1:
                tk.messagebox.showwarning("삭제 불가", "최소 1개의 썸네일 박스는 유지해야 합니다.")
                return
            
            # 삭제할 박스 선택 다이얼로그
            from tkinter import simpledialog
            box_names = [box['name'] for box in thumbnail_boxes]
            
            # 간단한 선택 창 만들기
            dialog = tk.Toplevel(self)
            dialog.title("삭제할 썸네일 박스 선택")
            dialog.geometry("300x200")
            
            tk.Label(dialog, text="삭제할 박스를 선택하세요:").pack(pady=10)
            
            selected_var = tk.StringVar()
            selected_var.set(box_names[-1])  # 마지막 박스 기본 선택
            
            for name in box_names:
                tk.Radiobutton(dialog, text=name, variable=selected_var, value=name).pack()
            
            def delete_selected():
                selected_name = selected_var.get()
                # 현재 썸네일 박스 다시 가져오기 (스코프 문제 해결)
                current_boxes = self.settings.get('coordinates.thumbnail_boxes', [])
                # 선택된 박스 제거
                updated_boxes = [box for box in current_boxes if box['name'] != selected_name]
                self.settings.set('coordinates.thumbnail_boxes', updated_boxes)
                
                # 화면 업데이트
                self.display_preview()  # update_preview가 아니라 display_preview 사용
                self.update_box_count()
                
                # 부모 창의 박스 목록 업데이트
                if hasattr(self.master.master, 'update_box_list'):
                    self.master.master.update_box_list()
                
                dialog.destroy()
                tk.messagebox.showinfo("삭제 완료", f"썸네일 박스 '{selected_name}'가 삭제되었습니다.")
            
            tk.Button(dialog, text="삭제", command=delete_selected, bg='#f44336', fg='white').pack(pady=10)
            tk.Button(dialog, text="취소", command=dialog.destroy).pack()
            
        except Exception as e:
            tk.messagebox.showerror("오류", f"썸네일 박스 삭제 실패: {str(e)}")
    
    def add_qr_box(self):
        """QR 박스 추가"""
        try:
            # 현재 QR 박스 가져오기
            qr_boxes = self.settings.get('coordinates.qr_boxes', [])
            
            # QR은 보통 1개만 사용하므로 경고 메시지
            if len(qr_boxes) >= 1:
                response = tk.messagebox.askyesno(
                    "QR 박스 추가",
                    "이미 QR 박스가 있습니다.\n추가로 QR 박스를 만드시겠습니까?\n(보통 QR은 1개만 사용합니다)"
                )
                if not response:
                    return
            
            # 새 박스 ID 생성
            new_id = f"qr_{len(qr_boxes) + 1}"
            
            # 기본 위치 계산 (기존 박스와 겹치지 않게)
            base_x = 315 + (len(qr_boxes) % 2) * 415
            base_y = 500
            
            # 새 박스 추가
            new_box = {
                "id": new_id,
                "name": f"QR {len(qr_boxes) + 1}",
                "x": base_x,
                "y": base_y,
                "size": 70,
                "rotation": 0
            }
            
            qr_boxes.append(new_box)
            self.settings.set('coordinates.qr_boxes', qr_boxes)
            
            # 화면 업데이트
            self.display_preview()
            self.update_box_count()
            
            # 부모 창의 박스 목록 업데이트
            if hasattr(self.master.master, 'update_box_list'):
                self.master.master.update_box_list()
            
            tk.messagebox.showinfo("추가 완료", f"QR 박스 '{new_box['name']}'가 추가되었습니다.")
            
        except Exception as e:
            tk.messagebox.showerror("오류", f"QR 박스 추가 실패: {str(e)}")
    
    def delete_qr_box(self):
        """QR 박스 삭제"""
        try:
            # 현재 QR 박스 가져오기
            qr_boxes = self.settings.get('coordinates.qr_boxes', [])
            
            if len(qr_boxes) == 0:
                tk.messagebox.showwarning("삭제 불가", "삭제할 QR 박스가 없습니다.")
                return
            
            # 삭제할 박스 선택 다이얼로그
            dialog = tk.Toplevel(self)
            dialog.title("삭제할 QR 박스 선택")
            dialog.geometry("300x200")
            
            tk.Label(dialog, text="삭제할 QR 박스를 선택하세요:").pack(pady=10)
            
            selected_var = tk.StringVar()
            box_names = [box['name'] for box in qr_boxes]
            selected_var.set(box_names[-1])  # 마지막 박스 기본 선택
            
            for name in box_names:
                tk.Radiobutton(dialog, text=name, variable=selected_var, value=name).pack()
            
            def delete_selected():
                selected_name = selected_var.get()
                # 현재 QR 박스 다시 가져오기
                current_boxes = self.settings.get('coordinates.qr_boxes', [])
                # 선택된 박스 제거
                updated_boxes = [box for box in current_boxes if box['name'] != selected_name]
                self.settings.set('coordinates.qr_boxes', updated_boxes)
                
                # 화면 업데이트
                self.display_preview()
                self.update_box_count()
                
                # 부모 창의 박스 목록 업데이트
                if hasattr(self.master.master, 'update_box_list'):
                    self.master.master.update_box_list()
                
                dialog.destroy()
                tk.messagebox.showinfo("삭제 완료", f"QR 박스 '{selected_name}'가 삭제되었습니다.")
            
            tk.Button(dialog, text="삭제", command=delete_selected, bg='#f44336', fg='white').pack(pady=10)
            tk.Button(dialog, text="취소", command=dialog.destroy).pack()
            
        except Exception as e:
            tk.messagebox.showerror("오류", f"QR 박스 삭제 실패: {str(e)}")
    
    def update_box_count(self):
        """박스 수 레이블 업데이트"""
        try:
            thumbnail_boxes = self.settings.get('coordinates.thumbnail_boxes', [])
            qr_boxes = self.settings.get('coordinates.qr_boxes', [])
            
            if hasattr(self, 'box_count_label'):
                self.box_count_label.config(
                    text=f"썸네일 박스: {len(thumbnail_boxes)}개 | QR 박스: {len(qr_boxes)}개"
                )
        except:
            pass
    
    def save_coordinates(self):
        """현재 좌표 설정을 저장"""
        try:
            # 설정 매니저에 저장
            if self.settings.save():
                # 성공 피드백
                tk.messagebox.showinfo("저장 완료", "좌표 설정이 저장되었습니다.")
                
                # 부모 창의 좌표 필드 업데이트
                if hasattr(self.master.master, 'update_coordinate_fields'):
                    self.master.master.update_coordinate_fields()
            else:
                tk.messagebox.showerror("저장 실패", "좌표 설정 저장에 실패했습니다.")
        except Exception as e:
            tk.messagebox.showerror("오류", f"저장 중 오류 발생: {str(e)}")
    
    def _update_parent_window(self):
        """부모 창의 좌표 목록을 실시간으로 업데이트"""
        try:
            # parent_window가 설정되어 있는지 확인
            if self.parent_window and hasattr(self.parent_window, 'update_box_list'):
                self.parent_window.update_box_list()
            # master.master 접근 방식도 시도 (fallback)
            elif hasattr(self, 'master') and hasattr(self.master, 'master'):
                parent = self.master.master
                if hasattr(parent, 'update_box_list'):
                    parent.update_box_list()
        except Exception as e:
            # 조용히 실패 (드래그 중 에러 방지)
            pass
    
    def set_parent_window(self, parent_window):
        """부모 창 참조 설정"""
        self.parent_window = parent_window