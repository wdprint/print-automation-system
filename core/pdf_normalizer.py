"""PDF 정규화 모듈 - 회전 수정 및 표준화"""

import os
from pathlib import Path
from typing import Optional, Tuple

import fitz  # PyMuPDF

from utils.logger import setup_logger

class PDFNormalizer:
    """PDF 정규화 - 회전 수정 및 표준화"""
    
    def __init__(self):
        """PDF 정규화기 초기화"""
        self.logger = setup_logger(self.__class__.__name__)
    
    def normalize(self, pdf_path: str, output_dir: str = None) -> str:
        """
        PDF 정규화 (회전 수정, 크기 표준화)
        
        Args:
            pdf_path: 원본 PDF 경로
            output_dir: 출력 디렉토리 (None이면 원본 위치)
            
        Returns:
            정규화된 PDF 경로 (변경 없으면 원본 경로)
        """
        try:
            doc = fitz.open(pdf_path)
            needs_normalization = False
            
            # 파일명에 "의뢰서"가 포함되어 있는지 확인
            is_order_pdf = "의뢰서" in os.path.basename(pdf_path)
            
            if is_order_pdf:
                # 의뢰서 PDF도 회전 확인 및 보정
                self.logger.info(f"의뢰서 PDF 감지: 회전 확인")
                for page_num, page in enumerate(doc):
                    rotation = page.rotation
                    if rotation != 0:
                        self.logger.info(f"페이지 {page_num + 1}: {rotation}도 회전 감지")
                        needs_normalization = True
                        break
            else:
                # 썸네일 PDF는 첫 페이지만 확인
                self.logger.info(f"썸네일 PDF: 첫 페이지만 회전 확인")
                if len(doc) > 0:
                    page = doc[0]
                    rotation = page.rotation
                    if rotation != 0:
                        self.logger.info(f"페이지 1: {rotation}도 회전 감지")
                        needs_normalization = True
                    
                    rect = page.rect
                    width = rect.width
                    height = rect.height
                    
                    if height > width:
                        self.logger.info(f"페이지 1: 세로 방향 감지")
                        needs_normalization = True
            
            # 정규화가 필요한 경우
            if needs_normalization:
                normalized_path = self._apply_normalization(doc, pdf_path, output_dir)
                doc.close()
                return normalized_path
            
            doc.close()
            return pdf_path
            
        except Exception as e:
            self.logger.error(f"PDF 정규화 실패: {e}")
            return pdf_path
    
    def _apply_normalization(self, doc: fitz.Document, original_path: str, 
                            output_dir: str = None) -> str:
        """
        실제 정규화 적용 - v1 방식 래스터화 포함
        
        Args:
            doc: PyMuPDF 문서 객체
            original_path: 원본 파일 경로
            output_dir: 출력 디렉토리
            
        Returns:
            정규화된 파일 경로
        """
        try:
            from PIL import Image
            from io import BytesIO
            
            # 출력 경로 생성
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(
                    output_dir,
                    f"normalized_{os.path.basename(original_path)}"
                )
            else:
                base_path = Path(original_path)
                output_path = str(base_path.parent / f"normalized_{base_path.name}")
            
            # 새 문서 생성
            new_doc = fitz.open()
            
            for page_num, page in enumerate(doc):
                rotation = page.rotation
                mediabox = page.mediabox
                rect = page.rect
                
                # 회전이 90도 또는 270도인 경우 래스터화 처리 (v1 방식)
                if rotation in [90, 270]:
                    self.logger.info(f"페이지 {page_num + 1}: {rotation}도 회전 - 래스터화 처리")
                    
                    # 페이지를 이미지로 변환 (적절한 해상도)
                    mat = fitz.Matrix(1.5, 1.5)  # 1.5배 해상도 (파일 크기 최적화)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    img_data = pix.pil_tobytes(format="PNG")
                    img = Image.open(BytesIO(img_data))
                    
                    # 실제로 가로로 보이도록 페이지 생성
                    # rect는 실제 보이는 크기 (842x595), mediabox는 물리적 크기 (595x842)
                    # 의뢰서는 항상 가로형이어야 하므로 842x595로 설정
                    new_width = max(rect.width, rect.height)  # 큰 값이 너비 (842)
                    new_height = min(rect.width, rect.height)  # 작은 값이 높이 (595)
                    new_page = new_doc.new_page(width=new_width, height=new_height)
                    # 회전 속성을 명시적으로 0으로 설정
                    new_page.set_rotation(0)
                    
                    # 이미지를 PNG로 저장 후 삽입 (PDF 저장 실패 방지)
                    img_buffer = BytesIO()
                    img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    
                    # PDF 페이지에 삽입
                    new_page.insert_image(new_page.rect, stream=img_buffer.getvalue())
                    
                elif rotation != 0:
                    # 180도 회전 등 다른 경우는 벡터 방식으로 처리
                    self.logger.info(f"페이지 {page_num + 1}: {rotation}도 회전 보정")
                    
                    width = mediabox.width
                    height = mediabox.height
                    new_page = new_doc.new_page(width=width, height=height)
                    
                    # 회전 보정
                    new_page.show_pdf_page(
                        new_page.rect,
                        doc, 
                        page_num,
                        rotate=-rotation
                    )
                    # 회전 속성을 명시적으로 0으로 설정
                    new_page.set_rotation(0)
                else:
                    # 회전이 없으면 원본 그대로 복사
                    width = mediabox.width
                    height = mediabox.height
                    new_page = new_doc.new_page(width=width, height=height)
                    new_page.show_pdf_page(
                        new_page.rect,
                        doc,
                        page_num
                    )
            
            # 저장 (압축 옵션 적용)
            new_doc.save(output_path, garbage=4, deflate=True, clean=True)
            new_doc.close()
            
            self.logger.info(f"PDF 정규화 완료: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"정규화 적용 실패: {e}")
            return original_path
    
    def detect_rotation(self, pdf_path: str) -> dict:
        """
        PDF 페이지별 회전 감지
        의뢰서 PDF는 모든 페이지, 썸네일 PDF는 첫 페이지만 확인
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            페이지별 회전 정보
        """
        rotations = {}
        
        try:
            doc = fitz.open(pdf_path)
            
            # 파일명에 "의뢰서"가 포함되어 있는지 확인
            is_order_pdf = "의뢰서" in os.path.basename(pdf_path)
            
            if is_order_pdf:
                # 의뢰서 PDF는 모든 페이지 확인
                for page_num, page in enumerate(doc):
                    rotation = page.rotation
                    mediabox = page.mediabox
                    
                    # 회전을 고려한 실제 방향 판단
                    if rotation in [90, 270]:
                        actual_width = mediabox.height
                        actual_height = mediabox.width
                    else:
                        actual_width = mediabox.width
                        actual_height = mediabox.height
                    
                    orientation = 'landscape' if actual_width > actual_height else 'portrait'
                    
                    rotations[page_num] = {
                        'rotation': rotation,
                        'mediabox': (mediabox.width, mediabox.height),
                        'actual_size': (actual_width, actual_height),
                        'orientation': orientation,
                        'needs_correction': rotation != 0
                    }
            else:
                # 썸네일 PDF는 첫 페이지만 확인
                if len(doc) > 0:
                    page = doc[0]
                    rotation = page.rotation
                    mediabox = page.mediabox
                    
                    if rotation in [90, 270]:
                        actual_width = mediabox.height
                        actual_height = mediabox.width
                    else:
                        actual_width = mediabox.width
                        actual_height = mediabox.height
                    
                    orientation = 'landscape' if actual_width > actual_height else 'portrait'
                    
                    rotations[0] = {
                        'rotation': rotation,
                        'mediabox': (mediabox.width, mediabox.height),
                        'actual_size': (actual_width, actual_height),
                        'orientation': orientation,
                        'needs_correction': rotation != 0
                    }
            
            doc.close()
            return rotations
            
        except Exception as e:
            self.logger.error(f"회전 감지 실패: {e}")
            return {}
    
    def _detect_orientation(self, page: fitz.Page) -> str:
        """
        페이지 방향 감지
        
        Args:
            page: PyMuPDF 페이지 객체
            
        Returns:
            'landscape' 또는 'portrait'
        """
        rect = page.rect
        width = rect.width
        height = rect.height
        
        # 회전 고려
        rotation = page.rotation
        if rotation in [90, 270]:
            width, height = height, width
        
        return 'landscape' if width > height else 'portrait'
    
    
    
    def process_for_thumbnail(self, pdf_path: str) -> str:
        """
        썸네일 생성을 위해 PDF 정규화
        썸네일 PDF는 회전 감지하지 않음 (리소스 절약)
        
        Args:
            pdf_path: 원본 PDF 경로
            
        Returns:
            str: 원본 PDF 경로 (회전 감지 없음)
        """
        # 썸네일 PDF는 회전 감지/보정하지 않고 원본 그대로 사용
        # 리소스 절약 및 성능 향상
        self.logger.debug(f"썸네일 PDF는 회전 감지 건너뛰기: {pdf_path}")
        return pdf_path
    
