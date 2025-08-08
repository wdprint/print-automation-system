# PDF 인쇄 의뢰서 자동화 시스템 - 완전한 프로젝트 명세서

## ⚡ AI 작업 지침 (필독)

**이 프로젝트는 한국 인쇄업체를 위한 PDF 자동화 시스템입니다.**

작업 전 체크리스트:
- [ ] 전체 프로젝트 구조를 이해했는가?
- [ ] 모든 모듈 간 의존성을 파악했는가?
- [ ] 한국어 사용자 인터페이스가 필수임을 인지했는가?
- [ ] Windows 환경 특화 기능을 고려했는가?
- [ ] 기존 코드와의 일관성을 유지하는가?

## 🎯 프로젝트 개요

### 비즈니스 컨텍스트
- **사용자**: 한국 인쇄업체 직원 (프로그래밍 지식 없음)
- **환경**: Windows 10/11, Python 미설치, AutoHotkey로 자동화
- **목적**: 반복적인 PDF 편집 작업 자동화로 생산성 향상
- **규모**: 일일 100-500개 파일 처리

### 핵심 워크플로우
1. **의뢰서 PDF** (2-up 레이아웃, A4 가로) - 필수
2. **인쇄 데이터 PDF** - 선택사항 (썸네일 생성용)
3. **QR 코드 이미지** - 선택사항 (주문 정보)

처리 방식:
- 모던 GUI: 폴더 모니터링으로 자동 감지 및 처리
- 클래식 GUI: 드래그앤드롭으로 수동 처리
- CLI: 명령줄 인자로 직접 처리

## 📁 완전한 프로젝트 구조

```
print_automation_system/
├── CLAUDE.md                    # 이 파일 (AI 컨텍스트)
├── README.md                     # 사용자 설명서
├── requirements.txt              # 의존성 목록
├── build.py                      # 빌드 스크립트
│
├── main.py                       # 메인 진입점
│
├── gui/                          # GUI 모듈
│   ├── __init__.py
│   ├── modern_main_window.py    # 모던 GUI - 폴더 모니터링 방식
│   ├── modern_settings.py       # 모던 설정 창 (탭 구조)
│   ├── coordinate_preview.py    # 좌표 미리보기 위젯
│   ├── main_window.py           # 클래식 GUI - 드래그앤드롭 방식
│   └── settings_window.py       # 클래식 설정 창
│
├── core/                         # 핵심 처리 모듈
│   ├── __init__.py
│   ├── pdf_processor.py         # PDF 처리 메인 엔진
│   ├── image_handler.py         # 이미지 생성 및 처리
│   ├── blank_detector.py        # 백지 감지 알고리즘
│   └── pdf_normalizer.py        # PDF 회전 정규화
│
├── config/                       # 설정 관리 모듈
│   ├── __init__.py
│   ├── settings_manager.py      # 설정 파일 관리
│   ├── preset_manager.py        # 프리셋 저장/로드
│   ├── rules_engine.py          # 처리 규칙 엔진
│   └── constants.py             # 상수 정의
│
├── utils/                        # 유틸리티 모듈
│   ├── __init__.py
│   ├── file_classifier.py       # 파일 타입 분류
│   ├── logger.py                # 로깅 시스템
│   └── performance.py           # 성능 최적화
│
├── tests/                        # 테스트 모듈
│   ├── __init__.py
│   ├── test_pdf_processor.py
│   ├── test_blank_detector.py
│   └── test_samples/             # 테스트용 샘플 파일
│
├── resources/                    # 리소스 파일
│   ├── icons/                   # 아이콘
│   └── fonts/                   # 폰트 (필요시)
│
├── data/                         # 데이터 파일 (자동 생성)
│   ├── settings.json            # 사용자 설정
│   ├── presets.json             # 저장된 프리셋
│   └── processing_log.json      # 처리 로그
│
├── 썸네일_화질_개선_방안.md      # 화질 개선 문서
│
└── dist/                         # 배포 디렉토리
    ├── print_automation.exe      # 컴파일된 실행 파일
    ├── settings.json            # 기본 설정
    └── autohotkey/
        └── print_automation.ahk  # AutoHotkey 스크립트
```

## 🔧 상세 모듈 명세

