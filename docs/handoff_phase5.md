# macromalt Phase 5 전체 완료 핸즈오프
**기준일: 2026-03-13 | 브랜치: `main` | 작업 브랜치: `claude/reverent-hypatia` | 미커밋 변경 포함**

---

## 1. 현재 상태

### 파이프라인 구조 (3단계, 변경 없음)
```
Step 1 — Gemini 2.5-flash
  뉴스 + 리서치(+PDF snippet) + DART 공시(+원문발췌) → 구조화 JSON
Step 2 — GPT-4o
  JSON → HTML 초고 (Post1 심층분석 / Post2 캐시의 픽)
Step 3 — Gemini 2.5-flash
  HTML 초고 → 팩트체크 → 수정본 채택
```

### 실운영 가능 여부
**가능.** Phase 5-A 기준 자동 검증 전체 PASS 이후 5-B/C/D 모두 비파괴적으로 추가됨.

---

## 2. Phase 5 전체 커밋 이력

| 커밋 | Phase | 내용 |
|---|---|---|
| `5b46c52` | 5-A | portfolio.json 발행 샘플 반영 |
| `2fad46a` | 5-B | DART 재무 연도 fallback + BROKER_KW/계정 1차 확장 |
| `ae27c8e` | 5-B | `resolved_bsns_year` / `used_fallback` 메타 추가 |
| `aff2854` | 5-B | `format_dart_for_prompt` 헤더 기준연도 노출 |
| `5dab826` | 5-B | BROKER_KW 2차 확장 (총 23개) |
| `8108ab9` | 5-B | PDF enrich 1차 — 네이버 금융 리포트 핵심 섹션 추출 |
| `d7994ef` | docs | Phase 5-A/B 핸즈오프 문서 추가 |
| *(미커밋)* | 5-C | DART 원문 파싱 (`document.json` → ZIP → XML) |
| *(미커밋)* | 5-D | 통합 품질 재검증 + 4건 수정 |

> **주의**: 5-C / 5-D 변경은 현재 커밋되지 않은 상태. Phase 6 시작 전 커밋 권장.

---

## 3. 파일별 현재 상태

| 파일 | 라인 수 | Phase 5 주요 변경 요약 |
|---|---|---|
| `scraper.py` | 1,705 | Section 15 신규(5-C): `_fetch_dart_document_zip`, `_extract_dart_xml_text`, `enrich_dart_disclosures_with_fulltext`. Section 16: `_fetch_pdf_bytes`, `enrich_research_with_pdf`. Section 14: `format_dart_for_prompt` full_text 노출 + `[:400]` 제한. `run_dart_financials` fallback 메타. |
| `generator.py` | 2,164 | `_PDF_PROMPT_SNIPPET_LEN=400` 상수 추가(5-D). `enrich_dart_disclosures_with_fulltext` import + 호출. `GEMINI_ANALYST_SYSTEM`에 DART 공시 처리 지침 추가(5-D). fallback facts에 `relevance_to_theme` 추가(5-D). |
| `.gitignore` | — | `.dart_doc_cache/` 추가 |

---

## 4. Phase 5-C / 5-D 구현 내용 (이번 세션 신규)

### Phase 5-C — OpenDART 원문 파싱
| 항목 | 내용 |
|---|---|
| API | `GET /api/document.json?crtfc_key=&rcept_no=` → ZIP 반환 |
| 캐시 | `.dart_doc_cache/{rcept_no}.zip` 7일 TTL |
| 파싱 | BeautifulSoup(`lxml-xml` → `html.parser` fallback). style/script/img 제거 후 `get_text()` |
| 출력 | `full_text` 최대 800자 추출 → `format_dart_for_prompt`에서 `[:400]`으로 프롬프트 삽입 |
| 적용 범위 | `run_dart_disclosure_scan` 결과 상위 3건(이벤트타입 "기타" 후순위 정렬) |
| 호출 위치 | `generator.py` — `run_dart_disclosure_scan()` 직후 `enrich_dart_disclosures_with_fulltext()` |

