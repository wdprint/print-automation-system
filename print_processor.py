import fitz
from PIL import Image, ImageEnhance, ImageOps
from pathlib import Path
import json
import os
from io import BytesIO
import numpy as np
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from datetime import datetime
import hashlib

class EnhancedPrintProcessor:
    """향상된 PDF 처리 엔진"""
    
    def __init__(self):
        self.dropped_files = {
            'order_pdf': None,
            'print_pdf': None,
            'qr_image': None
        }
        self.temp_normalized_file = None
        self.settings = self.load_enhanced_settings()
        self.blank_detection_cache = {}
        self.processing_queue = queue.Queue()
        
        # 멀티스레딩 설정
        if self.settings["performance"]["multithreading"]:
            self.executor = ThreadPoolExecutor(
                max_workers=self.settings["performance"]["max_concurrent_files"]
            )
        else:
            self.executor = None
    
    def load_enhanced_settings(self):
        """향상된 설정 로드"""
        settings_path = Path("enhanced_settings.json")
        
        if settings_path.exists():
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 기본 설정 로드
        return self._get_default_settings()
    
    def _get_default_settings(self):
        """기본 설정 반환"""
        return {
            "thumbnail": {
                "max_width": 160,
                "max_height": 250,
                "positions": [
                    {"x": 70, "y": 180},
                    {"x": 490, "y": 180}
                ],
                "multi_page": False,
                "page_selection": "1",
                "grayscale": False,
                "contrast": 1.0,
                "sharpness": 1.0
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
                "threshold": 95,
                "algorithm": "simple",
                "exclude_areas": {
                    "header": 50,
                    "footer": 50,
                    "left_margin": 20,
                    "right_margin": 20
                },
                "cache_enabled": True
            },
            "processing_rules": {
                "enabled": False,
                "rules": []
            },
            "performance": {
                "multithreading": True,
                "max_concurrent_files": 3,
                "cache_size_mb": 100
            }
        }
    
    def apply_processing_rules(self, file_path):
        """파일명에 따른 처리 규칙 적용"""
        if not self.settings["processing_rules"]["enabled"]:
            return None
        
        filename = os.path.basename(file_path)
        
        for rule in self.settings["processing_rules"]["rules"]:
            if re.search(rule["pattern"], filename, re.IGNORECASE):
                print(f"규칙 매칭: {rule['name']}")
                
                # 프리셋 적용
                if rule.get("preset"):
                    self.apply_preset(rule["preset"])
                
                # 액션 반환
                return rule.get("action")
        
        return None
    
    def apply_preset(self, preset_name):
        """프리셋 적용"""
        presets = self.settings.get("presets", {})
        if preset_name in presets:
            preset_settings = presets[preset_name].get("settings", {})
            
            # 설정 업데이트
            for key, value in preset_settings.items():
                if key in self.settings:
                    self.settings[key] = value.copy()
            
            # 사용 통계 업데이트
            presets[preset_name]["last_used"] = datetime.now().isoformat()
            presets[preset_name]["use_count"] = presets[preset_name].get("use_count", 0) + 1
            
            print(f"프리셋 '{presets[preset_name]['name']}' 적용됨")
    
    def is_page_blank_enhanced(self, page):
        """향상된 백지 감지"""
        if not self.settings["blank_detection"]["enabled"]:
            return False
        
        # 캐시 확인
        page_hash = self._get_page_hash(page)
        if self.settings["blank_detection"]["cache_enabled"] and page_hash in self.blank_detection_cache:
            return self.blank_detection_cache[page_hash]
        
        algorithm = self.settings["blank_detection"]["algorithm"]
        threshold = self.settings["blank_detection"]["threshold"]
        
        # 페이지를 이미지로 변환
        pix = page.get_pixmap(dpi=150)
        img_data = pix.pil_tobytes(format="PNG")
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
        
        if crop_box[2] > crop_box[0] and crop_box[3] > crop_box[1]:
            img = img.crop(crop_box)
        
        # 알고리즘별 처리
        is_blank = False
        if algorithm == "simple":
            is_blank = self._simple_blank_detection(img, threshold)
        elif algorithm == "entropy":
            is_blank = self._entropy_blank_detection(img, threshold)
        else:  # histogram
            is_blank = self._histogram_blank_detection(img, threshold)
        
        # 캐시 저장
        if self.settings["blank_detection"]["cache_enabled"]:
            self.blank_detection_cache[page_hash] = is_blank
        
        return is_blank
    
    def _get_page_hash(self, page):
        """페이지 해시 생성 (캐싱용)"""
        page_content = page.get_text().encode('utf-8')
        return hashlib.md5(page_content).hexdigest()
    
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
    
    def create_enhanced_thumbnail(self, pdf_path):
        """향상된 썸네일 생성"""
        doc = fitz.open(pdf_path)
        
        # 페이지 선택 파싱
        pages_to_use = self._parse_page_selection(
            self.settings["thumbnail"]["page_selection"],
            len(doc)
        )
        
        thumbnails = []
        
        for page_num in pages_to_use:
            if page_num >= len(doc):
                continue
            
            page = doc[page_num]
            
            # 백지 건너뛰기
            if self.is_page_blank_enhanced(page):
                print(f"페이지 {page_num + 1}은 백지입니다. 건너뜁니다.")
                continue
            
            # 페이지를 이미지로 변환
            mat = fitz.Matrix(2.0, 2.0)  # 2배 해상도
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_data = pix.pil_tobytes(format="PNG")
            img = Image.open(BytesIO(img_data))
            
            # 이미지 처리 적용
            img = self._apply_image_effects(img)
            
            thumbnails.append(img)
        
        doc.close()
        
        # 다중 페이지 처리
        if self.settings["thumbnail"]["multi_page"] and len(thumbnails) > 1:
            return self._combine_thumbnails(thumbnails)
        elif thumbnails:
            return thumbnails[0]
        else:
            return None
    
    def _parse_page_selection(self, selection_str, total_pages):
        """페이지 선택 문자열 파싱"""
        pages = []
        
        # 기본값: 첫 페이지만
        if not selection_str or selection_str == "1":
            return [0]
        
        parts = selection_str.split(',')
        for part in parts:
            part = part.strip()
            
            if '-' in part:
                # 범위 (예: 1-3)
                try:
                    start, end = part.split('-')
                    start = max(1, int(start))
                    end = min(total_pages, int(end))
                    pages.extend(range(start - 1, end))
                except:
                    pass
            else:
                # 단일 페이지
                try:
                    page_num = int(part) - 1
                    if 0 <= page_num < total_pages:
                        pages.append(page_num)
                except:
                    pass
        
        return pages if pages else [0]
    
    def _apply_image_effects(self, img):
        """이미지 효과 적용"""
        # 흑백 변환
        if self.settings["thumbnail"]["grayscale"]:
            img = ImageOps.grayscale(img)
        
        # 대비 조정
        contrast = self.settings["thumbnail"]["contrast"]
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)
        
        # 선명도 조정
        sharpness = self.settings["thumbnail"]["sharpness"]
        if sharpness != 1.0:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(sharpness)
        
        return img
    
    def _combine_thumbnails(self, thumbnails):
        """여러 썸네일을 하나로 결합"""
        if not thumbnails:
            return None
        
        # 2x2 그리드로 결합 (최대 4개)
        thumbnails = thumbnails[:4]
        
        # 각 썸네일 크기 조정
        thumb_size = (200, 280)  # 개별 썸네일 크기
        resized = []
        for thumb in thumbnails:
            thumb_resized = thumb.copy()
            thumb_resized.thumbnail(thumb_size, Image.Resampling.LANCZOS)
            resized.append(thumb_resized)
        
        # 결합 이미지 생성
        if len(resized) == 1:
            return resized[0]
        elif len(resized) == 2:
            # 가로로 배치
            combined = Image.new('RGB', (thumb_size[0] * 2, thumb_size[1]), 'white')
            combined.paste(resized[0], (0, 0))
            combined.paste(resized[1], (thumb_size[0], 0))
        else:
            # 2x2 그리드
            combined = Image.new('RGB', (thumb_size[0] * 2, thumb_size[1] * 2), 'white')
            positions = [(0, 0), (thumb_size[0], 0), (0, thumb_size[1]), (thumb_size[0], thumb_size[1])]
            for i, thumb in enumerate(resized):
                if i < 4:
                    combined.paste(thumb, positions[i])
        
        return combined
    
    def process_files_enhanced(self):
        """향상된 파일 처리"""
        try:
            # 처리 규칙 적용
            if self.dropped_files['print_pdf']:
                action = self.apply_processing_rules(self.dropped_files['print_pdf'])
                
                # 액션 실행
                if action == "crop_right_half":
                    self._crop_right_half = True
                elif action == "skip_blank_pages":
                    self._skip_blank_pages = True
                elif action == "force_grayscale":
                    self.settings["thumbnail"]["grayscale"] = True
            
            # 멀티스레딩 처리
            if self.executor and self.settings["performance"]["multithreading"]:
                return self._process_files_multithreaded()
            else:
                return self._process_files_single_threaded()
            
        except Exception as e:
            print(f"처리 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _process_files_multithreaded(self):
        """멀티스레드로 파일 처리"""
        futures = []
        
        # 작업 분할
        if self.dropped_files['print_pdf']:
            future = self.executor.submit(self.create_enhanced_thumbnail, self.dropped_files['print_pdf'])
            futures.append(('thumbnail', future))
        
        # 결과 수집
        results = {}
        for task_name, future in futures:
            try:
                result = future.result(timeout=30)
                results[task_name] = result
            except Exception as e:
                print(f"{task_name} 처리 실패: {e}")
                results[task_name] = None
        
        # 실제 PDF 처리 (단일 스레드로)
        return self._apply_to_pdf(results.get('thumbnail'))
    
    def _process_files_single_threaded(self):
        """단일 스레드로 파일 처리"""
        thumbnail = None
        
        if self.dropped_files['print_pdf']:
            thumbnail = self.create_enhanced_thumbnail(self.dropped_files['print_pdf'])
        
        return self._apply_to_pdf(thumbnail)
    
    def _apply_to_pdf(self, thumbnail):
        """PDF에 이미지 적용"""
        if not self.dropped_files['order_pdf']:
            return False
        
        try:
            # PDF 열기
            doc = fitz.open(self.dropped_files['order_pdf'])
            
            for page_num, page in enumerate(doc):
                # 백지 건너뛰기
                if self.is_page_blank_enhanced(page):
                    print(f"페이지 {page_num + 1}은 백지입니다. 건너뜁니다.")
                    continue
                
                # 썸네일 삽입
                if thumbnail:
                    for position in self.settings["thumbnail"]["positions"]:
                        rect = fitz.Rect(
                            position["x"],
                            position["y"],
                            position["x"] + self.settings["thumbnail"]["max_width"],
                            position["y"] + self.settings["thumbnail"]["max_height"]
                        )
                        
                        # PIL 이미지를 PDF에 삽입
                        img_buffer = BytesIO()
                        thumbnail.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        
                        page.insert_image(rect, stream=img_buffer.getvalue())
                
                # QR 코드 삽입
                if self.dropped_files['qr_image']:
                    for position in self.settings["qr"]["positions"]:
                        rect = fitz.Rect(
                            position["x"],
                            position["y"],
                            position["x"] + self.settings["qr"]["max_width"],
                            position["y"] + self.settings["qr"]["max_height"]
                        )
                        
                        page.insert_image(rect, filename=self.dropped_files['qr_image'])
            
            # 저장
            doc.save(self.dropped_files['order_pdf'], incremental=True, encryption=0)
            doc.close()
            
            print("처리 완료!")
            return True
            
        except Exception as e:
            print(f"PDF 처리 중 오류: {e}")
            return False
    
    def clear_cache(self):
        """캐시 비우기"""
        self.blank_detection_cache.clear()
        print("캐시가 비워졌습니다")
    
    def get_performance_stats(self):
        """성능 통계 반환"""
        stats = {
            "cache_size": len(self.blank_detection_cache),
            "cache_memory_mb": sys.getsizeof(self.blank_detection_cache) / 1024 / 1024,
            "multithreading": self.settings["performance"]["multithreading"],
            "max_concurrent": self.settings["performance"]["max_concurrent_files"]
        }
        return stats


# 독립 실행 테스트
if __name__ == "__main__":
    import sys
    
    processor = EnhancedPrintProcessor()
    
    # 테스트 파일 처리
    if len(sys.argv) > 1:
        files = sys.argv[1:]
        processor.dropped_files = {
            'order_pdf': None,
            'print_pdf': None,
            'qr_image': None
        }
        
        for file in files:
            ext = Path(file).suffix.lower()
            if ext == '.pdf':
                if '의뢰서' in file:
                    processor.dropped_files['order_pdf'] = file
                else:
                    processor.dropped_files['print_pdf'] = file
            elif ext in ['.jpg', '.jpeg', '.png']:
                processor.dropped_files['qr_image'] = file
        
        success = processor.process_files_enhanced()
        sys.exit(0 if success else 1)
    else:
        print("사용법: python enhanced_print_processor.py [파일들...]")