# macromalt GitHub Actions 운영 가이드

작성일: 2026-03-20

---

## 개요

macromalt 발행 파이프라인은 GitHub Actions로 완전 자동화됩니다.
로컬 맥북을 상시 켜두지 않아도 하루 3회 자동 발행, 주 1회 운영 정교화 리포트가 생성됩니다.

---

## 1. Workflow 목록

| Workflow 파일 | 역할 | 스케줄 |
|---|---|---|
| `.github/workflows/publish.yml` | 하루 3회 Post1 + Post2 자동 발행 | KST 08:17 / 14:17 / 20:17 |
| `.github/workflows/phase20-weekly.yml` | 주 1회 Phase 20 운영 리포트 생성 | 일요일 KST 22:30 |

---

## 2. KST / UTC cron 대응표

| 슬롯 | KST | UTC | cron 표현 |
|------|-----|-----|-----------|
| 아침 (morning) | 08:17 | 23:17 (전일) | `17 23 * * *` |
| 오후 (evening) | 14:17 | 05:17 | `17 5 * * *` |
| 저녁 (us_open) | 20:17 | 11:17 | `17 11 * * *` |
| 주간 리포트 | 일 22:30 | 일 13:30 | `30 13 * * 0` |

> KST = UTC+9. GitHub Actions의 cron은 항상 UTC 기준.
> 정각(00분)을 피하기 위해 의도적으로 분(17, 30)을 어긋나게 설정.

---

## 3. 필요한 GitHub Secrets

GitHub 저장소 → Settings → Secrets and variables → Actions → Secrets 에서 등록.

| Secret 이름 | 설명 | 예시 |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API 키 (GPT 작성 담당) | `sk-...` |
| `GEMINI_API_KEY` | Google Gemini API 키 (분석 + 검수 담당) | `AIza...` |
| `WORDPRESS_SITE_URL` | WordPress 사이트 URL | `https://macromalt.com` |
| `WORDPRESS_USERNAME` | WordPress 관리자 사용자명 | `admin` |
| `WORDPRESS_PASSWORD` | WordPress Application Password | `xxxx xxxx xxxx xxxx` |
| `WP_CATEGORY_ANALYSIS` | 심층분석 카테고리 ID | `3` |
| `WP_CATEGORY_PICKS` | 캐시의 픽 카테고리 ID | `5` |
| `WP_CATEGORY_DEFAULT` | 기본 카테고리 ID | `1` |
| `DART_API_KEY` | OpenDART API 키 (공시 데이터 수집) | `abc123...` |
| `HANKYUNG_USERNAME` | 한국경제 로그인 ID | `user@email.com` |
| `HANKYUNG_PASSWORD` | 한국경제 로그인 비밀번호 | `password` |

> **주의**: `.env` 파일의 값을 그대로 각 Secret에 복사하면 됩니다.

---

## 4. 필요한 GitHub Variables

GitHub 저장소 → Settings → Secrets and variables → Actions → Variables 에서 등록.

| Variable 이름 | 설명 | 기본값 |
|---|---|---|
| `TIMEZONE` | 타임존 설정 | `Asia/Seoul` |
| `SCRAPE_INTERVAL_MINUTES` | 수집 주기(분) | `60` |

---

## 5. 수동 실행 방법

1. GitHub 저장소 페이지 → **Actions** 탭
2. 왼쪽 목록에서 `macromalt Daily Publish` 또는 `macromalt Phase 20 Weekly Report` 클릭
3. 오른쪽 상단 **Run workflow** 버튼 클릭
4. 사유(reason) 입력 후 **Run workflow** 클릭

---

## 6. 실행 결과 확인 위치

### 발행 로그 (publish.yml)

```
Actions → 해당 run → publish → Upload logs artifact
→ artifact: publish-log-{run_id}
  ├── logs/macromalt_daily.log    (전체 파이프라인 로그)
  └── logs/publish_result.jsonl  (Phase 19 품질로그 JSONL)
```

### 주간 리포트 (phase20-weekly.yml)

