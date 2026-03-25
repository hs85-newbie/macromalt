# Phase 22 — 다중 테마 파이프라인 구현 보고서

> 작성일: 2026-03-25 | 브랜치: dev | 상태: 구현 완료

---

## 1. 설계 범위

### 배경
- 기존: 슬롯 1회 실행 → 테마 1개 → Post1 + Post2 = 2개 발행
- 변경: 슬롯 1회 실행 → 테마 5개 → Post1×5 + Post2×2 = 7개 발행
- 적용 시점: 즉시 (2026-03-25~)

### 확정 스펙
| 항목 | 값 |
|------|-----|
| 슬롯당 테마 수 | 5개 |
| Post2 (캐시의 픽) 생성 수 | 상위 2개 테마 |
| WordPress 카테고리 | 동적 생성 (ANALYSIS 부모=2, PICKS 부모=3) |
| 발행 방식 | 예약 발행 (30분 간격, KST 기준) |

### 예약 발행 시간표

| 슬롯 | Post1 (×5) | Post2 (×2) |
|------|-----------|-----------|
| morning | 07:00 / 07:30 / 08:00 / 08:30 / 09:00 | 09:30 / 10:00 |
| evening | 12:00 / 12:30 / 13:00 / 13:30 / 14:00 | 14:30 / 15:00 |
| us_open | 21:00 / 21:30 / 22:00 / 22:30 / 23:00 | 23:30 / 00:00(익일) |

---

## 2. 구현 내역

### 2-1. generator.py

#### `_GEMINI_THEME_SELECTOR_SYSTEM` + `gemini_select_themes()` 추가 (line ~5906)
- 경량 Gemini 호출로 오늘의 상위 N개 테마 리스트 반환
- 각 테마에 `priority`, `picks_priority`, `reason` 포함
- 실패 시 단일 fallback 테마 반환

```python
def gemini_select_themes(
    news_text, research_text, dart_text="",
    n=5, slot="default", history_context=""
) -> list[dict]
```

#### `gemini_analyze()` — `forced_theme` 파라미터 추가 (line ~5969)
- 테마 지정 모드: forced_theme이 있으면 user_msg에 테마 명시 지시 추가
- 기존 동작 완전 유지 (forced_theme="" 시 기존과 동일)

#### `generate_deep_analysis()` — `forced_theme` 파라미터 추가 (line ~6887)
- 내부 `gemini_analyze()` 호출에 forced_theme 전달

---

### 2-2. publisher.py

#### `get_or_create_wp_category()` 추가 (line ~78)
- 로컬 `category_cache.json` 캐시 활용 (반복 API 호출 방지)
- 캐시 미스 → WordPress REST API로 기존 카테고리 검색
- 없으면 신규 생성 후 캐시 저장
- 예외 발생 시 부모 카테고리 ID로 fallback

```python
def get_or_create_wp_category(theme_name: str, parent_id: int) -> int
```

#### `publish_draft()` — `scheduled_at` 파라미터 추가 (line ~171)
- `scheduled_at`가 있으면 `"status": "future"`, `"date": scheduled_at` 설정
- 없으면 기존과 동일하게 `"status": "publish"` 즉시 발행

---

### 2-3. main.py — `main()` 전면 교체

**파이프라인 흐름 변경:**

```
[이전]
Step 1: 수집 → Step 2A: Post1(1개) → Step 2B: Post2(1개) → Step 3: 발행

[Phase 22]
Step 1:  수집 (1회, 모든 테마 공유)
Step 0:  gemini_select_themes() → 테마 5개 선정
Step 2A: generate_deep_analysis() × 5 (테마별 루프)
Step 2B: generate_stock_picks_report() × 2 (picks_priority 1,2)
Step 2C: 이미지 준비 (테마별)
Step 3A: Post1 발행 × 5 (예약, 카테고리 동적)
Step 3B: Post2 발행 × 2 (예약, 카테고리 동적)
```

**`step_publish()` — `scheduled_at` 파라미터 추가**

---

## 3. 비용 영향

| 항목 | 이전 (1테마) | Phase 22 (5테마+2픽) |
|------|------------|---------------------|
| GPT 호출/슬롯 | 2회 | 7회 |
| GPT 호출/일 (3슬롯) | 6회 | 21회 |
| 월 GPT 비용 | ~$15 | ~$49 |
| 월 Gemini 비용 | ~₩6,700 | ~₩9,000 (테마선정 추가) |
| **월 합계** | **~₩28,000** | **~₩79,000** |

→ OpenAI 대시보드 상한 $60으로 상향 조정 완료 (cost_tracker.py: $60 / ₩14,000 기 반영)

---

## 4. 잔존 고려사항

| 항목 | 내용 | 후속 작업 |
|------|------|---------|
| `category_cache.json` 자동 생성 | 첫 실행 시 생성됨, `.gitignore` 추가 권장 | 필요 시 처리 |
| `_log_normal_publish_event` | Phase 22 main()에서 제거됨 (비치명) | Phase 23에서 복원 검토 |
| picks_priority 자동 선정 | Gemini가 선정 — 종목 픽 적합도에 따라 가변 | 모니터링 필요 |
| 테마 중복 방지 | 현재 history_context로 제한 — 완전하지 않음 | Phase 23 이후 개선 |

---

## 5. Phase 23 예정 (cost 고도화)

- OpenAI `usage.prompt_tokens_details.cached_tokens` 수집 → 캐시 절감 실적 가시화
- Gemini `usage_metadata` 수집 → 실제 청구 기준 비용 추적
- `category_cache.json` `.gitignore` 등록
- `_log_normal_publish_event` 다중 포스트 지원으로 복원
