# PDF 인쇄 자동화 시스템 - 기능 구현 계획서

## 📋 현재 시스템 분석 (2025.01.10)

### 현재 구현된 기능
- ✅ 드래그앤드롭 GUI (TkinterDnD)
- ✅ 프리셋 시스템 (F1-F4 단축키)
- ✅ 멀티스레딩 지원 (max_workers 설정)
- ✅ 설정 관리 시스템 (JSON 기반)
- ✅ 파일 분류기 (자동 파일 타입 인식)
- ✅ 로깅 시스템
- ✅ 좌표 미리보기 및 드래그 앤 드롭
- ✅ 여러 PDF 파일 동시 처리

### 기술 스택
- **언어**: Python 3.8+
- **GUI**: Tkinter, TkinterDnD2
- **PDF 처리**: PyMuPDF (fitz), PyPDF2
- **이미지 처리**: Pillow
- **빌드**: PyInstaller

---

## 🎯 요청 기능 구현 계획

### 1. 🔄 자동 업데이트 기능

#### 현실성 평가: ⭐⭐⭐⭐ (높음)
- GitHub API 활용 가능
- PyInstaller로 빌드된 exe 자체 업데이트 가능
- 현재 네트워크 라이브러리 없음 → requests 추가 필요

#### 구현 방안

```python
# core/auto_updater.py (신규)
import requests
import json
import subprocess
from packaging import version
from pathlib import Path

class AutoUpdater:
    """GitHub Releases 기반 자동 업데이트"""
    
    def __init__(self, repo_owner="wdprint", repo_name="print-automation-system"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version = "2.1.0"  # version.txt에서 읽기
        self.update_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        
    def check_for_updates(self) -> tuple[bool, str, str]:
        """
        업데이트 확인
        Returns: (업데이트 가능 여부, 최신 버전, 다운로드 URL)
        """
        try:
            response = requests.get(self.update_url, timeout=5)
            if response.status_code == 200:
                latest_release = response.json()
                latest_version = latest_release['tag_name'].lstrip('v')
                
                if version.parse(latest_version) > version.parse(self.current_version):
                    download_url = self._get_download_url(latest_release)
                    return True, latest_version, download_url
            
            return False, self.current_version, ""
            
        except Exception as e:
            self.logger.error(f"업데이트 확인 실패: {e}")
            return False, self.current_version, ""
    
    def download_update(self, download_url: str) -> bool:
        """업데이트 다운로드 및 설치"""
        try:
            # 1. 새 버전 다운로드
            response = requests.get(download_url, stream=True)
            temp_file = Path("update_temp.exe")
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 2. 업데이트 스크립트 생성
            self._create_update_script(temp_file)
            
            # 3. 업데이트 스크립트 실행
            subprocess.Popen(["update_script.bat"], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            return True
            
        except Exception as e:
            self.logger.error(f"업데이트 다운로드 실패: {e}")
            return False
    
    def _create_update_script(self, new_exe: Path):
        """업데이트 배치 스크립트 생성"""
        script = f"""
@echo off
timeout /t 2 /nobreak > nul
move /y "{new_exe}" "print_automation.exe"
start print_automation.exe
del "%~f0"
"""
        with open("update_script.bat", "w") as f:
            f.write(script)
```

#### GUI 통합
```python
# gui/modern_main_window.py 수정
def __init__(self):
    # ... 기존 코드 ...
    self.auto_updater = AutoUpdater()
    self.check_updates_on_startup()

def check_updates_on_startup(self):
    """시작 시 업데이트 확인"""
    has_update, version, url = self.auto_updater.check_for_updates()
    if has_update:
        if messagebox.askyesno("업데이트 알림", 
                              f"새 버전 {version}이 있습니다. 업데이트하시겠습니까?"):
            self.auto_updater.download_update(url)
            self.root.quit()
```

---

### 3. 🎯 AI 기반 자동 설정

