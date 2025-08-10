"""
하이브리드 PDF 처리기 - 최적화된 썸네일 삽입
1. PDF를 고품질로 래스터화
2. 흰색 배경 추가로 가독성 향상
3. 파일 크기 최적화
"""

import os
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from io import BytesIO
import tempfile

# PDF 처리
from PyPDF2 import PdfReader, PdfWriter, PageObject
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import white, black

# 이미지 처리
from PIL import Image, ImageEnhance, ImageOps, ImageFilter, ImageDraw

# 프로젝트 모듈
from config.settings_manager import SettingsManager
from utils.logger import setup_logger


class PDFHybridProcessor:
    """하이브리드 방식 PDF 처리기 - 고품질 래스터 + 백지 배경"""
    
    def __init__(self, settings_manager: SettingsManager):
        """
        초기화
        
        Args:
            settings_manager: 설정 관리자
        """
        self.settings = settings_manager
        self.logger = setup_logger(self.__class__.__name__)
        
        # 좌표 설정
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
        
        # GUI의 DPI 슬라이더와 연동
        # render_dpi를 우선 사용, 없으면 optimal_dpi 사용
        self.thumbnail_dpi = self.settings.get('thumbnail.render_dpi', 
                                              self.settings.get('thumbnail.optimal_dpi', 500))
    
    def process_optimized(self, order_pdf: str, print_pdfs: List[str], 
                         qr_image: str = None, output_path: str = None) -> bool:
        """
        최적화된 처리 - 고품질 래스터 썸네일 + 흰색 배경
        
        Args:
            order_pdf: 의뢰서 PDF 경로
            print_pdfs: 인쇄 데이터 PDF 리스트
            qr_image: QR 코드 이미지
            output_path: 출력 경로
            
        Returns:
            성공 여부
        """
        try:
            self.logger.info(f"최적화 처리 시작 - 의뢰서: {order_pdf}")
            
            # 경로 처리
            order_pdf = Path(order_pdf).resolve()
            if not output_path:
                output_path = self._generate_output_path(order_pdf)
            
            # 1단계: 썸네일 PDF를 고품질 이미지로 변환
            thumbnail_images = self._create_high_quality_thumbnails(print_pdfs)
            
            # 2단계: 흰색 배경이 있는 PDF 생성
            background_pdf = self._create_background_pdf(order_pdf, thumbnail_images, qr_image)
            
            # 3단계: 원본 의뢰서와 병합
            success = self._merge_with_original(order_pdf, background_pdf, output_path)
            
            # 임시 파일 정리
            if background_pdf and os.path.exists(background_pdf):
                os.unlink(background_pdf)
            
            if success:
                self.logger.info(f"[SUCCESS] 최적화 처리 완료: {output_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"[ERROR] 최적화 처리 실패: {e}")
            return False
    
    def _create_high_quality_thumbnails(self, print_pdfs: List[str]) -> List[Image.Image]:
        """
        PDF를 고품질 이미지로 변환
        
        Args:
            print_pdfs: 썸네일용 PDF 리스트
            
        Returns:
            PIL 이미지 리스트
        """
        thumbnail_images = []
        
        for pdf_path in print_pdfs:
            if not pdf_path or not os.path.exists(pdf_path):
                continue
            
            try:
                # PyMuPDF로 렌더링
                doc = fitz.open(str(Path(pdf_path).resolve()))
                page = doc[0]
                
                # 최적 DPI로 렌더링 (300 DPI가 적절한 균형)
                zoom = self.thumbnail_dpi / 72.0
                mat = fitz.Matrix(zoom, zoom)
                
                # 렌더링
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_data = pix.pil_tobytes(format="PNG")
                img = Image.open(BytesIO(img_data))
                
                # RGB로 변환
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 목표 크기로 리사이즈 (고품질 유지)
                target_size = (
                    int(self.thumbnail_size[0] * 2),  # 2배 크기로 먼저 생성
                    int(self.thumbnail_size[1] * 2)
                )
                
                # 비율 유지하며 리사이즈
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                # 샤프닝 적용
                img = img.filter(ImageFilter.SHARPEN)
                
                # 대비 향상
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.2)
                
                # 최종 크기로 조정
                img = img.resize(self.thumbnail_size, Image.Resampling.LANCZOS)
                
                thumbnail_images.append(img)
                self.logger.debug(f"썸네일 생성 완료: {pdf_path}")
                
                doc.close()
                
            except Exception as e:
                self.logger.warning(f"썸네일 생성 실패: {pdf_path} - {e}")
        
        return thumbnail_images
    
    def _create_background_pdf(self, order_pdf: str, thumbnails: List[Image.Image], 
                              qr_image: str = None) -> str:
        """
        흰색 배경과 썸네일이 있는 PDF 생성
        
        Args:
            order_pdf: 원본 의뢰서 (크기 참조용)
            thumbnails: 썸네일 이미지들
            qr_image: QR 이미지 경로
            
        Returns:
            생성된 PDF 경로
        """
        try:
            # 원본 PDF 크기 가져오기
            reader = PdfReader(str(order_pdf))
            first_page = reader.pages[0]
            page_width = float(first_page.mediabox.width)
            page_height = float(first_page.mediabox.height)
            
            # 임시 PDF 생성
            temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_path = temp_pdf.name
            temp_pdf.close()
            
            # ReportLab으로 캔버스 생성
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(temp_path, pagesize=(page_width, page_height))
            
            # 페이지별로 처리
            for page_num in range(len(reader.pages)):
                if page_num > 0:
                    c.showPage()
                
                # 썸네일 위치에 흰색 배경 그리기
                for position_key in ['left', 'right']:
                    x, y = self.thumbnail_positions[position_key]
                    width, height = self.thumbnail_size
                    
                    # 흰색 사각형 그리기 (배경)
                    c.setFillColorRGB(1, 1, 1)  # 흰색
                    c.rect(x, y, width, height, fill=1, stroke=0)
                    
                    # 테두리 그리기 (선택사항)
                    if self.settings.get('thumbnail.border', True):
                        c.setStrokeColorRGB(0.8, 0.8, 0.8)  # 연한 회색
                        c.setLineWidth(0.5)
                        c.rect(x, y, width, height, fill=0, stroke=1)
                
                # 썸네일 이미지 삽입
                if thumbnails:
                    for idx, position_key in enumerate(['left', 'right']):
                        if idx < len(thumbnails):
                            x, y = self.thumbnail_positions[position_key]
                            
                            # 이미지를 임시 파일로 저장
                            temp_img_path = tempfile.mktemp(suffix='.png')
                            thumbnails[idx % len(thumbnails)].save(temp_img_path, 'PNG')
                            
                            # 캔버스에 이미지 그리기
                            c.drawImage(temp_img_path, x, y, 
                                      width=self.thumbnail_size[0], 
                                      height=self.thumbnail_size[1])
                            
                            # 임시 이미지 파일 삭제
                            try:
                                os.unlink(temp_img_path)
                            except:
                                pass
                
                # QR 코드 삽입
                if qr_image and os.path.exists(qr_image):
                    for position_key in ['left', 'right']:
                        x, y = self.qr_positions[position_key]
                        
                        # QR 배경 (흰색)
                        c.setFillColorRGB(1, 1, 1)
                        c.rect(x-2, y-2, self.qr_size+4, self.qr_size+4, fill=1, stroke=0)
                        
                        # QR 이미지
                        c.drawImage(qr_image, x, y, 
                                  width=self.qr_size, 
                                  height=self.qr_size)
            
            # PDF 저장
            c.save()
            
            self.logger.debug(f"배경 PDF 생성 완료: {temp_path}")
            return temp_path
            
        except Exception as e:
            self.logger.error(f"배경 PDF 생성 실패: {e}")
            return None
    
    def _merge_with_original(self, original_pdf: str, overlay_pdf: str, 
                            output_path: str) -> bool:
        """
        원본 PDF와 오버레이 병합
        
        Args:
            original_pdf: 원본 의뢰서
            overlay_pdf: 썸네일이 있는 오버레이
            output_path: 출력 경로
            
        Returns:
            성공 여부
        """
        try:
            # PDF 읽기
            original_reader = PdfReader(str(original_pdf))
            overlay_reader = PdfReader(overlay_pdf)
            writer = PdfWriter()
            
            # 각 페이지 병합
            for page_num in range(len(original_reader.pages)):
                # 원본 페이지
                page = original_reader.pages[page_num]
                
                # 오버레이 페이지가 있으면 병합
                if page_num < len(overlay_reader.pages):
                    overlay_page = overlay_reader.pages[page_num]
                    page.merge_page(overlay_page)
                
                writer.add_page(page)
            
            # 저장
            with open(str(output_path), 'wb') as f:
                writer.write(f)
            
            return True
            
        except Exception as e:
            self.logger.error(f"PDF 병합 실패: {e}")
            return False
    
    def _generate_output_path(self, input_path: Path) -> Path:
        """출력 경로 생성"""
        base_name = input_path.stem
        output_name = f"{base_name}_processed.pdf"
        output_path = input_path.parent / output_name
        
        # 중복 방지
        counter = 1
        while output_path.exists():
            output_name = f"{base_name}_processed_{counter}.pdf"
            output_path = input_path.parent / output_name
            counter += 1
        
        return output_path
    
    def create_rasterized_vector_hybrid(self, order_pdf: str, print_pdfs: List[str],
                                       qr_image: str = None, output_path: str = None) -> bool:
        """
        벡터 PDF를 삽입 후 래스터화하는 하이브리드 방식
        
        1. 원본 의뢰서에 흰색 배경 먼저 추가
        2. PDF를 벡터로 삽입
        3. 해당 영역만 래스터화
        4. 파일 크기 최적화
        """
        try:
            self.logger.info("래스터화된 벡터 하이브리드 처리 시작")
            
            # 1단계: 원본 의뢰서 열기
            original_doc = fitz.open(str(Path(order_pdf).resolve()))
            
            # 흰색 배경 추가 (가독성 향상)
            if self.settings.get('processing.white_background', True):
                for page in original_doc:
                    # 각 썸네일 위치에 흰색 배경 그리기
                    for position_key in ['left', 'right']:
                        x, y = self.thumbnail_positions[position_key]
                        width, height = self.thumbnail_size
                        
                        # 흰색 사각형 그리기
                        rect = fitz.Rect(x, y, x + width, y + height)
                        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                        
                        # 테두리 (선택사항)
                        if self.settings.get('thumbnail.border', True):
                            page.draw_rect(rect, color=(0.8, 0.8, 0.8), fill=None, width=0.5)
            
            # 임시 파일로 저장 (흰색 배경이 있는 의뢰서)
            temp_with_bg = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_with_bg_path = temp_with_bg.name
            temp_with_bg.close()
            original_doc.save(temp_with_bg_path)
            original_doc.close()
            
            # 2단계: 흰색 배경이 있는 의뢰서에 벡터 썸네일 삽입
            temp_vector_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_vector_path = temp_vector_pdf.name
            temp_vector_pdf.close()
            
            # PyPDF2로 벡터 삽입
            from .pdf_vector_processor import PDFVectorProcessor
            vector_processor = PDFVectorProcessor(self.settings)
            vector_processor.process_with_vector(temp_with_bg_path, print_pdfs, qr_image, temp_vector_path)
            
            # 3단계: 벡터 PDF를 열어서 썸네일 영역만 래스터화
            doc = fitz.open(temp_vector_path)
            
            # 흰색 배경이 보이도록 여백 설정 (설정에서 가져오거나 기본값 3픽셀)
            border_margin = self.settings.get('thumbnail.white_border_size', 3)
            
            for page in doc:
                # 각 썸네일 위치에서 이미지 추출 및 재삽입
                for position_key in ['left', 'right']:
                    x, y = self.thumbnail_positions[position_key]
                    width, height = self.thumbnail_size
                    
                    # 해당 영역을 고품질로 래스터화
                    rect = fitz.Rect(x, y, x + width, y + height)
                    
                    # 먼저 이미지 추출 (고DPI)
                    zoom = self.thumbnail_dpi / 72.0
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat, clip=rect, alpha=False)
                    
                    # 추출한 이미지를 PIL로 변환하여 처리
                    img_data = pix.pil_tobytes(format="PNG")
                    img = Image.open(BytesIO(img_data))
                    
                    # 여백을 고려한 크기로 리사이즈 (흰 배경이 보이도록)
                    new_width = width - (border_margin * 2)
                    new_height = height - (border_margin * 2)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # 이미지를 다시 바이트로 변환
                    img_buffer = BytesIO()
                    img.save(img_buffer, format='PNG', optimize=True)
                    img_data = img_buffer.getvalue()
                    
                    # 여백을 두고 래스터 이미지 삽입 (흰 배경이 테두리로 보임)
                    inset_rect = fitz.Rect(
                        x + border_margin, 
                        y + border_margin, 
                        x + width - border_margin, 
                        y + height - border_margin
                    )
                    
                    # 기존 벡터 내용을 흰색으로 덮기 (선택사항)
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                    
                    # 래스터 이미지 삽입
                    page.insert_image(inset_rect, stream=img_data)
            
            # 저장
            if not output_path:
                output_path = self._generate_output_path(Path(order_pdf))
            
            doc.save(str(output_path), garbage=4, deflate=True, clean=True)
            doc.close()
            
            # 임시 파일 삭제
            for temp_file in [temp_with_bg_path, temp_vector_path]:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
            
            self.logger.info(f"[SUCCESS] 하이브리드 처리 완료: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"하이브리드 처리 실패: {e}")
            return False


def integrate_hybrid_processor(pdf_processor_instance):
    """
    기존 PDFProcessor에 하이브리드 프로세서 통합
    
    Args:
        pdf_processor_instance: PDFProcessor 인스턴스
    """
    # 하이브리드 프로세서 생성
    hybrid_processor = PDFHybridProcessor(pdf_processor_instance.settings)
    
    # 메서드 추가
    pdf_processor_instance.process_optimized = hybrid_processor.process_optimized
    pdf_processor_instance.process_rasterized_hybrid = hybrid_processor.create_rasterized_vector_hybrid
    
    return pdf_processor_instance