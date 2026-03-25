# macromalt 기술 종합 Know-How 보고서 V1

> 작성일: 2026-03-26 | 대상: 내부 참조 / 신규 개발자 온보딩 | Phase 23 기준

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
| **Phase 14** | 초기 | 기본 파이프라인 (수집→생성→발행) |
| **Phase 15** | 2026-03-17 | **시제 강제화** — 과거/현재/미래 혼용 금지, 복합시제 교정 핫픽스(A~E) |
| **Phase 16** | 2026-03-18 | **출력 품질 경화** — H1 중복 제거, 연속성 검증, 테마 로테이션, parse_failed 표준화 |
| **Phase 17** | 2026-03-19 | **스타일 토큰 중앙화** — `styles/tokens.py` 분리, CSS 하드코딩 제거 |
| **Phase 18** | 2026-03-20 | **4축 안정화** — closure 오류, fallback 누락, parse_failed 루프, 반복 테마 방지 |
| **Phase 19** | 2026-03-20 | **GitHub Actions 이관** — 로컬 스케줄 → CI/CD 완전 이관, 품질로그(JSONL) 시스템 |
| **Phase 20** | 2026-03-23 | **Editorial Planner + QA 체계** — Lead Metrics / Evidence / Closure 3단계 검증 |
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

### 5-4. cost_tracker.py (비용 추적)

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

### 6-9. [MEDIUM] DART API 공시 중복 수집

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

### 6-10. [MEDIUM] GitHub Actions Secrets 주입 실패

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

### 6-12. [MINOR] `_log_normal_publish_event` 제거 vs 복원

**배경**: Phase 19 Actions 이관 시 로컬 스케줄러 로그 함수를 제거했다가, Phase 19 후반에 복원.

**기능**: 각 포스팅 완료 시 `publish_result.jsonl`에 QA 결과 라인 기록
```json
{"run_id":"...","slot":"morning","post_type":"post1_2","final_status":"GO","public_url":"https://..."}
```
- **제거 시**: JSONL 로그 없음 → 주간 리포트에서 데이터 공백 발생
- **복원 이유**: Phase 20 주간 리포트가 이 JSONL을 파싱하여 집계하므로 필수

**결론**: 항상 유지해야 하는 함수. 제거 금지.

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

### 10-2. Phase 20 QA 체계 (Editorial Planner)

| 검증 항목 | 기준 | 실패 처리 |
|-----------|------|---------|
| **Lead Metrics** | 도입부 수치 5개 이상, 시기 명확 | 재작성 요청 |
| **Evidence** | 본문 인용 출처 3개 이상 | 경고 후 발행 |
| **Closure** | 도입부↔결론 연결성 | 클로저 재작성 |

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

*END — REPORT_TECHNICAL_KNOWHOW_V1.md*
*다음 갱신: Phase 24 (FastAPI SaaS 서버) 완료 시*
