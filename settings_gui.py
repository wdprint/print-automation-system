import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import fitz
from PIL import Image, ImageTk, ImageDraw
import json
import os
from pathlib import Path

class SettingsGUI:
    def __init__(self, parent=None):
        self.parent = parent
        self.window = tk.Toplevel() if parent else tk.Tk()
        self.window.title("인쇄 자동화 - 위치 설정")
        self.window.geometry("1000x700")
        
        # 설정값 초기화
        self.settings = self.load_settings()
        self.sample_pdf = None
        self.preview_image = None
        self.canvas_scale = 1.0
        
        # 현재 선택된 항목
        self.selected_item = None
        self.selected_index = 0
        
        self.setup_ui()
        
    def load_settings(self):
        """저장된 설정 로드 또는 기본값 사용"""
        settings_path = Path("settings.json")
        
        if settings_path.exists():
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 기본값 (썸네일 크기 업데이트)
        return {
            "thumbnail": {
                "max_width": 160,   # 변경됨
                "max_height": 250,  # 변경됨
                "positions": [
                    {"x": 70, "y": 180},    # Y 좌표도 조정 (상단으로 이동)
                    {"x": 490, "y": 180}    # Y 좌표도 조정 (상단으로 이동)
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
    
    def save_settings(self):
        """설정을 JSON 파일로 저장"""
        try:
            with open("settings.json", 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("저장 완료", "설정이 저장되었습니다.")
            return True
        except Exception as e:
            messagebox.showerror("저장 실패", f"설정 저장 중 오류가 발생했습니다:\n{str(e)}")
            return False
    
    def setup_ui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
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
        
        # 구분선
        ttk.Separator(control_frame, orient='horizontal').grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
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
        self.width_spinbox = ttk.Spinbox(size_frame, from_=10, to=300, width=10,  # 최대값 증가
                                        textvariable=self.width_var, command=self.update_preview)
        self.width_spinbox.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(size_frame, text="높이:").pack(side=tk.LEFT, padx=(10, 0))
        self.height_var = tk.IntVar(value=0)
        self.height_spinbox = ttk.Spinbox(size_frame, from_=10, to=300, width=10,  # 최대값 증가
                                         textvariable=self.height_var, command=self.update_preview)
        self.height_spinbox.pack(side=tk.LEFT, padx=5)
        
        # 미세 조정 버튼
        ttk.Label(control_frame, text="미세 조정:").grid(row=10, column=0, sticky=tk.W, pady=(10, 5))
        
        adjust_frame = ttk.Frame(control_frame)
        adjust_frame.grid(row=11, column=0, padx=20)
        
        # 방향키 스타일 배치
        ttk.Button(adjust_frame, text="↑", width=3, 
                  command=lambda: self.adjust_position(0, -5)).grid(row=0, column=1)
        ttk.Button(adjust_frame, text="←", width=3, 
                  command=lambda: self.adjust_position(-5, 0)).grid(row=1, column=0)
        ttk.Button(adjust_frame, text="→", width=3, 
                  command=lambda: self.adjust_position(5, 0)).grid(row=1, column=2)
        ttk.Button(adjust_frame, text="↓", width=3, 
                  command=lambda: self.adjust_position(0, 5)).grid(row=2, column=1)
        
        # 버튼들
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=12, column=0, pady=20)
        
        ttk.Button(button_frame, text="기본값 복원", command=self.reset_to_default).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="저장", command=self.save_and_close).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        
        # 힌트
        hint_text = "💡 미리보기 영역을 클릭하여 위치를 지정할 수도 있습니다."
        ttk.Label(control_frame, text=hint_text, foreground="blue").grid(row=13, column=0, pady=10)
        
        # 초기 선택 업데이트
        self.update_selection()
        
        # 윈도우 크기 조정 설정
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
    
    def load_sample_pdf(self):
        """샘플 PDF 파일 로드"""
        file_path = filedialog.askopenfilename(
            title="샘플 PDF 선택",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # PDF 첫 페이지를 이미지로 변환
                doc = fitz.open(file_path)
                page = doc[0]
                
                # 미리보기용 스케일 계산
                canvas_width = 600
                canvas_height = 500
                
                # 가로형 기준으로 스케일 계산
                if page.rect.width > page.rect.height:
                    # 실제 가로형
                    scale = min(canvas_width / page.rect.width, canvas_height / page.rect.height) * 0.9
                else:
                    # 세로형 (회전된 것으로 간주)
                    scale = min(canvas_width / page.rect.height, canvas_height / page.rect.width) * 0.9
                
                self.canvas_scale = scale
                
                # 이미지 생성
                mat = fitz.Matrix(scale, scale)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_data = pix.pil_tobytes(format="PNG")
                
                # PIL Image로 변환
                from io import BytesIO
                img = Image.open(BytesIO(img_data))
                
                # 회전이 필요한 경우
                if page.rect.width < page.rect.height and page.rotation in [90, 270]:
                    if page.rotation == 90:
                        img = img.rotate(-90, expand=True)
                    else:
                        img = img.rotate(90, expand=True)
                
                self.preview_image = img
                doc.close()
                
                # 미리보기 업데이트
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
        
        # 현재 값 로드
        pos = settings["positions"][self.selected_index]
        self.x_var.set(pos["x"])
        self.y_var.set(pos["y"])
        self.width_var.set(settings["max_width"])
        self.height_var.set(settings["max_height"])
        
        # 미리보기 업데이트
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
        # 썸네일 위치
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
        
        # 클릭 위치를 실제 좌표로 변환
        x = int(event.x / self.canvas_scale)
        y = int(event.y / self.canvas_scale)
        
        # 범위 제한
        x = max(0, min(x, 842))
        y = max(0, min(y, 595))
        
        # 값 설정
        self.x_var.set(x)
        self.y_var.set(y)
        
        # 미리보기 업데이트
        self.update_preview()
    
    def adjust_position(self, dx, dy):
        """위치 미세 조정"""
        new_x = self.x_var.get() + dx
        new_y = self.y_var.get() + dy
        
        # 범위 제한
        new_x = max(0, min(new_x, 842))
        new_y = max(0, min(new_y, 595))
        
        self.x_var.set(new_x)
        self.y_var.set(new_y)
        
        self.update_preview()
    
    def reset_to_default(self):
        """기본값으로 복원"""
        result = messagebox.askyesno("기본값 복원", "모든 설정을 기본값으로 복원하시겠습니까?")
        if result:
            self.settings = {
                "thumbnail": {
                    "max_width": 160,   # 업데이트된 기본값
                    "max_height": 250,  # 업데이트된 기본값
                    "positions": [
                        {"x": 70, "y": 180},    # 조정된 좌표
                        {"x": 490, "y": 180}    # 조정된 좌표
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
            self.update_selection()
            messagebox.showinfo("완료", "기본값으로 복원되었습니다.")
    
    def save_and_close(self):
        """저장하고 닫기"""
        if self.save_settings():
            if self.parent:
                # 메인 프로그램에 설정 변경 알림
                self.parent.reload_settings()
            self.window.destroy()
    
    def run(self):
        """독립 실행시"""
        if not self.parent:
            self.window.mainloop()


if __name__ == "__main__":
    # 독립 실행 테스트
    app = SettingsGUI()
    app.run()