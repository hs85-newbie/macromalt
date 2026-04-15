# generator.py 모듈 분할 계획 (HSD-360)

> **현황**: 단일 파일 8,107줄  
> **목표**: `generator/` 패키지 분할, 파일당 ≤300줄 (CLAUDE.md 기준)  
> **상위 이슈**: HSD-353

---

## 1. 제약 조건

- `main.py`의 `from generator import generate_deep_analysis, generate_stock_picks_report` **변경 불가** (하위 호환)
- 기존 파이프라인 회귀 금지 — 분할 후 단독 실행 테스트 필수
- 모듈 간 순환 의존성 금지

---

## 2. 현황 분석: 주요 함수 크기

| 함수 | 시작줄 | 크기(줄) | 비고 |
|------|--------|----------|------|
| `convert_to_html` | 4795 | 1,096 | 최대 단일 함수, 최우선 분할 |
| `_extract_post1_spine` | 1738 | 536 | 독립 모듈 필요 |
| `generate_stock_picks_report` | 7223 | 346 | 로깅 헬퍼 분리 가능 |
| `generate_deep_analysis` | 6922 | 301 | 한계치 |
| `_check_post_separation` | 847 | 244 | - |
| `_enforce_tense_correction` | 2497 | 140 | - |
| `_check_verifier_closure` | 1422 | 142 | - |
| `verify_draft` | 6752 | 137 | - |

---

## 3. 제안 패키지 구조

```
generator/
├── __init__.py              공개 API 재수출 (~30줄)
├── constants.py             슬롯 컨텍스트 딕셔너리, 전역 상수 (~120줄)
├── ai_client.py             AI 모델 호출 레이어 (~150줄)
├── stock_price.py           주가 데이터 조회 (~280줄)
├── history.py               발행 이력 + 컨텍스트 빌더 (~300줄)
├── fingerprint.py           테마/축 중복 핑거프린트 (~115줄)
├── quality_score.py         품질 점수 측정 (~240줄)
├── quality_check.py         구조/분리 검사 (~260줄)
├── quality_verify.py        팩트/수치/연속성 검사 (~300줄)
├── verify_draft.py          verify_draft 통합 진입점 (~140줄)
├── temporal_detect.py       시제 오류 감지 (~360줄)
├── temporal_enforce.py      시제 교정 적용 (~380줄)
├── temporal_ssot.py         시제 SSOT + P16 블록 빌더 (~185줄)
├── p16.py                   P16 전망 다듬기 (~300줄) *
├── interp_rewrite.py        해석 약화 블록 재작성 (~390줄) *
├── source_formatter.py      소스 포맷/정규화 (~210줄)
├── post1_spine.py           Post1 핵심 줄기 추출 (~300줄) *
├── content_postprocess.py   콘텐츠 조립 + 후처리 (~270줄)
├── content_html.py          HTML 변환 (convert_to_html 분할) **
│   ├── content_html_core.py   섹션 렌더링 로직 (~300줄) **
│   ├── content_html_picks.py  픽 박스 렌더링 (~300줄) **
│   └── content_html_footnote.py 각주/출처 렌더링 (~300줄) **
├── gemini.py                Gemini 분석 호출 (~135줄)
├── planner.py               편집 플래너 + 계약 빌더 (~280줄)
├── gpt_writer.py            GPT 작성 (Post1/Post2) (~200줄)
├── event_log.py             이벤트 로깅 + 분류 (~210줄)
├── picks.py                 픽 파싱/포트폴리오 저장 (~45줄)
├── orchestrator.py          generate_deep_analysis (~300줄)
└── picks_orchestrator.py    generate_stock_picks_report (~350줄) *
```

> `*` 300줄 초과 예상 — 2단계 추가 분할 필요  
> `**` convert_to_html 1,096줄 → 3개 서브모듈로 분할 필수

---

## 4. 모듈별 할당 함수 목록

### `constants.py`
- `_SLOT_ANALYST_CONTEXTS`, `_SLOT_POST1_WRITER_HINTS`, `_SLOT_POST2_WRITER_HINTS` (딕셔너리)
- `MAX_RETRIES`, `_PDF_PROMPT_SNIPPET_LEN`, `_PUBLISH_HISTORY_PATH`, `_PUBLISH_HISTORY_MAX`

