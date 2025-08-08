"""성능 최적화 및 모니터링 모듈"""

import time
import sys
import psutil
import threading
from functools import wraps, lru_cache
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional
from datetime import datetime

from .logger import setup_logger

class PerformanceMonitor:
    """성능 모니터링 클래스"""
    
    def __init__(self):
        """성능 모니터 초기화"""
        self.logger = setup_logger(self.__class__.__name__)
        self.stats = {}
        self.start_times = {}
        self.lock = threading.Lock()
    
    @contextmanager
    def measure(self, operation_name: str):
        """
        컨텍스트 매니저로 작업 시간 측정
        
        사용법:
            with monitor.measure("pdf_processing"):
                # 작업 수행
        """
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            memory_used = self._get_memory_usage() - start_memory
            
            with self.lock:
                if operation_name not in self.stats:
                    self.stats[operation_name] = {
                        'count': 0,
                        'total_time': 0,
                        'min_time': float('inf'),
                        'max_time': 0,
                        'avg_time': 0,
                        'total_memory': 0
                    }
                
                stats = self.stats[operation_name]
                stats['count'] += 1
                stats['total_time'] += elapsed
                stats['min_time'] = min(stats['min_time'], elapsed)
                stats['max_time'] = max(stats['max_time'], elapsed)
                stats['avg_time'] = stats['total_time'] / stats['count']
                stats['total_memory'] += memory_used
                
                self.logger.debug(f"{operation_name}: {elapsed:.3f}초, 메모리: {memory_used:.1f}MB")
    
    def _get_memory_usage(self) -> float:
        """현재 프로세스의 메모리 사용량 (MB)"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0
    
    def get_stats(self) -> Dict:
        """성능 통계 반환"""
        with self.lock:
            return self.stats.copy()
    
    def log_stats(self):
        """성능 통계 로깅"""
        stats = self.get_stats()
        
        self.logger.info("=== 성능 통계 ===")
        for operation, data in stats.items():
            self.logger.info(
                f"{operation}: "
                f"횟수={data['count']}, "
                f"평균={data['avg_time']:.3f}초, "
                f"최소={data['min_time']:.3f}초, "
                f"최대={data['max_time']:.3f}초, "
                f"메모리={data['total_memory']:.1f}MB"
            )
    
    def reset(self):
        """통계 초기화"""
        with self.lock:
            self.stats.clear()
            self.start_times.clear()

def cached_result(max_size: int = 128):
    """
    LRU 캐시 데코레이터
    
    Args:
        max_size: 최대 캐시 크기
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @lru_cache(maxsize=max_size)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # 캐시 관련 메서드 추가
        wrapper.cache_info = wrapper.cache_info
        wrapper.cache_clear = wrapper.cache_clear
        
        return wrapper
    return decorator

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    실패 시 재시도 데코레이터
    
    Args:
        max_retries: 최대 재시도 횟수
        delay: 재시도 간 대기 시간 (초)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = setup_logger("retry")
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"{func.__name__} 최종 실패: {e}")
                        raise
                    
                    logger.warning(
                        f"{func.__name__} 시도 {attempt + 1}/{max_retries} 실패: {e}"
                    )
                    time.sleep(delay * (attempt + 1))  # 지수 백오프
            
            return None
        return wrapper
    return decorator

