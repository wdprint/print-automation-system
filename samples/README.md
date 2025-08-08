# 샘플 파일 준비 가이드

이 디렉토리는 프로그램 테스트용 샘플 파일을 위한 공간입니다.

## 📁 필요한 샘플 파일

테스트를 위해 다음 파일들을 준비해주세요:

### 1. 의뢰서 PDF
- **파일명**: `의뢰서_샘플.pdf` (파일명에 "의뢰서" 포함 필수)
- **형식**: 2-up 레이아웃 (A4 가로, 좌/우 2페이지)
- **내용**: 인쇄 의뢰서 양식

### 2. 인쇄 데이터 PDF (선택사항)
- **파일명**: `인쇄데이터_샘플.pdf`
- **용도**: 썸네일 생성용 원본 데이터
- **형식**: 일반 PDF (세로/가로 무관)

### 3. QR 코드 이미지 (선택사항)
- **파일명**: `QR_샘플.png` 또는 `QR_샘플.jpg`
- **크기**: 200x200px 이상 권장
- **내용**: 주문 정보가 담긴 QR 코드

## 🔧 샘플 파일 생성 방법

### 빈 의뢰서 PDF 생성 (PowerShell)
```powershell
# 이 스크립트는 빈 2-up PDF를 생성합니다
# (실제 구현은 프로젝트 utils에 생성 도구 추가 예정)
python -c "from core.pdf_processor import PDFProcessor; PDFProcessor.create_sample_order_pdf('samples/의뢰서_샘플.pdf')"
```

### QR 코드 생성
```python
# Python으로 샘플 QR 코드 생성
import qrcode
qr = qrcode.QRCode(version=1, box_size=10, border=5)
qr.add_data('샘플 주문번호: 2024-001')
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
img.save('QR_샘플.png')
```

## 📝 테스트 방법

1. 위 파일들을 이 디렉토리에 준비
2. 프로그램 실행
3. 파일들을 드래그앤드롭 또는 폴더 모니터링으로 처리
4. 결과 확인

## ⚠️ 주의사항

- 실제 고객 데이터는 이 폴더에 넣지 마세요
- 테스트 후 생성된 파일은 정리해주세요
- 원본 파일은 백업 후 테스트하세요