### Phase 5-D — 통합 품질 재검증 및 수정
| 이슈 | 수정 내용 |
|---|---|
| `GEMINI_ANALYST_SYSTEM`에 DART 처리 지침 없음 | "DART 공시 처리 지침" 블록 추가 — 원문발췌를 공시 사실로 처리, source/date 명시 규칙 |
| `full_text` 800자 슬라이스 없이 삽입 | `format_dart_for_prompt`에서 `[:400]` 추가 |
| PDF snippet 상수 불일치 (`_PDF_SNIPPET_MAX=800` vs 삽입 `[:300]`) | `_PDF_PROMPT_SNIPPET_LEN=400` 상수 추가, `[:_PDF_PROMPT_SNIPPET_LEN]`으로 통일 |
| fallback facts에 `relevance_to_theme` 없음 | `"relevance_to_theme": "직접 관련"` 추가 |

---

## 5. 주요 상수 현재값

| 상수 | 위치 | 값 |
|---|---|---|
| `_DART_DOC_CACHE_TTL` | `scraper.py` | `7일` |
| `_DART_DOC_MAX_CHARS` | `scraper.py` | `800` (추출 상한) |
| `enrich_dart_disclosures_with_fulltext(max_fetch)` | `scraper.py` | 기본값 `3` |
| `format_dart full_text 삽입 컷` | `scraper.py` | `[:400]` |
| `_PDF_SNIPPET_MAX` | `scraper.py` | `800` (추출 상한) |
| `_PDF_PROMPT_SNIPPET_LEN` | `generator.py` | `400` (프롬프트 삽입 상한) |
| `enrich_research_with_pdf(max_pdf)` | `scraper.py` | 기본값 `3` |
| `DART_TARGET_ACCOUNTS` | `scraper.py` | `9개` 계정 |
| `BROKER_KW` | `generator.py` | `23개` 키워드 |

---

## 6. 확인된 리스크

| 리스크 | 수준 | 내용 |
|---|---|---|
| `document.json` 응답 속도 | 🟡 낮음 | ZIP 다운로드 timeout=20초. 캐시 hit 시 즉시 반환. 첫 실행만 느림 |
| lxml-xml 미설치 | 🟢 무시 | `html.parser` fallback 처리됨 |
| DART API 일일 한도 | 🟡 낮음 | 무료 키 기준 10,000회/일. 원문 조회 3건 추가로 일반 사용 범위 내 |
| 한경 PDF 세션 연동 | 🟡 낮음 | `_hankyung_login()` ↔ `enrich_research_with_pdf` 연결 미구현. 보류 중 |
| BROKER_KW 오탐 | 🟡 낮음 | `신한`/`NH`/`IBK` 금융 계열사 오탐 가능. 로그 모니터링 권고 |

---

## 7. Phase 6 시작 전 체크리스트

- [ ] 5-C/5-D 변경사항 커밋 (`git add scraper.py generator.py .gitignore && git commit`)
- [ ] `python generator.py` 자동 검증 14개 기준 재확인
- [ ] DART API 키 설정 확인 (`.env`의 `DART_API_KEY`)

## 8. Phase 6 후보 작업

| 순번 | 작업 | 내용 | 난이도 |
|---|---|---|---|
| 1 | 한경 세션 연동 | `_hankyung_login()` 세션을 `enrich_research_with_pdf`에 전달 | 낮음 |
| 2 | 사업보고서 섹션 파싱 | `pblntf_ty=A` (사업보고서) 대상 "사업의 내용" / MD&A 헤더 기반 섹션 추출 | 높음 |
| 3 | 종목 리포트 PDF URL 패턴 확인 | 개별 종목 리포트 URL 구조 검증 | 낮음 |
| 4 | BROKER_KW 오탐 정제 | 로그 기반 오탐 키워드 구체화 | 낮음 |

---

**repo**: `https://github.com/hs85-newbie/macromalt` | **branch**: `main` | **head**: `d7994ef` (+ 미커밋 5-C/5-D)
