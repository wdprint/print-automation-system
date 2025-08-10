"""
PDF 벡터 처리기 - 썸네일과 QR을 고품질로 삽입
벡터 방식과 고해상도 이미지 처리 통합
"""

import os
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from io import BytesIO
import tempfile

# PDF 처리
from PyPDF2 import PdfReader, PdfWriter, Transformation, PageObject
import fitz  # PyMuPDF (기존 의뢰서 처리용)

# 이미지 처리
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import numpy as np

# 프로젝트 모듈
from config.settings_manager import SettingsManager
from utils.logger import setup_logger


class PDFVectorProcessor:
    """벡터 방식 PDF 처리기 - 고품질 썸네일 및 QR 삽입"""
    
    def __init__(self, settings_manager: SettingsManager):
        """
        초기화
        
        Args:
            settings_manager: 설정 관리자
        """
        self.settings = settings_manager
        self.logger = setup_logger(self.__class__.__name__)
        
        # 기본 설정
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
    
    def process_with_vector(self, order_pdf: str, print_pdfs: List[str], 
                           qr_image: str = None, output_path: str = None) -> bool:
        """
        벡터 방식으로 PDF 처리
        
        Args:
            order_pdf: 의뢰서 PDF 경로
            print_pdfs: 인쇄 데이터 PDF 리스트 (썸네일용)
            qr_image: QR 코드 이미지 경로
            output_path: 출력 경로
            
        Returns:
            성공 여부
        """
        try:
            self.logger.info(f"벡터 처리 시작 - 의뢰서: {order_pdf}")
            
            # 파일 경로 UTF-8 처리
            order_pdf = Path(order_pdf).resolve()
            
            # 출력 경로 생성
            if not output_path:
                output_path = self._generate_output_path(order_pdf)
            
            # PyPDF2로 의뢰서 읽기
            order_reader = PdfReader(str(order_pdf), strict=False)
            writer = PdfWriter()
            
            # QR 이미지 준비 (고해상도 유지)
            qr_img_data = None
            if qr_image and os.path.exists(qr_image):
                qr_img_data = self._prepare_qr_image(qr_image)
            
            # 썸네일 PDF 리더들 준비
            thumbnail_readers = []
            if print_pdfs:
                for pdf_path in print_pdfs:
                    if pdf_path and os.path.exists(pdf_path):
                        try:
                            reader = PdfReader(str(Path(pdf_path).resolve()), strict=False)
                            thumbnail_readers.append(reader)
                            self.logger.info(f"썸네일 PDF 로드: {pdf_path}")
                        except Exception as e:
                            self.logger.warning(f"썸네일 PDF 로드 실패: {pdf_path} - {e}")
            
            # 각 페이지 처리
            for page_num, base_page in enumerate(order_reader.pages):
                self.logger.debug(f"페이지 {page_num + 1} 처리 중...")
                
                # 새 페이지 생성 (기존 내용 복사)
                new_page = PageObject.create_blank_page(
                    width=float(base_page.mediabox.width),
                    height=float(base_page.mediabox.height)
                )
                new_page.merge_page(base_page)
                
                # 벡터 썸네일 삽입
                if thumbnail_readers:
                    self._insert_vector_thumbnails(new_page, thumbnail_readers, page_num)
                
                # QR 이미지 삽입 (래스터)
                if qr_img_data:
                    self._insert_qr_on_page(new_page, qr_img_data)
                
                writer.add_page(new_page)
            
            # PDF 저장 (UTF-8 경로 지원)
            output_path = Path(output_path).resolve()
            with open(str(output_path), 'wb') as f:
                writer.write(f)
            
            self.logger.info(f"[SUCCESS] Vector processing complete: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"[ERROR] Vector processing failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def _insert_vector_thumbnails(self, page: PageObject, 
                                 thumbnail_readers: List[PdfReader], 
                                 page_num: int):
        """
        벡터 방식으로 썸네일 삽입
        
        Args:
            page: 대상 페이지
            thumbnail_readers: 썸네일 PDF 리더들
            page_num: 현재 페이지 번호
        """
        try:
            # 썸네일 위치별로 처리
            positions = ['left', 'right']
            
            for idx, position in enumerate(positions):
                # 썸네일 리더 선택 (순환)
                if not thumbnail_readers:
                    break
                    
                reader_idx = (page_num * 2 + idx) % len(thumbnail_readers)
                thumb_reader = thumbnail_readers[reader_idx]
                
                # 첫 페이지 가져오기
                thumb_page = thumb_reader.pages[0]
                
                # 원본 크기
                orig_width = float(thumb_page.mediabox.width)
                orig_height = float(thumb_page.mediabox.height)
                
                # 목표 크기 (픽셀을 포인트로 변환)
                target_width = self.thumbnail_size[0] * 0.75
                target_height = self.thumbnail_size[1] * 0.75
                
                # 스케일 계산 (비율 유지)
                scale = min(target_width / orig_width, target_height / orig_height)
                
                # 위치 가져오기
                x_pos, y_pos = self.thumbnail_positions[position]
                
                # 변환 매트릭스 적용
                transformation = Transformation().scale(
                    sx=scale, sy=scale
                ).translate(tx=x_pos, ty=y_pos)
                
                # 썸네일 페이지 복사 (재사용 방지)
                thumb_copy = thumb_reader.pages[0]
                thumb_copy.add_transformation(transformation)
                
                # 페이지에 병합
                page.merge_page(thumb_copy)
                
                self.logger.debug(f"썸네일 삽입 ({position}): scale={scale:.3f}")
                
        except Exception as e:
            self.logger.warning(f"썸네일 삽입 실패: {e}")
    
    def _prepare_qr_image(self, qr_image_path: str) -> Optional[bytes]:
        """
        QR 이미지를 고품질로 준비
        
        Args:
            qr_image_path: QR 이미지 경로
            
        Returns:
            PNG 바이트 데이터
        """
        try:
            # UTF-8 경로 처리
            qr_path = Path(qr_image_path).resolve()
            
            # 이미지 열기
            with Image.open(str(qr_path)) as img:
                # RGBA로 변환
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # QR 크기로 리사이즈 (고품질 리샘플링)
                qr_size_pixels = int(self.qr_size / 0.75)  # 포인트를 픽셀로
                
                # 원본이 작으면 업스케일, 크면 다운스케일
                if img.width < qr_size_pixels:
                    # 업스케일 시 NEAREST로 선명도 유지 (QR은 픽셀아트)
                    img = img.resize((qr_size_pixels, qr_size_pixels), 
                                   Image.Resampling.NEAREST)
                else:
                    # 다운스케일 시 LANCZOS로 부드럽게
                    img = img.resize((qr_size_pixels, qr_size_pixels), 
                                   Image.Resampling.LANCZOS)
                
                # 선명도 향상 (QR 코드용)
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(2.0)
                
                # 대비 향상
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.5)
                
                # PNG로 저장 (최고 품질)
                buffer = BytesIO()
                img.save(buffer, format='PNG', compress_level=0, optimize=False)
                
                self.logger.debug(f"QR 이미지 준비 완료: {qr_size_pixels}x{qr_size_pixels}")
                return buffer.getvalue()
                
        except Exception as e:
            self.logger.error(f"QR 이미지 준비 실패: {e}")
            return None
    
    def _insert_qr_on_page(self, page: PageObject, qr_img_data: bytes):
        """
        페이지에 QR 이미지 삽입
        
        Args:
            page: 대상 페이지
            qr_img_data: QR 이미지 데이터
        """
        try:
            # PyMuPDF를 사용하여 이미지 삽입 (더 나은 이미지 처리)
            # 임시 PDF 생성
            temp_pdf = BytesIO()
            
            # PyMuPDF로 페이지 크기 가져오기
            doc = fitz.open()
            fitz_page = doc.new_page(
                width=float(page.mediabox.width),
                height=float(page.mediabox.height)
            )
            
            # QR 이미지를 PyMuPDF로 삽입
            img = Image.open(BytesIO(qr_img_data))
            
            # 각 위치에 QR 삽입
            for position in ['left', 'right']:
                x_pos, y_pos = self.qr_positions[position]
                
                # PyMuPDF는 top-left 기준이므로 좌표 변환
                rect = fitz.Rect(
                    x_pos, 
                    float(page.mediabox.height) - y_pos - self.qr_size,
                    x_pos + self.qr_size, 
                    float(page.mediabox.height) - y_pos
                )
                
                # 이미지 삽입
                img_buffer = BytesIO()
                img.save(img_buffer, format='PNG')
                fitz_page.insert_image(rect, stream=img_buffer.getvalue())
            
            # PDF로 저장
            doc.save(temp_pdf)
            doc.close()
            
            # PyPDF2로 병합
            temp_pdf.seek(0)
            qr_reader = PdfReader(temp_pdf)
            if qr_reader.pages:
                page.merge_page(qr_reader.pages[0])
            
            self.logger.debug("QR 이미지 삽입 완료")
            
        except Exception as e:
            self.logger.warning(f"QR 삽입 실패 (대체 방법 시도): {e}")
            # 대체 방법: 직접 이미지 스트림 삽입 시도
            self._fallback_qr_insertion(page, qr_img_data)
    
    def _fallback_qr_insertion(self, page: PageObject, qr_img_data: bytes):
        """QR 삽입 대체 방법"""
        try:
            # reportlab 사용하여 QR 포함 PDF 생성
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4, landscape
            
            temp_pdf = BytesIO()
            c = canvas.Canvas(temp_pdf, pagesize=(float(page.mediabox.width), 
                                                 float(page.mediabox.height)))
            
            # QR 이미지를 임시 파일로 저장
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp.write(qr_img_data)
                tmp_path = tmp.name
            
            try:
                # 각 위치에 QR 그리기
                for position in ['left', 'right']:
                    x_pos, y_pos = self.qr_positions[position]
                    c.drawImage(tmp_path, x_pos, y_pos, 
                              width=self.qr_size, height=self.qr_size)
                
                c.save()
                
                # PyPDF2로 병합
                temp_pdf.seek(0)
                qr_reader = PdfReader(temp_pdf)
                if qr_reader.pages:
                    page.merge_page(qr_reader.pages[0])
                
            finally:
                # 임시 파일 삭제
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            self.logger.error(f"QR 대체 방법도 실패: {e}")
    
    def _generate_output_path(self, input_path: Path) -> Path:
        """
        출력 파일 경로 생성 (UTF-8 지원)
        
        Args:
            input_path: 입력 파일 경로
            
        Returns:
            출력 파일 경로
        """
        # 파일명에서 확장자 제거
        base_name = input_path.stem
        
        # '_processed' 추가
        output_name = f"{base_name}_processed.pdf"
        
        # 같은 디렉토리에 저장
        output_path = input_path.parent / output_name
        
        # 중복 방지
        counter = 1
        while output_path.exists():
            output_name = f"{base_name}_processed_{counter}.pdf"
            output_path = input_path.parent / output_name
            counter += 1
        
        return output_path
    
    def process_hybrid(self, order_pdf: str, print_pdfs: List[str], 
                      qr_image: str = None, output_path: str = None) -> bool:
        """
        하이브리드 처리 - 썸네일은 벡터, 의뢰서는 기존 방식
        
        Args:
            order_pdf: 의뢰서 PDF
            print_pdfs: 인쇄 PDF 리스트
            qr_image: QR 이미지
            output_path: 출력 경로
            
        Returns:
            성공 여부
        """
        try:
            # 이 방법은 PyMuPDF로 의뢰서를 처리하고
            # PyPDF2로 썸네일만 벡터로 삽입하는 하이브리드 방식
            
            self.logger.info("하이브리드 처리 모드 시작")
            
            # 1단계: PyMuPDF로 의뢰서 렌더링 및 QR 삽입
            temp_pdf = self._process_with_pymupdf(order_pdf, qr_image)
            
            if not temp_pdf:
                return False
            
            # 2단계: PyPDF2로 벡터 썸네일 삽입
            success = self.process_with_vector(temp_pdf, print_pdfs, None, output_path)
            
            # 임시 파일 삭제
            if os.path.exists(temp_pdf):
                os.unlink(temp_pdf)
            
            return success
            
        except Exception as e:
            self.logger.error(f"하이브리드 처리 실패: {e}")
            return False
    
    def _process_with_pymupdf(self, order_pdf: str, qr_image: str = None) -> Optional[str]:
        """
        PyMuPDF로 의뢰서 처리 및 QR 삽입
        
        Returns:
            임시 PDF 경로
        """
        try:
            # 임시 파일 생성
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            # PyMuPDF로 처리
            doc = fitz.open(str(Path(order_pdf).resolve()))
            
            # QR 이미지 처리
            if qr_image and os.path.exists(qr_image):
                qr_data = self._prepare_qr_image(qr_image)
                
                for page in doc:
                    # QR 삽입
                    for position in ['left', 'right']:
                        x_pos, y_pos = self.qr_positions[position]
                        
                        rect = fitz.Rect(
                            x_pos,
                            page.rect.height - y_pos - self.qr_size,
                            x_pos + self.qr_size,
                            page.rect.height - y_pos
                        )
                        
                        page.insert_image(rect, stream=qr_data)
            
            # 저장
            doc.save(temp_path)
            doc.close()
            
            return temp_path
            
        except Exception as e:
            self.logger.error(f"PyMuPDF 처리 실패: {e}")
            return None