### 1. main.py - 진입점
```python
"""
메인 진입점 - 명령줄 인자 처리 및 모드 선택
"""
import argparse
import sys
from gui.modern_main_window import ModernMainWindow
from gui.main_window import MainWindow
from gui.modern_settings import ModernSettingsWindow
from core.pdf_processor import PDFProcessor

def main():
    parser = argparse.ArgumentParser(description='PDF 인쇄 의뢰서 자동화 시스템')
    parser.add_argument('--mode', choices=['modern', 'classic'], default='modern',
                       help='GUI 모드 선택')
    parser.add_argument('--cli', action='store_true', help='CLI 모드 실행')
    parser.add_argument('--settings', action='store_true', help='설정 창 열기')
    parser.add_argument('--preset', type=str, help='사용할 프리셋 이름')
    parser.add_argument('files', nargs='*', help='처리할 파일들')
    
    args = parser.parse_args()
    
    if args.cli:
        # CLI 모드: GUI 없이 처리
        process_cli(args.files, args.preset)
    elif args.settings:
        # 설정 창 열기
        open_settings()
    else:
        # GUI 모드 선택
        if args.mode == 'modern':
            app = ModernMainWindow()
        else:
            app = MainWindow()
        app.run()
```

### 2. core/pdf_processor.py - 핵심 엔진
```python
class PDFProcessor:
    """PDF 처리 핵심 엔진"""
    
    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.image_handler = ImageHandler()
        self.blank_detector = BlankDetector()
        
    def process_files(self, order_pdf: str, print_pdf: str, qr_image: str) -> bool:
        """
        메인 처리 함수
        
        Args:
            order_pdf: 의뢰서 PDF 경로
            print_pdf: 인쇄 데이터 PDF 경로
            qr_image: QR 코드 이미지 경로
            
        Returns:
            bool: 성공 여부
        """
        # 1. 파일 검증
        # 2. PDF 정규화 (회전 수정)
        # 3. 썸네일 생성
        # 4. 각 페이지 처리
        #    - 백지 감지
        #    - 처리 규칙 적용
        #    - 이미지 삽입
        # 5. 저장
```

### 3. core/blank_detector.py - 백지 감지
```python
class BlankDetector:
    """백지 감지 알고리즘 구현"""
    
    ALGORITHMS = {
        'simple': '_detect_simple',      # 흰색 픽셀 비율
        'entropy': '_detect_entropy',    # 정보 엔트로피
        'histogram': '_detect_histogram' # 히스토그램 분석
    }
    
    def is_blank(self, page, algorithm='simple', threshold=95):
        """페이지가 백지인지 판단"""
        method = getattr(self, self.ALGORITHMS[algorithm])
        return method(page, threshold)
```

### 4. config/settings_manager.py - 설정 관리
```python
class SettingsManager:
    """설정 파일 관리 및 접근"""
    
    DEFAULT_SETTINGS = {
        "coordinates": {
            "thumbnail": {
                "left": {"x": 230, "y": 234, "width": 160, "height": 250},
                "right": {"x": 658, "y": 228, "width": 160, "height": 250}
            },
            "qr": {
                "left": {"x": 315, "y": 500, "size": 70},
                "right": {"x": 730, "y": 500, "size": 70}
            }
        },
        "blank_detection": {
            "enabled": False,
            "threshold": 95,
            "algorithm": "simple",
            "exclude_areas": {
                "header": 50,
                "footer": 50,
                "left_margin": 20,
                "right_margin": 20
            }
        },
        "processing_rules": [],
        "performance": {
            "multithreading": True,
            "max_workers": 4,
            "cache_enabled": True,
            "cache_size_mb": 100
        }
    }
    
    def load(self):
        """설정 파일 로드"""
        
    def save(self):
        """설정 파일 저장"""
        
    def get(self, key, default=None):
        """설정 값 가져오기"""
        
    def set(self, key, value):
        """설정 값 저장"""
```

### 5. config/preset_manager.py - 프리셋 관리
```python
class PresetManager:
    """프리셋 관리 - F1~F4 단축키 지원"""
    
    def __init__(self):
        self.presets = self.load_presets()
        self.current_preset = 'default'
        
    def save_preset(self, name: str, settings: dict):
        """현재 설정을 프리셋으로 저장"""
        
    def load_preset(self, name: str) -> dict:
        """프리셋 불러오기"""
        
    def quick_switch(self, index: int):
        """F1~F4 단축키로 빠른 전환"""
        
    def get_usage_stats(self) -> dict:
        """프리셋 사용 통계"""
```