### `ai_client.py`
- `_call_gpt` (46줄)
- `_call_gemini` (60줄)
- `_parse_json_response` (36줄)

### `stock_price.py`
- `_fetch_naver_price` (50줄)
- `_fetch_krx_price` (38줄)
- `fetch_stock_prices` (39줄)
- `_fetch_korean_stock_price` (49줄)
- `_get_price_for_ticker` (101줄)

### `history.py`
- `_load_publish_history` (12줄)
- `save_publish_history` (38줄)
- `_log_freshness_summary` (33줄)
- `_build_history_context` (211줄)

### `fingerprint.py`
- `_make_theme_fingerprint` (32줄)
- `_make_axes_fingerprint` (62줄)
- `_make_ticker_buckets` (17줄)

### `quality_score.py`
- `_build_numeric_highlight_block` (56줄)
- `_score_post_quality` (105줄)
- `_score_interpretation_quality` (77줄)

### `quality_check.py`
- `_check_post_separation` (244줄)
- `_inject_disclaimer` (15줄)

### `quality_verify.py`
- `_check_temporal_sanity` (73줄)
- `_check_numeric_sanity` (89줄)
- `_check_macro_facts` (77줄)
- `_check_verifier_closure` (142줄)
- `_check_post_continuity` (80줄)
- `_calc_quality_pass_fields` (55줄)

### `verify_draft.py`
- `verify_draft` (137줄)
- `_classify_parse_failed` (37줄)

### `temporal_detect.py`
- `_detect_interp_hedge_density` (54줄)
- `_extract_hedge_heavy_interp_blocks` (53줄)
- `_has_mixed_tense_residue` (22줄)
- `_detect_completed_year_as_forecast` (94줄)
- `_detect_internal_label_leakage` (75줄)
- `_detect_current_year_past_month_as_forecast` (73줄)

### `temporal_enforce.py`
- `_enforce_tense_correction` (140줄)
- `_enforce_current_year_month_settlement` (106줄)
- `_strip_misapplied_jeonmang_tags` (95줄)
- `_strip_all_jeonmang_haeseok_tags` (13줄)

### `temporal_ssot.py`
- `_build_temporal_ssot` (83줄)
- `_build_p16_generation_block` (46줄)
- `_build_p16_step3_block` (54줄)

### `p16.py`
- `_strip_current_year_past_month_jeonmang` (249줄)
- `_p16b_emergency_polish` (75줄)
- `_p16b_compute_intro_overlap` (77줄)
- `_p16f_diagnose_bridge` (62줄)
- `_p16j_check_theme_repeat` (55줄)

### `interp_rewrite.py`
- `_extract_weak_interp_blocks` (73줄)
- `_rewrite_weak_blocks` (86줄)
- `_apply_block_replacements` (26줄)
- `_enforce_interpretation_rewrite` (204줄)

### `source_formatter.py`
- `format_articles_for_prompt` (33줄)
- `format_research_for_prompt` (53줄)
- `_normalize_source_for_generation` (94줄)
- `_filter_irrelevant_facts` (64줄)

### `post1_spine.py`
- `_extract_post1_spine` (536줄) → 내부 단계별 분리 필요

### `content_postprocess.py`
- `_strip_code_fences` (52줄)
- `_fix_double_typing` (31줄)
- `_format_source_section` (94줄)
- `assemble_final_content` (26줄)
- `extract_title` (10줄)
- `_extract_seo_title` (11줄)

### `content_html.py` (서브모듈 3개로 분할)
- `convert_to_html` (1,096줄) → `content_html_core.py`, `content_html_picks.py`, `content_html_footnote.py`

### `gemini.py`
- `gemini_select_themes` (42줄)
- `gemini_analyze` (58줄)
- `gemini_select_tickers_v2` (33줄)

### `planner.py`
- `_validate_planner_evidence_ids` (43줄)
- `_call_editorial_planner` (77줄)
- `_build_writer_contract` (84줄)
- `_parse_writer_evidence_ids` (14줄)
- `_check_p20_lead_metrics` (55줄)

