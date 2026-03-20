# REPORT_PHASE19_GITHUB_ACTIONS_TOTAL_HANDOFF.md

작성일: 2026-03-20
범위: Phase 18 완료 ~ Phase 19 GO 전환 ~ GitHub Actions 자동 운영 구성
최종 커밋: `5050c23`
최종 판정: **GO — 상시 자동 운영 체제 전환 완료**

---

## 1. 작업 범위 요약

이 문서는 Phase 17 종료 이후 수행된 모든 작업의 완전한 인계 문서다.
크게 3개 트랙으로 구성된다.

| 트랙 | 내용 | 상태 |
|------|------|------|
| Track A | Phase 18 운영 정교화 4축 완료 | ✅ GO |
| Track B | Phase 19 로그 보강 + 정상 발행 품질로그 GO 전환 | ✅ GO |
| Track C | GitHub Actions 자동 운영 인프라 구성 | ✅ 운영 중 |

---

## 2. Track A — Phase 18 운영 정교화 4축

### Axis A: fallback 정책 정비
- WARN 허용 정책 명문화
- verifier_revision_closure PASS/WARN/FAIL 체계 확정

### Axis B: PARSE_FAILED 응답 규칙
- TYPE_A~TYPE_UNKNOWN 분류 체계 구축
- 유형별 재시도/포기 판단 기준 확립

### Axis C: PARSE_FAILED 응답 실전 규칙
- 운영 중 발생 시 즉각 대응 흐름 정의

### Axis D: 반복 안정성 검증
- generic opener 재발 방지 확인
- post2 pick-angle 구조 유지 검증

**보고서:** `REPORT_PHASE18_AXIS_A~D.md`, `REPORT_PHASE18_INTEGRATED_CLOSEOUT.md`

---

## 3. Track B — Phase 19 로그 보강

### T1: 로그 필드 보강

**변경 파일: `generator.py`**

| 함수 | 변경 내용 |
|------|-----------|
| `verify_draft()` | `slot`, `post_type` 파라미터 추가 |
| `_calc_quality_pass_fields(content)` | **신규** — 4개 pass 필드 계산 헬퍼 (단일 진실 소스) |
| `_log_normal_publish_event(...)` | **신규** — 정상 발행 경로 품질로그 기록 |
| `_log_parse_failed_event(...)` | 리팩터 — `_calc_quality_pass_fields()` 호출로 위임 |

**변경 파일: `main.py`**
- Phase 19 정상발행 품질로그 블록 추가 (line 270~294)
- Post1 / Post2 각각 `_log_normal_publish_event()` 호출

### T2: 실전 검증 (Route B)

**실전 run 3회 확인:**

| run_id | slot | Post1 final_status | Post2 final_status |
|--------|------|-------------------|-------------------|
| `20260320_132107` | default | GO | GO |
| `20260320_134131` | default | GO | GO |
| `20260320_154017` | evening | GO | GO |

**대표 로그 (run_id=20260320_154017):**
```
[Phase 19] 정상발행 품질로그 | run_id=20260320_154017 | slot=evening | post_type=post1 | final_status=GO | opener_pass=False | criteria_1_pass=True | criteria_5_pass=True | source_structure_pass=True
[Phase 19] 정상발행 품질로그 | run_id=20260320_154017 | slot=evening | post_type=post2 | final_status=GO | opener_pass=True | criteria_1_pass=True | criteria_5_pass=True | source_structure_pass=True
```

> `opener_pass=False` (post1): pick-angle 패턴은 Post2 전용이므로 정상값.

### BUG-POST2-TITLE-DUP-20260320 수정

**변경 파일: `publisher.py`**

```python
# Before
def _strip_leading_h1(content: str) -> str:
    return re.sub(r"^\s*<h1[^>]*>.*?</h1>\s*", "", content, count=1, flags=re.DOTALL)

# After (Phase 19 수정)
def _strip_leading_h1(content: str) -> str:
    return re.sub(
        r"^\s*(<!--.*?-->\s*)*<h1[^>]*>.*?</h1>\s*",
        "",
        content,
        count=1,
        flags=re.DOTALL,
    )
```

