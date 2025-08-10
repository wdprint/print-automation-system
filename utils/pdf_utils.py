"""PDF 처리 공통 유틸리티 모듈"""

import os
from pathlib import Path
from typing import Optional, Tuple
import hashlib
from datetime import datetime

from utils.logger import setup_logger


class PDFUtils:
    """PDF 처리 관련 공통 유틸리티"""
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
    
    @staticmethod
    def generate_output_path(input_path: str, suffix: str = "_완료", 
                           output_dir: Optional[str] = None) -> str:
        """
        출력 파일 경로 생성 (중복 방지 포함)
        
        Args:
            input_path: 입력 파일 경로
            suffix: 파일명에 추가할 접미사
            output_dir: 출력 디렉토리 (None이면 입력과 같은 위치)
            
        Returns:
            str: 생성된 출력 경로
        """
        input_path = Path(input_path)
        stem = input_path.stem
        ext = input_path.suffix
        
        if output_dir:
            parent = Path(output_dir)
            parent.mkdir(parents=True, exist_ok=True)
        else:
            parent = input_path.parent
        
        # 기본 출력 파일명
        output_name = f"{stem}{suffix}{ext}"
        output_path = parent / output_name
        
        # 파일이 이미 존재하면 번호 추가
        counter = 1
        while output_path.exists():
            output_name = f"{stem}{suffix}_{counter}{ext}"
            output_path = parent / output_name
            counter += 1
        
        return str(output_path)
    
    @staticmethod
    def get_page_hash(page_content: bytes) -> str:
        """
        페이지 내용의 해시값 생성 (캐싱용)
        
        Args:
            page_content: 페이지 내용 바이트
            
        Returns:
            str: MD5 해시값
        """
        return hashlib.md5(page_content).hexdigest()
    
    @staticmethod
    def parse_page_selection(selection_str: str, total_pages: int) -> list:
        """
        페이지 선택 문자열 파싱
        
        Args:
            selection_str: 페이지 선택 문자열 (예: "1", "1-3", "1,3,5", "1-3,5")
            total_pages: 전체 페이지 수
            
        Returns:
            list: 선택된 페이지 인덱스 리스트 (0-based)
            
        Examples:
            >>> parse_page_selection("1", 10)
            [0]
            >>> parse_page_selection("1-3", 10)
            [0, 1, 2]
            >>> parse_page_selection("1,3,5", 10)
            [0, 2, 4]
        """
        pages = []
        
        # 기본값: 첫 페이지만
        if not selection_str or selection_str == "1":
            return [0]
        
        parts = selection_str.split(',')
        for part in parts:
            part = part.strip()
            
            if '-' in part:
                # 범위 처리 (예: 1-3)
                try:
                    start, end = part.split('-')
                    start = max(1, int(start))
                    end = min(total_pages, int(end))
                    pages.extend(range(start - 1, end))
                except (ValueError, TypeError):
                    pass
            else:
                # 단일 페이지 처리
                try:
                    page_num = int(part) - 1
                    if 0 <= page_num < total_pages:
                        pages.append(page_num)
                except (ValueError, TypeError):
                    pass
        
        # 중복 제거 및 정렬
        return sorted(list(set(pages))) if pages else [0]
    
    @staticmethod
    def estimate_file_size(width: int, height: int, pages: int = 1, 
                          format: str = 'pdf') -> float:
        """
        예상 파일 크기 계산 (MB)
        
        Args:
            width: 페이지 너비 (픽셀)
            height: 페이지 높이 (픽셀)
            pages: 페이지 수
            format: 파일 형식
            
        Returns:
            float: 예상 크기 (MB)
        """
        # 픽셀당 바이트 수 (RGB)
        bytes_per_pixel = 3
        
        # 기본 크기 계산
        base_size = width * height * bytes_per_pixel * pages
        
        # 형식별 압축률 적용
        compression_rates = {
            'pdf': 0.1,  # PDF는 보통 10% 정도로 압축
            'png': 0.5,  # PNG는 50% 정도
            'jpg': 0.15  # JPEG는 15% 정도
        }
        
        rate = compression_rates.get(format, 0.5)
        estimated_size = base_size * rate / (1024 * 1024)  # MB로 변환
        
        return round(estimated_size, 2)
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        파일 크기를 읽기 쉬운 형식으로 변환
        
        Args:
            size_bytes: 바이트 단위 크기
            
        Returns:
            str: 포맷된 크기 문자열
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    @staticmethod
    def get_timestamp_suffix() -> str:
        """
        타임스탬프 기반 접미사 생성
        
        Returns:
            str: YYYYMMDD_HHMMSS 형식의 타임스탬프
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @staticmethod
    def validate_pdf_path(pdf_path: str) -> Tuple[bool, str]:
        """
        PDF 파일 경로 유효성 검증
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            tuple: (유효 여부, 오류 메시지)
        """
        if not pdf_path:
            return False, "파일 경로가 비어있습니다"
        
        path = Path(pdf_path)
        
        if not path.exists():
            return False, f"파일이 존재하지 않습니다: {pdf_path}"
        
        if not path.is_file():
            return False, f"파일이 아닙니다: {pdf_path}"
        
        if path.suffix.lower() != '.pdf':
            return False, f"PDF 파일이 아닙니다: {pdf_path}"
        
        # 파일 크기 확인 (0바이트 파일 방지)
        if path.stat().st_size == 0:
            return False, f"빈 파일입니다: {pdf_path}"
        
        return True, ""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        파일명에서 특수문자 제거
        
        Args:
            filename: 원본 파일명
            
        Returns:
            str: 정리된 파일명
        """
        # Windows에서 금지된 문자들
        invalid_chars = '<>:"|?*\\/\r\n'
        
        sanitized = filename
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # 앞뒤 공백 및 점 제거
        sanitized = sanitized.strip('. ')
        
        # 빈 문자열이면 기본값
        if not sanitized:
            sanitized = "unnamed"
        
        return sanitized