#### 현실성 평가: ⭐⭐⭐ (중간)
- PDF 레이아웃 분석은 가능
- 로컬 AI 모델은 용량/성능 문제
- OpenCV + 휴리스틱 알고리즘으로 대체 가능

#### 구현 방안

```python
# core/layout_analyzer.py (신규)
import cv2
import numpy as np
from PIL import Image
import fitz

class LayoutAnalyzer:
    """PDF 레이아웃 자동 분석 및 설정 제안"""
    
    def analyze_pdf_layout(self, pdf_path: str) -> dict:
        """
        PDF 레이아웃 분석
        Returns: 최적 좌표 제안
        """
        doc = fitz.open(pdf_path)
        page = doc[0]
        
        # 페이지를 이미지로 변환
        mat = fitz.Matrix(2, 2)  # 2x 확대
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        
        # OpenCV로 분석
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 1. 빈 영역 감지
        empty_regions = self._detect_empty_regions(img)
        
        # 2. 텍스트 영역 감지
        text_regions = self._detect_text_regions(img)
        
        # 3. 최적 썸네일 위치 계산
        optimal_positions = self._calculate_optimal_positions(
            empty_regions, text_regions, page.rect
        )
        
        return {
            "thumbnail_suggestions": optimal_positions,
            "confidence": self._calculate_confidence(optimal_positions),
            "layout_type": self._detect_layout_type(text_regions)
        }
    
    def _detect_empty_regions(self, img: np.ndarray) -> list:
        """빈 영역 감지"""
        # 그레이스케일 변환
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 엣지 감지
        edges = cv2.Canny(gray, 50, 150)
        
        # 윤곽선 찾기
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        # 큰 빈 영역 찾기
        empty_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 10000:  # 최소 크기 필터
                x, y, w, h = cv2.boundingRect(contour)
                empty_regions.append({"x": x, "y": y, "width": w, "height": h})
        
        return empty_regions
    
    def _detect_text_regions(self, img: np.ndarray) -> list:
        """텍스트 영역 감지 (OCR 없이 휴리스틱)"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 모폴로지 연산으로 텍스트 블록 찾기
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(gray, kernel, iterations=3)
        
        # 텍스트 영역 찾기
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        text_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            text_regions.append({"x": x, "y": y, "width": w, "height": h})
        
        return text_regions
    
    def _calculate_optimal_positions(self, empty_regions, text_regions, 
                                    page_rect) -> list:
        """최적 썸네일 위치 계산"""
        suggestions = []
        
        # 2-up 레이아웃 기준
        page_width = page_rect.width
        page_height = page_rect.height
        
        # 좌/우 페이지 중앙 근처 빈 공간 찾기
        left_center = page_width * 0.25
        right_center = page_width * 0.75
        
        for region in empty_regions:
            # 왼쪽 페이지 영역
            if abs(region['x'] + region['width']/2 - left_center) < 100:
                suggestions.append({
                    "side": "left",
                    "x": region['x'],
                    "y": region['y'],
                    "width": min(region['width'], 160),
                    "height": min(region['height'], 250)
                })
            
            # 오른쪽 페이지 영역  
            if abs(region['x'] + region['width']/2 - right_center) < 100:
                suggestions.append({
                    "side": "right",
                    "x": region['x'],
                    "y": region['y'],
                    "width": min(region['width'], 160),
                    "height": min(region['height'], 250)
                })
        
        return suggestions[:2]  # 최대 2개 제안
```

