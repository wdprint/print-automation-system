# 인쇄 자동화 시스템 설정 파일
# 이미지 삽입 위치와 크기를 조정할 수 있습니다

# A4 용지 크기 (포인트 단위)
PAGE_WIDTH = 595
PAGE_HEIGHT = 842

# 인쇄 자동화 시스템 설정 파일
# 이미지 삽입 위치와 크기를 조정할 수 있습니다

# A4 용지 크기 (포인트 단위)
PAGE_WIDTH = 595
PAGE_HEIGHT = 842

# 인쇄 자동화 시스템 기본 설정 파일
# 
# 주의: 이 파일은 기본값 제공용입니다.
# 실제 설정은 GUI의 "⚙ 설정" 버튼을 통해 변경하시고,
# 변경된 설정은 settings.json 파일에 저장됩니다.
#
# 우선순위: settings.json > config.py > 프로그램 내장 기본값

# 가로형 A4 용지 크기 (포인트 단위)
PAGE_WIDTH = 842
PAGE_HEIGHT = 595

# 썸네일 설정 (인쇄물 이미지)
# 가로형 2-Up 레이아웃 기준
THUMBNAIL_CONFIG = {
    'max_width': 160,      # 썸네일 최대 너비 (세로형 최적화)
    'max_height': 250,     # 썸네일 최대 높이 (세로형 최적화)
    'positions': [
        {
            'x': 230,      # 좌측 X 좌표
            'y': 234       # 좌측 Y 좌표 (적절한 위치로 조정)
        },
        {
            'x': 658,      # 우측 X 좌표
            'y': 228       # 우측 Y 좌표 (적절한 위치로 조정)
        }
    ]
}

# QR 코드 설정
QR_CONFIG = {
    'max_width': 70,       # QR 코드 최대 너비
    'max_height': 70,      # QR 코드 최대 높이
    'positions': [
        {
            'x': 315,      # 좌측 X 좌표 (외주 박스 우측)
            'y': 500       # 좌측 Y 좌표 (하단)
        },
        {
            'x': 730,      # 우측 X 좌표 (외주 박스 우측)
            'y': 500       # 우측 Y 좌표 (하단)
        }
    ]
}

# GUI 설정
GUI_CONFIG = {
    'window_width': 500,
    'window_height': 400,
    'always_on_top': True,
    'resizable': False
}

# 파일 처리 설정
PROCESSING_CONFIG = {
    'overwrite_original': True,    # 원본 파일 덮어쓰기
    'backup_before_save': False,   # 저장 전 백업 생성
    'backup_suffix': '_backup',    # 백업 파일 접미사
    'auto_normalize': True,        # PDF 자동 정규화 (세로형을 가로형으로 변환)
    'rasterize_final': True        # 최종 PDF 래스터화 (품질 유지 + 용량 최적화)
}

# 디버그 모드
DEBUG_MODE = False  # True로 설정하면 상세한 로그 출력

# 좌표 조정 가이드 (가로형 A4 기준):
# - X 좌표: 왼쪽에서 오른쪽으로 증가 (0 ~ 842)
# - Y 좌표: 위에서 아래로 증가 (0 ~ 595)
# - 좌측 의뢰서: X 좌표 0 ~ 421 범위
# - 우측 의뢰서: X 좌표 421 ~ 842 범위