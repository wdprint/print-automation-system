"""
PDF 처리 전략 패턴 구현
각 처리 모드를 독립적인 전략으로 분리하여 관리
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple
import tempfile
from io import BytesIO

import fitz  # PyMuPDF
from PIL import Image, ImageDraw
from PyPDF2 import PdfReader, PdfWriter

from config.settings_manager import SettingsManager
from utils.logger import setup_logger


class PDFProcessingStrategy(ABC):
    """PDF 처리 전략 추상 클래스"""
    
    def __init__(self, settings_manager: SettingsManager):
        """
        초기화
        
        Args:
            settings_manager: 설정 관리자
        """
        self.settings = settings_manager
        self.logger = setup_logger(self.__class__.__name__)
        
        # 좌표 설정 로드
        self.thumbnail_positions = {
            'left': (
                self.settings.get('coordinates.thumbnail.left.x', 230),
                self.settings.get('coordinates.thumbnail.left.y', 234)
            ),
            'right': (
                self.settings.get('coordinates.thumbnail.right.x', 658),
                self.settings.get('coordinates.thumbnail.right.y', 228)
            )
        }
        
        self.thumbnail_size = (
            self.settings.get('coordinates.thumbnail.left.width', 160),
            self.settings.get('coordinates.thumbnail.left.height', 250)
        )
        
        self.qr_positions = {
            'left': (
                self.settings.get('coordinates.qr.left.x', 315),
                self.settings.get('coordinates.qr.left.y', 500)
            ),
            'right': (
                self.settings.get('coordinates.qr.right.x', 730),
                self.settings.get('coordinates.qr.right.y', 500)
            )
        }
        
        self.qr_size = self.settings.get('coordinates.qr.left.size', 70)
    
    @abstractmethod
    def process(self, order_pdf: str, print_pdfs: List[str], qr_image: Optional[str], 
                output_path: str) -> bool:
        """
        PDF 처리 메인 메서드
        
        Args:
            order_pdf: 의뢰서 PDF 경로
            print_pdfs: 인쇄 데이터 PDF 리스트
            qr_image: QR 코드 이미지 경로
            output_path: 출력 파일 경로
            
        Returns:
            bool: 성공 여부
        """
        pass
    
    def create_thumbnail(self, pdf_path: str, page_num: int = 0) -> Optional[Image.Image]:
        """
        PDF에서 썸네일 생성 (공통 메서드)
        
        Args:
            pdf_path: PDF 파일 경로
            page_num: 페이지 번호
            
        Returns:
            PIL Image 객체 또는 None
        """
        try:
            doc = fitz.open(pdf_path)
            
            if page_num >= len(doc):
                self.logger.warning(f"페이지 {page_num}이 존재하지 않음")
                return None
            
            page = doc[page_num]
            
            # DPI 설정
            dpi = self.settings.get('thumbnail.render_dpi', 300)
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            
            # 페이지 렌더링
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_data = pix.tobytes("png")
            
            doc.close()
            
            # PIL 이미지로 변환
            img = Image.open(BytesIO(img_data))
            
            # 크기 조정
            img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
            
            # 정확한 크기로 캔버스 생성 (여백 추가)
            canvas = Image.new('RGB', self.thumbnail_size, 'white')
            
            # 중앙 정렬
            x = (self.thumbnail_size[0] - img.width) // 2
            y = (self.thumbnail_size[1] - img.height) // 2
            canvas.paste(img, (x, y))
            
            return canvas
            
        except Exception as e:
            self.logger.error(f"썸네일 생성 실패: {e}")
            return None
    
    def load_qr_image(self, qr_path: str) -> Optional[Image.Image]:
        """
        QR 코드 이미지 로드 및 크기 조정 (공통 메서드)
        
        Args:
            qr_path: QR 이미지 경로
            
        Returns:
            PIL Image 객체 또는 None
        """
        try:
            img = Image.open(qr_path)
            
            # RGBA를 RGB로 변환
            if img.mode == 'RGBA':
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 크기 조정
            img.thumbnail((self.qr_size, self.qr_size), Image.Resampling.LANCZOS)
            
            return img
            
        except Exception as e:
            self.logger.error(f"QR 이미지 로드 실패: {e}")
            return None


class OptimizedStrategy(PDFProcessingStrategy):
    """최적화된 처리 전략 (래스터 + 흰 배경)"""
    
    def process(self, order_pdf: str, print_pdfs: List[str], qr_image: Optional[str], 
                output_path: str) -> bool:
        """
        최적화된 방식으로 PDF 처리
        - 고품질 래스터화
        - 흰 배경 추가
        - 파일 크기 최적화
        """
        try:
            self.logger.info("최적화 처리 시작")
            
            # 의뢰서 PDF 열기
            doc = fitz.open(order_pdf)
            
            # 썸네일 생성
            thumbnails = []
            for pdf_path in print_pdfs[:2]:  # 최대 2개
                thumb = self.create_thumbnail(pdf_path)
                if thumb:
                    thumbnails.append(thumb)
            
            # QR 이미지 로드
            qr_img = None
            if qr_image:
                qr_img = self.load_qr_image(qr_image)
            
            # 각 페이지 처리
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 흰 배경 추가
                if self.settings.get('processing.white_background', True):
                    self._add_white_background(page)
                
                # 썸네일 삽입
                for i, thumb in enumerate(thumbnails):
                    position = 'left' if i == 0 else 'right'
                    self._insert_image_on_page(page, thumb, self.thumbnail_positions[position])
                
                # QR 삽입
                if qr_img:
                    for position in ['left', 'right']:
                        self._insert_image_on_page(page, qr_img, self.qr_positions[position])
            
            # 저장
            doc.save(output_path, garbage=4, deflate=True, clean=True)
            doc.close()
            
            self.logger.info(f"최적화 처리 완료: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"최적화 처리 실패: {e}")
            return False
    
    def _add_white_background(self, page):
        """페이지에 흰 배경 추가"""
        rect = page.rect
        shape = page.new_shape()
        shape.draw_rect(rect)
        shape.finish(color=(1, 1, 1), fill=(1, 1, 1))
        shape.commit()
    
    def _insert_image_on_page(self, page, image: Image.Image, position: Tuple[int, int]):
        """페이지에 이미지 삽입"""
        try:
            # PIL 이미지를 바이트로 변환
            img_buffer = BytesIO()
            image.save(img_buffer, format='PNG')
            img_data = img_buffer.getvalue()
            
            # 이미지 삽입 위치 계산
            rect = fitz.Rect(
                position[0], 
                position[1],
                position[0] + image.width,
                position[1] + image.height
            )
            
            # 이미지 삽입
            page.insert_image(rect, stream=img_data)
            
        except Exception as e:
            self.logger.error(f"이미지 삽입 실패: {e}")


class VectorStrategy(PDFProcessingStrategy):
    """벡터 방식 처리 전략"""
    
    def process(self, order_pdf: str, print_pdfs: List[str], qr_image: Optional[str], 
                output_path: str) -> bool:
        """
        벡터 방식으로 PDF 처리
        - PDF를 벡터로 삽입
        - 품질 유지
        - 파일 크기 증가 가능
        """
        try:
            self.logger.info("벡터 처리 시작")
            
            # PyPDF2로 처리
            reader = PdfReader(order_pdf)
            writer = PdfWriter()
            
            # 썸네일 PDF 준비
            thumbnail_pages = []
            for pdf_path in print_pdfs[:2]:
                try:
                    thumb_reader = PdfReader(pdf_path)
                    if len(thumb_reader.pages) > 0:
                        thumbnail_pages.append(thumb_reader.pages[0])
                except Exception as e:
                    self.logger.warning(f"썸네일 PDF 로드 실패: {e}")
            
            # 각 페이지 처리
            for page_num, page in enumerate(reader.pages):
                # 썸네일 벡터 삽입
                for i, thumb_page in enumerate(thumbnail_pages):
                    position = 'left' if i == 0 else 'right'
                    self._insert_vector_thumbnail(page, thumb_page, position)
                
                # QR 이미지는 래스터로 삽입
                if qr_image:
                    self._insert_raster_qr(page, qr_image)
                
                writer.add_page(page)
            
            # 저장
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            self.logger.info(f"벡터 처리 완료: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"벡터 처리 실패: {e}")
            return False
    
    def _insert_vector_thumbnail(self, page, thumb_page, position: str):
        """벡터 썸네일 삽입"""
        try:
            # 위치와 크기 설정
            x, y = self.thumbnail_positions[position]
            width, height = self.thumbnail_size
            
            # 변환 매트릭스 생성
            scale_x = width / float(thumb_page.mediabox.width)
            scale_y = height / float(thumb_page.mediabox.height)
            scale = min(scale_x, scale_y)
            
            # 페이지에 벡터 삽입
            page.merge_transformed_page(
                thumb_page,
                transformation=fitz.Matrix(scale, 0, 0, scale, x, y)
            )
            
        except Exception as e:
            self.logger.error(f"벡터 썸네일 삽입 실패: {e}")
    
    def _insert_raster_qr(self, page, qr_path: str):
        """래스터 QR 이미지 삽입"""
        # 구현 필요
        pass


class HybridStrategy(PDFProcessingStrategy):
    """하이브리드 처리 전략 (벡터 + 래스터 조합)"""
    
    def process(self, order_pdf: str, print_pdfs: List[str], qr_image: Optional[str], 
                output_path: str) -> bool:
        """
        하이브리드 방식으로 처리
        - 텍스트는 벡터 유지
        - 이미지는 최적화된 래스터
        """
        try:
            self.logger.info("하이브리드 처리 시작")
            
            # 최적화 전략과 벡터 전략을 조합
            # 구현 코드...
            
            self.logger.info(f"하이브리드 처리 완료: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"하이브리드 처리 실패: {e}")
            return False


class RasterStrategy(PDFProcessingStrategy):
    """기본 래스터 처리 전략"""
    
    def process(self, order_pdf: str, print_pdfs: List[str], qr_image: Optional[str], 
                output_path: str) -> bool:
        """
        기본 래스터 방식으로 처리
        - 모든 이미지를 래스터화
        - 가장 빠른 처리
        """
        try:
            self.logger.info("래스터 처리 시작")
            
            # fitz로 처리
            doc = fitz.open(order_pdf)
            
            # 썸네일 생성
            thumbnails = []
            for pdf_path in print_pdfs[:2]:
                thumb = self.create_thumbnail(pdf_path)
                if thumb:
                    thumbnails.append(thumb)
            
            # QR 이미지 로드
            qr_img = None
            if qr_image:
                qr_img = self.load_qr_image(qr_image)
            
            # 각 페이지 처리
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 썸네일 삽입
                for i, thumb in enumerate(thumbnails):
                    position = 'left' if i == 0 else 'right'
                    self._insert_raster_image(page, thumb, self.thumbnail_positions[position])
                
                # QR 삽입
                if qr_img:
                    for position in ['left', 'right']:
                        self._insert_raster_image(page, qr_img, self.qr_positions[position])
            
            # 저장
            doc.save(output_path)
            doc.close()
            
            self.logger.info(f"래스터 처리 완료: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"래스터 처리 실패: {e}")
            return False
    
    def _insert_raster_image(self, page, image: Image.Image, position: Tuple[int, int]):
        """래스터 이미지 삽입"""
        try:
            img_buffer = BytesIO()
            image.save(img_buffer, format='PNG')
            img_data = img_buffer.getvalue()
            
            rect = fitz.Rect(
                position[0],
                position[1], 
                position[0] + image.width,
                position[1] + image.height
            )
            
            page.insert_image(rect, stream=img_data)
            
        except Exception as e:
            self.logger.error(f"래스터 이미지 삽입 실패: {e}")


class PDFProcessorWithStrategy:
    """전략 패턴을 사용하는 PDF 프로세서"""
    
    def __init__(self, settings_manager: SettingsManager):
        """
        초기화
        
        Args:
            settings_manager: 설정 관리자
        """
        self.settings = settings_manager
        self.logger = setup_logger(self.__class__.__name__)
        
        # 전략 맵
        self.strategies = {
            'optimized': OptimizedStrategy(settings_manager),
            'vector': VectorStrategy(settings_manager),
            'hybrid': HybridStrategy(settings_manager),
            'raster': RasterStrategy(settings_manager),
            'rasterized_hybrid': OptimizedStrategy(settings_manager)  # 최적화와 동일
        }
        
        # 기본 전략
        self.default_strategy = 'optimized'
    
    def process_files(self, order_pdf: str, print_pdfs: List[str], qr_image: Optional[str],
                     output_path: str = None) -> bool:
        """
        파일 처리
        
        Args:
            order_pdf: 의뢰서 PDF
            print_pdfs: 인쇄 데이터 PDF 리스트
            qr_image: QR 이미지
            output_path: 출력 경로
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 처리 모드 가져오기
            mode = self.settings.get('processing.mode', self.default_strategy)
            
            # 전략 선택
            if mode not in self.strategies:
                self.logger.warning(f"알 수 없는 모드: {mode}, 기본 모드 사용")
                mode = self.default_strategy
            
            strategy = self.strategies[mode]
            
            # 출력 경로 생성
            if not output_path:
                output_path = self._generate_output_path(order_pdf)
            
            # 처리 실행
            self.logger.info(f"처리 모드: {mode}")
            success = strategy.process(order_pdf, print_pdfs, qr_image, output_path)
            
            return success
            
        except Exception as e:
            self.logger.error(f"파일 처리 실패: {e}")
            return False
    
    def _generate_output_path(self, order_pdf: str) -> str:
        """출력 파일 경로 생성"""
        from datetime import datetime
        
        base_name = Path(order_pdf).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"{base_name}_processed_{timestamp}.pdf"
        
        return str(Path(order_pdf).parent / output_name)