#### GUI 통합
```python
# gui/modern_settings.py 수정
def auto_detect_layout(self):
    """자동 레이아웃 감지 버튼 이벤트"""
    if not self.sample_pdf_path:
        messagebox.showwarning("경고", "먼저 샘플 PDF를 선택하세요")
        return
    
    analyzer = LayoutAnalyzer()
    suggestions = analyzer.analyze_pdf_layout(self.sample_pdf_path)
    
    if suggestions['confidence'] > 0.7:
        if messagebox.askyesno("자동 설정", 
                              f"레이아웃 타입: {suggestions['layout_type']}\n"
                              f"신뢰도: {suggestions['confidence']:.0%}\n"
                              f"제안된 설정을 적용하시겠습니까?"):
            self.apply_suggestions(suggestions['thumbnail_suggestions'])
    else:
        messagebox.showinfo("알림", "자동 감지 신뢰도가 낮습니다. 수동 설정을 권장합니다.")
```

---

### 4. ⚡ 배치 처리 개선

#### 현실성 평가: ⭐⭐⭐⭐⭐ (매우 높음)
- 현재 멀티스레딩 지원 있음
- queue 모듈로 쉽게 구현 가능
- tkinter 프로그레스바 지원

#### 구현 방안

```python
# core/batch_processor.py (신규)
import queue
import threading
from enum import Enum
from dataclasses import dataclass
from typing import List, Callable

class JobStatus(Enum):
    PENDING = "대기중"
    PROCESSING = "처리중"
    PAUSED = "일시정지"
    COMPLETED = "완료"
    FAILED = "실패"
    RETRY = "재시도중"

@dataclass
class ProcessJob:
    """처리 작업 단위"""
    id: str
    order_pdf: str
    print_pdfs: List[str]
    qr_image: str
    priority: int = 0
    status: JobStatus = JobStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    error_message: str = ""
    progress: float = 0.0

class BatchProcessor:
    """배치 처리 큐 시스템"""
    
    def __init__(self, max_workers: int = 4):
        self.job_queue = queue.PriorityQueue()
        self.active_jobs = {}
        self.completed_jobs = []
        self.failed_jobs = []
        
        self.max_workers = max_workers
        self.workers = []
        self.paused = False
        self.stop_flag = threading.Event()
        
        # 진행 상황 콜백
        self.progress_callback: Callable = None
        self.completion_callback: Callable = None
        
    def add_job(self, job: ProcessJob, priority: int = 0):
        """작업 추가 (우선순위 지원)"""
        job.priority = priority
        self.job_queue.put((-priority, job.id, job))  # 음수로 높은 우선순위 먼저
        
    def start_processing(self):
        """배치 처리 시작"""
        self.stop_flag.clear()
        
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_thread,
                args=(i,),
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
    
    def pause_processing(self):
        """처리 일시정지"""
        self.paused = True
        
    def resume_processing(self):
        """처리 재개"""
        self.paused = False
        
    def stop_processing(self):
        """처리 중지"""
        self.stop_flag.set()
        for worker in self.workers:
            worker.join(timeout=5)
    
    def _worker_thread(self, worker_id: int):
        """워커 스레드"""
        while not self.stop_flag.is_set():
            if self.paused:
                threading.Event().wait(0.1)
                continue
            
            try:
                # 큐에서 작업 가져오기
                priority, job_id, job = self.job_queue.get(timeout=1)
                
                # 작업 처리
                self.active_jobs[job_id] = job
                job.status = JobStatus.PROCESSING
                
                # 진행 상황 업데이트
                if self.progress_callback:
                    self.progress_callback(job_id, 0)
                
                # 실제 PDF 처리
                success = self._process_single_job(job, worker_id)
                
                if success:
                    job.status = JobStatus.COMPLETED
                    job.progress = 100
                    self.completed_jobs.append(job)
                else:
                    # 재시도 로직
                    if job.retry_count < job.max_retries:
                        job.retry_count += 1
                        job.status = JobStatus.RETRY
                        self.job_queue.put((-job.priority, job_id, job))
                    else:
                        job.status = JobStatus.FAILED
                        self.failed_jobs.append(job)
                
                # 완료 콜백
                if self.completion_callback:
                    self.completion_callback(job_id, job.status)
                
                del self.active_jobs[job_id]
                self.job_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}")
    
    def _process_single_job(self, job: ProcessJob, worker_id: int) -> bool:
        """단일 작업 처리"""
        try:
            # 설정 로드
            settings_manager = SettingsManager()
            processor = PDFProcessor(settings_manager)
            
            # 진행 상황 추적을 위한 콜백 설정
            def update_progress(value):
                job.progress = value
                if self.progress_callback:
                    self.progress_callback(job.id, value)
            
            processor.set_progress_callback(update_progress)
            
            # PDF 처리
            result = processor.process_files(
                job.order_pdf,
                job.print_pdfs,
                job.qr_image
            )
            
            return result
            
        except Exception as e:
            job.error_message = str(e)
            self.logger.error(f"Job {job.id} failed: {e}")
            return False
    
    def get_statistics(self) -> dict:
        """처리 통계"""
        return {
            "pending": self.job_queue.qsize(),
            "active": len(self.active_jobs),
            "completed": len(self.completed_jobs),
            "failed": len(self.failed_jobs),
            "total_progress": self._calculate_total_progress()
        }
```

