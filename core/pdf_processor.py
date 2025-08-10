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
from utils.pdf_utils import PDFUtils

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
        self.pdf_utils = PDFUtils()
        
        # 임시 디렉토리
        self.temp_dir = None
        
        # 캐시
        self.thumbnail_cache = {}
        self.blank_detection_cache = {}
        
        # 표지 처리 플래그
        self.has_cover = False
        
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
                self.is_normalized = False  # 정규화 여부 플래그
                original_order_pdf = order_pdf  # 원본 경로 저장
                if self.settings.get('pdf_normalization.enabled', True):
                    normalized_path = self._normalize_pdf(order_pdf)
                    if normalized_path != order_pdf:
                        self.logger.info(f"정규화된 PDF 사용: {normalized_path}")
                        order_pdf = normalized_path  # 정규화된 PDF로 교체
                        self.is_normalized = True  # 정규화됨 표시
                
                # 출력 파일명 생성 (원본 경로 기준)
                output_path = self._generate_output_path(original_order_pdf)
                
                # 처리 규칙 적용 (모든 PDF 파일 검사)
                if print_pdfs:
                    for pdf_path in print_pdfs:
                        self._apply_processing_rules(pdf_path)
                
                # 처리 모드 확인 (단순화: raster만 사용)
                processing_mode = self.settings.get('processing.mode', 'raster')
                
                # 래스터 방식만 사용 (안정적이고 예측 가능)
                self.logger.info("래스터 처리 모드 사용")
                
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
        return self.pdf_utils.generate_output_path(order_pdf, suffix="_완료")
    
    def _apply_processing_rules(self, file_path: str):
        """처리 규칙 적용"""
        # 기본적으로 항상 규칙 검사 (enabled 무시)
        filename = os.path.basename(file_path)
        
        # 표지 규칙 확인
        import re
        if re.search(r'표지|cover', filename, re.IGNORECASE):
            self.logger.info(f"표지 파일 감지: {filename}")
            # 표지 처리 플래그 설정 (인스턴스 변수로만 관리)
            self.has_cover = True
            self.cover_file_path = file_path  # 표지 파일 경로 저장
        else:
            # 표지가 아닌 파일은 플래그 설정하지 않음
            pass
        
        # 추가 규칙 처리 (설정에 있는 경우)
        if self.settings.get('processing_rules.enabled', False):
            rules = self.settings.get('processing_rules.rules', [])
            for rule in rules:
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
            
            # 썸네일 리스트 정리 및 표지 우선 배치
            cover_thumbnail = None
            content_thumbnails = []
            
            for idx in range(len(print_pdfs)):
                thumb_result = results.get(f'thumbnails_{idx}', [])
                if thumb_result:
                    # 표지인지 확인
                    import re
                    filename = os.path.basename(print_pdfs[idx])
                    if re.search(r'표지|cover', filename, re.IGNORECASE):
                        cover_thumbnail = thumb_result[0] if thumb_result else None
                    else:
                        content_thumbnails.extend(thumb_result)
            
            # 썸네일 리스트 재정렬: 표지가 있으면 첫 번째로
            if cover_thumbnail:
                all_thumbnails = [cover_thumbnail] + content_thumbnails
            else:
                all_thumbnails = content_thumbnails
            
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
            cover_thumbnail = None
            content_thumbnails = []
            
            if print_pdfs:
                for pdf_path in print_pdfs:
                    thumbnails = self._create_enhanced_thumbnails(pdf_path)
                    if thumbnails:
                        # 표지인지 확인
                        import re
                        filename = os.path.basename(pdf_path)
                        if re.search(r'표지|cover', filename, re.IGNORECASE):
                            cover_thumbnail = thumbnails[0] if thumbnails else None
                        else:
                            content_thumbnails.extend(thumbnails)
                
                # 썸네일 리스트 재정렬: 표지가 있으면 첫 번째로
                if cover_thumbnail:
                    all_thumbnails = [cover_thumbnail] + content_thumbnails
                else:
                    all_thumbnails = content_thumbnails
            
            # QR 이미지 로드
            qr_img = None
            if qr_image:
                qr_img = Image.open(qr_image)
            
            # PDF에 적용
            return self._apply_to_pdf_with_multiple_thumbnails(order_pdf, all_thumbnails, qr_img, output_path)
            
        except Exception as e:
            self.logger.error(f"단일 스레드 처리 중 오류: {e}")
            return False
    
    def _create_enhanced_thumbnails(self, pdf_path: str) -> List[dict]:
        """향상된 썸네일 생성 - PDF 페이지 직접 반환"""
        thumbnails = []
        
        try:
            # 썸네일 PDF는 회전 감지하지 않음 (리소스 절약)
            # 의뢰서만 회전 감지가 필요함
            
            doc = fitz.open(pdf_path)
            
            # 백지 감지 설정 확인
            blank_detection_enabled = self.settings.get('blank_detection.enabled', False)
            
            # 썸네일용 페이지 처리 (최대 2페이지만 확인)
            max_pages_to_check = 2 if blank_detection_enabled else 1
            pages_checked = 0
            page_num = 0
            
            while pages_checked < max_pages_to_check and page_num < len(doc):
                page = doc[page_num]
                
                # 백지 감지
                if blank_detection_enabled and self.blank_detector.is_blank_page(page):
                    self.logger.info(f"페이지 {page_num + 1}은 백지입니다. 다음 페이지 확인")
                    page_num += 1
                    pages_checked += 1
                    continue
                
                # PDF 페이지 정보를 직접 반환 (이미지 변환 없이)
                thumbnail_info = {
                    'pdf_path': pdf_path,
                    'page_num': page_num,
                    'doc': doc,  # 문서 객체 참조
                    'keep_doc_open': True  # 문서를 열어둔 상태로 유지
                }
                
                thumbnails.append(thumbnail_info)
                
                # 썸네일 하나만 필요하므로 처리 후 종료
                break
            
            # 문서는 나중에 닫음 (참조 유지)
            # doc.close()  # 나중에 닫음
            
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
        
        # 1. 엣지 강화로 텍스트 선명도 향상
        img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
        
        # 2. 강력한 언샵 마스크 적용 (고해상도 이미지에 최적화)
        img = img.filter(ImageFilter.UnsharpMask(
            radius=1.5,      # 더 큰 반경으로 효과 증대
            percent=200,     # 매우 강한 샤프닝
            threshold=1      # 낮은 임계값으로 모든 디테일 강화
        ))
        
        # 흑백 변환
        if self.settings.get('thumbnail.grayscale', False):
            img = ImageOps.grayscale(img)
        
        # 대비 자동 증가 (썸네일은 항상 대비 향상 필요)
        contrast = self.settings.get('thumbnail.contrast', 1.2)  # 기본값 1.2로 증가
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
    
    def _apply_to_pdf_with_multiple_thumbnails(self, order_pdf: str, thumbnails: List[dict],
                                              qr_img: Optional[Image.Image], output_path: str) -> bool:
        """PDF에 여러 썸네일 PDF 페이지 직접 적용"""
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
                    
                    # 썸네일 선택 로직 (표지는 이미 첫 번째로 정렬됨)
                    if len(thumbnails) == 1:
                        # 썸네일이 하나면 모든 박스에 동일한 PDF 사용
                        # (표지만 있는 경우 모든 박스에 표지가 들어감)
                        thumbnail = thumbnails[0]
                    elif thumb_idx < len(thumbnails):
                        # 여러 썸네일이 있으면 순서대로 사용
                        # (표지가 첫 번째, 내지들이 그 다음 순서로)
                        thumbnail = thumbnails[thumb_idx]
                    else:
                        # 썸네일이 부족하면 마지막 썸네일 반복
                        thumbnail = thumbnails[-1]
                    
                    # PDF 페이지 직접 삽입 (벡터 방식)
                    self._insert_pdf_page_to_page(page, thumbnail, box)
                
                # QR 코드 삽입
                if qr_img:
                    for qr_box in qr_boxes:
                        self._insert_image_to_page_with_box(page, qr_img, 'qr', qr_box)
            
            # PDF 저장 옵션: 최종 래스터화 여부
            if self.settings.get('processing.final_rasterize', False):
                # 최종 PDF를 고해상도로 래스터화
                self._save_as_rasterized(doc, output_path)
            else:
                # 벡터 그대로 저장 (압축 옵션 적용)
                doc.save(output_path, garbage=4, deflate=True, clean=True)
            
            doc.close()
            
            # 썸네일 문서들 닫기
            for thumb_info in thumbnails:
                if isinstance(thumb_info, dict) and 'doc' in thumb_info:
                    try:
                        thumb_info['doc'].close()
                    except:
                        pass
            
            self.logger.info(f"PDF 저장 완료: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"PDF 적용 중 오류: {e}", exc_info=True)
            return False
    
    def _insert_pdf_page_to_page(self, page, thumbnail_info: dict, box: dict):
        """페이지에 PDF 페이지 직접 삽입 (벡터 방식)"""
        try:
            x = box.get('x', 0)
            y = box.get('y', 0)
            width = box.get('width', 160)
            height = box.get('height', 250)
            original_width = width  # 원본 크기 저장
            original_height = height
            
            # 페이지 회전 확인 및 좌표 변환 (정규화된 PDF는 건너뛰)
            rotation = page.rotation
            if rotation != 0 and not getattr(self, 'is_normalized', False):
                self.logger.info(f"썸네일 삽입 페이지 회전 감지: {rotation}도")
                # 회전에 따른 좌표 변환
                x, y = self._transform_coordinates(x, y, width, height, rotation, page)
                # 90도 또는 270도 회전인 경우 크기도 바꿈
                if rotation in [90, 270]:
                    width, height = height, width
            elif rotation != 0 and getattr(self, 'is_normalized', False):
                self.logger.debug(f"정규화된 PDF - 회전 변환 건너뛰 (rotation: {rotation})")
            
            # 썸네일 원본 페이지 가져오기
            thumb_page = thumbnail_info['doc'][thumbnail_info['page_num']]
            
            # 썸네일 페이지 회전 감지
            thumb_rotation = thumb_page.rotation
            
            # 표지 처리: 오른쪽 50% 자르기 (현재 썸네일이 표지인 경우만)
            # has_cover 플래그와 무관하게 파일명 직접 체크
            thumb_filename = os.path.basename(thumbnail_info.get('pdf_path', ''))
            import re
            is_cover_thumbnail = bool(re.search(r'표지|cover', thumb_filename, re.IGNORECASE))
            
            if is_cover_thumbnail:
                self.logger.info(f"표지 처리: 오른쪽 50% 자르기 적용 - {thumb_filename} (회전: {thumb_rotation}도)")
                # 원본 페이지의 오른쪽 절반만 사용
                original_rect = thumb_page.rect
                
                # 회전된 페이지의 경우 크롭 영역 조정
                if thumb_rotation in [90, 270]:
                    # 90도/270도 회전된 경우
                    # 실제로는 세로로 보이지만, 내부적으로는 가로
                    # 따라서 하단 50%를 자르면 실제로 오른쪽 50%가 됨
                    crop_rect = fitz.Rect(
                        original_rect.x0,
                        original_rect.y0 + original_rect.height / 2,  # 하단 절반
                        original_rect.x1,
                        original_rect.y1
                    )
                    temp_width = original_rect.width
                    temp_height = original_rect.height / 2
                else:
                    # 정상 방향 (0도 또는 180도)
                    crop_rect = fitz.Rect(
                        original_rect.x0 + original_rect.width / 2,  # 중간부터
                        original_rect.y0,  # 위쪽 시작
                        original_rect.x1,  # 오른쪽 끝까지
                        original_rect.y1   # 아래쪽 끝
                    )
                    temp_width = original_rect.width / 2
                    temp_height = original_rect.height
                
                # 임시 PDF 생성하여 잘린 부분만 사용
                temp_doc = fitz.open()
                temp_page = temp_doc.new_page(
                    width=temp_width,
                    height=temp_height
                )
                
                # 항상 회전 보정과 함께 잘린 부분 삽입
                temp_page.show_pdf_page(
                    temp_page.rect,
                    thumbnail_info['doc'],
                    thumbnail_info['page_num'],
                    clip=crop_rect,
                    rotate=-thumb_rotation if thumb_rotation != 0 else 0  # 회전 보정
                )
                
                # 잘린 페이지 사용
                thumb_page = temp_page
                thumb_rect = temp_page.rect
            else:
                thumb_rect = thumb_page.rect
            thumb_ratio = thumb_rect.width / thumb_rect.height
            # 비율 계산 시 원본 크기 사용 (회전 영향 배제)
            if getattr(self, 'is_normalized', False) and page.rotation != 0:
                # 정규화된 PDF에서 회전 정보가 남아있는 경우
                # 원본 크기로 비율 계산
                box_ratio = original_width / original_height
            else:
                box_ratio = width / height
            
            # 실제 썸네일이 들어갈 크기 계산 (비율 유지)
            if thumb_ratio > box_ratio:
                # 썸네일이 더 넓은 경우 - 가로 맞춤
                actual_width = width
                actual_height = width / thumb_ratio
                actual_x = x
                actual_y = y + (height - actual_height) / 2  # 세로 중앙 정렬
            else:
                # 썸네일이 더 좁은 경우 - 세로 맞춤
                actual_height = height
                actual_width = height * thumb_ratio
                actual_x = x + (width - actual_width) / 2  # 가로 중앙 정렬
                actual_y = y
            
            # 실제 삽입 영역
            actual_rect = fitz.Rect(actual_x, actual_y, actual_x + actual_width, actual_y + actual_height)
            
            # 1. 실제 썸네일 크기만큼 흰색 배경 그리기
            shape = page.new_shape()
            shape.draw_rect(actual_rect)
            shape.finish(
                fill=(1, 1, 1),  # 흰색 배경
                color=(1, 1, 1),  # 흰색 테두리
                width=0  # 테두리 없음
            )
            shape.commit()
            
            # 2. PDF 페이지를 벡터로 직접 삽입 (품질 손실 없음)
            if is_cover_thumbnail:
                # 표지 처리: 이미 잘린 temp_page 사용
                page.show_pdf_page(
                    actual_rect,                        # 실제 삽입 영역
                    temp_doc,                           # 임시 문서
                    0,                                  # 첫 번째 페이지
                    keep_proportion=True,               # 비율 유지
                    overlay=True                        # 오버레이로 삽입
                )
                # 임시 문서 정리
                temp_doc.close()
            else:
                # 일반 처리: 항상 회전 값 체크하여 보정
                if thumb_rotation != 0:
                    self.logger.info(f"썸네일 회전 보정: {thumb_rotation}도")
                
                # 회전 값에 관계없이 동일한 방식으로 삽입 (회전 보정 포함)
                page.show_pdf_page(
                    actual_rect,                        # 실제 삽입 영역
                    thumbnail_info['doc'],              # 소스 PDF 문서
                    thumbnail_info['page_num'],         # 페이지 번호
                    keep_proportion=True,               # 비율 유지
                    overlay=True,                       # 오버레이로 삽입
                    rotate=-thumb_rotation if thumb_rotation != 0 else 0  # 회전 보정
                )
            
            self.logger.debug(f"PDF 페이지 삽입 성공 (실제 크기 흰 배경): {box.get('name', 'unknown')}")
            
        except Exception as e:
            self.logger.error(f"PDF 페이지 삽입 실패 ({box.get('name', 'unknown')}): {e}")
    
    def _save_as_rasterized(self, doc, output_path: str):
        """최종 PDF를 고해상도로 래스터화하여 저장"""
        try:
            # 새 문서 생성
            new_doc = fitz.open()
            
            # 각 페이지를 고해상도 이미지로 변환
            for page_num, page in enumerate(doc):
                # 고해상도 래스터화 (300 DPI)
                mat = fitz.Matrix(300/72, 300/72)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # 새 페이지 생성 (원본 크기)
                new_page = new_doc.new_page(
                    width=page.rect.width,
                    height=page.rect.height
                )
                
                # 이미지 삽입
                new_page.insert_image(
                    new_page.rect,
                    pixmap=pix
                )
            
            # 저장
            new_doc.save(output_path, garbage=4, deflate=True)
            new_doc.close()
            
            self.logger.info(f"PDF 래스터화 저장 완료: {output_path}")
            
        except Exception as e:
            self.logger.error(f"PDF 래스터화 실패: {e}")
            # 실패 시 원본 그대로 저장
            doc.save(output_path)
    
    def _insert_image_to_page_with_box(self, page, image: Image.Image, 
                                       image_type: str, box: dict):
        """페이지에 이미지 삽입 (박스 설정 사용) - QR코드용"""
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
            
            # 페이지 회전 확인 및 좌표 변환
            rotation = page.rotation
            if rotation != 0:
                self.logger.debug(f"페이지 회전 감지: {rotation}도, 좌표 변환 적용")
                x, y = self._transform_coordinates(x, y, width, height, rotation, page)
                
                # 90도 또는 270도 회전인 경우 이미지 크기도 바꿈
                if rotation in [90, 270]:
                    width, height = height, width
            
            # 고품질 이미지 리사이즈 (resize 메서드 사용)
            resized_img = image.copy()
            
            # 비율 유지하며 정확한 크기 계산
            img_ratio = resized_img.width / resized_img.height
            target_ratio = width / height
            
            if img_ratio > target_ratio:
                new_width = width
                new_height = int(width / img_ratio)
            else:
                new_height = height
                new_width = int(height * img_ratio)
            
            # resize로 고품질 리사이즈
            resized_img = resized_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 투명도 적용
            if opacity < 1.0:
                resized_img = resized_img.convert("RGBA")
                alpha = resized_img.split()[3]
                alpha = alpha.point(lambda p: p * opacity)
                resized_img.putalpha(alpha)
            
            # PIL 이미지를 바이트로 변환 (품질 최대화)
            img_buffer = BytesIO()
            # PNG 저장 시 압축 최소화로 품질 보존
            resized_img.save(img_buffer, format='PNG', compress_level=1, optimize=False)
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
            
            # 페이지 회전 확인 및 좌표 변환
            rotation = page.rotation
            if rotation != 0:
                self.logger.debug(f"레거시 메서드 - 페이지 회전 감지: {rotation}도")
                x, y = self._transform_coordinates(x, y, width, height, rotation, page)
                
                # 90도 또는 270도 회전인 경우 이미지 크기도 바꿈
                if rotation in [90, 270]:
                    width, height = height, width
            
            # 고품질 이미지 리사이즈 (resize 메서드 사용)
            resized_img = image.copy()
            
            # 비율 유지하며 정확한 크기 계산
            img_ratio = resized_img.width / resized_img.height
            target_ratio = width / height
            
            if img_ratio > target_ratio:
                new_width = width
                new_height = int(width / img_ratio)
            else:
                new_height = height
                new_width = int(height * img_ratio)
            
            # resize로 고품질 리사이즈
            resized_img = resized_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # PIL 이미지를 바이트로 변환 (품질 최대화)
            img_buffer = BytesIO()
            # PNG 저장 시 압축 최소화로 품질 보존
            resized_img.save(img_buffer, format='PNG', compress_level=1, optimize=False)
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
    
    def _transform_coordinates(self, x: float, y: float, width: float, height: float, 
                               rotation: int, page) -> Tuple[float, float]:
        """
        페이지 회전에 따른 좌표 변환
        
        Args:
            x, y: 원본 좌표
            width, height: 이미지 크기
            rotation: 페이지 회전 각도
            page: PyMuPDF 페이지 객체
            
        Returns:
            변환된 (x, y) 좌표
        """
        # 회전이 없으면 좌표 변환 불필요
        if rotation == 0:
            self.logger.debug(f"회전 없음 - 좌표 변환 건너뜀")
            return x, y
        
        # 회전이 있는 경우 좌표 변환 적용
        self.logger.info(f"페이지 회전 {rotation}도 감지 - 좌표 변환 적용")
        
        if rotation == 90:
            # 90도 시계방향 회전
            new_x = y
            new_y = page.rect.width - x - width
            self.logger.debug(f"90도 회전: ({x}, {y}) -> ({new_x}, {new_y})")
            return new_x, new_y
        elif rotation == 180:
            # 180도 회전
            new_x = page.rect.width - x - width
            new_y = page.rect.height - y - height
            self.logger.debug(f"180도 회전: ({x}, {y}) -> ({new_x}, {new_y})")
            return new_x, new_y
        elif rotation == 270:
            # 270도 시계방향 회전
            new_x = page.rect.height - y - height
            new_y = x
            self.logger.debug(f"270도 회전: ({x}, {y}) -> ({new_x}, {new_y})")
            return new_x, new_y
        else:
            # 알 수 없는 회전 각도
            self.logger.warning(f"알 수 없는 회전 각도: {rotation}도")
            return x, y