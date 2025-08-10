# 📊 테스트 파일 분석 및 정리 계획

## 🔍 현재 테스트 파일 구조

### 📁 tests/unit/ (9개 파일)
| 파일명 | 목적 | 중복도 | 필요성 | 조치 |
|--------|------|--------|--------|------|
| test_thumbnail_quality.py | 썸네일 품질 테스트 | 🔴 높음 | 낮음 | archive |
| test_thumbnail_only.py | 썸네일 생성 테스트 | 🔴 높음 | 낮음 | archive |
| test_improved_thumbnail.py | 개선된 썸네일 테스트 | 🔴 높음 | 낮음 | archive |
| test_high_quality_thumbnail.py | 고품질 썸네일 테스트 | 🔴 높음 | 낮음 | archive |
| test_pdf_to_jpg_resolution.py | PDF→JPG 해상도 테스트 | 🟡 중간 | 중간 | archive |
| test_optimized_mode.py | 최적화 모드 테스트 | 🟢 낮음 | 높음 | **유지** |
| test_white_background.py | 흰 배경 처리 테스트 | 🟢 낮음 | 높음 | **유지** |
| test_pdf_vector_insert.py | 벡터 삽입 테스트 | 🟡 중간 | 중간 | archive |
| test_vector_improved.py | 벡터 개선 테스트 | 🟡 중간 | 낮음 | archive |

### 📁 tests/integration/ (6개 파일)
| 파일명 | 목적 | 중복도 | 필요성 | 조치 |
|--------|------|--------|--------|------|
| test_dpi_integration.py | DPI 설정 통합 테스트 | 🟢 낮음 | 높음 | **유지** |
| test_final_integration.py | 최종 통합 테스트 | 🟢 낮음 | 높음 | **유지** |
| test_final_hq_thumbnail.py | 최종 고품질 썸네일 | 🔴 높음 | 낮음 | archive |
| test_vector_integration.py | 벡터 통합 테스트 | 🟡 중간 | 중간 | archive |
| vector_processor_integration.py | 벡터 프로세서 통합 | 🟡 중간 | 낮음 | archive |
| verify_rotation_fix.py | 회전 수정 검증 | 🟢 낮음 | 높음 | **유지** |

### 📁 tests/ (루트, 8개 파일)
| 파일명 | 목적 | 중복도 | 필요성 | 조치 |
|--------|------|--------|--------|------|
| test_multiple_pdfs.py | 다중 PDF 처리 테스트 | 🟢 낮음 | 높음 | **유지** |
| test_normalizer.py | PDF 정규화 테스트 | 🟢 낮음 | 높음 | **유지** |
| test_rotation_integration.py | 회전 통합 테스트 | 🟡 중간 | 중간 | integration/ 이동 |
| test_rotation_detail.py | 회전 상세 테스트 | 🔴 높음 | 낮음 | archive |
| test_preset_fix.py | 프리셋 수정 테스트 | 🟡 중간 | 중간 | archive |
| test_preset_preview.py | 프리셋 미리보기 테스트 | 🟡 중간 | 낮음 | archive |
| test_realtime_update.py | 실시간 업데이트 테스트 | 🟡 중간 | 낮음 | archive |
| test_improvements.py | 개선사항 테스트 | 🔴 높음 | 낮음 | archive |

## 📈 분석 결과

### 중복 패턴 발견
1. **썸네일 테스트 4개**: 거의 동일한 기능을 반복 테스트
   - test_thumbnail_quality.py
   - test_thumbnail_only.py
   - test_improved_thumbnail.py
   - test_high_quality_thumbnail.py
   → **1개로 통합 가능**

2. **벡터 테스트 3개**: 유사한 벡터 처리 테스트
   - test_pdf_vector_insert.py
   - test_vector_improved.py
   - test_vector_integration.py
   → **1개로 통합 가능**

3. **회전 테스트 2개**: 중복된 회전 테스트
   - test_rotation_integration.py
   - test_rotation_detail.py
   → **1개로 통합 가능**

## 🎯 정리 계획

### 1단계: archive 디렉토리 생성
```
archive/
├── tests/           # 보관용 테스트
├── experimental/    # 실험적 코드
└── deprecated/      # 더 이상 사용 안 함
```

### 2단계: 핵심 테스트만 유지
```
tests/
├── unit/
│   ├── test_optimized_mode.py     ✅
│   └── test_white_background.py   ✅
├── integration/
│   ├── test_dpi_integration.py    ✅
│   ├── test_final_integration.py  ✅
│   ├── test_rotation_integration.py ✅
│   └── verify_rotation_fix.py     ✅
├── test_multiple_pdfs.py          ✅
└── test_normalizer.py             ✅
```

### 3단계: 통합 테스트 생성
```python
# tests/test_thumbnail.py (통합)
- 모든 썸네일 관련 테스트 통합

# tests/test_vector.py (통합)
- 모든 벡터 관련 테스트 통합
```

## 📊 예상 효과

| 항목 | 현재 | 정리 후 | 감소율 |
|------|------|---------|--------|
| 테스트 파일 수 | 23개 | 8개 | -65% |
| 중복 코드 | ~40% | ~5% | -87% |
| 테스트 실행 시간 | ~5분 | ~2분 | -60% |
| 유지보수 부담 | 높음 | 낮음 | -70% |

## 🔄 실행 순서

1. **archive 디렉토리 생성**
2. **중복/불필요 테스트 이동**
3. **핵심 테스트 정리**
4. **통합 테스트 작성**
5. **pytest 구조 적용**

## ⚠️ 주의사항

- 하드코딩된 경로 제거 필요 (예: `c:\Users\dltjd\...`)
- 실제 파일 의존성 제거 (테스트용 픽스처 사용)
- 각 테스트가 독립적으로 실행 가능하도록 수정