# PDF 인쇄 의뢰서 자동화 시스템

## 📌 프로젝트 소개
PDF 인쇄 의뢰서에 썸네일과 QR 코드를 자동으로 삽입하는 Python 기반 자동화 도구입니다.

## 🚀 주요 기능
- PDF 파일에 썸네일 이미지 자동 삽입
- QR 코드 자동 배치
- 드래그 앤 드롭 지원 GUI
- 2-up 레이아웃 형식 지원

## 💻 실행 방법

### 기본 버전
```bash
python start.py
```

### 향상된 버전 (권장)
```bash
python start_enhanced.py
```

## 📁 파일 구조
- `print_automation.py` - 기본 GUI 애플리케이션
- `print_automation_enhanced.py` - 향상된 버전 (프리셋, 빈 페이지 감지)
- `settings_gui.py` - 설정 관리 인터페이스
- `normalize_pdf.py` - PDF 회전 정규화

## 🛠 필요한 라이브러리
- PyMuPDF (fitz)
- Pillow (PIL)
- tkinterdnd2
- numpy (향상된 버전)

## 📝 사용법
1. 프로그램 실행
2. 3개 파일을 드래그 앤 드롭:
   - 의뢰서 PDF (파일명에 "의뢰서" 포함)
   - 인쇄용 PDF
   - QR 코드 이미지
3. 자동으로 처리되어 저장됩니다

## ⚠️ 주의사항
- 원본 의뢰서 PDF 파일이 덮어쓰여집니다
- 처리 전 백업을 권장합니다

## 👤 개발자
- GitHub: [@wdprint](https://github.com/wdprint)
- Email: ibm3385@naver.com

## 📄 라이선스
이 프로젝트는 개인 사용 목적으로 개발되었습니다.