# 기존 PDFProcessor와의 통합을 위한 래퍼 함수
def upgrade_to_vector_processor(pdf_processor_instance):
    """
    기존 PDFProcessor를 벡터 방식으로 업그레이드
    
    Args:
        pdf_processor_instance: 기존 PDFProcessor 인스턴스
    """
    # 벡터 프로세서 생성
    vector_processor = PDFVectorProcessor(pdf_processor_instance.settings)
    
    # 메서드 교체
    pdf_processor_instance.process_files_vector = vector_processor.process_with_vector
    pdf_processor_instance.process_files_hybrid = vector_processor.process_hybrid
    
    # 기존 process_files 메서드 백업
    pdf_processor_instance._original_process_files = pdf_processor_instance.process_files
    
    # 새로운 process_files 정의
    def new_process_files(order_pdf, print_pdfs, qr_image=None):
        """벡터 방식을 기본으로 사용하는 process_files"""
        
        # 설정에서 처리 모드 확인
        mode = pdf_processor_instance.settings.get('processing.mode', 'vector')
        
        if mode == 'vector':
            return vector_processor.process_with_vector(order_pdf, print_pdfs, qr_image)
        elif mode == 'hybrid':
            return vector_processor.process_hybrid(order_pdf, print_pdfs, qr_image)
        else:  # 'raster' 또는 기타
            return pdf_processor_instance._original_process_files(order_pdf, print_pdfs, qr_image)
    
    # 메서드 교체
    pdf_processor_instance.process_files = new_process_files
    
    return pdf_processor_instance