def measure_time(func: Callable) -> Callable:
    """
    함수 실행 시간 측정 데코레이터
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = setup_logger("timing")
        start = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            logger.debug(f"{func.__name__}: {elapsed:.3f}초")
            return result
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"{func.__name__} 실패 ({elapsed:.3f}초): {e}")
            raise
    
    return wrapper

class ProgressTracker:
    """진행 상황 추적기"""
    
    def __init__(self, total: int, callback: Optional[Callable] = None):
        """
        진행 상황 추적기 초기화
        
        Args:
            total: 전체 작업 수
            callback: 진행 상황 콜백 함수
        """
        self.total = total
        self.current = 0
        self.callback = callback
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.logger = setup_logger(self.__class__.__name__)
    
    def update(self, increment: int = 1):
        """진행 상황 업데이트"""
        with self.lock:
            self.current += increment
            progress = (self.current / self.total) * 100 if self.total > 0 else 0
            
            # ETA 계산
            elapsed = time.time() - self.start_time
            if self.current > 0:
                eta = (elapsed / self.current) * (self.total - self.current)
            else:
                eta = 0
            
            # 콜백 호출
            if self.callback:
                self.callback({
                    'current': self.current,
                    'total': self.total,
                    'progress': progress,
                    'elapsed': elapsed,
                    'eta': eta
                })
            
            # 로깅
            self.logger.debug(
                f"진행: {self.current}/{self.total} ({progress:.1f}%), "
                f"경과: {elapsed:.1f}초, ETA: {eta:.1f}초"
            )
    
    def reset(self):
        """진행 상황 초기화"""
        with self.lock:
            self.current = 0
            self.start_time = time.time()

class ResourceMonitor:
    """시스템 리소스 모니터"""
    
    def __init__(self):
        """리소스 모니터 초기화"""
        self.logger = setup_logger(self.__class__.__name__)
    
    def get_system_info(self) -> Dict:
        """시스템 정보 반환"""
        try:
            return {
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': {
                    'total': psutil.virtual_memory().total / (1024**3),  # GB
                    'available': psutil.virtual_memory().available / (1024**3),
                    'percent': psutil.virtual_memory().percent
                },
                'disk': {
                    'total': psutil.disk_usage('/').total / (1024**3),
                    'free': psutil.disk_usage('/').free / (1024**3),
                    'percent': psutil.disk_usage('/').percent
                }
            }
        except Exception as e:
            self.logger.error(f"시스템 정보 수집 실패: {e}")
            return {}
    
    def check_resources(self, min_memory_gb: float = 1.0, 
                       min_disk_gb: float = 2.0) -> bool:
        """
        리소스 가용성 확인
        
        Args:
            min_memory_gb: 최소 필요 메모리 (GB)
            min_disk_gb: 최소 필요 디스크 공간 (GB)
            
        Returns:
            충분한 리소스 여부
        """
        info = self.get_system_info()
        
        if not info:
            return True  # 정보를 얻을 수 없으면 계속 진행
        
        # 메모리 확인
        if info['memory']['available'] < min_memory_gb:
            self.logger.warning(
                f"메모리 부족: {info['memory']['available']:.1f}GB < {min_memory_gb}GB"
            )
            return False
        
        # 디스크 확인
        if info['disk']['free'] < min_disk_gb:
            self.logger.warning(
                f"디스크 공간 부족: {info['disk']['free']:.1f}GB < {min_disk_gb}GB"
            )
            return False
        
        return True
    
    def log_resources(self):
        """현재 리소스 상태 로깅"""
        info = self.get_system_info()
        
        if info:
            self.logger.info(
                f"시스템 리소스 - "
                f"CPU: {info['cpu_percent']}%, "
                f"메모리: {info['memory']['percent']}% "
                f"({info['memory']['available']:.1f}GB 가용), "
                f"디스크: {info['disk']['percent']}% "
                f"({info['disk']['free']:.1f}GB 여유)"
            )

class BatchProcessor:
    """배치 처리 최적화"""
    
    def __init__(self, batch_size: int = 10, max_workers: int = 4):
        """
        배치 처리기 초기화
        
        Args:
            batch_size: 배치 크기
            max_workers: 최대 워커 수
        """
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.logger = setup_logger(self.__class__.__name__)
    
    def process_batch(self, items: list, process_func: Callable,
                     progress_callback: Optional[Callable] = None) -> list:
        """
        배치 단위로 아이템 처리
        
        Args:
            items: 처리할 아이템 목록
            process_func: 처리 함수
            progress_callback: 진행 상황 콜백
            
        Returns:
            처리 결과 목록
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = []
        total = len(items)
        processed = 0
        
        # 진행 상황 추적
        tracker = ProgressTracker(total, progress_callback)
        
        # 배치 처리
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 배치 단위로 작업 제출
            for i in range(0, total, self.batch_size):
                batch = items[i:i + self.batch_size]
                
                # 각 아이템을 병렬 처리
                futures = {
                    executor.submit(process_func, item): item 
                    for item in batch
                }
                
                # 결과 수집
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                        tracker.update()
                    except Exception as e:
                        self.logger.error(f"배치 처리 오류: {e}")
                        results.append(None)
                        tracker.update()
        
        return results