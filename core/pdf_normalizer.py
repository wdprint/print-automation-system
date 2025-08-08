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
            
            # 각 페이지 검사
            for page_num, page in enumerate(doc):
                # 회전 확인
                rotation = page.rotation
                if rotation != 0:
                    self.logger.info(f"페이지 {page_num + 1}: {rotation}도 회전 감지")
                    needs_normalization = True
                
                # 페이지 크기 확인 (A4 가로: 842 x 595 포인트)
                rect = page.rect
                width = rect.width
                height = rect.height
                
                # 세로 방향인지 확인
                if height > width:
                    self.logger.info(f"페이지 {page_num + 1}: 세로 방향 감지")
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
        실제 정규화 적용
        
        Args:
            doc: PyMuPDF 문서 객체
            original_path: 원본 파일 경로
            output_dir: 출력 디렉토리
            
        Returns:
            정규화된 파일 경로
        """
        try:
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
                # 페이지 복사
                rect = page.rect
                width = rect.width
                height = rect.height
                
                # 회전 처리
                rotation = page.rotation
                if rotation != 0:
                    # 회전 제거
                    page.set_rotation(0)
                    self.logger.debug(f"페이지 {page_num + 1}: 회전 제거 ({rotation}도)")
                
                # 세로를 가로로 변환
                if height > width:
                    # 90도 회전하여 가로로 만들기
                    page.set_rotation(90)
                    self.logger.debug(f"페이지 {page_num + 1}: 가로 방향으로 변환")
                
                # 표준 A4 가로 크기로 조정 (필요한 경우)
                target_width = 842
                target_height = 595
                
                # 페이지를 새 문서에 추가
                new_page = new_doc.new_page(width=target_width, height=target_height)
                
                # 원본 페이지 내용 복사
                new_page.show_pdf_page(new_page.rect, doc, page_num)
            
            # 저장
            new_doc.save(output_path)
            new_doc.close()
            
            self.logger.info(f"PDF 정규화 완료: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"정규화 적용 실패: {e}")
            return original_path
    
    def detect_rotation(self, pdf_path: str) -> dict:
        """
        PDF 페이지별 회전 감지
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            페이지별 회전 정보
        """
        rotations = {}
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num, page in enumerate(doc):
                rotation = page.rotation
                orientation = self._detect_orientation(page)
                
                rotations[page_num] = {
                    'rotation': rotation,
                    'orientation': orientation,
                    'needs_correction': rotation != 0 or orientation == 'portrait'
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
    
    def auto_crop(self, pdf_path: str, output_path: str = None) -> str:
        """
        PDF 자동 크롭 (여백 제거)
        
        Args:
            pdf_path: 원본 PDF 경로
            output_path: 출력 경로 (None이면 원본 덮어쓰기)
            
        Returns:
            크롭된 PDF 경로
        """
        try:
            doc = fitz.open(pdf_path)
            
            for page in doc:
                # 컨텐츠 영역 감지
                content_rect = self._detect_content_area(page)
                
                if content_rect:
                    # 페이지 크롭
                    page.set_cropbox(content_rect)
                    self.logger.debug(f"페이지 크롭: {content_rect}")
            
            # 저장
            if not output_path:
                output_path = pdf_path
            
            doc.save(output_path)
            doc.close()
            
            self.logger.info(f"자동 크롭 완료: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"자동 크롭 실패: {e}")
            return pdf_path
    
    def _detect_content_area(self, page: fitz.Page) -> Optional[fitz.Rect]:
        """
        페이지의 실제 컨텐츠 영역 감지
        
        Args:
            page: PyMuPDF 페이지 객체
            
        Returns:
            컨텐츠 영역 사각형 또는 None
        """
        try:
            # 텍스트 블록 가져오기
            blocks = page.get_text("blocks")
            
            if not blocks:
                return None
            
            # 컨텐츠 경계 찾기
            min_x = min(block[0] for block in blocks)
            min_y = min(block[1] for block in blocks)
            max_x = max(block[2] for block in blocks)
            max_y = max(block[3] for block in blocks)
            
            # 여백 추가 (10 포인트)
            margin = 10
            content_rect = fitz.Rect(
                max(0, min_x - margin),
                max(0, min_y - margin),
                min(page.rect.width, max_x + margin),
                min(page.rect.height, max_y + margin)
            )
            
            return content_rect
            
        except Exception as e:
            self.logger.warning(f"컨텐츠 영역 감지 실패: {e}")
            return None
    
    def split_2up(self, pdf_path: str, output_dir: str = None) -> Tuple[str, str]:
        """
        2-up 레이아웃 PDF를 좌우로 분할
        
        Args:
            pdf_path: 2-up PDF 경로
            output_dir: 출력 디렉토리
            
        Returns:
            (왼쪽 PDF 경로, 오른쪽 PDF 경로)
        """
        try:
            doc = fitz.open(pdf_path)
            
            # 출력 경로 설정
            if not output_dir:
                output_dir = os.path.dirname(pdf_path)
            
            base_name = Path(pdf_path).stem
            left_path = os.path.join(output_dir, f"{base_name}_left.pdf")
            right_path = os.path.join(output_dir, f"{base_name}_right.pdf")
            
            # 좌우 문서 생성
            left_doc = fitz.open()
            right_doc = fitz.open()
            
            for page in doc:
                rect = page.rect
                mid_x = rect.width / 2
                
                # 왼쪽 페이지
                left_rect = fitz.Rect(0, 0, mid_x, rect.height)
                left_page = left_doc.new_page(width=mid_x, height=rect.height)
                left_page.show_pdf_page(left_page.rect, doc, page.number, clip=left_rect)
                
                # 오른쪽 페이지
                right_rect = fitz.Rect(mid_x, 0, rect.width, rect.height)
                right_page = right_doc.new_page(width=mid_x, height=rect.height)
                right_page.show_pdf_page(right_page.rect, doc, page.number, clip=right_rect)
            
            # 저장
            left_doc.save(left_path)
            right_doc.save(right_path)
            
            # 정리
            left_doc.close()
            right_doc.close()
            doc.close()
            
            self.logger.info(f"2-up 분할 완료: {left_path}, {right_path}")
            return left_path, right_path
            
        except Exception as e:
            self.logger.error(f"2-up 분할 실패: {e}")
            return None, None