#### GUI 통합 - 진행률 표시
```python
# gui/batch_progress_window.py (신규)
import tkinter as tk
from tkinter import ttk
import threading

class BatchProgressWindow:
    """배치 처리 진행 상황 윈도우"""
    
    def __init__(self, parent, batch_processor):
        self.window = tk.Toplevel(parent)
        self.window.title("배치 처리 진행 상황")
        self.window.geometry("600x400")
        
        self.batch_processor = batch_processor
        self.job_widgets = {}
        
        self.setup_ui()
        self.update_progress()
    
    def setup_ui(self):
        """UI 구성"""
        # 전체 진행률
        self.overall_frame = tk.Frame(self.window, relief='ridge', bd=2)
        self.overall_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(self.overall_frame, text="전체 진행률", 
                font=('Arial', 12, 'bold')).pack()
        
        self.overall_progress = ttk.Progressbar(
            self.overall_frame, 
            mode='determinate',
            style='Overall.Horizontal.TProgressbar'
        )
        self.overall_progress.pack(fill='x', padx=10, pady=5)
        
        self.stats_label = tk.Label(self.overall_frame, text="")
        self.stats_label.pack()
        
        # 컨트롤 버튼
        control_frame = tk.Frame(self.window)
        control_frame.pack(pady=10)
        
        self.pause_btn = tk.Button(
            control_frame, 
            text="일시정지",
            command=self.toggle_pause,
            width=15
        )
        self.pause_btn.pack(side='left', padx=5)
        
        self.stop_btn = tk.Button(
            control_frame,
            text="중지",
            command=self.stop_processing,
            width=15
        )
        self.stop_btn.pack(side='left', padx=5)
        
        # 개별 작업 목록
        list_frame = tk.Frame(self.window)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 스크롤바
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        # 트리뷰로 작업 목록 표시
        self.job_tree = ttk.Treeview(
            list_frame,
            columns=('파일', '상태', '진행률', '재시도'),
            yscrollcommand=scrollbar.set
        )
        
        self.job_tree.heading('#0', text='ID')
        self.job_tree.heading('파일', text='파일명')
        self.job_tree.heading('상태', text='상태')
        self.job_tree.heading('진행률', text='진행률')
        self.job_tree.heading('재시도', text='재시도')
        
        self.job_tree.column('#0', width=80)
        self.job_tree.column('파일', width=200)
        self.job_tree.column('상태', width=100)
        self.job_tree.column('진행률', width=100)
        self.job_tree.column('재시도', width=80)
        
        self.job_tree.pack(fill='both', expand=True)
        scrollbar.config(command=self.job_tree.yview)
    
    def toggle_pause(self):
        """일시정지/재개 토글"""
        if self.batch_processor.paused:
            self.batch_processor.resume_processing()
            self.pause_btn.config(text="일시정지")
        else:
            self.batch_processor.pause_processing()
            self.pause_btn.config(text="재개")
    
    def update_progress(self):
        """진행 상황 업데이트"""
        stats = self.batch_processor.get_statistics()
        
        # 전체 진행률 업데이트
        self.overall_progress['value'] = stats['total_progress']
        
        # 통계 라벨 업데이트
        self.stats_label.config(
            text=f"대기: {stats['pending']} | "
                 f"처리중: {stats['active']} | "
                 f"완료: {stats['completed']} | "
                 f"실패: {stats['failed']}"
        )
        
        # 100ms 후 다시 업데이트
        self.window.after(100, self.update_progress)
```