### `gpt_writer.py`
- `gpt_write_analysis` (72줄)
- `gpt_write_picks` (129줄)

### `event_log.py`
- `_log_normal_publish_event` (38줄)
- `_log_parse_failed_event` (82줄)
- `_log_picks_section_lengths` (40줄)
- `_postprocess_density_check` (87줄)

### `picks.py`
- `parse_picks_from_content` (14줄)
- `save_portfolio` (29줄)

### `orchestrator.py`
- `generate_deep_analysis` (301줄)

### `picks_orchestrator.py`
- `generate_stock_picks_report` (346줄)
- `_count_whisky_metaphors` (9줄)
- `_verify_no_unsourced_price` (25줄)

### `__init__.py`
```python
from .orchestrator import generate_deep_analysis
from .picks_orchestrator import generate_stock_picks_report
from .stock_price import fetch_stock_prices
from .picks import parse_picks_from_content, save_portfolio
from .verify_draft import verify_draft
```

---

## 5. 의존성 다이어그램

```
__init__.py
  └── orchestrator.py
        ├── ai_client.py
        ├── gemini.py         → ai_client.py
        ├── gpt_writer.py     → ai_client.py, planner.py
        ├── source_formatter.py
        ├── history.py
        ├── fingerprint.py
        ├── temporal_*.py     (3개, 상호 독립)
        ├── p16.py            → temporal_ssot.py
        ├── interp_rewrite.py → ai_client.py
        ├── quality_*.py      (3개, 상호 독립)
        ├── verify_draft.py   → quality_*.py
        ├── content_postprocess.py
        └── content_html.py   → content_html_*.py
  └── picks_orchestrator.py
        ├── stock_price.py
        ├── picks.py
        ├── gpt_writer.py
        └── event_log.py
```

---

## 6. 작업 순서 (권장)

| 단계 | 모듈 | 이유 |
|------|------|------|
| 1 | `ai_client.py` | 의존성 없음, 테스트 용이 |
| 2 | `stock_price.py` | 의존성 없음, 독립 실행 가능 |
| 3 | `constants.py` | 전역 상수 정리 선행 필요 |
| 4 | `fingerprint.py`, `picks.py` | 소규모, 독립 |
| 5 | `temporal_*.py` (3개) | 내부 의존만 존재 |
| 6 | `quality_*.py` (3개) | `temporal_*.py` 이후 |
| 7 | `verify_draft.py` | `quality_*.py` 이후 |
| 8 | `source_formatter.py`, `history.py` | 독립 |
| 9 | `content_html.py` (서브모듈 분할) | 최대 규모, 신중 처리 |
| 10 | `content_postprocess.py` | `content_html.py` 이후 |
| 11 | `post1_spine.py` | 내부 분할 병행 |
| 12 | `p16.py`, `interp_rewrite.py` | 중간 복잡도 |
| 13 | `planner.py`, `gemini.py`, `gpt_writer.py` | AI 레이어 |
| 14 | `event_log.py` | 독립 |
| 15 | `orchestrator.py`, `picks_orchestrator.py` | 최종 조합 |
| 16 | `__init__.py` | 마지막 — 공개 API 고정 |

---

## 7. 검증 기준 (각 단계 완료 조건)

```bash
# 단계별 검증
python -c "from generator import generate_deep_analysis, generate_stock_picks_report; print('OK')"
python generator/__main__.py  # 또는 기존 단독 실행

# 타입/린트 (조건 충족 시)
mypy generator/ --ignore-missing-imports
```

- 공개 API 시그니처 변경 없음
- `main.py` import 수정 불필요
- 기존 `if __name__ == "__main__":` 블록은 `generator/__main__.py`로 이동

---

## 8. 주의 사항

- `convert_to_html` 분할 시 내부 클로저/중첩 함수 주의 (줄별 읽기 후 경계 확인)
- `_extract_post1_spine` 536줄: 내부 단계(step1~step5)가 있으면 단계별 분리
- 전역 `logger = logging.getLogger("macromalt")` — 각 모듈에서 재선언 (패키지 루트 의존 금지)
- `from styles.tokens import ...` 및 `import cost_tracker` — `ai_client.py` 또는 직접 사용 모듈에 이동