**원인:** `_P14_ANALYTICAL_SPINE_ENFORCEMENT`로 GPT가 `<h1>` 앞에 `<!-- SPINE: ... -->` 주석 삽입
→ 기존 regex `^\s*<h1` 매칭 실패 → `<h1>` 미제거 → WordPress 제목 2회 출력
**수정:** regex에 선행 HTML 주석 0개 이상 패턴 추가
**검증:** 4개 케이스 Python 테스트 전건 PASS

**보고서:** `REPORT_PHASE19_*.md` (6종), `REPORT_BUG_POST2_TITLE_DUPLICATION.md`

---

## 4. Track C — GitHub Actions 자동 운영 인프라

### 4-1. 신규 파일 목록

| 파일 | 역할 |
|------|------|
| `.github/workflows/publish.yml` | 하루 3회 자동 발행 |
| `.github/workflows/phase20-weekly.yml` | 주 1회 운영 정교화 리포트 |
| `scripts/publish_daily.py` | main.py 래퍼 + Phase 19 JSONL 추출 |
| `scripts/phase20_weekly_report.py` | GitHub artifact 집계 → 주간 MD 리포트 |
| `reports/.gitkeep` | reports/ 디렉토리 git 추적 |
| `docs/github-actions-ops.md` | 운영 가이드 전문 |

### 4-2. 스케줄 (UTC cron)

| 슬롯 | KST | UTC | cron |
|------|-----|-----|------|
| 아침 | 08:17 | 23:17 | `17 23 * * *` |
| 오후 | 14:17 | 05:17 | `17 5 * * *` |
| 저녁 | 20:17 | 11:17 | `17 11 * * *` |
| 주간 리포트 | 일 22:30 | 일 13:30 | `30 13 * * 0` |

### 4-3. GitHub Environment 구성

| 항목 | 값 |
|------|---|
| Environment 이름 | `GitHub Actions` |
| Secret | `SECRETS` — `.env` 파일 전체 내용 |
| Variable | `VARIABLES` — dotenv 포맷 설정값 |

### 4-4. 환경변수 주입 구조

```
secrets.SECRETS (전체 .env 내용)
  ├── A: printf → .env 파일 작성      → load_dotenv() 경로
  └── B: grep KEY=VALUE → $GITHUB_ENV → OS env 직접 상속 (subprocess 포함)

vars.VARIABLES (비민감 설정)
  └── grep KEY=VALUE → $GITHUB_ENV 주입

Run publish pipeline step:
  env:
    TIMEZONE: ${{ vars.TIMEZONE || 'Asia/Seoul' }}
    SCRAPE_INTERVAL_MINUTES: ${{ vars.SCRAPE_INTERVAL_MINUTES || '60' }}
```

### 4-5. 트러블슈팅 이력

| 커밋 | 원인 | 수정 |
|------|------|------|
| `e03e6dd` | `str \| None` Python 3.10+ 전용 타입 힌트 | `Optional[str]`로 교체 |
| `f1475bf` | `echo "${{ secrets.ENV }}"` 직접 치환 시 `$` 기호 쉘 해석으로 API 키 파괴 | `printf '%s'` + env var 전달로 변경 |
| `931ef84` | secret/environment 이름 불일치 | `ENV` → `SECRETS`, `Configure .env` → `Configure GitHub Actions` |
| `5050c23` | environment 이름 최종 불일치 | `Configure GitHub Actions` → `GitHub Actions` |
| `62d600e` | `vars.VARIABLES` 전달 누락 | VARIABLES 파싱 + 명시적 step env 추가 |

### 4-6. artifact 구조

```
publish-log-{github.run_id}        (보존 14일)
  ├── logs/macromalt_daily.log
  └── logs/publish_result.jsonl    ← Phase 19 품질로그 JSONL

phase20-weekly-report-{github.run_id}  (보존 90일)
  └── reports/REPORT_PHASE20_WEEKLY.md
```

### 4-7. `publish_result.jsonl` 포맷