---

### 10. 🔧 고급 설정

#### 현실성 평가: ⭐⭐⭐⭐⭐ (매우 높음)
- 설정 구조만 확장하면 됨
- PyMuPDF가 PDF 최적화 지원
- OCR은 선택적 구현 가능

#### 구현 방안

```python
# config/settings_manager.py 수정
class SettingsManager:
    DEFAULT_SETTINGS = {
        # ... 기존 설정 ...
        
        "advanced": {
            "pdf_optimization": {
                "enabled": True,
                "compress_images": True,
                "image_quality": 85,  # JPEG 품질 (0-100)
                "remove_duplicates": True,
                "optimize_fonts": True,
                "linearize": True,  # 웹 최적화
                "garbage_collect": 4,  # 가비지 컬렉션 레벨 (0-4)
                "clean_pages": True
            },
            "ocr": {
                "enabled": False,
                "engine": "tesseract",  # tesseract, easyocr
                "language": "kor+eng",
                "confidence_threshold": 0.8,
                "preprocess": True,  # 이미지 전처리
                "searchable_pdf": False  # 검색 가능한 PDF 생성
            },
            "network": {
                "proxy": {
                    "enabled": False,
                    "http": "",
                    "https": "",
                    "no_proxy": "localhost,127.0.0.1"
                },
                "timeout": 30,
                "retry_count": 3,
                "retry_delay": 1
            },
            "processing": {
                "parallel_pages": True,  # 페이지 병렬 처리
                "chunk_size": 10,  # 한 번에 처리할 페이지 수
                "memory_limit_mb": 1024,  # 메모리 제한
                "temp_directory": "temp",  # 임시 파일 디렉토리
                "keep_temp_files": False  # 임시 파일 유지
            },
            "quality": {
                "thumbnail_dpi": 300,
                "thumbnail_format": "JPEG",  # JPEG, PNG
                "thumbnail_compression": "high",  # low, medium, high
                "pdf_version": "1.7",  # PDF 버전
                "color_space": "RGB"  # RGB, CMYK, Grayscale
            },
            "logging": {
                "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
                "file_logging": True,
                "console_logging": True,
                "max_file_size_mb": 10,
                "backup_count": 5,
                "format": "detailed"  # simple, detailed, json
            }
        }
    }
```