### 6. config/rules_engine.py - 처리 규칙
```python
class RulesEngine:
    """파일명 패턴에 따른 처리 규칙"""
    
    def __init__(self, rules_config):
        self.rules = rules_config
        
    def apply_rules(self, filename: str, processor_config: dict) -> dict:
        """
        파일명에 따라 처리 설정 조정
        
        예시 규칙:
        - "표지" 포함 → QR 코드 제외
        - "급행" 포함 → 우선 처리
        - 특정 고객명 → 전용 프리셋 적용
        """
        modified_config = processor_config.copy()
        
        for rule in self.rules:
            if self._match_pattern(filename, rule['pattern']):
                modified_config = self._apply_action(modified_config, rule['action'])
                
        return modified_config
```

### 7. gui/modern_main_window.py - 모던 GUI
```python
class ModernMainWindow:
    """폴더 모니터링 기반 자동 처리 윈도우"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_modern_ui()
        self.setup_folder_monitoring()
        
    def setup_modern_ui(self):
        """모던 UI 구성"""
        # - 상단: 폴더 선택 영역
        # - 중앙: 파일 목록 (트리뷰)
        # - 하단: 처리 상태 표시
        # - 우측: 빠른 설정 패널
        
    def monitor_folder(self):
        """폴더 변경 감지 및 자동 처리"""
        # 의뢰서 PDF 감지 시 즉시 처리 시작
        # 연관 파일 자동 매칭
        # 실시간 상태 업데이트
```

### 8. gui/main_window.py - 클래식 GUI  
```python
class MainWindow:
    """드래그앤드롭 기반 수동 처리 윈도우"""
    
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.setup_ui()
        self.setup_drag_drop()
        
    def on_drop(self, event):
        """드래그앤드롭 이벤트 처리"""
        files = self.parse_dropped_files(event.data)
        classified = self.classify_files(files)
        
        if self.validate_files(classified):
            self.process_files(classified)
```

### 9. gui/modern_settings.py - 모던 설정 GUI
```python
class SettingsWindow:
    """설정 관리 윈도우 - 탭 구조"""
    
    def __init__(self, parent=None):
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.setup_tabs()
        
    def setup_tabs(self):
        """탭 구성"""
        # Tab 1: 좌표 설정 (시각적 미리보기)
        # Tab 2: 백지 감지 설정
        # Tab 3: 프리셋 관리
        # Tab 4: 처리 규칙
        # Tab 5: 성능 옵션
```

## 💾 데이터 구조

### settings.json - 전체 설정
```json
{
  "version": "2.0",
  "coordinates": {
    "page_size": {"width": 842, "height": 595},
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
  },
  "blank_detection": {
    "enabled": false,
    "threshold": 95,
    "algorithm": "simple",
    "exclude_areas": {
      "header": 50,
      "footer": 50,
      "left_margin": 20,
      "right_margin": 20
    },
    "cache_enabled": true
  },
  "processing_rules": [
    {
      "name": "표지 처리",
      "pattern": "표지|cover",
      "action": {
        "type": "modify_config",
        "changes": {
          "skip_qr": true,
          "thumbnail_opacity": 0.8
        }
      }
    },
    {
      "name": "급행 처리",
      "pattern": "급행|urgent",
      "action": {
        "type": "priority",
        "level": "high"
      }
    }
  ],
  "presets": {
    "default": {
      "name": "기본",
      "description": "표준 설정",
      "hotkey": "F1",
      "coordinates": { /* ... */ },
      "usage_count": 0,
      "last_used": null
    },
    "preset_1": {
      "name": "A사 전용",
      "description": "A사 양식에 최적화",
      "hotkey": "F2",
      "coordinates": { /* ... */ },
      "usage_count": 0,
      "last_used": null
    }
  },
  "performance": {
    "multithreading": true,
    "max_workers": 4,
    "cache_enabled": true,
    "cache_size_mb": 100,
    "log_level": "INFO"
  },
  "ui": {
    "language": "ko",
    "theme": "default",
    "window_always_on_top": true,
    "show_tooltips": true,
    "confirm_before_process": false
  }
}
```

## 📊 현재 구현 상태

### 완료된 기능
- ✅ 모던 GUI (폴더 모니터링)
- ✅ 클래식 GUI (드래그앤드롭)
- ✅ PDF 처리 엔진
- ✅ 썸네일 생성 (고화질)
- ✅ QR 코드 삽입
- ✅ 좌표 미리보기 (드래그 앤 드롭 크기 조정 포함)
- ✅ 프리셋 관리 (사용자 정의 이름 및 핫키)
- ✅ 설정 저장/로드
- ✅ 확대된 미리보기 창 (1400x800)
- ✅ 좌표 설정 저장 버튼
- ✅ 사용자 정의 핫키 입력 (다양한 키 조합 지원)

