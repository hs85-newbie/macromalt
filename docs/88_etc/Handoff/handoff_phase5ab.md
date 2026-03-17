# macromalt Phase 5-A / 5-B 완료 핸즈오프
**기준일: 2026-03-13 | 브랜치: `main` | 최신 커밋: `8108ab9`**

---

## 1. 현재 상태

### 파이프라인 구조 (3단계, 변경 없음)
```
Step 1 — Gemini 2.5-flash
  뉴스 + 리서치(+PDF snippet) + DART 공시 → 구조화 JSON (facts, theme, tickers)
Step 2 — GPT-4o
  JSON → HTML 초고 (Post1 심층분석 / Post2 캐시의 픽)
Step 3 — Gemini 2.5-flash
  HTML 초고 → 팩트체크 → 수정본 채택
```

### 실운영 가능 여부
**가능.** Phase 5-A 기준 Post1 14/14, Post2 10/10 자동 검증 전체 PASS 이후
Phase 5-B 기능은 기존 파이프라인에 비파괴적으로 추가됨.

---

## 2. 이번 세션에서 커밋된 내역 (6개 커밋)

| 커밋 | 내용 |
|---|---|
| `2fad46a` | DART 재무 연도 fallback (`bsns_year -1` retry) + BROKER_KW/DART_TARGET_ACCOUNTS 1차 확장 |
| `ae27c8e` | DART 재무 결과에 `resolved_bsns_year` / `used_fallback` 메타 추가 |
| `aff2854` | `format_dart_for_prompt` 헤더에 기준연도 및 fallback 문구 노출 |
| `5dab826` | BROKER_KW 2차 확장 (신한/NH/LS증권/DB금융/IBK/BNK/부국/신영/토스증권) |
| `f2116aa` | `docs/macromalt_prd_final_v2.md` 추가, initial PRD gitignore 처리 |
| `8108ab9` | Phase 5-B PDF enrich 1차 — 네이버 금융 리포트 핵심 섹션 추출 |

---

## 3. 파일별 현재 상태

| 파일 | 라인 수 | 주요 변경 |
|---|---|---|
| `scraper.py` | 1,576 | Section 15 신규: `_fetch_pdf_bytes`, `_extract_pdf_key_sections`, `enrich_research_with_pdf`. `run_dart_financials` fallback 로직 + 메타 필드 추가. `DART_TARGET_ACCOUNTS` 확장. |
| `generator.py` | 2,151 | `enrich_research_with_pdf` import + 두 generate 함수에 호출 1줄씩. `format_research_for_prompt`에 `[PDF 본문 발췌]` 출력 블록 추가. BROKER_KW 2차 확장. |
| `requirements.txt` | — | `pdfplumber>=0.11` 추가 |
| `docs/macromalt_prd_final_v2.md` | — | PRD v2 문서 |
| `.gitignore` | — | `docs/macromalt_prd_final.md` 제외 |

---

## 4. Phase 5-A / 5-B 구현 내용 요약

### Phase 5-A (이전 세션 완료 — 참고용)
| 항목 | 내용 |
|---|---|
| DART 공시 스캔 | 최근 14일 전체 시장 주요사항보고서 100건 자동 수집 |
| corp_code 조회 | corpCode.xml ZIP → 로컬 캐시 (TTL 1일) |
| 재무 수치 조회 | 매출·영업이익·부채비율 등 GPT context 주입 |
| 후처리 3종 | h1 중복 제거 / 오탈자 교정 / 참고출처 그룹화 |

### Phase 5-B (이번 세션 완료)
| 항목 | 내용 |
|---|---|
| DART 재무 연도 fallback | 당년 미공시 시 전년도 자동 재조회. `resolved_bsns_year` / `used_fallback` 메타 결과에 저장 |
| 기준연도 프롬프트 노출 | `DART 재무 기준연도: 2024 (fallback 적용)` 형태로 헤더에 1줄 표시 |
| DART_TARGET_ACCOUNTS 확장 | `영업활동현금흐름` / `영업활동으로인한현금흐름` 추가 |
| BROKER_KW 확장 (1+2차) | 총 17개 증권사 키워드 (기존 6 → 23) |
| PDF enrich 1차 | `pdfplumber` 기반. 네이버 금융 직링크 PDF → 핵심 섹션 800자 추출 → `pdf_snippet` 필드 → 프롬프트 300자 출력 |

---

## 5. 주요 상수 현재값

| 상수 | 위치 | 값 |
|---|---|---|
| `_PDF_SNIPPET_MAX` | `scraper.py` | `800` |
| `_PDF_MAX_BYTES` | `scraper.py` | `5 MB` |
| `enrich_research_with_pdf(max_pdf)` | `scraper.py` | 기본값 `3` |
| `pdf_snippet` 출력 컷 | `generator.py` | `300자` |
| `DART_TARGET_ACCOUNTS` | `scraper.py` | 9개 계정 |
| `BROKER_KW` | `generator.py` | 23개 키워드 |

---

## 6. 확인된 리스크

| 리스크 | 수준 | 내용 |
|---|---|---|
| BROKER_KW 오탐 가능성 | 🟡 낮음 | `신한` → 신한은행/신한카드, `NH` → NH농협, `IBK` → IBK기업은행 오탐 가능. 실운영 로그 모니터링 권고 |
| pdfplumber 미설치 시 | 🟢 무시 | `ImportError` catch → 빈 문자열 반환. 파이프라인 중단 없음 |
| 네이버 PDF 스캔 이미지 | 🟡 낮음 | 텍스트 추출 불가 → 빈 문자열 fallback. 이번 테스트 2건은 텍스트 PDF 확인 |
| `_PDF_SNIPPET_MAX` 800 vs 출력 300 중복 컷 | 🟢 무시 | 실질 출력 한도 300자. 기능 문제 없음. 추후 `400`으로 정렬 가능 |
| 한경 PDF 세션 연동 | 🟡 낮음 | 이번 단계 보류. 한경 인증 세션(`_hankyung_login()`)과 `enrich_research_with_pdf` 연결 미구현 |
| DART API 일일 한도 | 🟡 낮음 | 무료 키 기준 일 10,000회. 픽 종목 수 증가 시 재확인 필요 |

---

## 7. 다음에 할 일

### Phase 5-C 후보 (우선순위 순)
| 순번 | 작업 | 내용 | 난이도 |
|---|---|---|---|
| 1 | 한경 세션 연동 | `_hankyung_login()` 세션을 `enrich_research_with_pdf`에 전달 | 낮음 |
| 2 | `_PDF_SNIPPET_MAX` 400 조정 | 출력 300자 컷과 일관성 확보 | 최소 |
| 3 | DART 주요사항보고서 원문 XML 파싱 | `document.xml` 접근. 수주계약 금액 등 정형 데이터 추출 | 높음 |
| 4 | 종목 리포트 PDF URL 패턴 확인 | 산업 리포트 외 개별 종목 리포트 URL 구조 검증 | 낮음 |

### 즉시 적용 가능한 소수정
| 항목 | 내용 |
|---|---|
| `_PDF_SNIPPET_MAX` 조정 | `800` → `400` |
| BROKER_KW 오탐 모니터링 | 실운영 후 `신한` / `NH` / `IBK` 오탐 발생 시 키워드 구체화 (예: `신한투자` → `신한투자증권`) |

---

**repo**: `https://github.com/hs85-newbie/macromalt` | **branch**: `main` | **head**: `8108ab9`
