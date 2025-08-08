"""백지 감지 알고리즘 모듈"""

import hashlib
from io import BytesIO
from typing import Optional, Dict, Any

import fitz  # PyMuPDF
from PIL import Image
import numpy as np

from config.settings_manager import SettingsManager
from utils.logger import setup_logger

class BlankDetector:
    """백지 감지 알고리즘 구현 - v1 기능 통합"""
    
    ALGORITHMS = {
        'simple': '_detect_simple',      # 흰색 픽셀 비율
        'entropy': '_detect_entropy',    # 정보 엔트로피
        'histogram': '_detect_histogram' # 히스토그램 분석
    }
    
    def __init__(self, settings_manager: SettingsManager):
        """
        백지 감지기 초기화
        
        Args:
            settings_manager: 설정 관리자
        """
        self.settings = settings_manager
        self.logger = setup_logger(self.__class__.__name__)
        self.cache = {}  # 페이지 해시별 캐시
    
    def is_blank_page(self, page: fitz.Page) -> bool:
        """
        페이지가 백지인지 판단 (PyMuPDF 페이지 객체 사용)
        
        Args:
            page: PyMuPDF 페이지 객체
            
        Returns:
            백지 여부
        """
        # 백지 감지 비활성화 시
        if not self.settings.get('blank_detection.enabled', False):
            return False
        
        # 캐시 확인
        page_hash = self._get_page_hash(page)
        if self.settings.get('blank_detection.cache_enabled', True):
            if page_hash in self.cache:
                self.logger.debug(f"캐시에서 백지 감지 결과 반환: {page_hash[:8]}")
                return self.cache[page_hash]
        
        # 알고리즘 선택
        algorithm = self.settings.get('blank_detection.algorithm', 'simple')
        threshold = self.settings.get('blank_detection.threshold', 95)
        
        # 백지 감지 실행
        is_blank = self._detect_blank(page, algorithm, threshold)
        
        # 캐시 저장
        if self.settings.get('blank_detection.cache_enabled', True):
            self.cache[page_hash] = is_blank
        
        return is_blank
    
    def _get_page_hash(self, page: fitz.Page) -> str:
        """
        페이지 해시 생성 (캐싱용)
        
        Args:
            page: PyMuPDF 페이지 객체
            
        Returns:
            페이지 해시값
        """
        try:
            # 페이지 텍스트 기반 해시
            page_content = page.get_text().encode('utf-8')
            
            # 텍스트가 없으면 이미지 기반 해시
            if not page_content:
                pix = page.get_pixmap(dpi=72)  # 저해상도로 빠른 해시 생성
                page_content = pix.tobytes()
            
            return hashlib.md5(page_content).hexdigest()
        except Exception as e:
            self.logger.warning(f"페이지 해시 생성 실패: {e}")
            return str(id(page))  # 폴백: 객체 ID 사용
    
    def _detect_blank(self, page: fitz.Page, algorithm: str, threshold: float) -> bool:
        """
        백지 감지 실행
        
        Args:
            page: PyMuPDF 페이지 객체
            algorithm: 사용할 알고리즘
            threshold: 임계값
            
        Returns:
            백지 여부
        """
        try:
            # 페이지를 이미지로 변환
            pix = page.get_pixmap(dpi=150)
            img_data = pix.pil_tobytes(format="PNG")
            img = Image.open(BytesIO(img_data))
            
            # 제외 영역 적용
            img = self._apply_exclusion_areas(img)
            
            # 알고리즘 실행
            method_name = self.ALGORITHMS.get(algorithm, '_detect_simple')
            method = getattr(self, method_name)
            
            is_blank = method(img, threshold)
            
            if is_blank:
                self.logger.debug(f"백지 감지됨 (알고리즘: {algorithm}, 임계값: {threshold})")
            
            return is_blank
            
        except Exception as e:
            self.logger.error(f"백지 감지 중 오류: {e}")
            return False  # 오류 시 백지가 아닌 것으로 처리
    
    def _apply_exclusion_areas(self, img: Image.Image) -> Image.Image:
        """
        제외 영역 적용 (헤더, 푸터, 여백 제거)
        
        Args:
            img: PIL 이미지
            
        Returns:
            크롭된 이미지
        """
        try:
            exclude = self.settings.get('blank_detection.exclude_areas', {})
            
            header = exclude.get('header', 50)
            footer = exclude.get('footer', 50)
            left_margin = exclude.get('left_margin', 20)
            right_margin = exclude.get('right_margin', 20)
            
            width, height = img.size
            
            # 크롭 영역 계산
            crop_box = (
                left_margin,
                header,
                width - right_margin,
                height - footer
            )
            
            # 유효한 크롭 영역인지 확인
            if crop_box[2] > crop_box[0] and crop_box[3] > crop_box[1]:
                return img.crop(crop_box)
            else:
                return img
                
        except Exception as e:
            self.logger.warning(f"제외 영역 적용 실패: {e}")
            return img
    
    def _detect_simple(self, img: Image.Image, threshold: float) -> bool:
        """
        단순 백지 감지 - 흰색 픽셀 비율
        
        Args:
            img: PIL 이미지
            threshold: 백지 판정 임계값 (%)
            
        Returns:
            백지 여부
        """
        try:
            # threshold를 float으로 확실하게 변환
            threshold = float(threshold) if isinstance(threshold, (str, int)) else threshold
            
            # 그레이스케일 변환
            gray = img.convert('L')
            
            # NumPy 배열로 변환
            pixels = np.array(gray)
            
            # 흰색 픽셀 비율 계산 (250 이상을 흰색으로 간주)
            white_pixels = np.sum(pixels > 250)
            total_pixels = pixels.size
            
            if total_pixels == 0:
                return True
            
            white_ratio = (white_pixels / total_pixels) * 100
            
            self.logger.debug(f"흰색 픽셀 비율: {white_ratio:.2f}%")
            
            return white_ratio > threshold
            
        except Exception as e:
            self.logger.error(f"단순 백지 감지 실패: {e}")
            return False
    
    def _detect_entropy(self, img: Image.Image, threshold: float) -> bool:
        """
        엔트로피 기반 백지 감지 - 정보 엔트로피 계산
        
        Args:
            img: PIL 이미지
            threshold: 백지 판정 임계값 (%)
            
        Returns:
            백지 여부
        """
        try:
            # 그레이스케일 변환
            gray = img.convert('L')
            
            # 히스토그램 계산
            histogram = gray.histogram()
            
            # 0이 아닌 값만 필터링
            histogram = [h for h in histogram if h > 0]
            
            if not histogram:
                return True  # 모든 픽셀이 같은 값 = 백지
            
            # 확률 분포 계산
            total = sum(histogram)
            probabilities = [h / total for h in histogram]
            
            # 엔트로피 계산
            entropy = -sum(p * np.log2(p) for p in probabilities if p > 0)
            
            # 낮은 엔트로피는 백지를 의미
            # 임계값을 엔트로피 값으로 변환 (0-8 범위)
            entropy_threshold = (100 - threshold) / 10
            
            self.logger.debug(f"엔트로피: {entropy:.2f}, 임계값: {entropy_threshold:.2f}")
            
            return entropy < entropy_threshold
            
        except Exception as e:
            self.logger.error(f"엔트로피 백지 감지 실패: {e}")
            return False
    
    def _detect_histogram(self, img: Image.Image, threshold: float) -> bool:
        """
        히스토그램 기반 백지 감지 - 색상 분포 분석
        
        Args:
            img: PIL 이미지
            threshold: 백지 판정 임계값 (%)
            
        Returns:
            백지 여부
        """
        try:
            # 그레이스케일 변환
            gray = img.convert('L')
            
            # 히스토그램 계산
            histogram = gray.histogram()
            
            # 백색 영역 (250-255)의 픽셀 수
            white_pixels = sum(histogram[250:])
            
            # 거의 백색 영역 (240-255)의 픽셀 수
            near_white_pixels = sum(histogram[240:])
            
            # 전체 픽셀 수
            total_pixels = sum(histogram)
            
            if total_pixels == 0:
                return True
            
            # 백색 비율 계산
            white_ratio = (white_pixels / total_pixels) * 100
            near_white_ratio = (near_white_pixels / total_pixels) * 100
            
            self.logger.debug(f"백색 비율: {white_ratio:.2f}%, "
                            f"준백색 비율: {near_white_ratio:.2f}%")
            
            # 더 정교한 판단: 완전 백색과 거의 백색을 구분
            if white_ratio > threshold:
                return True
            elif near_white_ratio > (threshold + 5):  # 약간 더 관대한 기준
                return True
            
            # 색상 분포의 표준편차 계산
            pixels = np.array(gray)
            std_dev = np.std(pixels)
            
            # 표준편차가 매우 낮으면 백지
            if std_dev < 5:
                self.logger.debug(f"낮은 표준편차: {std_dev:.2f}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"히스토그램 백지 감지 실패: {e}")
            return False
    
    def clear_cache(self):
        """캐시 초기화"""
        self.cache.clear()
        self.logger.debug("백지 감지 캐시 초기화 완료")
    
    def get_cache_size(self) -> int:
        """캐시 크기 반환"""
        return len(self.cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        return {
            'cache_size': len(self.cache),
            'algorithm': self.settings.get('blank_detection.algorithm', 'simple'),
            'threshold': self.settings.get('blank_detection.threshold', 95),
            'enabled': self.settings.get('blank_detection.enabled', False)
        }