#### PDF 최적화 구현
```python
# core/pdf_optimizer.py (신규)
import fitz
from PIL import Image
import io

class PDFOptimizer:
    """PDF 최적화 엔진"""
    
    def __init__(self, settings: dict):
        self.settings = settings['pdf_optimization']
        
    def optimize_pdf(self, input_path: str, output_path: str) -> dict:
        """PDF 최적화"""
        doc = fitz.open(input_path)
        original_size = os.path.getsize(input_path)
        
        stats = {
            "original_size": original_size,
            "optimized_size": 0,
            "compression_ratio": 0,
            "images_compressed": 0,
            "duplicates_removed": 0,
            "fonts_optimized": 0
        }
        
        if self.settings['compress_images']:
            stats['images_compressed'] = self._compress_images(doc)
        
        if self.settings['remove_duplicates']:
            stats['duplicates_removed'] = self._remove_duplicate_images(doc)
        
        if self.settings['optimize_fonts']:
            stats['fonts_optimized'] = self._optimize_fonts(doc)
        
        if self.settings['clean_pages']:
            self._clean_pages(doc)
        
        # 가비지 컬렉션
        if self.settings['garbage_collect'] > 0:
            doc.save(
                output_path,
                garbage=self.settings['garbage_collect'],
                deflate=True,
                linear=self.settings.get('linearize', False)
            )
        else:
            doc.save(output_path)
        
        doc.close()
        
        stats['optimized_size'] = os.path.getsize(output_path)
        stats['compression_ratio'] = (
            (original_size - stats['optimized_size']) / original_size * 100
        )
        
        return stats
    
    def _compress_images(self, doc: fitz.Document) -> int:
        """이미지 압축"""
        compressed_count = 0
        quality = self.settings.get('image_quality', 85)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    # PIL로 변환하여 압축
                    img_data = pix.tobytes("jpeg", quality=quality)
                    
                    # 압축된 이미지로 교체
                    doc._deleteObject(xref)
                    doc._insert_image(page, img_data)
                    compressed_count += 1
                
                pix = None
        
        return compressed_count
    
    def _remove_duplicate_images(self, doc: fitz.Document) -> int:
        """중복 이미지 제거"""
        image_hashes = {}
        removed_count = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img in image_list:
                xref = img[0]
                img_data = doc.extract_image(xref)
                img_hash = hashlib.md5(img_data['image']).hexdigest()
                
                if img_hash in image_hashes:
                    # 중복 이미지를 원본 참조로 교체
                    doc._deleteObject(xref)
                    removed_count += 1
                else:
                    image_hashes[img_hash] = xref
        
        return removed_count
```

#### OCR 통합 (선택적)
```python
# core/ocr_engine.py (신규)
try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False

class OCREngine:
    """OCR 엔진 래퍼"""
    
    def __init__(self, settings: dict):
        self.settings = settings
        self.engine = settings.get('engine', 'tesseract')
        
        if self.engine == 'easyocr' and HAS_EASYOCR:
            self.reader = easyocr.Reader(['ko', 'en'])
        
    def extract_text(self, image_path: str) -> str:
        """이미지에서 텍스트 추출"""
        if not self.settings['enabled']:
            return ""
        
        if self.engine == 'tesseract' and HAS_TESSERACT:
            return self._tesseract_ocr(image_path)
        elif self.engine == 'easyocr' and HAS_EASYOCR:
            return self._easyocr_ocr(image_path)
        
        return ""
    
    def _tesseract_ocr(self, image_path: str) -> str:
        """Tesseract OCR"""
        config = f"--oem 3 --psm 6"
        text = pytesseract.image_to_string(
            Image.open(image_path),
            lang=self.settings['language'],
            config=config
        )
        return text
    
    def _easyocr_ocr(self, image_path: str) -> str:
        """EasyOCR"""
        results = self.reader.readtext(image_path)
        text = " ".join([result[1] for result in results 
                        if result[2] > self.settings['confidence_threshold']])
        return text
```

---

### 12. 🔄 워크플로우 자동화

#### 현실성 평가: ⭐⭐⭐⭐ (높음)
- watchdog 라이브러리로 폴더 감시 가능
- 이메일/FTP는 표준 라이브러리 지원
- 현재 구조에 쉽게 통합 가능

#### 구현 방안