```jsonl
{"run_id":"20260320_154017","slot":"evening","post_type":"post1","final_status":"GO","opener_pass":false,"criteria_1_pass":true,"criteria_5_pass":true,"source_structure_pass":true,"public_url":"https://macromalt.com/...","logged_at":"2026-03-20T..."}
{"run_id":"20260320_154017","slot":"evening","post_type":"post2","final_status":"GO","opener_pass":true,"criteria_1_pass":true,"criteria_5_pass":true,"source_structure_pass":true,"public_url":"https://macromalt.com/...","logged_at":"2026-03-20T..."}
```

---

## 5. 불변 원칙 (Phase 20 이후에도 변경 금지)

| 원칙 | 설명 |
|------|------|
| Post2 pick-angle opener 구조 | `왜 지금 X인가` 패턴 유지 |
| generic opener 금지 | `최근 시장은`, `글로벌 금융시장` 등 금지 |
| fallback WARN 허용 정책 | WARN은 발행 차단 아님 |
| PARSE_FAILED TYPE_A~TYPE_UNKNOWN | 분류 체계 변경 금지 |
| 기준1 / 기준5 판정 원칙 | 권유성 표현 / 소스 구조 기준 |
| 정상 발행 품질로그 6개 필드 | `slot`, `post_type`, `opener_pass`, `criteria_1_pass`, `criteria_5_pass`, `source_structure_pass` |
| 공개 URL 기준 검증 | `public_url` 실 발행본 URL 기준 |

---

## 6. 커밋 이력 (Phase 17 이후)

| 커밋 | 내용 |
|------|------|
| `7ae1ce2` | Phase 18~19 완료 + GitHub Actions 자동 운영 구성 (메인 반영) |
| `495dff4` | workflows: Configure .env Environment 방식으로 전환 |
| `e03e6dd` | fix: Python 3.9 호환 타입 힌트 수정 |
| `f1475bf` | fix: .env 복원 방식 변경 — printf + env var로 $기호 보존 |
| `931ef84` | fix: GitHub Environment 이름 및 Secret 이름 업데이트 |
| `2152747` | fix: 환경변수 주입 이중 방어 구조로 교체 |
| `62d600e` | fix: Variables 전달 누락 보완 + 환경변수 주입 구조 정비 |
| `5050c23` | fix: environment 이름 수정 — 'GitHub Actions'로 변경 |

---

## 7. 현재 운영 상태

| 항목 | 상태 |
|------|------|
| 자동 발행 (하루 3회) | ✅ 활성 — KST 08:17 / 14:17 / 20:17 |
| 주간 리포트 (주 1회) | ✅ 활성 — 일요일 KST 22:30 |
| Phase 19 품질로그 | ✅ 정상 기록 확인 |
| BUG-POST2-TITLE-DUP | ✅ 수정 완료, 재발 없음 |
| 로컬 맥북 상시 가동 | ❌ 불필요 — GitHub Actions 전환 완료 |

---

## 8. Phase 20 권장 후속 작업

| 항목 | 우선순위 | 설명 |
|------|---------|------|
| `opener_pass` Post1/Post2 기준 분리 | 높음 | Post1은 현재 항상 `False` — 형식별 기준 분리 필요 |
| Slack/Discord 발행 알림 | 중간 | 발행 완료/실패 시 알림 |
| 실패 시 GitHub Issue 자동 생성 | 중간 | HOLD/exit 1 시 이슈 자동 등록 |
| PARSE_FAILED 주간 자동 집계 | 낮음 | 주간 리포트에 TYPE별 건수 추가 |
| Python 3.9 → 3.11 업그레이드 | 낮음 | EOL 경고 해소 (google-auth FutureWarning) |
| weekly report → repo 자동 커밋 | 낮음 | `contents: write` 권한 추가 필요 |

---

## 9. 최종 판정

**GO**

- Phase 18 운영 정교화 4축 완료
- Phase 19 로그 보강 + 정상 발행 품질로그 실전 검증 완료
- BUG-POST2-TITLE-DUP-20260320 수정 및 재발 없음 확인
- GitHub Actions 자동 운영 인프라 구성 완료 및 실동 확인
- 로컬 맥북 상시 가동 의존 해소

macromalt는 이 시점부터 **완전 자동 운영 체제**에 진입한다.
