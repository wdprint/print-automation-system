"""로깅 시스템 모듈"""

import logging
import colorlog
from pathlib import Path
from datetime import datetime
import json

from config.constants import LOG_FILE, LOG_FORMAT, LOG_DATE_FORMAT

def setup_logger(name: str = None, level: str = 'INFO') -> logging.Logger:
    """
    로거 설정
    
    Args:
        name: 로거 이름
        level: 로그 레벨
        
    Returns:
        설정된 로거
    """
    # 로거 생성
    logger = logging.getLogger(name or 'PDFAutomation')
    
    # 이미 핸들러가 있으면 반환
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # 콘솔 핸들러 (컬러)
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # 컬러 포맷터
    color_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt=LOG_DATE_FORMAT,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    console_handler.setFormatter(color_formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러
    try:
        log_file = Path(LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"로그 파일 생성 실패: {e}")
    
    return logger

class ProcessingLogger:
    """처리 로그 관리"""
    
    def __init__(self):
        """처리 로거 초기화"""
        self.log_file = Path(LOG_FILE).parent / "processing_log.json"
        self.logger = setup_logger(self.__class__.__name__)
        self.current_session = {
            'session_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'start_time': datetime.now().isoformat(),
            'processed_files': [],
            'errors': [],
            'statistics': {
                'total_files': 0,
                'successful': 0,
                'failed': 0,
                'processing_time': 0
            }
        }
    
    def log_file_processed(self, order_pdf: str, print_pdf: str, 
                          qr_image: str, success: bool, error: str = None):
        """
        파일 처리 로그 기록
        
        Args:
            order_pdf: 의뢰서 파일
            print_pdf: 인쇄 파일
            qr_image: QR 이미지
            success: 성공 여부
            error: 오류 메시지
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'order_pdf': order_pdf,
            'print_pdf': print_pdf,
            'qr_image': qr_image,
            'success': success,
            'error': error
        }
        
        self.current_session['processed_files'].append(entry)
        self.current_session['statistics']['total_files'] += 1
        
        if success:
            self.current_session['statistics']['successful'] += 1
        else:
            self.current_session['statistics']['failed'] += 1
            if error:
                self.current_session['errors'].append({
                    'timestamp': datetime.now().isoformat(),
                    'file': order_pdf,
                    'error': error
                })
    
    def save_session(self):
        """세션 로그 저장"""
        try:
            self.current_session['end_time'] = datetime.now().isoformat()
            
            # 기존 로그 로드
            existing_logs = []
            if self.log_file.exists():
                try:
                    with open(self.log_file, 'r', encoding='utf-8') as f:
                        existing_logs = json.load(f)
                except Exception:
                    pass
            
            # 새 세션 추가
            existing_logs.append(self.current_session)
            
            # 최근 100개 세션만 유지
            if len(existing_logs) > 100:
                existing_logs = existing_logs[-100:]
            
            # 저장
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(existing_logs, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"세션 로그 저장 완료: {self.current_session['session_id']}")
            
        except Exception as e:
            self.logger.error(f"세션 로그 저장 실패: {e}")
    
    def get_statistics(self) -> dict:
        """통계 정보 반환"""
        return self.current_session['statistics']
    
    def get_recent_errors(self, count: int = 10) -> list:
        """최근 오류 반환"""
        return self.current_session['errors'][-count:]