```python
# core/workflow_automation.py (신규)
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import smtplib
import ftplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import time

class PDFWatchHandler(FileSystemEventHandler):
    """PDF 파일 감시 핸들러"""
    
    def __init__(self, processor, workflow_config):
        self.processor = processor
        self.config = workflow_config
        self.processing_queue = []
        self.processed_files = set()
        
    def on_created(self, event):
        """새 파일 생성 시"""
        if event.is_directory:
            return
        
        if event.src_path.endswith('.pdf'):
            # 의뢰서 PDF인지 확인
            if '의뢰서' in os.path.basename(event.src_path):
                self.process_new_order(event.src_path)
    
    def process_new_order(self, order_pdf_path):
        """새 의뢰서 처리"""
        if order_pdf_path in self.processed_files:
            return
        
        self.processed_files.add(order_pdf_path)
        
        # 연관 파일 자동 찾기
        directory = os.path.dirname(order_pdf_path)
        base_name = os.path.splitext(os.path.basename(order_pdf_path))[0]
        
        # 동일한 이름 패턴의 파일 찾기
        print_pdfs = []
        qr_image = None
        
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            
            if base_name in file:
                if file.endswith('.pdf') and '의뢰서' not in file:
                    print_pdfs.append(file_path)
                elif file.endswith(('.png', '.jpg', '.jpeg')):
                    qr_image = file_path
        
        # 처리 시작
        self._start_processing(order_pdf_path, print_pdfs, qr_image)
    
    def _start_processing(self, order_pdf, print_pdfs, qr_image):
        """자동 처리 시작"""
        try:
            # PDF 처리
            result = self.processor.process_files(
                order_pdf, print_pdfs, qr_image
            )
            
            if result:
                output_file = result['output_path']
                
                # 완료 폴더로 이동
                if self.config['move_to_completed']:
                    self._move_to_completed(output_file)
                
                # 알림 전송
                if self.config['notifications']['enabled']:
                    self._send_notification(output_file)
                
                # FTP 업로드
                if self.config['ftp']['enabled']:
                    self._upload_to_ftp(output_file)
                
        except Exception as e:
            self.logger.error(f"자동 처리 실패: {e}")
            self._send_error_notification(str(e))
    
    def _move_to_completed(self, file_path):
        """완료 폴더로 이동"""
        completed_dir = self.config['completed_folder']
        if not os.path.exists(completed_dir):
            os.makedirs(completed_dir)
        
        dest_path = os.path.join(
            completed_dir, 
            os.path.basename(file_path)
        )
        shutil.move(file_path, dest_path)
        
        return dest_path
    
    def _send_notification(self, file_path):
        """처리 완료 알림"""
        if self.config['notifications']['email']['enabled']:
            self._send_email_notification(file_path)
        
        if self.config['notifications']['webhook']['enabled']:
            self._send_webhook_notification(file_path)
    
    def _send_email_notification(self, file_path):
        """이메일 알림"""
        config = self.config['notifications']['email']
        
        msg = MIMEMultipart()
        msg['From'] = config['from']
        msg['To'] = config['to']
        msg['Subject'] = f"PDF 처리 완료: {os.path.basename(file_path)}"
        
        body = f"""
        PDF 처리가 완료되었습니다.
        
        파일명: {os.path.basename(file_path)}
        처리 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        파일 크기: {os.path.getsize(file_path) / 1024 / 1024:.2f} MB
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # 첨부 파일
        if config['attach_file']:
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'pdf')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={os.path.basename(file_path)}'
                )
                msg.attach(part)
        
        # 이메일 전송
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            if config['use_tls']:
                server.starttls()
            server.login(config['username'], config['password'])
            server.send_message(msg)
    
    def _upload_to_ftp(self, file_path):
        """FTP 업로드"""
        config = self.config['ftp']
        
        with ftplib.FTP(config['host'], config['username'], 
                       config['password']) as ftp:
            if config['directory']:
                ftp.cwd(config['directory'])
            
            with open(file_path, 'rb') as f:
                ftp.storbinary(
                    f"STOR {os.path.basename(file_path)}", 
                    f
                )

class WorkflowAutomation:
    """워크플로우 자동화 관리자"""
    
    def __init__(self, workflow_config):
        self.config = workflow_config
        self.observer = Observer()
        self.handlers = []
        
    def start_monitoring(self, folders: list):
        """폴더 모니터링 시작"""
        for folder in folders:
            if os.path.exists(folder):
                handler = PDFWatchHandler(
                    PDFProcessor(SettingsManager()),
                    self.config
                )
                self.observer.schedule(
                    handler, 
                    folder, 
                    recursive=self.config.get('recursive', False)
                )
                self.handlers.append(handler)
        
        self.observer.start()
        
    def stop_monitoring(self):
        """모니터링 중지"""
        self.observer.stop()
        self.observer.join()
```

