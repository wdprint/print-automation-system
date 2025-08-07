# PDF 인쇄 의뢰서 자동화 시스템 - 문제 해결 컨텍스트

## 🎯 프로젝트 개요
Python 기반 PDF 처리 프로그램으로, 인쇄 의뢰서 PDF에 썸네일과 QR 코드를 자동으로 삽입하는 시스템입니다.

### 주요 기능
1. 의뢰서 PDF (2-up 레이아웃)에 인쇄물 썸네일 삽입
2. QR 코드 이미지 삽입
3. 드래그 앤 드롭 인터페이스
4. 자동 PDF 정규화 (세로형 → 가로형 변환)

### 기술 스택
- Python 3.13
- PyMuPDF (fitz) - PDF 처리
- PIL (Pillow) - 이미지 처리
- tkinterdnd2 - 드래그 앤 드롭
- Tkinter - GUI

## 🔴 현재 핵심 문제

### 1. **90도 회전된 PDF 처리 오류**
- **증상**: 원본 내용이 좌측 상단으로 축소되고 일부가 잘림
- **원인**: 일러스트레이터에서 생성된 PDF가 내부적으로는 세로형이지만 90도 회전 속성으로 가로로 표시됨
- **파일 예시**: 이진성작업의뢰서25년7월.pdf

### 2. **좌표 시스템 불일치**
- PDF 내부 좌표계와 표시 좌표계가 다름
- rotation=90인 경우 width와 height가 바뀌어야 하는데 제대로 처리되지 않음

## 📋 시도한 해결 방법들

### 1. **강제 A4 정규화 (실패)**
```python
# 모든 PDF를 A4 크기로 강제 변환
# 문제: 원본이 이미 A4인데 축소됨
```

### 2. **A4 백지 위에 배치 (부분 실패)**
```python
def normalize_pdf_to_landscape(self, input_path):
    # A4 백지 생성 후 원본 페이지 올리기
    # 문제: 회전된 PDF의 경우 여전히 크기/위치 오류
```

### 3. **회전 처리 로직**
```python
if rotation == 90:
    new_page.show_pdf_page(new_page.rect, doc, page_num, rotate=-90)
elif rotation == 270:
    new_page.show_pdf_page(new_page.rect, doc, page_num, rotate=90)
```

## 🔍 문제 상세 분석

### PDF 속성 예시
```
원본 페이지: 595.0x842.0 (세로형)
회전: 90도
MediaBox: 동일
실제 표시: 842x595 (가로형으로 보임)
```

### 현재 동작
1. 90도 회전된 PDF를 열면
2. A4 백지(842x595) 생성
3. `show_pdf_page()`로 원본 페이지 배치
4. **문제**: 페이지가 축소되고 잘림

### 예상 원인
- `show_pdf_page()`의 타겟 rect가 소스 페이지 크기와 맞지 않음
- 회전 변환 시 크기 계산 오류
- PyMuPDF의 회전 처리 방식 이해 부족

## 💡 검토 필요 사항

### 1. **PyMuPDF 회전 처리**
- `page.rotation`과 `rotate` 파라미터의 상호작용
- `show_pdf_page()`에서 rect 크기 자동 조정 여부
- MediaBox vs CropBox 처리

### 2. **좌표 변환 매트릭스**
```python
# 현재는 단순 rotate만 사용
# Matrix 변환이 필요할 수도?
mat = fitz.Matrix(1, 0, 0, 1, 0, 0)  # 기본
mat.prerotate(90)  # 회전 적용
```

### 3. **대안 접근법**
- PDF를 이미지로 변환 후 재구성
- 다른 PDF 라이브러리 (PyPDF2, pdfrw) 검토
- 페이지 내용을 xobject로 추출 후 재배치

## 📁 관련 파일 구조
```
print_automation.py  # 메인 처리 로직
config.py           # 설정 파일
settings_gui.py     # 설정 GUI
start.py           # 시작 스크립트
```

## 🎯 목표
1. 90도 회전된 PDF가 축소/잘림 없이 정상 처리
2. 모든 PDF가 A4 크기로 통일
3. 썸네일/QR 위치 정확성 유지

## 📊 테스트 케이스
1. **정상 가로형 PDF**: ✅ 작동
2. **세로형 PDF**: ✅ 작동 
3. **90도 회전 PDF**: ❌ 축소/잘림
4. **270도 회전 PDF**: ❌ 테스트 필요

## 🔧 현재 코드 핵심 부분

### normalize_pdf_to_landscape 메서드
```python
# 흰색 A4 가로형 페이지 생성
new_page = new_doc.new_page(width=A4_LANDSCAPE_WIDTH, height=A4_LANDSCAPE_HEIGHT)

# 회전된 페이지 처리
if rotation == 90:
    new_page.show_pdf_page(new_page.rect, doc, page_num, rotate=-90)
```

### 문제가 되는 부분
- `new_page.rect`를 그대로 사용 (842x595)
- 원본 페이지가 595x842인데 회전 후에도 크기 조정 없음
- 결과적으로 내용이 축소됨

## 🚀 다음 단계 제안

1. **정확한 크기 계산**
   - 회전된 페이지의 실제 표시 크기 계산
   - 타겟 rect를 소스 크기에 맞게 조정

2. **디버그 정보 강화**
   - 변환 전후 크기 비교
   - Matrix 변환 상세 로그

3. **대체 라이브러리 테스트**
   - pdf2image + PIL 조합
   - PyPDF2의 페이지 병합 기능

## 📝 추가 정보
- 이미지 품질 문제는 PDF 직접 삽입 방식으로 개선됨
- 최종 래스터화 옵션으로 파일 크기 최적화 가능
- 표지 파일의 경우 오른쪽 50% 크롭 기능 구현

## ❓ 핵심 질문
1. PyMuPDF에서 회전된 페이지를 A4 크기에 맞게 배치하는 올바른 방법은?
2. `show_pdf_page()`의 rect 파라미터가 자동으로 스케일링되는가?
3. 회전 변환 시 종횡비를 유지하면서 크기를 조정하는 방법은?

---

이 문서는 새로운 Claude 세션에서 문제 해결을 계속하기 위한 컨텍스트입니다.
현재까지의 시도와 남은 문제점을 정리했습니다.