```
Actions → 해당 run → weekly-report → Upload weekly report artifact
→ artifact: phase20-weekly-report-{run_id}
  └── reports/REPORT_PHASE20_WEEKLY.md
```

### 빠른 확인 — Phase 19 품질로그 형식

```jsonl
{"run_id": "20260320_154017", "slot": "evening", "post_type": "post1", "final_status": "GO", "opener_pass": false, "criteria_1_pass": true, "criteria_5_pass": true, "source_structure_pass": true, "public_url": "https://macromalt.com/..."}
{"run_id": "20260320_154017", "slot": "evening", "post_type": "post2", "final_status": "GO", "opener_pass": true, "criteria_1_pass": true, "criteria_5_pass": true, "source_structure_pass": true, "public_url": "https://macromalt.com/..."}
```

---

## 7. 장애 시 확인 위치

| 증상 | 확인 위치 |
|------|-----------|
| 발행이 안 됨 | Actions → 해당 run → 로그에서 `[ERROR]` 또는 `exit code` 확인 |
| API 오류 | Secrets 값 확인 (특히 만료된 WordPress App Password) |
| cron이 실행 안 됨 | Actions → `.github/workflows/publish.yml` → "This scheduled workflow is disabled" 여부 확인 |
| artifact가 없음 | 실행 자체가 실패했거나 15분 timeout 초과 가능성 |
| Phase 19 JSONL이 비어 있음 | main.py가 PARSE_FAILED 경로로 분기됐거나 실행 오류 → `macromalt_daily.log` artifact 확인 |

> GitHub Actions 예약 실행은 서버 부하에 따라 최대 15분 지연될 수 있습니다.

---

## 8. concurrency 정책

```yaml
# publish.yml
concurrency:
  group: macromalt-publish
  cancel-in-progress: false   # 이전 run이 끝나야 다음 시작 (강제 취소 없음)

# phase20-weekly.yml
concurrency:
  group: macromalt-phase20-weekly
  cancel-in-progress: false
```

같은 슬롯에 수동 실행과 자동 실행이 겹쳐도 동시 실행되지 않고 순차 처리됩니다.

---

## 9. artifact 보존 기간

| artifact 종류 | 보존 기간 |
|---|---|
| `publish-log-{run_id}` | 14일 |
| `phase20-weekly-report-{run_id}` | 90일 |

> 주간 리포트가 최근 7일 artifact를 참조하므로 publish-log의 14일 보존은 충분합니다.

---

## 10. 권장 후속 작업

| 항목 | 설명 | 우선순위 |
|------|------|---------|
| Slack/Discord 알림 | 발행 완료 또는 실패 시 알림 전송 | 권장 |
| 실패 시 GitHub Issue 자동 생성 | HOLD / exit 1 시 issue 생성 | 권장 |
| 주간 리포트 repo 커밋 | `reports/REPORT_PHASE20_WEEKLY.md`를 repo에 자동 커밋 | 선택 |
| opener_pass Post1 기준 분리 | Phase 20: post_type별 opener 판정 기준 분리 | 기술 부채 |
| PARSE_FAILED 자동 집계 | 주간 리포트에 TYPE_A~TYPE_UNKNOWN 건수 추가 | 기술 부채 |

---

## 부록 — 처음 설정 체크리스트

- [ ] 저장소 GitHub에 push 완료
- [ ] Secrets 11종 모두 등록
- [ ] Variables 2종 등록 (선택)
- [ ] Actions 탭에서 workflow 두 개 활성화 확인
- [ ] `macromalt Daily Publish` 수동 실행 1회 테스트
- [ ] artifact `publish-log-*` 생성 확인
- [ ] `publish_result.jsonl` 내용 확인 (Phase 19 품질로그)
- [ ] 공개 URL 실제 접속 확인
- [ ] `macromalt Phase 20 Weekly Report` 수동 실행 1회 테스트
- [ ] artifact `phase20-weekly-report-*` → `REPORT_PHASE20_WEEKLY.md` 내용 확인
