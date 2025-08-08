"""파일 타입 분류 모듈"""

import os
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass

from config.constants import FILE_PATTERNS
from .logger import setup_logger

@dataclass
class ClassifiedFiles:
    """분류된 파일 정보"""
    order_pdf: Optional[str] = None
    print_pdfs: List[str] = None  # 여러 PDF 파일 지원
    qr_image: Optional[str] = None
    unknown_files: List[str] = None
    
    def __post_init__(self):
        if self.unknown_files is None:
            self.unknown_files = []
        if self.print_pdfs is None:
            self.print_pdfs = []
    
    def is_valid(self) -> bool:
        """필수 파일이 모두 있는지 확인"""
        # 의뢰서 PDF만 필수, 썸네일 PDF는 선택사항
        return self.order_pdf is not None
    
    def get_error(self) -> Optional[str]:
        """오류 메시지 반환"""
        if not self.order_pdf:
            return "의뢰서 PDF 파일이 없습니다"
        return None
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'order_pdf': self.order_pdf,
            'print_pdfs': self.print_pdfs,  # 여러 PDF 파일
            'qr_image': self.qr_image,
            'unknown_files': self.unknown_files
        }
    
    # 하위 호환성을 위한 속성
    @property
    def print_pdf(self) -> Optional[str]:
        """첫 번째 인쇄 PDF 반환 (하위 호환성)"""
        return self.print_pdfs[0] if self.print_pdfs else None

class FileClassifier:
    """파일 타입 분류기"""
    
    def __init__(self):
        """파일 분류기 초기화"""
        self.logger = setup_logger(self.__class__.__name__)
        self.patterns = FILE_PATTERNS
    
    def classify(self, files: List[str]) -> ClassifiedFiles:
        """
        파일 목록을 분류
        
        Args:
            files: 파일 경로 리스트
            
        Returns:
            분류된 파일 정보
        """
        result = ClassifiedFiles()
        
        for file_path in files:
            if not file_path:
                continue
                
            # 문자열 정리 (따옴표 제거 등)
            file_path = file_path.strip().strip('"').strip("'")
            
            if not os.path.exists(file_path):
                self.logger.warning(f"파일이 존재하지 않습니다: {file_path}")
                result.unknown_files.append(file_path)
                continue
            
            file_type = self._identify_file_type(file_path)
            
            if file_type == 'order_pdf':
                if result.order_pdf:
                    self.logger.warning(f"의뢰서 PDF가 중복됩니다: {file_path}")
                    result.unknown_files.append(file_path)
                else:
                    result.order_pdf = file_path
                    self.logger.debug(f"의뢰서 PDF로 분류: {file_path}")
                    
            elif file_type == 'print_pdf':
                # 여러 인쇄 PDF 허용
                result.print_pdfs.append(file_path)
                self.logger.debug(f"인쇄 PDF로 분류: {file_path}")
                    
            elif file_type == 'qr_image':
                if result.qr_image:
                    self.logger.warning(f"QR 이미지가 중복됩니다: {file_path}")
                    result.unknown_files.append(file_path)
                else:
                    result.qr_image = file_path
                    self.logger.debug(f"QR 이미지로 분류: {file_path}")
                    
            else:
                result.unknown_files.append(file_path)
                self.logger.debug(f"알 수 없는 파일: {file_path}")
        
        self.logger.info(f"파일 분류 완료 - 의뢰서: {bool(result.order_pdf)}, "
                        f"인쇄 PDF 수: {len(result.print_pdfs)}, QR: {bool(result.qr_image)}")
        
        return result
    
    def _identify_file_type(self, file_path: str) -> Optional[str]:
        """
        파일 타입 식별
        
        Args:
            file_path: 파일 경로
            
        Returns:
            파일 타입 ('order_pdf', 'print_pdf', 'qr_image') 또는 None
        """
        path = Path(file_path)
        filename = path.name.lower()
        extension = path.suffix.lower()
        
        # 의뢰서 PDF 확인
        for pattern in self.patterns['order_pdf']:
            if pattern.lower() in filename and extension == '.pdf':
                return 'order_pdf'
        
        # 이미지 파일 확인
        for pattern in self.patterns['qr_image']:
            if extension == pattern.lower():
                return 'qr_image'
        
        # 나머지 PDF는 인쇄 데이터로 분류
        if extension == '.pdf':
            return 'print_pdf'
        
        return None
    
    def validate_files(self, classified: ClassifiedFiles) -> bool:
        """
        분류된 파일 검증
        
        Args:
            classified: 분류된 파일 정보
            
        Returns:
            유효성 여부
        """
        # 필수 파일 확인 (의뢰서 PDF만 필수)
        if not classified.order_pdf:
            self.logger.error("의뢰서 PDF가 없습니다")
            return False
        
        # 파일 존재 확인
        if not os.path.exists(classified.order_pdf):
            self.logger.error(f"의뢰서 파일이 존재하지 않습니다: {classified.order_pdf}")
            return False
        
        # 여러 인쇄 PDF 파일 확인
        for pdf_path in classified.print_pdfs:
            if not os.path.exists(pdf_path):
                self.logger.error(f"인쇄 파일이 존재하지 않습니다: {pdf_path}")
                return False
        
        if classified.qr_image and not os.path.exists(classified.qr_image):
            self.logger.error(f"QR 이미지가 존재하지 않습니다: {classified.qr_image}")
            return False
        
        # 파일 크기 확인
        if os.path.getsize(classified.order_pdf) == 0:
            self.logger.error("의뢰서 PDF가 비어있습니다")
            return False
        
        # 여러 인쇄 PDF 파일 크기 확인
        for pdf_path in classified.print_pdfs:
            if os.path.getsize(pdf_path) == 0:
                self.logger.error(f"인쇄 PDF가 비어있습니다: {pdf_path}")
                return False
        
        return True
    
    def classify_by_rules(self, files: List[str], rules: Dict) -> ClassifiedFiles:
        """
        규칙 기반 파일 분류
        
        Args:
            files: 파일 경로 리스트
            rules: 분류 규칙
            
        Returns:
            분류된 파일 정보
        """
        # 기본 분류 수행
        result = self.classify(files)
        
        # 규칙 적용
        if rules:
            # 커스텀 규칙 처리
            # 예: 특정 고객사별 파일명 패턴
            pass
        
        return result