### 개발 중
- ⏳ 백지 감지 알고리즘
- ⏳ 처리 규칙 엔진
- ⏳ AutoHotkey 통합
- ⏳ 성능 최적화

## 🚀 AutoHotkey 통합 (예정)

### print_automation.ahk
```autohotkey
#NoEnv
#SingleInstance Force
SetWorkingDir %A_ScriptDir%

; 전역 변수
global ProcessQueue := []
global CurrentSet := {}

; F3: 선택된 파일 처리
F3::
{
    files := GetSelectedFiles()
    if (files.Count() < 2) {
        MsgBox, 최소 2개 파일을 선택하세요
        return
    }
    
    ; 파일 분류
    order_pdf := ""
    print_pdf := ""
    qr_image := ""
    
    for index, file in files {
        if (InStr(file, "의뢰서") && EndsWith(file, ".pdf"))
            order_pdf := file
        else if (EndsWith(file, ".pdf"))
            print_pdf := file
        else if (EndsWith(file, ".png") || EndsWith(file, ".jpg"))
            qr_image := file
    }
    
    ; CLI 모드로 실행
    cmd := "print_automation.exe --cli"
    if (order_pdf)
        cmd .= " """ . order_pdf . """"
    if (print_pdf)
        cmd .= " """ . print_pdf . """"
    if (qr_image)
        cmd .= " """ . qr_image . """"
    
    RunWait, %cmd%, , Hide
    
    ; 완료 알림
    SoundBeep, 800, 200
    TrayTip, 완료, PDF 처리가 완료되었습니다, 3
}

; Ctrl+F3: 설정 열기
^F3::
{
    Run, print_automation.exe --settings
}

; Shift+F3: GUI 모드 실행
+F3::
{
    Run, print_automation.exe
}

; F1-F4: 프리셋 전환
F1::SwitchPreset(1)
F2::SwitchPreset(2)
F3::SwitchPreset(3)
F4::SwitchPreset(4)

SwitchPreset(index) {
    ; 프리셋 전환 명령
    Run, print_automation.exe --preset %index%, , Hide
}
```

## 💡 주요 기능 특징

### 1. 듀얼 GUI 시스템
- **모던 GUI**: 폴더 모니터링, 자동 처리, 실시간 상태 표시
- **클래식 GUI**: 드래그앤드롭, 수동 처리, 간단한 인터페이스

### 2. 고화질 썸네일 생성
- DPI 설정 가능 (기본 300)
- 안티앨리어싱 적용
- 캐싱으로 성능 최적화

### 3. 유연한 파일 처리
- 의뢰서 PDF만으로도 처리 가능
- 썸네일/QR 선택적 적용
- 자동 파일 분류

## 🧪 테스트 케이스

### 1. 기본 동작 테스트
- [ ] 드래그앤드롭으로 3개 파일 처리
- [ ] CLI 모드로 파일 처리
- [ ] 설정 변경 후 적용 확인

### 2. 엣지 케이스
- [ ] 회전된 PDF 처리
- [ ] 한글 파일명 처리
- [ ] 대용량 PDF (100페이지 이상)
- [ ] 손상된 PDF 파일

### 3. 백지 감지 테스트
- [ ] 완전 백지 페이지
- [ ] 헤더/푸터만 있는 페이지
- [ ] 워터마크만 있는 페이지

### 4. 프리셋 테스트
- [ ] F1-F4 단축키 동작
- [ ] 프리셋 저장/불러오기
- [ ] 사용 통계 기록

### 5. 처리 규칙 테스트
- [ ] 파일명 패턴 매칭
- [ ] 조건부 처리 적용
- [ ] 우선순위 처리

## 🐛 알려진 이슈 및 해결 방법

### 1. PDF 회전 문제
**문제**: 일부 PDF가 내부적으로 회전되어 있어 좌표가 맞지 않음
**해결**: pdf_normalizer.py에서 자동 감지 및 정규화

### 2. 한글 인코딩
**문제**: 파일 경로에 한글 포함 시 오류
**해결**: 모든 파일 작업에 UTF-8 인코딩 명시

### 3. 메모리 누수
**문제**: 대량 파일 처리 시 메모리 증가
**해결**: 각 파일 처리 후 명시적 가비지 컬렉션

## 📈 성능 최적화 전략

1. **멀티스레딩**: 여러 파일 동시 처리
2. **캐싱**: 반복되는 썸네일 생성 결과 캐싱
3. **지연 로딩**: 필요한 모듈만 import
4. **메모리 관리**: 큰 PDF는 페이지 단위로 처리

