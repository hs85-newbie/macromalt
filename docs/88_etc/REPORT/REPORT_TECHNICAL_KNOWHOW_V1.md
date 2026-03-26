# macromalt 기술 종합 Know-How 보고서 V1

> 작성일: 2026-03-26 | 대상: 내부 참조 / 신규 개발자 온보딩 | Phase 23 기준 (최종 갱신: 2026-03-26, Phase 4.3/5-A 항목 보강)

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [기술 스택 전체](#2-기술-스택-전체)
3. [아키텍처 구조](#3-아키텍처-구조)
4. [Phase별 진화 이력](#4-phase별-진화-이력)
5. [핵심 모듈 상세](#5-핵심-모듈-상세)
6. [에러 사례 및 해결법 (Know-How)](#6-에러-사례-및-해결법)
7. [WordPress 연동 노하우](#7-wordpress-연동-노하우)
8. [GitHub Actions 운영 노하우](#8-github-actions-운영-노하우)
9. [비용 관리 노하우](#9-비용-관리-노하우)
10. [품질 보증 체계](#10-품질-보증-체계)
11. [환경 설정 완전 가이드](#11-환경-설정-완전-가이드)
12. [운영 트러블슈팅 매뉴얼](#12-운영-트러블슈팅-매뉴얼)
13. [AI 글쓰기 품질 개선 Know-How (Phase 20)](#13-ai-글쓰기-품질-개선-know-how)
14. [Phase 5~17 파이프라인 진화 Know-How](#14-phase-517-파이프라인-진화-know-how)

---

## 1. 프로젝트 개요

### 1-1. 한 줄 정의

> **macromalt**: 금융 뉴스·공시·리서치 데이터를 자동 수집하여 AI(GPT-4o + Gemini)로 투자 분석 글을 생성하고, WordPress에 자동 발행하는 풀 파이프라인.

### 1-2. 규모

| 항목 | 수치 |
|------|------|
| Python 파일 수 | 13개 |
| 총 코드 라인 | ~12,000줄 |
| 핵심 함수/클래스 | 180+ 개 |
| 외부 API | 7개 |
| 보고서 파일 | 56개 (Phase 14~23) |
| GitHub Actions 워크플로우 | 2개 |
| Phase 22 기준 일 발행량 | **21개 포스팅/일** (3슬롯 × 7개) |
| 월 발행량 | **~630개/월** |

### 1-3. 파이프라인 한눈에 보기

```
[데이터 수집]          [AI 생성]               [발행]
 RSS/웹 뉴스 ──┐       ┌─ Gemini 분석 ─┐       ┌─ WordPress REST API
 DART 공시 ───┤──→─→──┤  GPT 작성    ├──→──→─┤  예약 발행 (future)
 네이버금융 ───┤       │  Gemini 검수  │       │  카테고리 동적 생성
 한경컨센서스 ─┘       └──────────────┘       └─ 이미지 첨부
```

---

## 2. 기술 스택 전체

### 2-1. 핵심 Python 라이브러리

| 분류 | 라이브러리 | 버전 | 용도 |
|------|----------|------|------|
| HTTP/크롤링 | `requests` | 2.32.3 | API 호출, 웹 스크래핑 |
| HTML 파싱 | `beautifulsoup4` | 4.12.3 | 웹 스크래핑 |
|  | `lxml` | 5.3.0 | HTML 구조 분석 |
| RSS | `feedparser` | 6.0.11 | RSS/Atom 수집 |
| **OpenAI** | `openai` | ≥2.0.0 | GPT-4o API |
| **Gemini** | `google-genai` | ≥1.0.0 | Gemini 2.5-flash |
| WordPress | `python-wordpress-xmlrpc` | 2.3 | REST API 포스팅 |
| 스케줄링 | `schedule` | 1.2.2 | 정기 실행 |
| 재시도 | `tenacity` | 9.0.0 | 네트워크 오류 자동 재시도 |
| 한국 주식 | `pykrx` | ≥1.0.47 | KRX 종목 시세 |
| 미국 주식 | `yfinance` | ≥1.2.0 | NASDAQ/NYSE 종가 |
| 차트 | `matplotlib` | ≥3.8 | 주가 차트 생성 |
| 이미지 | `Pillow` | ≥10.0 | 이미지 편집 |
| PDF | `pdfplumber` | ≥0.11 | 증권사 리포트 추출 |
| 마크다운 | `markdown` | 3.9 | MD → WordPress HTML |
| HTML→텍스트 | `html2text` | 2024.2.26 | HTML 태그 제거 |
| 환경변수 | `python-dotenv` | 1.0.1 | .env 로드 |
| 데이터 | `pandas` | 2.2.3 | JSON/CSV 처리 |
| 날짜 | `python-dateutil` | 2.9.0 | 날짜 파싱 |

### 2-2. 외부 API & 데이터 소스

| API | 환경변수 | 비용 | 용도 |
|-----|----------|------|------|
| **OpenAI GPT-4o** | `OPENAI_API_KEY` | 유료 | 분석글/픽스글 작성 |
| **Google Gemini 2.5-flash** | `GEMINI_API_KEY` | 유료 | 테마선정, 팩트체크 |
| **OpenDART** | `DART_API_KEY` | 무료 | 기업 공시/재무정보 |
| **FRED (미국 연준)** | `FRED_API_KEY` | 무료 | 금리/CPI/실업률 |
| **BOK (한국은행)** | `BOK_API_KEY` | 무료 | 기준금리/환율 |
| **Unsplash** | `UNSPLASH_ACCESS_KEY` | 무료 | 포스트 대표 이미지 |
| **WordPress** | `WORDPRESS_USERNAME/PASSWORD` | 무료 | 블로그 발행 |
| **한국경제** | `HANKYUNG_USERNAME/PASSWORD` | 무료 | 컨센서스 데이터 |
| **KRX (pykrx)** | 불필요 | 무료 | 종목 시세 |

### 2-3. 인프라

| 항목 | 사용 서비스 |
|------|-----------|
| 코드 호스팅 | GitHub (Private) |
| 자동화 | GitHub Actions (Cron) |
| 블로그 | WordPress (자체 호스팅) |
| 도메인/SSL | 10년 선납 완료 (₩3,200/월 환산) |

---

## 3. 아키텍처 구조

### 3-1. 디렉토리 구조

```
macromalt/
├── main.py                    # ★ 메인 파이프라인 오케스트레이터
├── generator.py               # ★ AI 콘텐츠 생성 엔진 (8,043줄)
├── scraper.py                 # ★ 다중 소스 데이터 수집
├── publisher.py               # WordPress 발행 + 카테고리 관리
├── cost_tracker.py            # API 비용 추적/경보
├── editorial_config.py        # 편집 철학 / 스타일 가이드
├── macro_data.py              # 거시지표 (FRED/BOK)
├── knowledge_base.py          # RAG 지식 베이스
├── images.py                  # 이미지 수집/생성/첨부
│
├── styles/
│   └── tokens.py              # CSS 스타일 토큰 (Phase 17 중앙화)
│
├── scripts/
│   ├── publish_daily.py       # GitHub Actions 실행 래퍼
│   └── phase20_weekly_report.py  # 주간 QA 보고서 생성
│
├── .github/workflows/
│   ├── publish.yml            # 일일 발행 자동화
│   └── phase20-weekly.yml     # 주간 리포트 자동화
│
├── data/                      # 정적 데이터 (sources.json 등)
├── logs/                      # 실행 로그 (gitignore)
├── jobs/                      # 과거 실행 아티팩트
├── docs/88_etc/REPORT/        # 56개 Phase 보고서
│
├── sources.json               # 뉴스/리서치 소스 정의
├── portfolio.json             # 종목 픽 이력
├── publish_history.json       # 발행 이력 (최근 5회)
├── cost_log.json              # 월별 API 비용 누적
├── dart_corp_codes.json       # 한국 상장사 코드 맵
├── category_cache.json        # WP 카테고리 캐시 (Phase 22)
└── requirements.txt           # 의존성 (58개)
```

### 3-2. Phase 22 메인 파이프라인 흐름

```
main() 실행
    │
    ├─ [Step 1] 데이터 수집 (1회 공유)
    │     ├── scraper.run_all_sources()       → news[] (기사 수백 건)
    │     └── scraper.run_research_sources()  → research[] (리서치)
    │
    ├─ [Step 0] 테마 선정 (Gemini 초경량 호출)
    │     └── gemini_select_themes(n=5)       → themes[5]
    │           └── [{"priority":1, "theme":"반도체", "picks_priority":1, ...}, ...]
    │
    ├─ [Step 2A] Post1 생성 × 5 (테마별 루프)
    │     └── generate_deep_analysis(forced_theme=theme)  → post1_content
    │           ├── Gemini 분석 (JSON 재료)
    │           ├── GPT-4o 작성 (HTML 원고)
    │           └── Gemini 팩트체크 (검수/수정)
    │
    ├─ [Step 2B] Post2 생성 × 2 (picks_priority 상위)
    │     └── generate_stock_picks_report()   → post2_content
    │
    ├─ [Step 2C] 이미지 준비 (루프)
    │     ├── images.attach_post1_image()
    │     └── images.inject_chart()
    │
    └─ [Step 3] 예약 발행
          ├── Post1×5: +10, +40, +70, +100, +130분
          ├── Post2×2: +160, +190분
          └── publisher.get_or_create_wp_category()  → 카테고리 동적 생성
```

---

## 4. Phase별 진화 이력

| Phase | 날짜(추정) | 핵심 변경 내용 |
|-------|-----------|--------------|
| **Phase 4.3** | 2026-03-13 | **리포트 밀도 복원·주제 집중도 강화** — REVISER 보존형 편집장 재정의(90% 보존 강제), `_strip_code_fences()` 공통화, 자동 검증 14/10 기준, P6/P8 프롬프트 강화 |
| **Phase 5-A~D** | 2026-03-13 | DART 연동(corpCode.xml 캐시, 재무 YoY 비교), PDF enrich (pdfplumber), WordPress 자동 발행 기초 |
| **Phase 6** | 2026-03-13 | 한경컨센서스 세션 로그인, DART XML 수정공시 처리 |
| **Phase 7~9** | 2026-03-13 | 실 발행 검증 3회, 투자 권유 억제 (기준5: "매수/유망/담아야" 금지) |
| **Phase 10** | 2026-03-16 | 슬롯 분기 (morning/evening/us_open/default) + 이력 반복 완화 |
| **Phase 11** | 2026-03-16 | Fingerprint 기반 반복 완화 엔진 — theme/axes/ticker 3종 버킷 |
| **Phase 12** | 2026-03-16 | 증거 밀도 강화 — `_build_numeric_highlight_block()`, `_score_post_quality()` |
| **Phase 13** | 2026-03-16 | 해석 지성 + 시간·수치 신뢰성 — `_score_interpretation_quality()` (HOLD→GO) |
| **Phase 14** | 초기 | 기본 파이프라인 (수집→생성→발행) |
| **Phase 15** | 2026-03-17 | **시제 강제화** — 과거/현재/미래 혼용 금지, 복합시제 교정 핫픽스(A~E) |
| **Phase 16** | 2026-03-18 | **출력 품질 경화** — H1 중복 제거, 연속성 검증, 테마 로테이션, parse_failed 표준화 |
| **Phase 15A~E** | 2026-03-17 | **시제 강제화** — 복합시제 교정 핫픽스, `[전망]` 오주입 제거, 현재 연도 과거 월 통합 교정 |
| **Phase 16** | 2026-03-17 | **Temporal SSOT** — 시제 단일 진실 공급원 레이어, step3_status 4-state enum |
| **Phase 16B~K** | 2026-03-18~19 | 출력 품질 경화 — H1 중복 제거, intro_overlap, bridge guard, theme rotation, PARSE_FAILED 표준화 |
| **Pre-Phase 17** | 2026-03-19 | **스타일 분리 트랙** — `styles/tokens.py`, CSS 3종, child-theme 분리 |
| **Phase 17** | 2026-03-19 | **Post2 opener pick-angle 강제** + **PARSE_FAILED TYPE_A~E 런타임 분류 체계** 구현 |
| **Phase 18** | 2026-03-20 | **4축 안정화** — closure 오류, fallback 누락, parse_failed 루프, 반복 테마 방지 |
| **Phase 19** | 2026-03-20 | **GitHub Actions 이관** — 로컬 스케줄 → CI/CD 완전 이관, 품질로그(JSONL) 시스템 |
| **Phase 20-1~3** | 2026-03-23 | **Editorial Planner Track** — Step1.5 플래너 삽입, 4-tier writer contract, stance_type 5종 |
| **Phase 20-4** | 2026-03-26 | **Verifier 구조 검사** — 기준 26~30, lead_recall/lead_focus 이중 지표 |
| **Phase 21** | 2026-03-20 | **SEO 최적화** — 슬러그 이중화, 인라인 출처 미니태그, OpenGraph 최적화 |
| **Phase 22** | 2026-03-25 | **다중 테마 파이프라인** — 1테마/슬롯 → 5테마, 7포스팅, 예약 발행 30분 간격 |
| **Phase 23** | 2026-03-25 | **Cost 고도화** — OpenAI 캐시 토큰 수집, Gemini usage_metadata 수집, 절감액 가시화 |

---

## 5. 핵심 모듈 상세

### 5-1. generator.py (AI 생성 엔진)

**규모**: 8,043줄 | 81개 함수

#### 주요 함수 목록

| 함수명 | 역할 | 비용 단위 |
|--------|------|---------|
| `gemini_select_themes()` | 5개 투자 테마 선정 | Gemini 경량 1호출 |
| `gemini_analyze()` | 뉴스→구조화 JSON 생성 | Gemini 중형 1호출 |
| `gpt_write_analysis()` | JSON→HTML 분석글 작성 | GPT-4o 대형 1호출 |
| `gpt_write_picks()` | 종목 픽 글 작성 | GPT-4o 대형 1호출 |
| `verify_draft()` | Gemini 팩트체크 | Gemini 중형 1호출 |
| `gemini_select_tickers_v2()` | 테마별 종목 추천 | Gemini 경량 1호출 |
| `generate_deep_analysis()` | Post1 전체 생성 (진입점) | 위 3개 호출 포함 |
| `generate_stock_picks_report()` | Post2 전체 생성 (진입점) | 위 3개 호출 포함 |
| `assemble_final_content()` | 최종 HTML 조립 | 무료 |
| `_call_gpt()` | GPT 내부 호출 + 토큰 기록 | 내부 |
| `_call_gemini()` | Gemini 내부 호출 | 내부 |
| `_score_post_quality()` | 품질 점수 계산 | 내부 |
| `save_publish_history()` | 발행 이력 JSON 저장 | 무료 |

#### 3단계 교차 검증 구조

```python
# Step 1: Gemini 분석 (재료 생성)
raw_analysis = gemini_analyze(news_text, research_text, forced_theme=theme)
# → {"main_theme": "반도체", "key_data": [...], "tickers": [...], ...}

# Step 2: GPT-4o 작성 (원고 생성)
draft_html = gpt_write_analysis(raw_analysis, slot=slot)
# → "<h2>...</h2><p>...</p>..."

# Step 3: Gemini 팩트체크 (검수)
verified = verify_draft(draft_html, raw_analysis)
# → {"pass": true} or {"pass": false, "corrected_html": "..."}
```

### 5-2. scraper.py (데이터 수집)

**규모**: ~2,000줄

#### 주요 데이터 소스

```json
// sources.json 구조
{
  "rss_sources": [
    {"name": "Bloomberg", "url": "...", "weight": 10},
    {"name": "CNBC", "url": "...", "weight": 8},
    {"name": "Reuters", "url": "...", "weight": 8}
  ],
  "web_sources": [
    {"name": "네이버금융", "url": "...", "type": "scrape"}
  ]
}
```

#### DART API 활용 패턴

```python
# 공시 스캔 (최근 N일)
disclosures = run_dart_disclosure_scan(days=3)

# 재무정보 (연간/분기)
financials = run_dart_financials(corp_code="...", bgn_de="20250101")

# 기업정보
corp_info = run_dart_company_info(stock_code="005930")  # 삼성전자
```

### 5-3. publisher.py (WordPress 연동)

**규모**: 307줄

#### 핵심 함수

```python
# 카테고리 동적 생성 (Phase 22)
category_id = get_or_create_wp_category(
    theme_name="반도체",
    parent_id=2   # ANALYSIS=2, PICKS=3
)
# → 캐시 조회 → 없으면 REST API 생성 → category_cache.json 저장

# 발행 (즉시 vs 예약)
result = publish_draft(
    title="반도체 시장 분석 ...",
    content="<h2>...</h2>...",
    category_ids=[15, 2],          # 테마 하위 + 부모
    featured_media_id=123,
    seo_title="반도체 투자 분석 ...",
    scheduled_at="2026-03-26T07:10:00"  # 비어있으면 즉시 발행
)
```

#### WordPress REST API 주의사항

```python
# ✅ 올바른 예약 발행 형식 (KST → UTC 변환 없이 site_tz 기준)
payload = {
    "status": "future",
    "date": "2026-03-26T07:10:00",  # WordPress site_tz 기준 (KST 설정 시 KST 그대로)
    "date_gmt": "2026-03-25T22:10:00"  # UTC
}

# ❌ 흔한 실수: date를 UTC로 넣으면 9시간 일찍 발행됨
```

### 5-4. Editorial Planner (Phase 20 Step 1.5)

#### 핵심 문제 인식

```
[기존 파이프라인의 구조적 결함]
Gemini Step1 → 평탄한 사실 묶음 JSON (모든 facts가 동등한 중요도)
     ↓
GPT → "이 JSON을 HTML로 변환하라" (neutral fact serializer 역할)
     ↓
결과: 균등 배분 구조 → 모든 섹션 동형 반복 → AI처럼 읽힘

[해결 방향]
structured facts → editorial plan → writer draft → verify/revise
                       ↑
             "lead_angle 1개 선택"이 핵심
             GPT는 이미 계획된 contract를 소비하는 writer
```

#### Step1 스키마 확장 (Phase 20-1)

facts 배열 항목에 추가된 필드:
```json
{
  "id": "fact_1",
  "causal_path": "금리 인상 → 달러 강세 → 수출 기업 원화 수익 감소",
  "confidence": "high | medium | low"
}
```

신규 perspective fields:
```json
"why_now":          { "claim": "...", "evidence_ids": ["fact_1"], "confidence": "high" },
"market_gap":       { "claim": "...", "evidence_ids": [...], "confidence": "..." },
"analyst_surprise": { "level": "none|mild|strong", "claim": "...", "evidence_ids": [...] },
"stance_type":      "consensus_miss | underpriced_risk | overread | low_confidence | neutral",
"stance_evidence_ids": [...],
"risk_of_overstatement": [{ "text": "...", "reason": "..." }]
```

**생성 규칙:**
- `evidence_ids`가 실제 facts id와 불일치하면 해당 필드 omit
- `why_now`: today's specific trigger 필수 (범용 설명 금지)
- `stance_type` 근거 없으면 강제로 `"neutral"`
- `risk_of_overstatement`: why_now/market_gap 존재 시 1개 이상 필수

#### Planner 구조 (Phase 20-2)

```python
GEMINI_PLANNER_POST1_SYSTEM = """
# Post1 전용: macro_mechanism / transmission_path / market_structure / counterpoint
# lead_angle 1개 필수 (pick 금지)
# drop_ids 최소 1개 필수 (편집 의지 표명)
# word_budget_ratio: lead ≥ 0.35
"""

GEMINI_PLANNER_POST2_SYSTEM = """
# Post2 전용: pick_trigger / stock_sensitivity / selection_logic / counterpoint
# pick_trigger 없이 시작 금지 (Phase 17 규칙 유지)
"""
```

플래너 출력 → 4-tier writer contract:
```json
{
  "lead_facts":         ["fact_2"],
  "secondary_facts":    ["fact_1", "fact_3"],
  "background_facts":   ["bg_1", "bg_2"],
  "disallowed_fact_ids": ["fact_5"],
  "lead_angle":         { "claim": "...", "evidence_ids": ["fact_2"] },
  "stance_type":        "underpriced_risk",
  "narrative_shape":    "conclusion_first | contradiction_first | question_first",
  "section_plan":       [...]
}
```

**GPT는 원본 step1 facts 배열을 받지 않는다** — 재균등 배분 원천 차단.

#### Fallback 보장 원칙

```python
try:
    planner = _call_editorial_planner(step1=materials, post_type="post1", ...)
    if planner:
        contract = _build_writer_contract(step1=materials, planner=planner, ...)
except Exception as e:
    logger.warning(f"[Phase 20] planner 예외 — fallback | {e}")
    contract = None  # None이면 기존 파이프라인 그대로 작동
```

로그:
- 성공: `[Phase 20] editorial planner OK | planner_used=True | stance_type=... | narrative_shape=...`
- 실패: `[Phase 20] planner FAILED | planner_used=False | fallback=step1_only`

#### writer HTML 주석 (Phase 20-3)

GPT 작성 출력 끝에 실제 사용 facts 추적:
```html
<!-- macromalt:evidence_ids_used=[fact_2,fact_5,bg_1] -->
```

파싱:
```python
def _parse_writer_evidence_ids(html: str) -> list:
    m = re.search(r'<!--\s*macromalt:evidence_ids_used=\[(.*?)\]\s*-->', html)
    if m:
        return [x.strip() for x in m.group(1).split(',') if x.strip()]
    return []
```

로그: `[Phase 20] writer evidence | writer_used_evidence_ids=[fact_2,fact_5,bg_1]`

---

### 5-5. Temporal SSOT 레이어 (Phase 16)

#### 설계 배경

GPT-4o가 시제를 스스로 결정하면 동일 문단에서 과거/현재/미래가 뒤섞이는 문제 발생.
Phase 15 hotfix 시리즈(A~E)로 복합시제 regex 교정을 쌓았으나 근본 해결이 안 됨.
→ Phase 16에서 "시점 단일 진실 공급원(SSOT)" 레이어를 구축하여 모든 레이어에 주입.

```python
def _build_temporal_ssot(run_year: int, run_month: int) -> dict:
    """실행 시점 기반 SSOT 생성 — GPT/Gemini 모두 이 기준으로 시제 판단"""
    return {
        "run_date":        f"{run_year}-{run_month:02d}",
        "confirmed_past":  f"{run_year}년 {run_month-1}월 이전",  # 과거형 강제 구간
        "open_present":    f"{run_year}년 {run_month}월",         # 현재 진행형 허용
        "forecast_future": f"{run_year}년 {run_month+1}월 이후",  # 미래형 허용
    }

# SSOT는 아래 3곳에 동시 주입
_build_p16_generation_block(ssot)  # GPT Step2 context
_build_p16_step3_block(ssot)       # Gemini Verifier/Reviser
```

#### Phase 15 hotfix 시리즈 (regex 교정 레이어)

| Phase | 함수 | 대상 패턴 |
|-------|------|---------|
| 15A | `_P15A_COMPOUND_RE_FORMAL/INFORMAL` | "증가했을 것입니다" 등 복합 완료형 |
| 15B | `_P15B_COMPOUND_RE_CONNECTIVE` | 연결어미 복합시제 |
| 15C | `_P15C_POST2_LABEL_BAN` | Post2에 Post1 레이블 혼입 차단 |
| 15D | `_strip_misapplied_jeonmang_tags()` | 확정 어미 뒤 `[전망]` 태그 제거 |
| 15E | `_enforce_current_year_month_settlement()` | 현재 연도 과거 월 시제 통합 |

---

### 5-6. step3_status 4-state enum + p16b_guard (Phase 16F~16J)

#### step3_status enum 설계

단순 pass/fail 이분법으로는 "수정 시도했으나 실패" vs "파싱 자체 불가"를 구분 불가.
→ Phase 16F에서 4-state enum 표준화.

| 상태 | 발생 조건 | 수정 시도 | 발행 경로 |
|------|----------|----------|----------|
| `PASS` | Step3 이슈 없음 | 없음 | GPT 초안 원본 |
| `REVISED` | Step3 이슈 발견 → 수정 성공 | 있음 (성공) | Gemini 수정본 |
| `FAILED_NO_REVISION` | 수정 API 실패 (503/timeout) | 있음 (실패) | GPT 초안 원본 |
| `PARSE_FAILED` | Gemini 응답 JSON 파싱 불가 | **없음 (skip)** | GPT 초안 원본 (fallback) |

> **운영 원칙**: `PARSE_FAILED`는 "오류가 없었다"가 아니라 "관측 가능성 확보"가 목표. 발생 시 분류·로그·fallback 동작을 검증하는 방향으로 관리.

#### p16b_guard 딕셔너리 구조

각 run마다 Post1/Post2 별도로 생성되는 품질 진단 컨테이너.

```python
# Post2 p16b_guard (전체 필드)
p16b_guard = {
    "step3_status":      str,   # PASS/REVISED/FAILED_NO_REVISION/PARSE_FAILED
    "fallback_triggered": bool,  # FAILED_NO_REVISION인 경우 True
    "parse_failed":       bool,  # PARSE_FAILED인 경우 True [Phase 16J]
    "emergency_polish":   dict,  # {status, unique_marker_count, total_occurrence_count, markers}
    "intro_overlap":      dict,  # {overlap_ratio, status, shared_ngram_count}
    "bridge_diag":        dict,  # {found, mode, picks} [Phase 16F]
    "theme_repeat_diag":  dict,  # {is_repeat, repeat_count, theme_fp, matched_slots} [Phase 16J]
}
```

#### intro_overlap 계산 방식

Post1/Post2가 같은 매크로 배경 도입부를 중복 서술하는 문제 감지.

```
기준: Post1 intro 300자 / Post2 intro 600자
방식: char-level 4-gram overlap
공식: shared_ngrams / max(ng1_count, ng2_count)
구간: LOW < 15% / MEDIUM 15~30% / HIGH ≥ 30%
실패 기준: n-gram 중복 ≥ 3 OR bg_repeat ≥ 2
```

---

### 5-7. Phase 17: Post2 opener pick-angle 강제 + PARSE_FAILED 분류 체계

#### Post2 opener 구조 개편 배경

Phase 16K까지 opener가 `_P16J_POST2_SAME_THEME_OPENER` 주입 후에도
"오늘 이 테마를 보는 이유" generic H3로 생성되는 문제 잔존.
→ Phase 17에서 H3 금지 패턴 + 허용 패턴 명세 + 첫 문장 규칙 3중 강제.

```python
# _P17_POST2_OPENER_ENFORCEMENT (~line 3220 in generator.py)
# gpt_write_picks() user_msg 최우선(첫 번째) 위치에 주입

# ❌ H3 금지 패턴 6종
"오늘 이 테마를 보는 이유"
"최근 거시 환경을 먼저 보면"
"이번 시장 변수는"
"왜 지금 이 테마인가"    # 픽명 없는 generic
"현재 시장 상황"
"투자 포인트"

# ✅ H3 허용 패턴 5종
"왜 지금 {메인 픽}인가"
"{메인 픽}을 먼저 봐야 하는 이유"
"{메인 픽}: {핵심 변수} 각도"
"왜 지금 {핵심 섹터}인가"
"{핵심 섹터}에서 {메인 픽}이 부각되는 이유"

# 첫 문장 3중 강제 규칙
# 1) 메인 픽명 또는 핵심 섹터명 반드시 포함
# 2) 거시 배경 재서술(macro recap)로 시작 금지
# 3) 수주/판가/재고/CAPEX/정책 수혜/실적 민감도/가격 전가력 중 핵심 변수 1개 이상
```

#### PARSE_FAILED TYPE 분류 체계 (`_classify_parse_failed()`)

```python
# generator.py ~line 5355
def _classify_parse_failed(raw: str, normalized: Optional[str] = None) -> str:
    """PARSE_FAILED 발생 원인을 TYPE_A~E 또는 TYPE_UNKNOWN으로 분류"""

# TYPE_A: H2/H3 태그 전무 — 섹션 구조 누락 (글 자체가 날아간 경우)
# TYPE_B: 금지된 opener 패턴 포함 (6종) — reviser가 금지 패턴을 삽입
# TYPE_C: 오픈/클로즈 태그 수 차이 >5 — HTML 파손 (응답 중단 등)
# TYPE_D: PICKS 주석 누락 (>500자 본문에서) — 구조 주석 소실
# TYPE_E: normalized < raw * 0.6 — reviser 과도 축소 (내용 60% 이상 삭제)
# TYPE_UNKNOWN: 위 분류 외
```

#### `_log_parse_failed_event()` 10필드 로그

```python
# generator.py ~line 5382
# 필수 필드 10종
run_id               # "20260319_180909"
slot                 # morning/evening/us_premarket/default
post_type            # post1/post2
failure_type         # TYPE_A~E / TYPE_UNKNOWN
parse_stage          # "Step3:verifier:json_parse"
failed_section_name  # "verifier_response"
raw_output_snapshot  # 원본 200자 스냅샷
normalized_output_snapshot  # 정규화본 200자 스냅샷 (있는 경우)
fallback_used        # True/False
publish_blocked      # True/False (현재 정책: False — 발행 허용)
```

**실전 작동 확인**: Phase 17 샘플 5건 중 Post 187에서 TYPE_D 실제 발생 → 10필드 정상 기록.

---

### 5-8. Pre-Phase 17: WordPress 스타일 분리 트랙

#### 배경

`generator.py`에 CSS 인라인 상수가 수백 줄 하드코딩되어 있던 문제.
Phase 17 착수 전 분리 트랙으로 처리.

#### 분리 구조

```
styles/
├── __init__.py          # 패키지 노출
├── tokens.py            # 색상·폰트·간격 등 디자인 토큰 중앙 관리
└── wordpress/
    ├── base.css         # 기본 레이아웃
    ├── typography.css   # 타이포그래피 (폰트 크기, 줄간격, 제목 계층)
    └── components.css   # 박스, 카드, 하이라이트 등 컴포넌트

theme/
└── child-theme/
    └── style.css        # WordPress child theme 진입 스타일
```

```python
# generator.py (import 방식)
from styles.tokens import (  # Pre-Phase 17: 스타일 토큰 중앙 관리
    COLOR_PRIMARY, COLOR_ACCENT,
    FONT_SIZE_BODY, LINE_HEIGHT_BODY,
    ...
)
```

**핵심 효과**: generator.py CSS 하드코딩 제거 → styles/tokens.py 단일 수정으로 전체 적용.

---

### 5-9. lead_metrics 이중 지표 (Phase 20-4)

#### 설계 배경

단일 `lead_drift` 지표로는 두 가지 다른 실패 패턴을 구분할 수 없다:

| 실패 패턴 | 설명 |
|-----------|------|
| **lead 누락** | planner가 지정한 lead_ids를 writer가 실제로 안 씀 |
| **강조 희석** | lead_ids는 썼지만 secondary/background도 대량 사용 → 균등 배분 회귀 |

#### 이중 지표 정의

```python
def _check_p20_lead_metrics(
    lead_ids: list,
    used_ids: list,
    run_id: str,
    post_type: str,
) -> dict:
    """
    lead_recall : len(lead_ids ∩ used_ids) / len(lead_ids)
                  → planner 지정 핵심 근거를 writer가 얼마나 사용했나 (누락 감지)
    lead_focus  : len(lead_ids ∩ used_ids) / len(used_ids)
                  → writer 사용 전체 ids 중 lead 비중 (강조 희석 감지)
    """
```

| 지표 | 공식 | 감지 실패 모드 |
|------|------|---------------|
| `lead_recall` | `\|lead ∩ used\| / \|lead\|` | planner 지정 리드를 writer가 누락 |
| `lead_focus` | `\|lead ∩ used\| / \|used\|` | writer가 secondary/background에 집중 → 균등 배분 회귀 |

#### WARN 조건

```
recall < 0.5   → "[Phase 20] WARN lead_metrics | lead_recall=0.xx — lead_ids 절반 이상 미사용"
focus  < 0.25  → "[Phase 20] WARN lead_metrics | lead_focus=0.xx — 사용 facts 중 lead 비중 25% 미만"
```

**두 지표가 잡는 패턴 조합:**
- `low recall + high focus`: 일부 lead만 썼지만 그나마 비중 높음 → lead 누락
- `high recall + low focus`: lead 전부 썼지만 secondary도 대량 → 균등 배분 회귀 (흔한 패턴)
- `low recall + low focus`: 두 문제 동시 발생

#### 로그 (항상 출력)

```
[Phase 20] lead_metrics | run_id=20260326_070533 | post_type=post1 |
lead_ids=[fact_2] | writer_used_ids=[fact_1,fact_2,fact_3,fact_4,fact_5] |
missing_lead_ids=[] | lead_recall=1.00 | lead_focus=0.20
```

---

### 5-6. cost_tracker.py (비용 추적)

**규모**: 390줄

#### 비용 단가 (2026-03 기준)

```python
# OpenAI GPT-4o
OPENAI_INPUT_PRICE_PER_1M  = 2.50   # USD
OPENAI_CACHED_PRICE_PER_1M = 0.625  # USD (75% 할인)
OPENAI_OUTPUT_PRICE_PER_1M = 10.00  # USD

# Gemini 2.5-flash
GEMINI_INPUT_PRICE_PER_1M  = 0.075  # USD
GEMINI_OUTPUT_PRICE_PER_1M = 0.30   # USD

USD_TO_KRW = 1_380  # 고정 환율
```

#### 월간 한도 & 알림

```python
OPENAI_LIMIT_USD  = 60.00    # $60
GEMINI_LIMIT_KRW  = 14_000   # ₩14,000

# 알림 임계값: 50% → ℹ️, 80% → ⚠️, 95% → 🚨
```

---

## 6. 에러 사례 및 해결법 (Know-How)

### 6-1. [CRITICAL] H1 제목 WordPress 중복 출력

**증상**: 포스팅에 제목이 2번 나타남 (WordPress 자동 삽입 + 본문 H1 중복)

**원인**: GPT가 본문 첫 줄에 `<h1>제목</h1>`을 포함하여 작성

**해결** (Phase 16):
```python
# publisher.py
def _strip_leading_h1(content: str) -> str:
    """본문 첫 H1 태그 제거 — WordPress 제목 중복 방지"""
    import re
    return re.sub(r'^\s*<h1[^>]*>.*?</h1>\s*', '', content, count=1, flags=re.DOTALL | re.IGNORECASE)
```

---

### 6-2. [MAJOR] parse_failed 루프 — JSON 파싱 무한 실패

**증상**: Gemini가 JSON을 반환해야 하는데 마크다운 코드블록(`\`\`\`json`)으로 감싸서 반환 → `json.loads()` 실패 → 재시도 → 동일 실패 반복

**원인**: Gemini 모델이 JSON 응답에 `\`\`\`json ... \`\`\`` 포맷을 사용

**해결** (Phase 16):
```python
def _safe_parse_json(raw: str) -> dict:
    """코드블록 마크다운 제거 후 JSON 파싱"""
    # 1차: 직접 파싱
    try:
        return json.loads(raw)
    except:
        pass
    # 2차: 코드블록 제거
    cleaned = re.sub(r'^```(?:json)?\s*', '', raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    try:
        return json.loads(cleaned)
    except:
        pass
    # 3차: 중괄호 추출
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"JSON 파싱 최종 실패: {raw[:200]}")
```

---

### 6-3. [MAJOR] 시제 혼용 — "지난주 상승했습니다" vs "상승할 것입니다"

**증상**: 동일 문단에서 과거/현재/미래 시제가 뒤섞임 → 신뢰도 저하

**원인**: GPT-4o가 단독으로 작성 시 시제 통일성 미보장

**해결** (Phase 15):
```python
# editorial_config.py
TEMPORAL_RULES = {
    "force_past_for_closed_events": True,   # 마감된 이벤트는 과거시제 강제
    "force_present_for_analysis": True,     # 분석/전망은 현재시제
    "ban_compound_tense": True,             # 복합시제 금지 ("상승했을 것입니다" 등)
    "settlement_date_rule": "current_month_past_month"  # 정산일 기준 시제
}

# Gemini 팩트체크 단계에서 시제 일관성 검증
```

---

### 6-4. [MAJOR] GitHub Actions 타임아웃 — 실행 30분 초과

**증상**: Phase 22 다중 테마(7포스팅) 도입 후 Actions가 30분 타임아웃으로 중단

**원인**: Post1×5 + Post2×2 = 7회 AI 호출 × (분석+작성+검수) = 21회 API 호출

**해결** (Phase 22):
```yaml
# .github/workflows/publish.yml
jobs:
  publish:
    timeout-minutes: 45   # 30 → 45분으로 상향
```

---

### 6-5. [MAJOR] WordPress 예약 발행 시간 오류 (9시간 차이)

**증상**: 오전 7시 예약이 오후 4시에 발행됨

**원인**: `date` 필드에 UTC를 넣었으나, WordPress가 site_tz 기준으로 해석

**해결** (Phase 22):
```python
# ✅ 올바른 방법: WordPress site_tz = Asia/Seoul인 경우 KST 그대로 전달
scheduled_dt = datetime.now(ZoneInfo("Asia/Seoul")) + timedelta(minutes=offset_minutes)
scheduled_at = scheduled_dt.strftime("%Y-%m-%dT%H:%M:%S")  # KST, TZ suffix 없이

# ❌ 잘못된 방법: UTC 변환 후 전달하면 9시간 오차 발생
```

---

### 6-6. [MEDIUM] OpenAI SDK v2 마이그레이션 Breaking Change

**증상**: `openai.ChatCompletion.create()` → `AttributeError`

**원인**: openai 라이브러리 v1 → v2 API 구조 변경

**해결**:
```python
# ✅ v2 방식
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "..."}],
    response_format={"type": "json_object"}  # JSON 모드 활성화
)
content = response.choices[0].message.content
tokens = response.usage  # .prompt_tokens, .completion_tokens

# ❌ v1 방식 (Deprecated)
import openai
response = openai.ChatCompletion.create(...)
```

---

### 6-7. [MEDIUM] Gemini google-genai SDK 구조 변경

**증상**: `genai.GenerativeModel()` → `AttributeError` or 동작 이상

**원인**: `google-generativeai` → `google-genai` 패키지명 변경 및 API 구조 리팩터링

**해결**:
```python
# ✅ 현재 방식 (google-genai ≥1.0.0)
from google import genai
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
response = client.models.generate_content(
    model="gemini-2.5-flash-preview-04-17",
    contents=prompt,
    config=genai.types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=4096
    )
)
text = response.text
# 토큰 사용량
usage = response.usage_metadata
# → .prompt_token_count, .candidates_token_count, .cached_content_token_count
```

---

### 6-8. [MEDIUM] pykrx 장 마감 전 데이터 미수집

**증상**: 오전 슬롯 실행 시 "오늘 시세 없음" 오류

**원인**: pykrx는 당일 장 마감(15:30) 이후에야 당일 종가 데이터 제공

**해결**:
```python
def get_stock_price(ticker: str) -> float:
    from pykrx import stock
    today = datetime.now().strftime("%Y%m%d")

    # 장 마감 전이면 전일 데이터 사용
    df = stock.get_market_ohlcv_by_date(today, today, ticker)
    if df.empty:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        df = stock.get_market_ohlcv_by_date(yesterday, yesterday, ticker)

    return float(df["종가"].iloc[-1]) if not df.empty else None
```

---

### 6-9. [CRITICAL] DART `company.json` stock_code 파라미터 미지원 → corpCode.xml 캐시 방식 전환

**증상**: `run_dart_financials(["005930"])` 호출 시 `status=100 message=필수값(corp_code)이 누락되었습니다` 오류, 재무 수치 0개 반환.

**원인**: `company.json` API는 `corp_code`(8자리 고유번호)를 **입력**으로 받는 엔드포인트이지, `stock_code`(6자리 종목코드)로 역방향 조회를 지원하지 않는다. 초기 구현에서 이 방향을 잘못 가정했다.

**해결** (Phase 5-A bugfix):
```python
# 1. corpCode.xml ZIP 다운로드 (전 상장사 코드 목록)
CORP_CODE_CACHE_FILE = Path("dart_corp_codes.json")
CORP_CODE_CACHE_TTL  = 86400  # 1일 (초)

def _load_corp_code_map() -> dict:
    """stock_code → corp_code 매핑 딕셔너리. 캐시 없거나 TTL 만료 시 재다운로드."""
    if CORP_CODE_CACHE_FILE.exists():
        data = json.loads(CORP_CODE_CACHE_FILE.read_text(encoding="utf-8"))
        if time.time() - data.get("_ts", 0) < CORP_CODE_CACHE_TTL:
            return data.get("map", {})

    key = _get_dart_api_key()
    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={key}"
    resp = requests.get(url, timeout=30)
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        xml_bytes = z.read("CORPCODE.xml")
    root = ET.fromstring(xml_bytes)

    mapping = {}
    for item in root.findall("list"):
        sc = (item.findtext("stock_code") or "").strip()
        cc = (item.findtext("corp_code") or "").strip()
        if sc and cc:
            mapping[sc] = cc

    CORP_CODE_CACHE_FILE.write_text(
        json.dumps({"_ts": time.time(), "map": mapping}, ensure_ascii=False),
        encoding="utf-8"
    )
    return mapping

def _stock_code_to_corp_code(stock_code: str) -> Optional[str]:
    """캐시에서 stock_code → corp_code 변환. 캐시 미스 시 None 반환."""
    corp_map = _load_corp_code_map()
    return corp_map.get(stock_code.strip())
```

**결과**: 삼성전자(005930) CFS 재무 조회 성공, 기업정보 2개 종목 정상 반환 확인.

**교훈**:
- OpenDART `company.json`은 `corp_code`를 알고 있을 때만 사용 가능.
- `stock_code → corp_code` 변환은 반드시 `corpCode.xml`(전체 목록 ZIP) 경유.
- 캐시 TTL 1일로 설정하면 API 호출 1회/일로 절약.
- `dart_corp_codes.json`은 `.gitignore`에 추가 (로컬 캐시 파일).

---

### 6-10. [MEDIUM] DART API 공시 중복 수집

**증상**: 동일 공시가 여러 번 발행 기사에 반영됨

**원인**: DART API에서 수정공시(`rcept_no` 동일)가 별도 항목으로 반환

**해결**:
```python
def deduplicate_disclosures(disclosures: list) -> list:
    """rcept_no 기준 중복 제거 (최신 수정본만 유지)"""
    seen = {}
    for d in sorted(disclosures, key=lambda x: x.get("rcept_dt", ""), reverse=True):
        key = d.get("rcept_no", "")[:14]  # 접수번호 앞 14자리 = 원공시 식별자
        if key not in seen:
            seen[key] = d
    return list(seen.values())
```

---

### 6-10. [MAJOR] Gemini REVISER 과도 축소 — 보존형 편집장 정책으로 해결

**증상**: Step3 REVISER가 수정 후 GPT 초안 대비 70~80%로 축소. 메인픽 분량 400자 미달. 이전 대비 품질 저하.

**원인**: REVISER 역할이 "편집자"로만 정의되어 분량 유지 목표 없이 자유롭게 축약.

**해결** (Phase 4.3):
```python
# GEMINI_REVISER_SYSTEM 핵심 추가 내용
"""
[★ 분량 보존 원칙 — 최우선 준수]
- 수정 후 HTML 총 글자 수는 원문의 90% 이상이어야 한다.
- 문장을 삭제하지 말 것. 삭제 대신 표현만 교체하라.
- 숫자, 출처, 인과관계 설명, 반대 포인트 — 이 4가지는 어떤 이유로도 삭제 금지.
- 메인 픽: 400자 미만이면 4구조 보완하여 400자 이상으로 확장.
- 보조 픽: 300자 미만이면 업황/반대포인트 추가하여 300자 이상으로 확장.
[★ 위스키/바텐더 비유 금지]
- 도입부에 이미 있는 경우, 수정 중 추가 생성 금지. 보강 목적 신규 비유 생성 금지.
"""
```

**보존율 측정 코드 (verify_draft 내부)**:
```python
draft_len   = len(draft)
revised_len = len(revised)
ratio = revised_len / draft_len * 100 if draft_len else 0
logger.info(f"Step3 수정본 채택 | GPT초안 {draft_len}자 → Step3수정본 {revised_len}자 ({ratio:.1f}% 보존)")
if ratio < 90:
    logger.warning(f"⚠ REVISER 과도 축소 감지: {draft_len - revised_len}자 감소")
```

**결과**: Post1 159.2%, Post2 115.8% 보존 실측 확인 (90% 기준 초과 달성).

---

### 6-11. [MAJOR] PICKS 주석 소실 + 검증 오류 (assemble_final_content 이후 검사 문제)

**증상 1**: `assemble_final_content()` 이후 본문에서 `<!-- PICKS: [...] -->` 주석이 사라짐. P10 검증 항목이 항상 FAIL.

**원인 1**: `assemble_final_content()`는 설계 상 PICKS 주석을 제거하는 함수. 그런데 P10 테스트를 최종 content에서 검사하면 항상 미존재 → FAIL.

**증상 2**: REVISER가 수정 과정에서 PICKS 주석을 누락 생성.

**해결**:
```python
# generate_stock_picks_report() 반환값에 raw 단계 플래그 추가
picks_comment_in_raw = bool(re.search(r"<!--\s*PICKS:", raw_content))
return {
    ...,
    "picks_comment_in_raw": picks_comment_in_raw,  # assemble 이전 raw 기준
}

# P10 검증: final_content 대신 picks_comment_in_raw 사용
has_picks_comment = post2.get("picks_comment_in_raw", False)

# PICKS 주석 자동 복원 (verify_draft 내부)
picks_in_draft   = "<!-- PICKS:" in draft
picks_in_revised = "<!-- PICKS:" in revised
if picks_in_draft and not picks_in_revised:
    picks_match = re.search(r"<!--\s*PICKS:.*?-->", draft, re.DOTALL)
    if picks_match:
        revised = revised.rstrip() + "\n" + picks_match.group(0)
```

**교훈**: 후처리 함수가 의도적으로 제거하는 마커를 최종 결과물에서 검증하면 항상 FAIL. 검증 기준을 처리 단계에 맞춰야 함.

---

### 6-12. [MEDIUM] 오탈자/중복 타이핑 — `[해해석]`, `미 미칠` 등 LLM 출력 패턴

**증상**: GPT 또는 Gemini 출력물에 `[해해석]`, `[전전망]`, `[해 해석]`, `미 미칠`, `을 을` 등 단어/태그 이중 출력 발생.

**원인**: LLM이 태그를 생성하다 중단 후 재시작하거나, 스트리밍 중 중복 입력 발생.

**해결** (Phase 5-A 후처리):
```python
def _fix_double_typing(text: str) -> str:
    """LLM 출력 오탈자 교정 — 태그/단어 이중 출력 제거"""
    # 태그 이중: [해해석] → [해석], [전전망] → [전망]
    text = re.sub(r'\[해\s*해석\]', '[해석]', text)
    text = re.sub(r'\[전\s*전망\]', '[전망]', text)
    # 한글 단어 즉시 중복: "미 미칠" → "미칠", "을 을" → "을"
    text = re.sub(r'(\b\w+)\s+\1\b', r'\1', text)
    # 연속 공백 정리
    text = re.sub(r'  +', ' ', text)
    return text
```

적용 위치: `assemble_final_content()`, `generate_deep_analysis()` Step3 수정본 채택 직후.

---

### 6-13. [MINOR] 참고 출처 섹션 단조로움 — 그룹화로 해결

**증상**: 참고 출처가 `<p>NH투자증권, 한국경제, Bloomberg...</p>` 형태의 단일 문자열로 나열.

**해결** (Phase 5-A):
```python
def _format_source_section(content: str) -> str:
    """참고 출처 섹션을 증권사 리서치 / 뉴스 기사 / 기타로 그룹화"""
    BROKER_KW = ["증권", "투자", "리서치", "자산운용", "캐피탈"]
    NEWS_KW   = ["경제", "일보", "뉴스", "Reuters", "Bloomberg", "CNBC",
                 "매경", "한경", "조선", "중앙", "동아", "연합"]
    # 출처 문자열 파싱 → 분류 → <ul><li> 그룹 구조로 재구성
    ...
```

**교훈**: 출처 분류는 키워드 기반이므로 신규 증권사(예: 카카오페이증권) 추가 시 `BROKER_KW` 확장 필요.

---

### 6-14. [MEDIUM] GitHub Actions Secrets 주입 실패

**증상**: Actions에서 `OPENAI_API_KEY=None` 오류

**원인**: Secrets는 `${{ secrets.VAR }}` 문법, Variables는 `${{ vars.VAR }}` 문법 혼용 필요

**해결** (publish.yml):
```yaml
- name: Inject secrets
  run: |
    echo "OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}" >> $GITHUB_ENV
    echo "GEMINI_API_KEY=${{ secrets.GEMINI_API_KEY }}" >> $GITHUB_ENV
    echo "WORDPRESS_USERNAME=${{ secrets.WORDPRESS_USERNAME }}" >> $GITHUB_ENV

    # .env 파일에도 동시 기록 (python-dotenv 대응)
    echo "OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}" >> .env
    echo "GEMINI_API_KEY=${{ secrets.GEMINI_API_KEY }}" >> .env
```

---

### 6-11. [MINOR] WordPress 앱 비밀번호 인증 오류

**증상**: `401 Unauthorized` 발행 실패

**원인**: WordPress 앱 비밀번호에 공백이 포함된 형태(`xxxx xxxx xxxx xxxx xxxx xxxx`)를 그대로 입력

**해결**:
```python
# 앱 비밀번호에서 공백 제거
password = os.getenv("WORDPRESS_PASSWORD", "").replace(" ", "")
```

---

### 6-12. [MAJOR] Post2 opener "오늘 이 테마를 보는 이유" 지속 생성

**증상**: Phase 16J에서 `_P16J_POST2_SAME_THEME_OPENER` 주입 후에도 generic H3 "오늘 이 테마를 보는 이유"가 계속 생성됨. GPT가 시스템 프롬프트 중간 위치의 금지 규칙을 무시.

**원인**: 규칙이 `system_msg` 또는 `user_msg` 중간에 삽입되어 우선순위 낮음.

**해결** (Phase 17):
```python
# gpt_write_picks() 내부 user_msg 구성
user_msg_parts = [
    _P17_POST2_OPENER_ENFORCEMENT,  # ★★ 최우선 (첫 번째 위치에 강제 주입)
    _P16J_POST2_SAME_THEME_OPENER,  # 기존 규칙
    # ... 나머지 컨텍스트
]
user_msg = "\n\n".join(user_msg_parts)
```

**결과**: Phase 17 샘플 5건 전부 pick-angle opener 생성 성공 (0/5 → 5/5).

---

### 6-13. [MAJOR] PARSE_FAILED TYPE_D — PICKS 주석 누락으로 fallback 발행

**증상**: Gemini verifier 응답이 JSON 파싱 불가 → step3_status=PARSE_FAILED → reviser skip → GPT 초안 원본 발행. 검수 없이 발행.

**원인**: Gemini가 verifier 응답을 `{"pass": true, ...}` JSON 대신 자연어 형태로 반환. PICKS 주석(`<!-- PICKS: [...] -->`)이 본문 500자 이상에서 누락된 경우(TYPE_D) 특히 발생률 높음.

**해결 방향** (Phase 17에서 관측 인프라 구축, Phase 18에서 정책 정교화 예정):
```python
# Phase 17: 분류 + 로그 (관측 인프라)
failure_type = _classify_parse_failed(raw, normalized)  # TYPE_D 등 자동 분류
_log_parse_failed_event(run_id, slot, post_type, failure_type, ...)  # 10필드 기록

# Phase 18 예정: TYPE별 발행 차단 정책
# TYPE_A (구조 전무) / TYPE_B (금지 패턴) / TYPE_C (HTML 파손) → 발행 차단 검토
# TYPE_D (PICKS 주석 누락) / TYPE_E (reviser 과도 축소) → 발행 허용 유지
```

**임시 운영 원칙**: `PARSE_FAILED` 시 `publish_blocked=False` (전 유형 발행 허용). TYPE_A~C 발생 시 수동 확인 필요.

---

### 6-14. [MEDIUM] verifier_revision_closure FAIL/WARN false positive

**증상**: Gemini reviser가 이슈를 실제로 수정했음에도 closure 재점검에서 FAIL/WARN 판정. "수정됐으나 새 이슈 발생"처럼 보이는 로그.

**원인**: Step3 verifier가 조건부 서술 표현(`가능성이`, `수 있습니다`, `된다면`)을 사실 오류로 오분류. reviser가 이를 수정하면 다른 문장에서 동일 패턴 재감지 → 무한 WARN 순환.

**해결**:
```python
# generator.py: STYLE_RESIDUAL_KW 등록 (합법적 조건부 표현)
STYLE_RESIDUAL_KW = [
    "가능성이",     # "~가능성이 높습니다" — 확률적 분석
    "수 있습니다",  # 조건부 서술
    "만약",         # 조건 시나리오
    "된다면",       # 조건 종속절
    "않는다면",     # 부정 조건
]
# 위 패턴 포함 미해소 이슈는 truly_unresolved에서 제외 → WARN으로 완화
```

**교훈**: `verifier_revision_closure: FAIL`이 반드시 발행 품질 문제를 의미하지 않음. 스타일 잔류 키워드(STYLE_RESIDUAL_KW)가 업데이트되지 않으면 false positive가 지속됨.

---

### 6-15. [MINOR] `_log_normal_publish_event` 제거 vs 복원

**배경**: Phase 19 Actions 이관 시 로컬 스케줄러 로그 함수를 제거했다가, Phase 19 후반에 복원.

**기능**: 각 포스팅 완료 시 `publish_result.jsonl`에 QA 결과 라인 기록
```json
{"run_id":"...","slot":"morning","post_type":"post1_2","final_status":"GO","public_url":"https://..."}
```
- **제거 시**: JSONL 로그 없음 → 주간 리포트에서 데이터 공백 발생
- **복원 이유**: Phase 20 주간 리포트가 이 JSONL을 파싱하여 집계하므로 필수

**결론**: 항상 유지해야 하는 함수. 제거 금지.

### 6-16. [MINOR] Python AST 탐지 — AnnAssign vs Assign 오탐

**증상**: `ast.walk(tree)` 후 `isinstance(node, ast.Assign)`으로 상수 존재 여부 확인 시 "not found" 오탐 발생. 해당 상수는 코드에 실제로 존재함.

**원인**: Python 타입 주석을 포함한 변수 선언(`var: str = value`)은 `ast.Assign`이 아닌 `ast.AnnAssign` 노드로 파싱됨.

```python
# ❌ 탐지 실패
_P16J_POST2_SAME_THEME_OPENER: str = "..."  # AnnAssign → ast.Assign으로 탐지 불가

# ✅ 올바른 탐지 방법
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == VAR_NAME:
                found = True
    elif isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name) and node.target.id == VAR_NAME:
            found = True

# 또는 grep 기반으로 검증 (더 간단)
# grep로 확인 후 AST 검사 생략하는 것도 실용적 선택
```

**교훈**: 코드 존재 여부 확인 시 AST보다 grep(ripgrep)이 오탐 없이 빠름. AST는 구조 분석에만 사용.

---

## 7. WordPress 연동 노하우

### 7-1. REST API 인증

```python
import requests
from requests.auth import HTTPBasicAuth

WP_URL = os.getenv("WORDPRESS_SITE_URL")
auth = HTTPBasicAuth(
    os.getenv("WORDPRESS_USERNAME"),
    os.getenv("WORDPRESS_PASSWORD").replace(" ", "")  # 공백 제거 필수
)

# 포스팅 발행
response = requests.post(
    f"{WP_URL}/wp-json/wp/v2/posts",
    json=payload,
    auth=auth,
    timeout=30
)
```

### 7-2. 카테고리 동적 생성 패턴 (Phase 22)

```python
# category_cache.json 구조
# { "2:반도체": 15, "2:2차전지": 18, "3:SK하이닉스": 22 }

def get_or_create_wp_category(theme_name: str, parent_id: int) -> int:
    cache = _load_category_cache()
    key = f"{parent_id}:{theme_name}"

    if key in cache:
        return cache[key]

    # REST API로 기존 카테고리 검색
    resp = requests.get(f"{WP_URL}/wp-json/wp/v2/categories",
                        params={"search": theme_name, "parent": parent_id}, auth=auth)
    for cat in resp.json():
        if cat["name"] == theme_name and cat["parent"] == parent_id:
            cache[key] = cat["id"]
            _save_category_cache(cache)
            return cat["id"]

    # 없으면 신규 생성
    resp = requests.post(f"{WP_URL}/wp-json/wp/v2/categories",
                         json={"name": theme_name, "parent": parent_id}, auth=auth)
    cat_id = resp.json()["id"]
    cache[key] = cat_id
    _save_category_cache(cache)
    return cat_id
```

### 7-3. 이미지 첨부 (Featured Media)

```python
# 1. 이미지 업로드
with open(image_path, "rb") as f:
    resp = requests.post(
        f"{WP_URL}/wp-json/wp/v2/media",
        headers={"Content-Disposition": f'attachment; filename="{filename}"',
                 "Content-Type": "image/jpeg"},
        data=f.read(),
        auth=auth
    )
media_id = resp.json()["id"]

# 2. 포스트에 연결
payload["featured_media"] = media_id
```

---

## 8. GitHub Actions 운영 노하우

### 8-1. 크론 스케줄 (KST 기반)

```yaml
schedule:
  - cron: '50 21 * * *'   # KST 06:50 → morning 슬롯
  - cron: '10 5  * * *'   # KST 14:10 → evening 슬롯
  - cron: '35 12 * * *'   # KST 21:35 → us_open (DST)
  - cron: '35 13 * * *'   # KST 22:35 → us_open (non-DST)
```

> **주의**: GitHub Actions cron은 UTC 기준. KST = UTC+9 이므로 `크론 UTC = KST - 9`

### 8-2. 동시성 제어

```yaml
concurrency:
  group: macromalt-publish
  cancel-in-progress: false  # 이전 run 완료 후 다음 시작 (중복 방지)
```

### 8-3. 타임존 설정

```yaml
env:
  TZ: Asia/Seoul   # 전체 실행 환경을 KST로 고정
```

### 8-4. Artifact 업로드 (로그 보관)

```yaml
- name: Upload logs
  uses: actions/upload-artifact@v4
  if: always()   # 실패해도 로그 업로드
  with:
    name: macromalt-logs-${{ github.run_number }}
    path: |
      logs/macromalt_daily.log
      logs/publish_result.jsonl
    retention-days: 30
```

### 8-5. Variables vs Secrets 사용 기준

| 구분 | 사용 예 | GitHub UI |
|------|---------|---------|
| **Secrets** | API 키, 비밀번호 | Settings → Secrets → Actions |
| **Variables** | 타임존, 슬롯 간격 등 비민감 설정 | Settings → Variables → Actions |

```yaml
# Secrets: ${{ secrets.VAR_NAME }}
# Variables: ${{ vars.VAR_NAME }}
```

---

## 9. 비용 관리 노하우

### 9-1. Phase 22 기준 비용 구조

| 슬롯 | GPT 호출수 | Gemini 호출수 | 예상 비용 |
|------|-----------|-------------|---------|
| morning | 7 Post × 3단계 = 21회 | 1(테마)+7(분석)+7(검수) = 15회 | GPT~$0.55, Gemini~₩100 |
| evening | 동일 | 동일 | 동일 |
| us_open | 동일 | 동일 | 동일 |
| **1일 합계** | 63회 | 45회 | GPT~$1.65, Gemini~₩300 |
| **월 합계** | ~1,890회 | ~1,350회 | **GPT~$49, Gemini~₩9,000** |

### 9-2. OpenAI 캐시 활용 (Phase 23)

- **캐시 조건**: 프롬프트 길이 ≥ 1,024 토큰, 동일 프롬프트 prefix
- **현재 시스템 프롬프트**: 3,000~4,000 토큰 → 자동 캐싱 대상
- **절감률**: 캐시 히트 시 입력 토큰 75% 할인
- **예상 월 절감**: $7~10 (캐시 히트율 70~85% 가정)

```python
# 캐시 토큰 확인
usage = response.usage
cached_tokens = getattr(usage.prompt_tokens_details, "cached_tokens", 0)
regular_tokens = usage.prompt_tokens - cached_tokens

cost = (regular_tokens * 2.50 + cached_tokens * 0.625) / 1_000_000
```

### 9-3. 비용 급증 방지 체크리스트

- [ ] `OPENAI_LIMIT_USD` 설정 확인 (현재 $60)
- [ ] `GEMINI_LIMIT_KRW` 설정 확인 (현재 ₩14,000)
- [ ] API 대시보드 월 한도 설정과 일치 여부 확인
- [ ] 95% 알림 수신 후 즉시 Actions disable 또는 API 키 임시 교체
- [ ] 테스트 실행 시 mock 모드 또는 `--dry-run` 플래그 사용

---

## 10. 품질 보증 체계

### 10-1. 3단계 검증 파이프라인

```
[1단계] Gemini 분석 품질
  └── 입력 뉴스 신뢰도 점수 > 0.6 이상만 처리

[2단계] GPT 작성 품질 (Phase 16~18 안정화)
  ├── 시제 일관성 검증
  ├── 숫자/통계 출처 명시 여부
  ├── H1 중복 제거
  └── 최소 길이 기준 (1,500자 이상)

[3단계] Gemini 팩트체크 (Phase 7~)
  ├── 데이터 포인트 교차 검증
  ├── 주가/지표 수치 이상값 탐지
  └── 필요 시 1회 자동 수정 후 재검수
```

### 10-2. Phase 20 QA 체계 (Editorial Planner + Verifier 구조 검사)

#### Verifier 기준 26~30 (Phase 20-4 신규)

| 기준 | 검사 항목 | 위반 시 |
|------|----------|---------|
| **26. 섹션 동형 반복** | 연속 2개+ 섹션이 "주장→수치→시사" 3단 구조 반복 | pass=false |
| **27. 강조 분산** | 3개+ 섹션 균등 배분, 명확한 lead 섹션 부재 | pass=false |
| **28. 리드 드리프트** | 도입부 핵심 각도가 중반 이후 사라짐 | pass=false (뚜렷한 경우) |
| **29. 일반 문장 과잉** | 숫자·날짜·인과·출처 없는 문장 40%+ | pass=false |
| **30. 근거 없는 단정** | consensus_miss/underpriced_risk 계열 단정 근거 없이 서술 | pass=false |

> **적용 우선순위**: 26번(섹션 동형 반복), 28번(리드 드리프트) 엄격 적용

#### Reviser 허용 범위 11~12번 (Phase 20-4 신규)

```
11. 섹션 동형 반복 → 반복 섹션 opener를 역접형/인과형/질문형으로 교체
    (수치·논리 원문 보존, 섹션 길이 유지)
12. 리드 논거 약화 → counterpoint 직전 섹션 끝에 lead 연결 문장 1개 추가
    (날짜·수치 발명 금지, 기존 사실만 참조, 추가 문장 1개 제한)
```

#### lead_metrics 이중 지표 (Python-level 정량 모니터링)

| 지표 | WARN 기준 | 의미 |
|------|---------|------|
| `lead_recall` | < 0.5 | lead_ids 절반 이상 미사용 |
| `lead_focus` | < 0.25 | 사용 facts 중 lead 비중 25% 미만 (균등 배분 회귀) |

#### QA 플로우 전체 (Phase 20 완성 기준)

```
[Step 1] Gemini 분석 → facts + perspective_fields (stance_type, why_now, ...)
[Step 1.5] Planner → lead_angle 선택 → 4-tier contract 생성
[Step 2] GPT 작성 (contract 소비) → HTML + evidence_ids_used 주석
[Step 2.5] _check_p20_lead_metrics() → lead_recall / lead_focus 계산 → WARN 로그
[Step 3] Gemini Verifier (기준 1~30) → pass/fail → 필요 시 Reviser 실행
[Step 4] 발행 → publish_result.jsonl 기록 (GO/WARN/HOLD)
```

### 10-3. Phase 19 JSONL 품질 로그

```json
// logs/publish_result.jsonl
{"run_id":"20260326_070533","slot":"morning","post_type":"post1_1",
 "final_status":"GO","opener_pass":1,"criteria_1_pass":1,"criteria_5_pass":1,
 "source_structure_pass":1,"public_url":"https://macromalt.com/?p=12345"}
```

**`final_status` 값**:
- `GO`: 품질 기준 통과, 정상 발행
- `WARN`: 경고 있으나 발행 (세부 항목 중 1개 실패)
- `HOLD`: 발행 보류 (2개 이상 실패)

---

## 11. 환경 설정 완전 가이드

### 11-1. .env 파일 (전체)

```env
# ====== 필수 (없으면 실행 불가) ======

# OpenAI (유료)
OPENAI_API_KEY=sk-proj-...

# Google Gemini (유료, 단 월 무료 한도 있음)
GEMINI_API_KEY=AIzaSy...

# WordPress (무료)
WORDPRESS_SITE_URL=https://your-blog.com
WORDPRESS_USERNAME=your-username
WORDPRESS_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx   # 앱 비밀번호 (공백 포함 가능)

# ====== 권장 (없으면 일부 기능 비활성화) ======

# 한국 공시 (무료)
DART_API_KEY=abc123...

# 한경 컨센서스 (무료 가입)
HANKYUNG_USERNAME=...
HANKYUNG_PASSWORD=...

# 미국 연준 거시지표 (무료)
FRED_API_KEY=...

# 한국은행 거시지표 (무료)
BOK_API_KEY=...

# 이미지 (무료, 월 50회)
UNSPLASH_ACCESS_KEY=...

# ====== 선택 ======

# 타임존 (기본: Asia/Seoul)
TIMEZONE=Asia/Seoul
```

### 11-2. GitHub Actions Secrets 목록

```
OPENAI_API_KEY
GEMINI_API_KEY
DART_API_KEY
WORDPRESS_SITE_URL
WORDPRESS_USERNAME
WORDPRESS_PASSWORD
HANKYUNG_USERNAME
HANKYUNG_PASSWORD
FRED_API_KEY
BOK_API_KEY
UNSPLASH_ACCESS_KEY
```

### 11-3. GitHub Actions Variables 목록

```
TIMEZONE=Asia/Seoul
SCRAPE_INTERVAL_MINUTES=60
```

---

## 12. 운영 트러블슈팅 매뉴얼

### 12-1. 자주 발생하는 오류 vs 해결

| 증상 | 가능한 원인 | 즉시 조치 |
|------|-----------|---------|
| Actions 실패, 로그 없음 | 환경 변수 누락 | Secrets 목록 재확인 |
| "수집 기사 0건" | sources.json 오류 또는 블락 | RSS URL 직접 접근 테스트 |
| "WordPress 401 Unauthorized" | 앱 비밀번호 오류 | WP 관리자에서 앱 비밀번호 재발급 |
| "GPT 호출 실패 (429)" | API 한도 초과 | 대시보드 사용량 확인, 월말 초과 여부 체크 |
| "예약 발행 시간 오류 (+9h)" | date TZ 설정 오류 | KST 그대로 전달, UTC 변환 하지 말 것 |
| "카테고리 중복 생성" | category_cache.json 손상 | 파일 삭제 → 재생성 (자동 복구) |
| Actions 45분 초과 | Post 생성 시간 증가 | timeout-minutes 60으로 증가 |
| 동일 테마 반복 발행 | publish_history.json 손상 | 파일 초기화 또는 삭제 |

### 12-2. 로그 분석 방법

```bash
# 최근 실행 로그 확인
tail -200 logs/macromalt_daily.log

# 비용 현황
python -m cost_tracker

# 품질 로그 분석 (최근 10건)
tail -10 logs/publish_result.jsonl | python -m json.tool

# HOLD 상태 포스트 확인
grep '"final_status":"HOLD"' logs/publish_result.jsonl

# 테마 중복 확인
cat publish_history.json | python -m json.tool
```

### 12-3. 긴급 중단 방법

```
1. GitHub → Repository → Actions 탭
2. 현재 실행 중인 Workflow 선택
3. "Cancel run" 클릭

또는

1. GitHub → Settings → Actions → General
2. "Disable Actions for this repository"
```

---

## 부록: 주요 설계 결정 배경

| 결정 | 선택한 방향 | 이유 |
|------|-----------|------|
| 분석 모델 | Gemini 2.5-flash | 비용 대비 분석력 우수, JSON 반환 안정 |
| 작성 모델 | GPT-4o | 한국어 글쓰기 품질 최상위 |
| 검수 모델 | Gemini (Gemini로 통일) | 비용 절감 + GPT 자기검증 편향 회피 |
| 발행 방식 | WordPress REST API | XML-RPC 대비 안정적, 예약 발행 지원 |
| 자동화 | GitHub Actions | 서버리스, 무료 한도 충분, Secret 관리 편리 |
| 카테고리 | 동적 생성 + JSON 캐시 | 테마 예측 불가 → 유연한 구조 필요 |
| 스케줄 | 하루 3슬롯 (morning/evening/us_open) | 한국 투자자 활동 시간대 최적화 |

---

## 13. AI 글쓰기 품질 개선 Know-How

### 13-1. "AI처럼 읽힌다"의 진짜 원인

> **어휘 교체(상투어 제거)로는 해결 불가.** 근본 원인은 파이프라인 인식 구조에 있다.

| 표면 증상 | 실제 원인 |
|-----------|---------|
| 모든 섹션이 비슷한 구조 | GPT가 facts를 균등 배분하기 때문 |
| "왜 오늘 이게 중요한가"가 없음 | 중요도 결정 레이어 부재 |
| 동형 섹션 반복 | lead_angle이 없으면 모든 섹션이 동등한 서술 단위 |
| 단정적 표현 과잉 | stance 근거 없이 분석 결론을 단정 |

**핵심 해법**: GPT를 "fact serializer"에서 "thesis-expansion engine"으로 전환
- Before: `raw facts JSON → GPT → HTML`
- After: `facts → planner(lead 선택) → pre-sorted contract → GPT → HTML`

---

### 13-2. stance_type 5종 열거

근거 없는 stance 사용 방지를 위해 freeform 대신 열거형으로 제한:

| stance | 의미 | 사용 조건 |
|--------|------|---------|
| `consensus_miss` | 시장 컨센서스가 놓친 각도 | analyst_surprise.level = strong |
| `underpriced_risk` | 시장이 저평가한 리스크 | why_now + risk_of_overstatement 필수 |
| `overread` | 시장이 과대해석한 이슈 | 반대 evidence_ids 필수 |
| `low_confidence` | 불확실성이 높아 판단 유보 | confidence=low facts가 lead일 때 |
| `neutral` | 중립 서술 | 근거 불충분 시 강제 할당 |

---

### 13-3. narrative_shape 3종

글의 진입 방식을 제어하여 섹션 opener 단조로움 방지:

| shape | 구조 | 효과 |
|-------|------|------|
| `conclusion_first` | 결론 → 근거 | 핵심 주장이 리드에 나옴 |
| `contradiction_first` | 반례/역설 → 분석 | 독자 주의 집중 |
| `question_first` | 질문 → 답 | 분석 흐름을 독자 관점으로 구성 |

---

### 13-4. Post1 vs Post2 planner 역할 분리

두 포스트 유형을 동일한 planner로 처리하면 적합하지 않은 angle이 생성됨.

| Post | Planner 초점 | 금지 패턴 |
|------|-------------|---------|
| **Post1** (매크로 분석) | macro_mechanism / transmission_path / market_structure / counterpoint | 종목 pick 언급 금지 |
| **Post2** (종목 픽) | pick_trigger / stock_sensitivity / selection_logic / counterpoint | pick_trigger 없이 시작 금지 |

---

### 13-5. evidence_ids 기반 설계 원칙

**근거 없는 주관적 표현 방지를 위한 ID 추적 설계:**

1. Gemini Step1에서 모든 사실에 `id` 부여 (`fact_1`, `fact_2`, `bg_1`, ...)
2. Planner가 `lead_angle.evidence_ids`, `why_now.evidence_ids` 등 모든 주장에 근거 id 첨부
3. `_validate_planner_evidence_ids()`: id 불일치 시 해당 claim 제거 (hallucination 방지)
4. Writer 출력 주석에서 실제 사용 id 추출 → `_check_p20_lead_metrics()` 입력
5. `lead_recall + lead_focus` 계산으로 writer가 contract를 실제로 따랐는지 검증

**설계 원칙**: "근거 id 없는 주장은 claim 자격 없음"

---

### 13-6. STYLE_RESIDUAL_KW 분류 주의점

Gemini Verifier가 조건부 분석 서술을 사실 오류로 오분류하는 패턴 주의:

```python
# 오분류되기 쉬운 합법적 표현들 (STYLE_RESIDUAL_KW에 등록 필요)
"가능성이",     # "~가능성이 높습니다" — 확률적 분석
"만약",         # 조건부 시나리오
"수 있습니다",  # 조건부 서술
"된다면",       # 조건 종속절
"않는다면",     # 부정 조건
"숫자나 기준",  # [기준10] writing quality 지적 (사실 오류 아님)
```

`truly_unresolved`로 분류되면 `verifier_revision_closure: FAIL` → 발행 차단.
새로운 조건부 표현이 추가될 때마다 `STYLE_RESIDUAL_KW` 업데이트 필요.

---

### 13-7. _log_normal_publish_event 제거 금지

Phase 19 Actions 이관 시 실수로 제거 → Phase 20 주간 리포트 데이터 공백 발생.

**이 함수가 없으면**: `publish_result.jsonl` 미기록 → `phase20_weekly_report.py` 집계 불가 → 주간 리포트 빈 파일 생성.

> **규칙**: `_log_normal_publish_event()`는 항상 유지. 리팩터링 시 제거 금지.

---

---

## 14. Phase 5~17 파이프라인 진화 Know-How

### 14-1. Fingerprint 기반 반복 완화 엔진 (Phase 11)

**문제**: 동일 테마(예: "중동 리스크")가 연일 반복 발행됨.

**해결**: 3차원 fingerprint로 테마·축·종목 유사도를 복합 판단.

```python
# Phase 11 핵심 함수들
_make_theme_fingerprint(theme_text)  # macro 10종 keyword → frozenset
_make_axes_fingerprint(step1_json)   # sub_axes 11종 → frozenset
_make_ticker_buckets(picks_list)     # 섹터 버킷 8종 → dict

# 발행 이력 5건(publish_history.json)과 비교 → STRONG/MODERATE/WEAK 감지
_p16j_check_theme_repeat(current_theme)  # Phase 16J에서 더 정밀화
```

**운영 원칙**: `publish_history.json`이 손상되면 자동으로 반복 방지가 풀림. 파일 손상 시 빈 배열 `[]`로 초기화 (완전 삭제 금지).

---

### 14-2. DART 연동 3종 패턴 (Phase 5~6)

```python
# 1. 공시 스캔 (최근 N일치 신규 공시)
disclosures = run_dart_disclosure_scan(days=3)

# 2. 재무정보 (연간/분기 수치 — 실적 근거용)
financials = run_dart_financials(corp_code="005930", bgn_de="20250101")

# 3. 기업 기본정보 (업종/상장시장 등 맥락용)
corp_info = run_dart_company_info(stock_code="005930")

# 수정공시 중복 제거 (Phase 6 추가)
# rcept_no 앞 14자리 기준 — 같은 공시의 수정본은 최신만 유지
```

---

### 14-3. 한경컨센서스 세션 로그인 (Phase 6)

**문제**: 한경컨센서스는 로그인 세션이 있어야만 컨센서스 데이터 접근 가능.

```python
# scraper.py 내 세션 관리 패턴
session = requests.Session()
login_payload = {"userId": USERNAME, "userPwd": PASSWORD}
session.post(LOGIN_URL, data=login_payload)
# 이후 session.get()으로 컨센서스 데이터 요청 (쿠키 자동 포함)
```

**주의**: 세션 만료 시 자동 재로그인 로직 필요. 응답 HTML에 "로그인" 문자열 포함 여부로 세션 유효성 판단.

---

### 14-4. 품질 게이트 단계별 진화 이력

Phase가 진행되면서 품질 검증 기준이 누적된 방식:

| Phase | 추가된 검증 레이어 | 목적 |
|-------|-----------------|------|
| 7~9 | 기준5: 권유성 표현 금지 | "매수/유망/담아야 한다" 등 제거 |
| 13 | `_score_interpretation_quality()` | hedge 과잉 / weak 해석 탐지 |
| 14I | `_detect_interp_hedge_density()` | 헤징 어미 10종 밀도 측정 |
| 15A~E | 복합 시제 regex 5레이어 | 시제 일관성 |
| 16 | Temporal SSOT 전 레이어 주입 | 근본적 시제 오류 원천 차단 |
| 16B | `_p16b_calc_intro_overlap()` | Post1/Post2 도입부 중복 감지 |
| 16F | `_p16f_check_bridge_alignment()` | 브릿지-픽 정합성 |
| 16J | `_p16j_check_theme_repeat()` + `_P16J_POST2_SAME_THEME_OPENER` | 동일 theme 연속 슬롯 감지 → Post2 opener 각도 다양화 조건부 주입 |
| 17 | opener H3 패턴 + PARSE_FAILED TYPE | opener 각도 품질 + 런타임 오류 분류 |
| 20 | Verifier 기준 26~30 + lead_metrics | 편집 구조 품질 + planner 준수율 |

---

### 14-5. 운영 중 발견된 반면교사 패턴

| 실수 | 결과 | 올바른 접근 |
|------|------|-----------|
| 규칙을 프롬프트 중간에 삽입 | GPT가 무시 (Phase 16K~17 opener 문제) | 최우선 위치(첫 번째)에 강제 주입 |
| PARSE_FAILED를 "0건=정상"으로 표현 | 실제 발생 케이스 숨김 | "발생 시 분류·로그·fallback 확인됨"으로 표현 |
| step3 FAIL = 발행 품질 나쁨으로 단순 해석 | STYLE_RESIDUAL_KW false positive 혼동 | closure 상태와 실제 발행 품질 분리 판단 |
| `_log_normal_publish_event` 제거 | Phase 20 주간 리포트 데이터 공백 | 함수 항상 유지 (제거 금지) |
| CSS 인라인 상수 generator.py에 직접 작성 | 스타일 변경 시 수백 줄 수정 필요 | styles/tokens.py 분리 (Pre-Phase 17) |
| handoff 없이 대화 종료 | 다음 대화에서 맥락 완전 소실 | Phase 종료마다 통합 핸드오프 문서 작성 |
| `ast.Assign`으로 타입 주석 할당 탐지 | `AnnAssign`은 탐지 못 함 (false "not found") | `isinstance(node, (ast.Assign, ast.AnnAssign))` 병용 |
| CONDITIONAL GO 상태에서 계열 종료 진행 | 잔여 이슈가 누적될 경우 다음 세션에서 맥락 소실 | CONDITIONAL GO 종료 시 반드시 Phase 17 우선순위 항목 + 잔여 이슈 목록을 total handoff에 명시 |
| OpenDART `company.json`에 stock_code 직접 전달 | `status=100` 오류, 재무 수치 0건 | `corpCode.xml` ZIP 다운로드 → 로컬 캐시 매핑 경유 (6-9 참조) |
| REVISER를 역할 지정 없이 단순 편집자로 정의 | GPT 초안 대비 70~80% 축소, 품질 저하 | "보존형 편집장" 명시 + 90% 보존 강제 + 분량 미달 시 보강 규칙 (6-10 참조) |
| PICKS 주석 검증을 assemble_final_content() 이후 content에서 수행 | 설계상 주석 제거 함수이므로 P10 항상 FAIL | 반환값에 `picks_comment_in_raw` 필드 추가 → raw 단계에서 검증 (6-11 참조) |

---

### 14-6. Phase 4.3 자동 검증 체계 Know-How

#### 설계 배경

글 생성 후 품질을 사람이 매번 확인하면 운영 비용 급증. `__main__` 진입점에 자동 검증 기준을 내장해 CI 수준의 품질 보증 구현.

#### Post1 14개 기준 / Post2 10개 기준

**Post1 핵심 기준:**

| 번호 | 기준 | 판단 방식 |
|------|------|---------|
| 1 | Gemini 출력 구조화 JSON 여부 | `isinstance(materials, dict) and "theme" in materials` |
| 8 | 위스키·바텐더 비유 1회 이하 | regex count (도입부 이후 제외) |
| 11 | 숫자 없는 문단 연속 2개 미만 | 반대시각·체크포인트 섹션 **예외 처리** 적용 |
| 12 | 완충 문장 4회 미만 | "긍정적이다", "수혜가 예상된다" 등 패턴 카운트 |

**Post2 핵심 기준:**

| 번호 | 기준 | 판단 방식 |
|------|------|---------|
| P4 | 보조픽 분량 ≥ 300자 | `_log_picks_section_lengths()` 실측값 |
| P6 | 왜지금 구조 | 현재 시점 트리거 키워드 (`수주`, `실적`, `공시` 등) 포함 여부 |
| P8 | 반영변수(PER/수급/괴리율) | 밸류에이션 키워드 포함 여부 |
| P10 | PICKS 주석 존재 | `picks_comment_in_raw` 필드 — assemble 이전 raw 기준 |

#### 11번 기준 예외 처리 (반대시각/체크포인트 섹션)

반대 시각, 리스크 섹션은 의도적으로 정성적 서술. 숫자 없는 문단이 연속으로 나와도 정상.

```python
_EXEMPT_SECTIONS = ["반대 시각", "체크포인트", "반대포인트", "리스크 요인", "불확실"]
_cur_h3 = ""
for _tag in _soup.find_all(["h3", "p"]):
    if _tag.name == "h3":
        _cur_h3 = _tag.get_text(strip=True)
        cur = 0
    elif _tag.name == "p":
        if any(kw in _cur_h3 for kw in _EXEMPT_SECTIONS):
            continue  # 해당 섹션 카운터 제외
```

#### `_strip_code_fences()` 공통 헬퍼

GPT/Gemini 출력에서 코드펜스, 백틱 래퍼, 설명 텍스트를 공통 제거. 모든 게시 경로에서 일관 적용.

```python
def _strip_code_fences(text: str) -> str:
    text = re.sub(r"^```(?:html)?\s*\n?", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\n?```\s*$", "", text, flags=re.IGNORECASE)
    # 문서 내 잔여 코드펜스, 따옴표 래퍼, HTML 앞뒤 설명 텍스트 추가 제거
    ...
    return text.strip()
```

**적용 위치**: `assemble_final_content()`, `generate_deep_analysis()` draft, `generate_stock_picks_report()` draft, `verify_draft()` Step3b 수정본 — 총 4곳.

#### P6(왜지금) / P8(반영변수) 프롬프트 강화 패턴

단순 "테마와 관련 있기 때문"이 P6를 통과하지 못하도록 GPT_WRITER_PICKS_SYSTEM에 ✅/❌ 예시 명시:

```
문장 1 — 왜 지금 이 종목인가 [P6 강화]
✅ 충족: "이번 주 NVIDIA 실적 발표 후 HBM 공급사에 수주 문의가 집중됐기 때문이다"
❌ 불충족: "AI 인프라 투자 확대 테마에서 수혜가 기대되는 종목이기 때문이다"

문장 4 — 반영 변수 [P8 강화]
✅ 충족: "HBM 기대감은 이미 주가에 반영돼 PER이 역사적 평균 대비 40% 프리미엄 구간이다"
❌ 불충족: "글로벌 경기 둔화와 불확실성이 리스크로 존재한다"
```

---

### 14-7. DART 공시 → Gemini facts 주입 파이프라인 (Phase 5-A)

#### 전체 데이터 흐름

```
run_dart_disclosure_scan(days=14)        # 전체 시장 100건 공시 스캔 (심층분석용)
    ↓ format_dart_for_prompt()
    ↓ {dart_text} → GEMINI_ANALYST_USER 주입
    ↓ Gemini가 공시 이벤트를 facts로 필터링 (테마 관련성 판단)

gemini_select_tickers_v2()               # 픽 종목 확정 후
    ↓
run_dart_financials(kr_stock_codes)      # KR 픽 종목만 재무 조회 (좁게)
run_dart_company_info(kr_stock_codes)
    ↓ format_dart_for_prompt(financials=..., company_info=...)
    ↓ context_text에 병합 → GPT_WRITER_PICKS_SYSTEM 참고 데이터로 주입
```

#### DART_DISCLOSURE_EVENT_MAP 키워드 매핑 (확장 가능 상수)

```python
DART_DISCLOSURE_EVENT_MAP: dict = {
    "단일판매":      "수주계약",
    "공급계약":      "수주계약",
    "자기주식 취득": "자사주취득",
    "유상증자":      "유상증자",
    "전환사채":      "CB발행",
    "신주인수권부사채": "BW발행",
    "합병":          "합병",
    "소송":          "소송",
    ...
}
# → 새 이벤트 추가 시 이 딕셔너리만 수정. 코드 전체 변경 불필요.
```

#### 재무 수치 YoY 비교 구조

```python
# fnlttSinglAcnt 응답 → accounts 딕셔너리
accounts["매출액"] = {
    "thstrm": 300151643,  # 당기 (백만원)
    "frmtrm": 258935494,  # 전기 (백만원) — YoY 비교 가능
    "unit":   "백만원",
}
# 부채비율: 직접 계산 (부채총계 / 자본총계 × 100)
# CFS(연결재무제표) 우선, 없으면 OFS(개별재무제표) fallback
```

#### API_KEY 미설정 시 파이프라인 안전 보장

```python
def _get_dart_api_key() -> str:
    key = os.getenv("DART_API_KEY", "").strip()
    if not key:
        raise ValueError("DART_API_KEY 미설정")  # _dart_get() 내부에서 catch
    return key

def _dart_get(endpoint, params, label="") -> dict | None:
    try:
        key = _get_dart_api_key()
    except ValueError as e:
        logger.warning(f"[DART{label}] {e}")
        return None  # ← None 반환으로 파이프라인 계속 진행
```

`dart_text=""` 기본값으로 DART 키 없는 환경에서도 `GEMINI_ANALYST_USER.format(dart_text="")` 정상 동작.

---

### 14-8. 보고서 작성 기준 (Phase 17 확정)

Phase 17에서 확정된 상세 보고서 작성 기준 (`PHASE17_REPORT_FULL_BODY_REQUIREMENT.md`):

| 필수 항목 | 내용 |
|---------|------|
| Post ID | WordPress post ID |
| 발행 시각 | 실제 발행 timestamp |
| 최종 H2/H3 구조 | 목차 전체 |
| 발행본 본문 전체 | URL만 나열 금지 — 본문 텍스트 직접 포함 |
| opener H3 문구 | pick-angle 여부 검증 |
| opener 첫 2~3문장 | 별도 발췌 |
| 메인 픽 포함 여부 | opener 첫 문장에 픽명 명시 확인 |
| 금지 패턴 미포함 여부 | 6종 generic 패턴 점검 |
| 참고 출처 포함 여부 | 증권사 리서치 / 뉴스 / 기타 구조 |
| verifier/reviser 로그 | 이슈 건수, 보존율, closure 상태 |

**제외 항목**: 커밋 해시, main 푸시 여부, Git 상태 전반 (사용자 별도 검증).

**최종 판정 표현 원칙**: GO를 "전면 완료"가 아닌 "핵심 범위 기준 GO"로 범위 한정. 잔여 이슈와 Phase 인계 포인트 반드시 분리 명시.

---

*END — REPORT_TECHNICAL_KNOWHOW_V1.md*
*Phase 23 기준 최종 갱신: 2026-03-26 (Phase 17 항목 보강 포함)*
*2026-03-13 보강: Phase 4.3 자동 검증 체계 + Phase 5-A DART 연동 상세 + 에러 사례 6-9~6-13 신규 추가*
*다음 갱신 예정: Phase 24 (FastAPI SaaS 서버) 또는 SEO/수익화 트랙 완료 시*
