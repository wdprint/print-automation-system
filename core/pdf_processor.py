"""PDF 처리 핵심 엔진 - v1 기능 통합"""

import os
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import tempfile
import shutil
from io import BytesIO
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

import fitz  # PyMuPDF
from PIL import Image, ImageEnhance, ImageOps
import numpy as np

from config.settings_manager import SettingsManager
from .image_handler import ImageHandler
from .blank_detector import BlankDetector
from .pdf_normalizer import PDFNormalizer
from utils.logger import setup_logger
from utils.performance import PerformanceMonitor, cached_result

class PDFProcessor:
    """PDF 처리 핵심 엔진 - v1 기능 통합"""
    
    def __init__(self, settings_manager: SettingsManager):
        """
        PDF 처리기 초기화
        
        Args:
            settings_manager: 설정 관리자
        """
        self.settings = settings_manager
        self.image_handler = ImageHandler(settings_manager)
        self.blank_detector = BlankDetector(settings_manager)
        self.pdf_normalizer = PDFNormalizer()
        self.logger = setup_logger(self.__class__.__name__)
        self.performance_monitor = PerformanceMonitor()
        
        # 임시 디렉토리
        self.temp_dir = None
        
        # 캐시
        self.thumbnail_cache = {}
        self.blank_detection_cache = {}
        
        # 멀티스레딩 설정
        if self.settings.get('performance.multithreading', True):
            max_workers = self.settings.get('performance.max_workers', 4)
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
        else:
            self.executor = None
    
    def process_files(self, order_pdf: str, print_pdfs: list, qr_image: str = None) -> bool:
        """
        메인 처리 함수 - 여러 PDF 파일 지원
        
        Args:
            order_pdf: 의뢰서 PDF 경로
            print_pdfs: 인쇄 데이터 PDF 경로 리스트 (썸네일용)
            qr_image: QR 코드 이미지 경로
            
        Returns:
            bool: 성공 여부
        """
        with self.performance_monitor.measure("total_processing"):
            try:
                # print_pdfs가 문자열인 경우 리스트로 변환
                if isinstance(print_pdfs, str):
                    print_pdfs = [print_pdfs] if print_pdfs else []
                elif print_pdfs is None:
                    print_pdfs = []
                
                self.logger.info(f"처리 시작 - 의뢰서: {order_pdf}, 인쇄 파일 수: {len(print_pdfs)}, QR: {qr_image}")
                
                # 파일 검증
                if not self._validate_files(order_pdf, print_pdfs, qr_image):
                    return False
                
                # 임시 디렉토리 생성
                self.temp_dir = tempfile.mkdtemp(prefix="pdf_process_")
                self.logger.debug(f"임시 디렉토리 생성: {self.temp_dir}")
                
                # PDF 정규화 (회전 수정)
                if self.settings.get('pdf_normalization.enabled', True):
                    order_pdf = self._normalize_pdf(order_pdf)
                
                # 출력 파일명 생성
                output_path = self._generate_output_path(order_pdf)
                
                # 처리 규칙 적용 (첫 번째 PDF 파일명 기준)
                if print_pdfs:
                    self._apply_processing_rules(print_pdfs[0])
                
                # PDF 처리 (멀티스레딩 옵션)
                if self.executor and self.settings.get('performance.multithreading', True):
                    success = self._process_pdf_multithreaded(order_pdf, print_pdfs, qr_image, output_path)
                else:
                    success = self._process_pdf_single_threaded(order_pdf, print_pdfs, qr_image, output_path)
                
                if success:
                    self.logger.info(f"처리 완료: {output_path}")
                    self.performance_monitor.log_stats()
                else:
                    self.logger.error("PDF 처리 실패")
                
                return success
                
            except Exception as e:
                self.logger.error(f"처리 중 오류 발생: {e}", exc_info=True)
                return False
                
            finally:
                # 임시 디렉토리 정리
                if self.temp_dir and os.path.exists(self.temp_dir):
                    try:
                        shutil.rmtree(self.temp_dir)
                        self.logger.debug("임시 디렉토리 삭제 완료")
                    except Exception as e:
                        self.logger.warning(f"임시 디렉토리 삭제 실패: {e}")
    
    def _validate_files(self, order_pdf: str, print_pdfs: list, qr_image: str = None) -> bool:
        """파일 유효성 검증"""
        try:
            # 파일 존재 확인
            if not os.path.exists(order_pdf):
                self.logger.error(f"의뢰서 파일이 존재하지 않습니다: {order_pdf}")
                return False
            
            # 여러 인쇄 PDF 파일 검증
            if print_pdfs:
                for pdf_path in print_pdfs:
                    if not os.path.exists(pdf_path):
                        self.logger.error(f"인쇄 파일이 존재하지 않습니다: {pdf_path}")
                        return False
            
            if qr_image and not os.path.exists(qr_image):
                self.logger.error(f"QR 이미지가 존재하지 않습니다: {qr_image}")
                return False
            
            # PDF 파일 검증
            try:
                doc = fitz.open(order_pdf)
                doc.close()
            except Exception as e:
                self.logger.error(f"의뢰서 PDF 파일이 손상되었습니다: {e}")
                return False
            
            # 여러 인쇄 PDF 파일 검증
            if print_pdfs:
                for pdf_path in print_pdfs:
                    try:
                        doc = fitz.open(pdf_path)
                        doc.close()
                    except Exception as e:
                        self.logger.error(f"인쇄 PDF 파일이 손상되었습니다 [{pdf_path}]: {e}")
                        return False
            
            # 이미지 파일 검증
            if qr_image:
                try:
                    Image.open(qr_image)
                except Exception as e:
                    self.logger.error(f"QR 이미지 파일이 손상되었습니다: {e}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"파일 검증 중 오류: {e}")
            return False
    
    def _normalize_pdf(self, pdf_path: str) -> str:
        """PDF 정규화 (회전 수정)"""
        try:
            normalized_path = self.pdf_normalizer.normalize(pdf_path, self.temp_dir)
            if normalized_path != pdf_path:
                self.logger.info(f"PDF 정규화 완료: {normalized_path}")
            return normalized_path
        except Exception as e:
            self.logger.warning(f"PDF 정규화 실패, 원본 사용: {e}")
            return pdf_path
    
    def _generate_output_path(self, order_pdf: str) -> str:
        """출력 파일 경로 생성"""
        base_path = Path(order_pdf)
        stem = base_path.stem
        parent = base_path.parent
        
        # "_완료" 접미사 추가
        output_name = f"{stem}_완료.pdf"
        output_path = parent / output_name
        
        # 파일이 이미 존재하면 번호 추가
        counter = 1
        while output_path.exists():
            output_name = f"{stem}_완료_{counter}.pdf"
            output_path = parent / output_name
            counter += 1
        
        return str(output_path)
    
    def _apply_processing_rules(self, file_path: str):
        """처리 규칙 적용"""
        if not self.settings.get('processing_rules.enabled', False):
            return
        
        rules = self.settings.get('processing_rules.rules', [])
        filename = os.path.basename(file_path)
        
        for rule in rules:
            import re
            if re.search(rule.get('pattern', ''), filename, re.IGNORECASE):
                self.logger.info(f"처리 규칙 매칭: {rule.get('name')}")
                
                # 액션 적용
                action = rule.get('action', {})
                if action.get('type') == 'modify_config':
                    changes = action.get('changes', {})
                    for key, value in changes.items():
                        self.settings.set(key, value)
    
    def _process_pdf_multithreaded(self, order_pdf: str, print_pdfs: list, 
                                   qr_image: str, output_path: str) -> bool:
        """멀티스레드로 PDF 처리"""
        try:
            futures = []
            
            # 여러 PDF에서 썸네일 생성 작업
            if print_pdfs:
                for idx, pdf_path in enumerate(print_pdfs):
                    future_thumbnail = self.executor.submit(
                        self._create_enhanced_thumbnails, pdf_path
                    )
                    futures.append((f'thumbnails_{idx}', future_thumbnail))
            
            # QR 이미지 로드 작업
            if qr_image:
                future_qr = self.executor.submit(
                    Image.open, qr_image
                )
                futures.append(('qr', future_qr))
            
            # 결과 수집
            results = {}
            for name, future in futures:
                try:
                    results[name] = future.result(timeout=30)
                except Exception as e:
                    self.logger.error(f"{name} 처리 실패: {e}")
                    results[name] = None
            
            # 썸네일 리스트 정리
            all_thumbnails = []
            for idx in range(len(print_pdfs)):
                thumb_result = results.get(f'thumbnails_{idx}', [])
                if thumb_result:
                    all_thumbnails.extend(thumb_result)
            
            # PDF에 적용
            return self._apply_to_pdf_with_multiple_thumbnails(
                order_pdf, 
                all_thumbnails if all_thumbnails else [],
                results.get('qr'),
                output_path
            )
            
        except Exception as e:
            self.logger.error(f"멀티스레드 처리 중 오류: {e}")
            return False
    
    def _process_pdf_single_threaded(self, order_pdf: str, print_pdfs: list,
                                     qr_image: str, output_path: str) -> bool:
        """단일 스레드로 PDF 처리"""
        try:
            # 여러 PDF에서 썸네일 생성
            all_thumbnails = []
            if print_pdfs:
                for pdf_path in print_pdfs:
                    thumbnails = self._create_enhanced_thumbnails(pdf_path)
                    if thumbnails:
                        all_thumbnails.extend(thumbnails)
            
            # QR 이미지 로드
            qr_img = None
            if qr_image:
                qr_img = Image.open(qr_image)
            
            # PDF에 적용
            return self._apply_to_pdf_with_multiple_thumbnails(order_pdf, all_thumbnails, qr_img, output_path)
            
        except Exception as e:
            self.logger.error(f"단일 스레드 처리 중 오류: {e}")
            return False
    
    def _create_enhanced_thumbnails(self, pdf_path: str) -> List[Image.Image]:
        """향상된 썸네일 생성 (v1 기능 통합)"""
        thumbnails = []
        
        try:
            # PDF 정규화 (회전 수정) - 썸네일 생성 전에 적용
            if self.settings.get('pdf_normalization.enabled', True):
                normalized_path = self.pdf_normalizer.process_for_thumbnail(pdf_path)
                if normalized_path != pdf_path:
                    self.logger.info(f"썸네일용 PDF 정규화: {normalized_path}")
                    pdf_path = normalized_path
            
            doc = fitz.open(pdf_path)
            
            # 페이지 선택 파싱
            page_selection = self.settings.get('thumbnail.page_selection', '1')
            pages_to_use = self._parse_page_selection(page_selection, len(doc))
            
            for page_num in pages_to_use:
                if page_num >= len(doc):
                    continue
                
                page = doc[page_num]
                
                # 백지 감지
                if self.blank_detector.is_blank_page(page):
                    self.logger.info(f"페이지 {page_num + 1}은 백지입니다. 건너뜁니다.")
                    continue
                
                # 페이지를 이미지로 변환 (고해상도)
                # DPI 기반 해상도 설정 (432 DPI = 6배)
                dpi = self.settings.get('thumbnail.render_dpi', 432)
                zoom = dpi / 72.0  # 72 DPI가 기본값
                mat = fitz.Matrix(zoom, zoom)  # 432 DPI = 6배
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_data = pix.pil_tobytes(format="PNG")
                img = Image.open(BytesIO(img_data))
                
                # 이미지 효과 적용
                img = self._apply_image_effects(img)
                
                # 썸네일 크기 가져오기 (설정에서 통일)
                thumb_width = self.settings.get('thumbnail.max_width', 200)
                thumb_height = self.settings.get('thumbnail.max_height', 300)
                
                # 두 단계 리사이징으로 품질 향상
                # 1단계: 목표 크기의 2배로 먼저 리사이즈
                intermediate_size = (thumb_width * 2, thumb_height * 2)
                img.thumbnail(intermediate_size, Image.Resampling.LANCZOS)
                
                # 2단계: 최종 크기로 리사이즈
                img.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                
                thumbnails.append(img)
            
            doc.close()
            
            # 다중 페이지 처리
            if self.settings.get('thumbnail.multi_page', False) and len(thumbnails) > 1:
                return [self._combine_thumbnails(thumbnails)]
            
            return thumbnails
            
        except Exception as e:
            self.logger.error(f"썸네일 생성 실패: {e}")
            return []
    
    def _parse_page_selection(self, selection_str: str, total_pages: int) -> List[int]:
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
    
    def _apply_image_effects(self, img: Image.Image) -> Image.Image:
        """이미지 효과 적용"""
        from PIL import ImageFilter
        
        # 언샵 마스크는 항상 적용 (PDF→이미지 변환 시 블러 보정)
        img = img.filter(ImageFilter.UnsharpMask(
            radius=1,
            percent=120,
            threshold=3
        ))
        
        # 흑백 변환
        if self.settings.get('thumbnail.grayscale', False):
            img = ImageOps.grayscale(img)
        
        # 대비 조정
        contrast = self.settings.get('thumbnail.contrast', 1.0)
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)
        
        # 선명도 조정
        sharpness = self.settings.get('thumbnail.sharpness', 1.0)
        if sharpness != 1.0:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(sharpness)
        
        # 밝기 조정
        brightness = self.settings.get('thumbnail.brightness', 1.0)
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)
        
        return img
    
    def _combine_thumbnails(self, thumbnails: List[Image.Image]) -> Image.Image:
        """여러 썸네일을 하나로 결합"""
        if not thumbnails:
            return None
        
        if len(thumbnails) == 1:
            return thumbnails[0]
        
        # 2x2 그리드로 결합 (최대 4개)
        thumbnails = thumbnails[:4]
        
        # 썸네일 크기 (설정에서 가져오기)
        thumb_size = (
            self.settings.get('thumbnail.max_width', 200),
            self.settings.get('thumbnail.max_height', 300)
        )
        
        # 결합 이미지 생성
        if len(thumbnails) == 2:
            # 가로로 배치
            combined = Image.new('RGB', (thumb_size[0] * 2, thumb_size[1]), 'white')
            combined.paste(thumbnails[0], (0, 0))
            combined.paste(thumbnails[1], (thumb_size[0], 0))
        else:
            # 2x2 그리드
            combined = Image.new('RGB', (thumb_size[0] * 2, thumb_size[1] * 2), 'white')
            positions = [(0, 0), (thumb_size[0], 0), (0, thumb_size[1]), (thumb_size[0], thumb_size[1])]
            for i, thumb in enumerate(thumbnails[:4]):
                combined.paste(thumb, positions[i])
        
        return combined
    
    def _apply_to_pdf(self, order_pdf: str, thumbnails: List[Image.Image],
                     qr_img: Optional[Image.Image], output_path: str) -> bool:
        """PDF에 이미지 적용 (기존 호환성 유지)"""
        # 새로운 메서드로 위임
        return self._apply_to_pdf_with_multiple_thumbnails(order_pdf, thumbnails, qr_img, output_path)
    
    def _apply_to_pdf_with_multiple_thumbnails(self, order_pdf: str, thumbnails: List[Image.Image],
                                              qr_img: Optional[Image.Image], output_path: str) -> bool:
        """PDF에 여러 썸네일 이미지 적용"""
        try:
            # thumbnails가 None인 경우 빈 리스트로 초기화
            if thumbnails is None:
                thumbnails = []
                
            # PDF 열기
            doc = fitz.open(order_pdf)
            
            # 썸네일 박스 설정 가져오기
            thumbnail_boxes = self.settings.get('coordinates.thumbnail_boxes', [])
            qr_boxes = self.settings.get('coordinates.qr_boxes', [])
            
            # 각 페이지 처리
            for page_num, page in enumerate(doc):
                # 백지 감지
                if self.blank_detector.is_blank_page(page):
                    self.logger.info(f"페이지 {page_num + 1}은 백지입니다. 건너뜁니다.")
                    continue
                
                # 썸네일 박스별로 처리
                for box_idx, box in enumerate(thumbnail_boxes):
                    # 썸네일 인덱스 계산
                    thumb_idx = page_num * len(thumbnail_boxes) + box_idx
                    
                    if not thumbnails or len(thumbnails) == 0:
                        # 썸네일이 없으면 건너뛰기
                        continue
                    elif len(thumbnails) == 1:
                        # 썸네일이 하나면 모든 박스에 동일한 이미지 사용
                        thumbnail = thumbnails[0]
                    elif thumb_idx < len(thumbnails):
                        # 여러 썸네일이 있으면 순서대로 사용
                        thumbnail = thumbnails[thumb_idx]
                    else:
                        # 썸네일이 부족하면 마지막 썸네일 반복
                        thumbnail = thumbnails[-1]
                    
                    self._insert_image_to_page_with_box(page, thumbnail, 'thumbnail', box)
                
                # QR 코드 삽입
                if qr_img:
                    for qr_box in qr_boxes:
                        self._insert_image_to_page_with_box(page, qr_img, 'qr', qr_box)
            
            # PDF 저장
            doc.save(output_path)
            doc.close()
            
            self.logger.info(f"PDF 저장 완료: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"PDF 적용 중 오류: {e}", exc_info=True)
            return False
    
    def _insert_image_to_page_with_box(self, page, image: Image.Image, 
                                       image_type: str, box: dict):
        """페이지에 이미지 삽입 (박스 설정 사용)"""
        try:
            if image_type == 'thumbnail':
                x = box.get('x', 0)
                y = box.get('y', 0)
                width = box.get('width', 160)
                height = box.get('height', 250)
                opacity = box.get('opacity', 1.0)
            else:  # qr
                x = box.get('x', 0)
                y = box.get('y', 0)
                size = box.get('size', 70)
                width = height = size
                opacity = 1.0
            
            # 이미지 리사이즈
            resized_img = image.copy()
            resized_img.thumbnail((width, height), Image.Resampling.LANCZOS)
            
            # 투명도 적용
            if opacity < 1.0:
                resized_img = resized_img.convert("RGBA")
                alpha = resized_img.split()[3]
                alpha = alpha.point(lambda p: p * opacity)
                resized_img.putalpha(alpha)
            
            # PIL 이미지를 바이트로 변환
            img_buffer = BytesIO()
            resized_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # PDF 페이지에 삽입
            rect = fitz.Rect(x, y, x + width, y + height)
            page.insert_image(rect, stream=img_buffer.getvalue())
            
        except Exception as e:
            self.logger.error(f"이미지 삽입 실패 ({image_type}, {box.get('name', 'unknown')}): {e}")
    
    def _insert_image_to_page(self, page, image: Image.Image, 
                             image_type: str, position: str):
        """페이지에 이미지 삽입 (레거시 메서드)"""
        try:
            # 좌표 가져오기
            if image_type == 'thumbnail':
                coords = self.settings.get(f'coordinates.thumbnail.{position}')
                if not coords:
                    return
                
                x = coords.get('x', 0)
                y = coords.get('y', 0)
                width = coords.get('width', 160)
                height = coords.get('height', 250)
                
            else:  # qr
                coords = self.settings.get(f'coordinates.qr.{position}')
                if not coords:
                    return
                
                x = coords.get('x', 0)
                y = coords.get('y', 0)
                size = coords.get('size', 70)
                width = height = size
            
            # 이미지 리사이즈
            resized_img = image.copy()
            resized_img.thumbnail((width, height), Image.Resampling.LANCZOS)
            
            # PIL 이미지를 바이트로 변환
            img_buffer = BytesIO()
            resized_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # PDF 페이지에 삽입
            rect = fitz.Rect(x, y, x + width, y + height)
            page.insert_image(rect, stream=img_buffer.getvalue())
            
        except Exception as e:
            self.logger.error(f"이미지 삽입 실패 ({image_type}, {position}): {e}")
    
    def clear_cache(self):
        """캐시 초기화"""
        self.thumbnail_cache.clear()
        self.blank_detection_cache.clear()
        self.image_handler.clear_cache()
        self.logger.debug("모든 캐시 초기화 완료")
    
    def get_cache_stats(self) -> Dict:
        """캐시 통계 반환"""
        return {
            'thumbnail_cache': len(self.thumbnail_cache),
            'blank_cache': len(self.blank_detection_cache),
            'image_cache': self.image_handler.get_cache_size(),
            'performance_stats': self.performance_monitor.get_stats()
        }