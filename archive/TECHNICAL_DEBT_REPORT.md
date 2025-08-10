# 🔍 기술 부채 분석 보고서

## 📊 현재 상태 요약

### 프로젝트 규모
- 총 파일 수: 약 150개+
- 핵심 코드: ~10개 모듈
- 테스트/임시 파일: ~50개+
- 중복/백업 파일: ~10개

## 🚨 주요 기술 부채 (우선순위 순)

### 1. 🔴 긴급 - 파일 구조 혼란
**문제점:**
- 루트 디렉토리에 15개 이상의 테스트 파일 산재
- 테스트 출력 디렉토리 4개가 정리되지 않음
- 임시 PDF/이미지 파일들이 프로젝트 루트에 방치

**영향:**
- 프로젝트 구조 파악 어려움
- 실제 코드와 테스트 코드 구분 불명확
- 버전 관리 복잡도 증가

**해결 방안:**
```
# 제안하는 구조
tests/
  ├── integration/     # 통합 테스트
  ├── unit/           # 단위 테스트
  └── fixtures/       # 테스트용 샘플 파일
temp/                 # 임시 파일 (gitignore)
output/              # 테스트 출력 (gitignore)
```

### 2. 🔴 긴급 - 코어 모듈 중복
**문제점:**
```
core/
  ├── pdf_normalizer.py          (메인 - 15,759 bytes)
  ├── pdf_normalizer_backup.py   (빈 파일 - 90 bytes)
  ├── pdf_normalizer_improved.py (미사용 - 11,105 bytes)
  ├── pdf_normalizer_original.py (미사용 - 11,515 bytes)
  
  ├── pdf_processor.py           (메인 - 32,883 bytes)
  ├── pdf_hybrid_processor.py    (서브 - 19,011 bytes)
  ├── pdf_vector_processor.py    (서브 - 18,889 bytes)
```

**영향:**
- 어떤 코드가 실제 사용되는지 불명확
- 유지보수 시 혼란
- 불필요한 코드 로딩

**해결 방안:**
- 백업/원본 파일들을 archive/ 폴더로 이동 또는 삭제
- 실제 사용되는 모듈만 core/에 유지

### 3. 🟡 중요 - 처리 모드의 복잡성
**문제점:**
- 4가지 처리 모드 (optimized, vector, hybrid, raster)가 분산되어 구현
- PDFProcessor가 3개의 다른 프로세서를 관리
- 각 프로세서 간 코드 중복 존재

**영향:**
- 유지보수 어려움
- 버그 수정 시 여러 곳 수정 필요
- 테스트 복잡도 증가

**해결 방안:**
```python
# 전략 패턴으로 통합
class PDFProcessor:
    def __init__(self):
        self.strategies = {
            'optimized': OptimizedStrategy(),
            'vector': VectorStrategy(),
            'hybrid': HybridStrategy(),
            'raster': RasterStrategy()
        }
```

### 4. 🟡 중요 - 테스트 코드 정리 필요
**루트에 있는 테스트 파일들:**
```
test_dpi_integration.py
test_final_hq_thumbnail.py
test_final_integration.py
test_high_quality_thumbnail.py
test_improved_thumbnail.py
test_optimized_mode.py
test_pdf_to_jpg_resolution.py
test_pdf_vector_insert.py
test_thumbnail_only.py
test_thumbnail_quality.py
test_vector_improved.py
test_vector_integration.py
test_white_background.py
vector_processor_integration.py
verify_rotation_fix.py
```

**해결 방안:**
- tests/ 디렉토리로 이동
- 중복 테스트 통합
- pytest 구조로 정리

### 5. 🟢 보통 - 설정 파일 중복
**문제점:**
- settings.json, settings.example.json, .claude/settings.local.json
- 설정 관리 로직이 여러 곳에 분산

**해결 방안:**
- 단일 설정 관리 체계 구축
- 환경별 설정 분리 (dev/prod)

### 6. 🟢 보통 - 임시 파일 관리
**루트의 임시 PDF들:**
```
coordinate_test.pdf
final_test_normal.pdf
final_test_rotated.pdf
method1_rotate_param.pdf
method2_copy_rotate.pdf
method3_scaled.pdf
test_rotation_fixed.pdf
test_vector_final.pdf
```

**해결 방안:**
- samples/ 또는 tests/fixtures/로 이동
- 필요없는 파일 삭제

## 📈 리팩토링 로드맵

### Phase 1: 즉시 정리 (1일)
1. ✅ 테스트 파일들을 tests/ 디렉토리로 이동
2. ✅ 임시 PDF/이미지 파일 정리
3. ✅ 백업/원본 파일 삭제 또는 아카이빙
4. ✅ .gitignore 업데이트

### Phase 2: 구조 개선 (2-3일)
1. ✅ 코어 모듈 통합 (전략 패턴 적용)
2. ✅ 테스트 코드 정리 및 pytest 구조화
3. ✅ 설정 관리 체계 단일화

### Phase 3: 최적화 (1주)
1. ✅ 중복 코드 제거
2. ✅ 성능 병목 지점 개선
3. ✅ 문서화 강화

## 📊 정리 대상 파일 목록

### 삭제 가능
```
core/pdf_normalizer_backup.py    # 빈 파일
core/pdf_normalizer_improved.py  # 미사용
core/pdf_normalizer_original.py  # 미사용
test_render_*.png                # 임시 테스트 이미지
```

### 이동 필요
```
test_*.py → tests/
verify_*.py → tests/
vector_*.py → tests/
*.pdf (테스트용) → tests/fixtures/
test_output*/ → temp/ 또는 삭제
comparison_output/ → temp/ 또는 삭제
thumbnail_test_output/ → temp/ 또는 삭제
```

### 통합 필요
```
pdf_processor.py + pdf_hybrid_processor.py + pdf_vector_processor.py
→ pdf_processor.py (전략 패턴)
```

## 💰 예상 효과

1. **코드 가독성**: 70% 향상
2. **유지보수성**: 60% 향상
3. **파일 수**: 50% 감소
4. **중복 코드**: 40% 감소
5. **테스트 실행 시간**: 30% 단축

## 🎯 우선순위 매트릭스

| 작업 | 긴급도 | 중요도 | 예상 시간 | ROI |
|-----|--------|--------|-----------|-----|
| 파일 구조 정리 | 높음 | 높음 | 2시간 | 매우 높음 |
| 테스트 파일 이동 | 높음 | 중간 | 1시간 | 높음 |
| 백업 파일 삭제 | 높음 | 낮음 | 30분 | 높음 |
| 코어 모듈 통합 | 중간 | 높음 | 1일 | 중간 |
| 설정 파일 정리 | 낮음 | 중간 | 2시간 | 낮음 |

## 🔧 즉시 실행 가능한 작업

```bash
# 1. 테스트 디렉토리 구조 생성
mkdir -p tests/integration tests/unit tests/fixtures

# 2. 테스트 파일 이동
mv test_*.py tests/
mv verify_*.py tests/
mv vector_processor_integration.py tests/

# 3. 임시 디렉토리 정리
mkdir -p temp
mv test_output* temp/
mv comparison_output temp/
mv thumbnail_test_output temp/

# 4. 테스트용 PDF 이동
mkdir -p tests/fixtures
mv *test*.pdf tests/fixtures/
mv method*.pdf tests/fixtures/

# 5. 백업 파일 삭제
rm core/pdf_normalizer_backup.py
rm core/pdf_normalizer_improved.py
rm core/pdf_normalizer_original.py

# 6. .gitignore 업데이트
echo "temp/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore
```

---

작성일: 2025-08-09
작성자: Claude Code Assistant