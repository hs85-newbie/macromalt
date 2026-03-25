# Phase 23 — Cost 고도화 보고서

> 작성일: 2026-03-25 | 브랜치: dev | 상태: 구현 완료

---

## 1. 설계 범위

### 목표
API 호출 비용 추적의 정확도 향상 및 캐시 절감 실적 가시화

### 범위 결정 근거
| 항목 | 결정 | 이유 |
|------|------|------|
| OpenAI cached_tokens | ✅ 구현 | 자동 캐싱 활성화 — 즉시 절감 효과 |
| Gemini usage_metadata | 이미 구현됨 | Phase 20에서 완전히 수집 중 |
| Gemini Context Cache API | 미구현 | 32K+ 토큰 요건 미충족, 별도 설정 필요 |

---

## 2. 구현 내역

### 2-1. cost_tracker.py

#### 요금표 추가
```python
OPENAI_CACHED_INPUT_PRICE_PER_M = 0.625  # USD / 1M (일반 입력 대비 75% 할인)
```

#### `_init_month()` — 신규 필드 추가
```python
"cached_input_tokens": 0,   # 캐시 히트 토큰 누적
"cache_savings_usd": 0.0,   # 캐시 절감액 누적
```

#### `record_openai_usage()` — cached_tokens 파라미터 추가
- 비용 계산 공식 변경:
  ```
  이전: cost = input × $2.50/M + output × $10.00/M
  이후: cost = (input - cached) × $2.50/M + cached × $0.625/M + output × $10.00/M
  ```
- 절감액 계산: `cached × ($2.50 - $0.625) / M`
- 호출 로그에 캐시 히트 시 절감액 표시

#### `print_monthly_summary()` — 캐시 실적 표시 추가
```
🤖 OpenAI GPT-4o
   입력 토큰 : 120,000  (캐시 히트: 85,000 / 70.8%)
   캐시 절감 : $0.1594  (₩220)
```

### 2-2. generator.py — `_call_gpt()` 캐시 토큰 추출

```python
_cached = 0
try:
    _cached = response.usage.prompt_tokens_details.cached_tokens or 0
except AttributeError:
    pass
cost_tracker.record_openai_usage(..., cached_tokens=_cached)
```

- `prompt_tokens_details` 미지원 SDK 버전 대비 `AttributeError` 방어 처리

---

## 3. 예상 절감 효과

GPT 시스템 프롬프트(`GPT_WRITER_ANALYSIS_SYSTEM` 등) 길이 약 3,000~4,000토큰.
OpenAI 자동 캐싱 조건(1,024토큰 이상) 충족 → **캐시 히트 시 입력 비용 75% 절감**.

| 시나리오 | 캐시 히트율 | 월간 GPT 비용 | 절감액 |
|---------|-----------|-------------|------|
| 캐시 없음 (이전) | 0% | ~$49 | - |
| 캐시 히트 70% | 70% | ~$42 | ~$7 |
| 캐시 히트 85% | 85% | ~$39 | ~$10 |

캐시 히트율은 실제 운영 후 `print_monthly_summary()` 또는 `cost_log.json`으로 확인 가능.

---

## 4. Gemini 현황 (변경 없음)

`_call_gemini()`는 이미 Phase 20에서 `response.usage_metadata`를 완전히 수집 중:
- `prompt_token_count` → `record_gemini_usage(input_tokens)`
- `candidates_token_count` → `record_gemini_usage(output_tokens)`

Gemini Context Cache API(명시적 캐싱)는 32K+ 토큰 요건으로 현재 미적용.
향후 시스템 프롬프트가 32K를 초과하면 별도 검토.

---

## 5. 잔존 고려사항

| 항목 | 내용 |
|------|------|
| 환율 수동 관리 | `USD_TO_KRW = 1_380` — 월 1회 수동 업데이트 권장 |
| 기존 cost_log.json 호환 | `setdefault()` 처리로 구버전 데이터 자동 호환 |