#### 워크플로우 설정 구조
```json
{
  "workflow": {
    "enabled": true,
    "watch_folders": [
      "C:/Orders/Input",
      "D:/PDF_Queue"
    ],
    "recursive": false,
    "file_patterns": ["*의뢰서*.pdf"],
    "auto_match_files": true,
    "completed_folder": "C:/Orders/Completed",
    "error_folder": "C:/Orders/Error",
    "move_to_completed": true,
    
    "notifications": {
      "enabled": true,
      "email": {
        "enabled": true,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "use_tls": true,
        "username": "your-email@gmail.com",
        "password": "app-password",
        "from": "your-email@gmail.com",
        "to": "recipient@example.com",
        "attach_file": false
      },
      "webhook": {
        "enabled": false,
        "url": "https://hooks.slack.com/services/...",
        "method": "POST"
      }
    },
    
    "ftp": {
      "enabled": false,
      "host": "ftp.example.com",
      "port": 21,
      "username": "ftpuser",
      "password": "ftppass",
      "directory": "/uploads",
      "passive": true
    },
    
    "schedule": {
      "enabled": false,
      "times": ["09:00", "14:00", "18:00"],
      "days": ["mon", "tue", "wed", "thu", "fri"]
    }
  }
}
```

---

## 📊 구현 우선순위 및 난이도

| 기능 | 난이도 | 소요시간 | 우선순위 | 의존성 |
|------|--------|----------|----------|--------|
| **배치 처리 개선** | ⭐⭐ | 2-3일 | 높음 | 없음 |
| **고급 설정** | ⭐ | 1-2일 | 높음 | 없음 |
| **워크플로우 자동화** | ⭐⭐⭐ | 3-4일 | 중간 | watchdog |
| **자동 업데이트** | ⭐⭐⭐ | 2-3일 | 중간 | requests |
| **AI 자동 설정** | ⭐⭐⭐⭐ | 5-7일 | 낮음 | OpenCV |

## 🛠 필요한 추가 라이브러리

```txt
# requirements.txt 추가
requests>=2.28.0        # 자동 업데이트
packaging>=23.0         # 버전 비교
opencv-python>=4.8.0    # AI 레이아웃 분석
watchdog>=3.0.0        # 폴더 모니터링
pytesseract>=0.3.10    # OCR (선택적)
easyocr>=1.7.0         # OCR (선택적)
```

## 💡 구현 권장사항

### 단계별 구현 전략

#### 1단계 (즉시 구현 가능)
- ✅ 배치 처리 큐 시스템
- ✅ 진행률 표시
- ✅ 고급 설정 (PDF 최적화)

#### 2단계 (중기 목표)
- ✅ 폴더 모니터링
- ✅ 자동 업데이트
- ✅ 이메일/FTP 통합

#### 3단계 (장기 목표)
- ✅ AI 레이아웃 분석
- ✅ OCR 통합
- ✅ 웹 인터페이스

## 🎯 결론

요청하신 5가지 기능 모두 **현실적으로 구현 가능**합니다:

1. **자동 업데이트** - GitHub API 활용으로 쉽게 구현
2. **AI 자동 설정** - OpenCV로 충분히 구현 가능
3. **배치 처리 개선** - 현재 구조에서 가장 쉽게 추가 가능
4. **고급 설정** - 설정 구조 확장만으로 구현
5. **워크플로우 자동화** - watchdog으로 안정적 구현

특히 **배치 처리 개선**과 **고급 설정**은 현재 코드베이스와 잘 맞아 즉시 구현 가능하며, 사용자 경험을 크게 향상시킬 것입니다.