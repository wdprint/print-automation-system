# PDF 인쇄 의뢰서 자동화 시스템 v2

## 📌 프로젝트 소개
한국 인쇄업체를 위한 PDF 자동화 시스템입니다. 의뢰서 PDF에 썸네일과 QR 코드를 자동으로 삽입하여 생산성을 극대화합니다.

## 🚀 주요 기능
- **듀얼 GUI 시스템**
  - 모던 GUI: 폴더 모니터링 기반 자동 처리
  - 클래식 GUI: 드래그앤드롭 수동 처리
- **고화질 썸네일 생성** (DPI 설정 가능)
- **QR 코드 자동 배치**
- **백지 감지 알고리즘** (3가지 방식)
- **프리셋 관리** (F1~F4 단축키)
- **처리 규칙 엔진** (파일명 패턴 인식)
- **2-up 레이아웃 지원** (A4 가로)

## 💻 실행 방법

### GUI 모드 (기본)
```bash
# 모던 GUI (폴더 모니터링)
python main.py

# 클래식 GUI (드래그앤드롭)
python main.py --mode classic
```

### CLI 모드
```bash
# 명령줄에서 직접 처리
python main.py --cli 의뢰서.pdf 데이터.pdf QR.png

# 특정 프리셋 사용
python main.py --cli --preset "A사전용" 의뢰서.pdf
```

### 설정 창
```bash
python main.py --settings
```

## 📁 프로젝트 구조
```
print_automation_system/
├── main.py                 # 메인 진입점
├── gui/                    # GUI 모듈
│   ├── modern_main_window.py    # 모던 GUI (폴더 모니터링)
│   ├── main_window.py           # 클래식 GUI (드래그앤드롭)
│   ├── modern_settings.py       # 설정 창 (탭 구조)
│   └── coordinate_preview.py    # 좌표 미리보기 위젯
├── core/                   # 핵심 처리 모듈
│   ├── pdf_processor.py        # PDF 처리 엔진
│   ├── image_handler.py        # 이미지 생성/처리
│   ├── blank_detector.py       # 백지 감지
│   └── pdf_normalizer.py       # PDF 회전 정규화
├── config/                 # 설정 관리
│   ├── settings_manager.py     # 설정 파일 관리
│   ├── preset_manager.py       # 프리셋 저장/로드
│   └── rules_engine.py         # 처리 규칙
└── utils/                  # 유틸리티
    ├── file_classifier.py       # 파일 타입 분류
    └── logger.py               # 로깅 시스템
```

## 🛠 필요한 라이브러리
```bash
pip install -r requirements.txt
```

주요 의존성:
- `PyMuPDF` (fitz) - PDF 처리
- `Pillow` (PIL) - 이미지 처리
- `tkinterdnd2` - 드래그앤드롭
- `numpy` - 백지 감지 알고리즘

## 📝 사용법

### 1. 모던 GUI (권장)
1. 프로그램 실행 후 작업 폴더 선택
2. 폴더에 파일 추가 시 자동 감지 및 처리
3. 실시간 처리 상태 확인

### 2. 클래식 GUI
1. 프로그램 실행
2. 3개 파일을 드래그앤드롭:
   - **의뢰서 PDF** (파일명에 "의뢰서" 포함)
   - **인쇄 데이터 PDF** (썸네일용, 선택사항)
   - **QR 코드 이미지** (선택사항)
3. 자동 처리 및 저장

### 3. 프리셋 사용
- **F1~F4**: 빠른 프리셋 전환
- 설정 창에서 프리셋 관리
- 고객별 맞춤 설정 저장

## ⚙️ 설정 옵션

### 좌표 설정
- 썸네일 위치/크기 조정
- QR 코드 위치/크기 조정
- 시각적 미리보기 제공
- 드래그로 위치 조정 가능

### 백지 감지
- **Simple**: 흰색 픽셀 비율
- **Entropy**: 정보 엔트로피
- **Histogram**: 히스토그램 분석

### 처리 규칙
- 파일명 패턴 인식
- 조건부 처리 적용
- 우선순위 설정

## 🔨 빌드 방법

### Windows EXE 빌드
```bash
python build.py
```

생성 위치: `dist/print_automation.exe`

## ⚠️ 주의사항
- 원본 의뢰서 PDF가 덮어쓰여집니다
- 처리 전 백업을 권장합니다
- Windows 10/11 환경 최적화

## 🐛 문제 해결

### PDF 회전 문제
- 자동으로 감지 및 정규화됩니다

### 한글 파일명 오류
- UTF-8 인코딩으로 자동 처리됩니다

### 메모리 부족
- 대용량 PDF는 페이지 단위로 처리됩니다

## 📈 성능 최적화
- **멀티스레딩**: 여러 파일 동시 처리
- **캐싱**: 반복 작업 최적화
- **지연 로딩**: 필요시에만 모듈 로드

## 🔄 버전 정보
- **현재 버전**: 2.0.0
- **최종 업데이트**: 2024-01-08

## 👤 개발자
- **GitHub**: [@wdprint](https://github.com/wdprint)
- **Email**: ibm3385@naver.com

## 📄 라이선스
이 프로젝트는 개인 및 상업적 사용이 가능합니다.

---

**문제 발생 시 [이슈](https://github.com/wdprint/print-automation-system/issues)를 등록해주세요.**