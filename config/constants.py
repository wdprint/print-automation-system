"""상수 정의"""

from pathlib import Path

# 버전 정보
VERSION = "2.0.0"
APP_NAME = "PDF 인쇄 의뢰서 자동화 시스템"

# 경로 설정
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RESOURCES_DIR = BASE_DIR / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"
FONTS_DIR = RESOURCES_DIR / "fonts"

# 파일 경로
SETTINGS_FILE = DATA_DIR / "settings.json"
PRESETS_FILE = DATA_DIR / "presets.json"
LOG_FILE = DATA_DIR / "processing_log.json"

# PDF 설정
DEFAULT_PAGE_WIDTH = 842  # A4 가로 (points)
DEFAULT_PAGE_HEIGHT = 595  # A4 가로 (points)
DEFAULT_DPI = 150  # 썸네일 생성 DPI

# 좌표 기본값 (2-up 레이아웃)
DEFAULT_COORDINATES = {
    "page_size": {
        "width": DEFAULT_PAGE_WIDTH,
        "height": DEFAULT_PAGE_HEIGHT
    },
    "thumbnail": {
        "left": {
            "x": 230,
            "y": 234,
            "width": 160,
            "height": 250,
            "rotation": 0,
            "opacity": 1.0
        },
        "right": {
            "x": 658,
            "y": 228,
            "width": 160,
            "height": 250,
            "rotation": 0,
            "opacity": 1.0
        }
    },
    "qr": {
        "left": {
            "x": 315,
            "y": 500,
            "size": 70,
            "rotation": 0
        },
        "right": {
            "x": 730,
            "y": 500,
            "size": 70,
            "rotation": 0
        }
    }
}

# 백지 감지 설정
BLANK_DETECTION_ALGORITHMS = ['simple', 'entropy', 'histogram']
DEFAULT_BLANK_THRESHOLD = 95  # 백지 판정 임계값 (%)

# 성능 설정
DEFAULT_MAX_WORKERS = 4
DEFAULT_CACHE_SIZE_MB = 100

# UI 설정
WINDOW_TITLE = APP_NAME
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
DROP_ZONE_HEIGHT = 300

# 색상 팔레트
COLORS = {
    "primary": "#0066CC",
    "secondary": "#666666",
    "success": "#00AA00",
    "warning": "#FF9900",
    "error": "#CC0000",
    "background": "#F5F5F5",
    "text": "#333333"
}

# 파일 패턴
FILE_PATTERNS = {
    "order_pdf": ["의뢰서", "order", "주문서"],
    "print_pdf": [".pdf"],
    "qr_image": [".png", ".jpg", ".jpeg", ".bmp"]
}

# 메시지
MESSAGES = {
    "drop_zone": "파일 3개를 여기에 드래그하세요\n(의뢰서 PDF, 인쇄 PDF, QR 이미지)",
    "processing": "처리 중...",
    "success": "✅ PDF 처리가 완료되었습니다!",
    "error": "❌ 오류가 발생했습니다: {error}",
    "invalid_files": "올바른 파일을 선택해주세요",
    "file_not_found": "파일을 찾을 수 없습니다",
    "permission_denied": "파일 접근 권한이 없습니다"
}

# 로깅 설정
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"