## 🎨 UI/UX 가이드라인

### 디자인 원칙
1. **단순함**: 핵심 기능만 노출
2. **명확함**: 모든 메시지 한국어로 명확하게
3. **일관성**: 동일한 작업은 동일한 방식으로
4. **피드백**: 모든 작업에 시각적/청각적 피드백

### 색상 팔레트
- 주 색상: #0066CC (파란색)
- 보조 색상: #666666 (회색)
- 성공: #00AA00 (녹색)
- 경고: #FF9900 (주황색)
- 오류: #CC0000 (빨간색)

### 메시지 톤
- 친근하고 명확한 한국어
- 기술 용어 최소화
- 구체적인 해결 방법 제시

## 🔐 보안 고려사항

1. **파일 검증**: 악성 PDF 감지
2. **경로 검증**: 경로 탐색 공격 방지
3. **권한 관리**: 필요 최소 권한으로 실행
4. **로깅**: 모든 처리 기록 보관

## 📦 빌드 및 배포

### 개발 환경 설정
```bash
# 가상환경 생성
python -m venv venv
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 개발 모드 실행 (모던 GUI)
python main.py

# 클래식 GUI 실행
python main.py --mode classic

# CLI 모드 실행
python main.py --cli 의뢰서.pdf 데이터.pdf QR.png
```

### EXE 빌드
```python
# build.py
import PyInstaller.__main__

PyInstaller.__main__.run([
    'main.py',
    '--name=print_automation',
    '--onefile',
    '--windowed',
    '--icon=resources/icons/app.ico',
    '--add-data=resources;resources',
    '--add-data=data;data',
    '--hidden-import=tkinterdnd2',
    '--hidden-import=PIL._tkinter_finder',
    '--clean'
])
```

### 배포 패키지 구조
```
print_automation_installer.zip
├── print_automation.exe
├── settings.json (기본 설정)
├── autohotkey/
│   ├── print_automation.ahk
│   └── 설치_안내.txt
└── README.pdf (사용 설명서)
```

## 🔄 버전 관리

### 버전 규칙
- Major.Minor.Patch (예: 2.1.0)
- Major: 대규모 변경
- Minor: 기능 추가
- Patch: 버그 수정

### 변경 로그 형식
```markdown
## [2.1.0] - 2024-01-15
### 추가
- 백지 감지 알고리즘 3종 추가
- F1-F4 프리셋 단축키 지원

### 변경
- 설정 GUI를 탭 구조로 개선
- 처리 속도 30% 향상

### 수정
- PDF 회전 문제 해결
- 한글 파일명 인코딩 오류 수정
```

## 📝 개발 시 주의사항

1. **모든 함수에 타입 힌트 사용**
```python
def process_files(order_pdf: str, print_pdf: str, qr_image: str) -> bool:
```

2. **명확한 docstring 작성**
```python
"""
함수 설명

Args:
    param1: 설명
    param2: 설명

Returns:
    반환값 설명

Raises:
    예외 설명
"""
```

3. **에러 처리 패턴**
```python
try:
    # 작업 수행
except SpecificError as e:
    logger.error(f"구체적 오류: {e}")
    # 복구 시도
except Exception as e:
    logger.critical(f"예상치 못한 오류: {e}")
    # 안전한 종료
```

4. **설정 접근 패턴**
```python
# 직접 접근 금지
# BAD: settings['coordinates']['thumbnail']['left']['x']

# 안전한 접근
# GOOD: settings_manager.get('coordinates.thumbnail.left.x', default=0)
```

## 🎯 최종 체크리스트

개발 완료 전 확인:
- [ ] 모든 메시지 한국어화
- [ ] 예외 처리 완벽
- [ ] 로깅 구현
- [ ] 테스트 케이스 통과
- [ ] AutoHotkey 연동 테스트
- [ ] 메모리 누수 검사
- [ ] 대용량 파일 테스트
- [ ] 사용자 매뉴얼 작성
- [ ] 빌드 및 배포 테스트

---

## 📞 지원 정보

프로젝트 관련 정보:
- 개발자: wdprint
- 이메일: ibm3385@naver.com
- GitHub: https://github.com/wdprint/print-automation-system

---

**이 문서는 프로젝트의 현재 상태와 향후 계획을 담고 있습니다.**
**새로운 기능 추가 시 이 문서를 업데이트하여 일관성을 유지하세요.**