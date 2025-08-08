"""이미지 처리 및 생성 모듈"""

import io
import os
from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps, ImageFilter

from config.settings_manager import SettingsManager
from utils.logger import setup_logger

class ImageHandler:
    """이미지 생성 및 처리"""
    
    def __init__(self, settings_manager: SettingsManager):
        """
        이미지 핸들러 초기화
        
        Args:
            settings_manager: 설정 관리자
        """
        self.settings = settings_manager
        self.logger = setup_logger(self.__class__.__name__)
        
        # 캐시
        self.thumbnail_cache = {}
        self.qr_cache = {}
    
    def create_thumbnail(self, image_path: str, size: Tuple[int, int] = None) -> Optional[Image.Image]:
        """
        이미지 썸네일 생성
        
        Args:
            image_path: 원본 이미지 경로
            size: 썸네일 크기 (width, height)
            
        Returns:
            PIL Image 객체 또는 None
        """
        try:
            # 캐시 확인
            cache_key = f"{image_path}_{size}"
            if cache_key in self.thumbnail_cache:
                self.logger.debug(f"캐시에서 썸네일 반환: {cache_key}")
                return self.thumbnail_cache[cache_key]
            
            # 기본 크기
            if size is None:
                size = (
                    self.settings.get('coordinates.thumbnail.left.width', 160),
                    self.settings.get('coordinates.thumbnail.left.height', 250)
                )
            
            # 이미지 열기
            with Image.open(image_path) as img:
                # RGBA로 변환 (투명도 지원)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # 비율 유지하며 리사이즈
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # 정확한 크기로 캔버스 생성
                thumbnail = Image.new('RGBA', size, (255, 255, 255, 0))
                
                # 중앙 정렬
                x = (size[0] - img.width) // 2
                y = (size[1] - img.height) // 2
                thumbnail.paste(img, (x, y))
                
                # 캐시 저장
                if self.settings.get('performance.cache_enabled', True):
                    self.thumbnail_cache[cache_key] = thumbnail
                
                self.logger.debug(f"썸네일 생성 완료: {image_path} -> {size}")
                return thumbnail
                
        except Exception as e:
            self.logger.error(f"썸네일 생성 실패: {e}")
            return None
    
    def resize_image(self, image: Image.Image, size: Tuple[int, int], 
                    maintain_aspect: bool = True) -> Image.Image:
        """
        이미지 리사이즈
        
        Args:
            image: PIL Image 객체
            size: 목표 크기 (width, height)
            maintain_aspect: 비율 유지 여부
            
        Returns:
            리사이즈된 이미지
        """
        try:
            if maintain_aspect:
                # 비율 유지하며 리사이즈
                image.thumbnail(size, Image.Resampling.LANCZOS)
                
                # 정확한 크기로 캔버스 생성
                resized = Image.new('RGBA', size, (255, 255, 255, 0))
                
                # 중앙 정렬
                x = (size[0] - image.width) // 2
                y = (size[1] - image.height) // 2
                resized.paste(image, (x, y))
                
                return resized
            else:
                # 비율 무시하고 리사이즈
                return image.resize(size, Image.Resampling.LANCZOS)
                
        except Exception as e:
            self.logger.error(f"이미지 리사이즈 실패: {e}")
            return image
    
    def rotate_image(self, image: Image.Image, angle: float) -> Image.Image:
        """
        이미지 회전
        
        Args:
            image: PIL Image 객체
            angle: 회전 각도 (도)
            
        Returns:
            회전된 이미지
        """
        try:
            # 회전 (expand=True로 잘림 방지)
            rotated = image.rotate(angle, expand=True, fillcolor=(255, 255, 255, 0))
            return rotated
            
        except Exception as e:
            self.logger.error(f"이미지 회전 실패: {e}")
            return image
    
    def adjust_opacity(self, image: Image.Image, opacity: float) -> Image.Image:
        """
        이미지 투명도 조정
        
        Args:
            image: PIL Image 객체
            opacity: 투명도 (0.0 ~ 1.0)
            
        Returns:
            투명도가 조정된 이미지
        """
        try:
            # RGBA로 변환
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # 알파 채널 조정
            alpha = image.split()[3]
            alpha = alpha.point(lambda p: p * opacity)
            image.putalpha(alpha)
            
            return image
            
        except Exception as e:
            self.logger.error(f"투명도 조정 실패: {e}")
            return image
    
    def load_qr_image(self, image_path: str, size: int = 70) -> Optional[Image.Image]:
        """
        QR 이미지 파일 로드 및 리사이즈
        
        Args:
            image_path: QR 이미지 파일 경로
            size: QR 코드 크기 (픽셀)
            
        Returns:
            QR 이미지 또는 None
        """
        try:
            # 캐시 확인
            cache_key = f"{image_path}_{size}"
            if cache_key in self.qr_cache:
                self.logger.debug(f"캐시에서 QR 이미지 반환: {cache_key}")
                return self.qr_cache[cache_key]
            
            # 이미지 로드
            qr_image = Image.open(image_path)
            
            # RGBA로 변환
            if qr_image.mode != 'RGBA':
                qr_image = qr_image.convert('RGBA')
            
            # 크기 조정
            qr_image = qr_image.resize((size, size), Image.Resampling.LANCZOS)
            
            # 캐시 저장
            if self.settings.get('performance.cache_enabled', True):
                self.qr_cache[cache_key] = qr_image
            
            self.logger.debug(f"QR 이미지 로드 완료: {image_path} -> {size}x{size}")
            return qr_image
            
        except Exception as e:
            self.logger.error(f"QR 이미지 로드 실패: {e}")
            return None
    
    def add_border(self, image: Image.Image, border_width: int = 1, 
                  border_color: str = 'black') -> Image.Image:
        """
        이미지에 테두리 추가
        
        Args:
            image: PIL Image 객체
            border_width: 테두리 두께
            border_color: 테두리 색상
            
        Returns:
            테두리가 추가된 이미지
        """
        try:
            # 새 캔버스 생성
            width = image.width + 2 * border_width
            height = image.height + 2 * border_width
            
            bordered = Image.new('RGBA', (width, height), border_color)
            bordered.paste(image, (border_width, border_width))
            
            return bordered
            
        except Exception as e:
            self.logger.error(f"테두리 추가 실패: {e}")
            return image
    
    def composite_images(self, background: Image.Image, foreground: Image.Image,
                        position: Tuple[int, int], opacity: float = 1.0) -> Image.Image:
        """
        이미지 합성
        
        Args:
            background: 배경 이미지
            foreground: 전경 이미지
            position: 전경 이미지 위치 (x, y)
            opacity: 전경 이미지 투명도
            
        Returns:
            합성된 이미지
        """
        try:
            # 배경 복사
            result = background.copy()
            
            # 전경 투명도 조정
            if opacity < 1.0:
                foreground = self.adjust_opacity(foreground, opacity)
            
            # 합성
            if foreground.mode == 'RGBA':
                result.paste(foreground, position, foreground)
            else:
                result.paste(foreground, position)
            
            return result
            
        except Exception as e:
            self.logger.error(f"이미지 합성 실패: {e}")
            return background
    
    def save_image(self, image: Image.Image, path: str, format: str = 'PNG',
                  quality: int = 95) -> bool:
        """
        이미지 저장
        
        Args:
            image: PIL Image 객체
            path: 저장 경로
            format: 이미지 포맷
            quality: JPEG 품질 (1-100)
            
        Returns:
            성공 여부
        """
        try:
            # 디렉토리 생성
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            # 저장
            if format.upper() == 'JPEG' or format.upper() == 'JPG':
                # JPEG는 RGBA를 지원하지 않음
                if image.mode == 'RGBA':
                    # 흰색 배경 추가
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3] if len(image.split()) > 3 else None)
                    image = background
                
                image.save(path, format=format, quality=quality)
            else:
                image.save(path, format=format)
            
            self.logger.debug(f"이미지 저장 완료: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"이미지 저장 실패: {e}")
            return False
    
    def clear_cache(self):
        """캐시 초기화"""
        self.thumbnail_cache.clear()
        self.qr_cache.clear()
        self.logger.debug("이미지 캐시 초기화 완료")
    
    def get_cache_size(self) -> dict:
        """캐시 크기 반환"""
        return {
            'thumbnail_count': len(self.thumbnail_cache),
            'qr_count': len(self.qr_cache),
            'total_count': len(self.thumbnail_cache) + len(self.qr_cache)
        }
    
    # v1 통합: 이미지 효과 기능들
    def apply_image_effects(self, image: Image.Image, settings: dict = None) -> Image.Image:
        """
        이미지 효과 적용 - v1 기능 통합
        
        Args:
            image: PIL Image 객체
            settings: 효과 설정 (None이면 기본 설정 사용)
            
        Returns:
            효과가 적용된 이미지
        """
        try:
            if settings is None:
                settings = {
                    'grayscale': self.settings.get('thumbnail.grayscale', False),
                    'contrast': self.settings.get('thumbnail.contrast', 1.0),
                    'sharpness': self.settings.get('thumbnail.sharpness', 1.0),
                    'brightness': self.settings.get('thumbnail.brightness', 1.0),
                    'saturation': self.settings.get('thumbnail.saturation', 1.0)
                }
            
            result = image.copy()
            
            # 흑백 변환
            if settings.get('grayscale', False):
                result = self.convert_to_grayscale(result)
            
            # 대비 조정
            contrast = settings.get('contrast', 1.0)
            if contrast != 1.0:
                result = self.adjust_contrast(result, contrast)
            
            # 선명도 조정
            sharpness = settings.get('sharpness', 1.0)
            if sharpness != 1.0:
                result = self.adjust_sharpness(result, sharpness)
            
            # 밝기 조정
            brightness = settings.get('brightness', 1.0)
            if brightness != 1.0:
                result = self.adjust_brightness(result, brightness)
            
            # 채도 조정
            saturation = settings.get('saturation', 1.0)
            if saturation != 1.0:
                result = self.adjust_saturation(result, saturation)
            
            return result
            
        except Exception as e:
            self.logger.error(f"이미지 효과 적용 실패: {e}")
            return image
    
    def convert_to_grayscale(self, image: Image.Image, method: str = 'L') -> Image.Image:
        """
        이미지를 흑백으로 변환
        
        Args:
            image: PIL Image 객체
            method: 변환 방법 ('L', 'desaturate')
            
        Returns:
            흑백 이미지
        """
        try:
            if method == 'desaturate':
                # 채도 제거 방법
                return ImageOps.grayscale(image)
            else:
                # 루미넌스 방법 (기본)
                if image.mode == 'RGBA':
                    # 알파 채널 보존
                    rgb = image.convert('RGB')
                    gray = rgb.convert('L')
                    gray_rgba = gray.convert('RGBA')
                    gray_rgba.putalpha(image.split()[-1])  # 원본 알파 채널 복사
                    return gray_rgba
                else:
                    return image.convert('L')
                    
        except Exception as e:
            self.logger.error(f"흑백 변환 실패: {e}")
            return image
    
    def adjust_contrast(self, image: Image.Image, factor: float) -> Image.Image:
        """
        이미지 대비 조정
        
        Args:
            image: PIL Image 객체
            factor: 대비 계수 (0.0 = 회색, 1.0 = 원본, 2.0 = 2배)
            
        Returns:
            대비가 조정된 이미지
        """
        try:
            enhancer = ImageEnhance.Contrast(image)
            return enhancer.enhance(factor)
            
        except Exception as e:
            self.logger.error(f"대비 조정 실패: {e}")
            return image
    
    def adjust_sharpness(self, image: Image.Image, factor: float) -> Image.Image:
        """
        이미지 선명도 조정
        
        Args:
            image: PIL Image 객체
            factor: 선명도 계수 (0.0 = 블러, 1.0 = 원본, 2.0 = 2배)
            
        Returns:
            선명도가 조정된 이미지
        """
        try:
            enhancer = ImageEnhance.Sharpness(image)
            return enhancer.enhance(factor)
            
        except Exception as e:
            self.logger.error(f"선명도 조정 실패: {e}")
            return image
    
    def adjust_brightness(self, image: Image.Image, factor: float) -> Image.Image:
        """
        이미지 밝기 조정
        
        Args:
            image: PIL Image 객체
            factor: 밝기 계수 (0.0 = 검정, 1.0 = 원본, 2.0 = 2배)
            
        Returns:
            밝기가 조정된 이미지
        """
        try:
            enhancer = ImageEnhance.Brightness(image)
            return enhancer.enhance(factor)
            
        except Exception as e:
            self.logger.error(f"밝기 조정 실패: {e}")
            return image
    
    def adjust_saturation(self, image: Image.Image, factor: float) -> Image.Image:
        """
        이미지 채도 조정
        
        Args:
            image: PIL Image 객체
            factor: 채도 계수 (0.0 = 흑백, 1.0 = 원본, 2.0 = 2배)
            
        Returns:
            채도가 조정된 이미지
        """
        try:
            # RGBA 모드에서는 RGB로 변환 후 처리
            if image.mode == 'RGBA':
                alpha = image.split()[-1]
                rgb_image = image.convert('RGB')
                
                enhancer = ImageEnhance.Color(rgb_image)
                enhanced = enhancer.enhance(factor)
                
                # 알파 채널 복원
                enhanced = enhanced.convert('RGBA')
                enhanced.putalpha(alpha)
                return enhanced
            else:
                enhancer = ImageEnhance.Color(image)
                return enhancer.enhance(factor)
                
        except Exception as e:
            self.logger.error(f"채도 조정 실패: {e}")
            return image
    
    def apply_filter(self, image: Image.Image, filter_type: str) -> Image.Image:
        """
        이미지 필터 적용
        
        Args:
            image: PIL Image 객체
            filter_type: 필터 유형 ('blur', 'sharpen', 'emboss', 'edge_enhance')
            
        Returns:
            필터가 적용된 이미지
        """
        try:
            filters = {
                'blur': ImageFilter.BLUR,
                'sharpen': ImageFilter.SHARPEN,
                'emboss': ImageFilter.EMBOSS,
                'edge_enhance': ImageFilter.EDGE_ENHANCE,
                'edge_enhance_more': ImageFilter.EDGE_ENHANCE_MORE,
                'smooth': ImageFilter.SMOOTH,
                'smooth_more': ImageFilter.SMOOTH_MORE
            }
            
            if filter_type not in filters:
                self.logger.warning(f"알 수 없는 필터 유형: {filter_type}")
                return image
            
            return image.filter(filters[filter_type])
            
        except Exception as e:
            self.logger.error(f"필터 적용 실패: {e}")
            return image
    
    def create_thumbnail_with_effects(self, image_path: str, size: Tuple[int, int] = None,
                                    effects: dict = None) -> Optional[Image.Image]:
        """
        효과가 적용된 썸네일 생성
        
        Args:
            image_path: 원본 이미지 경로
            size: 썸네일 크기
            effects: 적용할 효과들
            
        Returns:
            효과가 적용된 썸네일
        """
        try:
            # 기본 썸네일 생성
            thumbnail = self.create_thumbnail(image_path, size)
            if thumbnail is None:
                return None
            
            # 효과 적용
            if effects:
                thumbnail = self.apply_image_effects(thumbnail, effects)
            
            return thumbnail
            
        except Exception as e:
            self.logger.error(f"효과 적용 썸네일 생성 실패: {e}")
            return None
    
    def combine_images(self, images: List[Image.Image], layout: str = 'horizontal') -> Optional[Image.Image]:
        """
        여러 이미지를 하나로 결합 - v1 기능
        
        Args:
            images: 결합할 이미지들
            layout: 레이아웃 ('horizontal', 'vertical', 'grid')
            
        Returns:
            결합된 이미지
        """
        try:
            if not images:
                return None
            
            if len(images) == 1:
                return images[0]
            
            if layout == 'horizontal':
                return self._combine_horizontal(images)
            elif layout == 'vertical':
                return self._combine_vertical(images)
            elif layout == 'grid':
                return self._combine_grid(images)
            else:
                self.logger.warning(f"알 수 없는 레이아웃: {layout}")
                return images[0]
                
        except Exception as e:
            self.logger.error(f"이미지 결합 실패: {e}")
            return None
    
    def _combine_horizontal(self, images: List[Image.Image]) -> Image.Image:
        """이미지를 가로로 결합"""
        total_width = sum(img.width for img in images)
        max_height = max(img.height for img in images)
        
        combined = Image.new('RGBA', (total_width, max_height), (255, 255, 255, 0))
        
        x_offset = 0
        for img in images:
            y_offset = (max_height - img.height) // 2  # 세로 중앙 정렬
            combined.paste(img, (x_offset, y_offset))
            x_offset += img.width
        
        return combined
    
    def _combine_vertical(self, images: List[Image.Image]) -> Image.Image:
        """이미지를 세로로 결합"""
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images)
        
        combined = Image.new('RGBA', (max_width, total_height), (255, 255, 255, 0))
        
        y_offset = 0
        for img in images:
            x_offset = (max_width - img.width) // 2  # 가로 중앙 정렬
            combined.paste(img, (x_offset, y_offset))
            y_offset += img.height
        
        return combined
    
    def _combine_grid(self, images: List[Image.Image]) -> Image.Image:
        """이미지를 격자로 결합 (2x2 기본)"""
        if len(images) == 0:
            return None
        
        # 2x2 그리드로 제한
        grid_images = images[:4]
        
        # 각 이미지 크기를 동일하게 조정
        thumb_size = (200, 280)
        resized_images = []
        
        for img in grid_images:
            resized = img.copy()
            resized.thumbnail(thumb_size, Image.Resampling.LANCZOS)
            resized_images.append(resized)
        
        # 그리드 생성
        if len(resized_images) == 1:
            return resized_images[0]
        elif len(resized_images) == 2:
            # 가로 배치
            combined = Image.new('RGB', (thumb_size[0] * 2, thumb_size[1]), 'white')
            combined.paste(resized_images[0], (0, 0))
            combined.paste(resized_images[1], (thumb_size[0], 0))
        else:
            # 2x2 그리드
            combined = Image.new('RGB', (thumb_size[0] * 2, thumb_size[1] * 2), 'white')
            positions = [(0, 0), (thumb_size[0], 0), (0, thumb_size[1]), (thumb_size[0], thumb_size[1])]
            
            for i, img in enumerate(resized_images):
                if i < 4:
                    combined.paste(img, positions[i])
        
        return combined
    
    def create_preview_image(self, image: Image.Image, effects: dict) -> Image.Image:
        """
        효과 미리보기 이미지 생성
        
        Args:
            image: 원본 이미지
            effects: 적용할 효과들
            
        Returns:
            미리보기 이미지
        """
        try:
            # 작은 크기로 미리보기 생성 (성능 향상)
            preview_size = (200, 200)
            preview = image.copy()
            preview.thumbnail(preview_size, Image.Resampling.LANCZOS)
            
            # 효과 적용
            preview = self.apply_image_effects(preview, effects)
            
            return preview
            
        except Exception as e:
            self.logger.error(f"미리보기 생성 실패: {e}")
            return image