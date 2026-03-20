# MACROMALT_GITHUB_ACTIONS_SETUP_GUIDE.md

작성일: 2026-03-20

## 목적

Macromalt에서 아래 두 가지를 **노트북을 켜 두지 않고** 자동 운영하기 위한 GitHub 설정 가이드.

1. **하루 3회 발행**
2. **주 1회 Phase 20 운영 정교화 리포트**

---

## 1. 전체 구조

권장 구조는 다음과 같다.

- **Claude Code**
  - 저장소 안의 워크플로 파일, 실행 스크립트, 리포트 생성 스크립트를 만든다.
- **GitHub Actions**
  - 스케줄에 따라 자동 실행한다.
- **GitHub Secrets / Variables**
  - API 키, WP 자격정보, 슬롯명, 사이트 URL 같은 설정을 저장한다.
- **Artifacts / 커밋된 MD 리포트**
  - 주간 리포트를 남긴다.

이 방식은 GitHub-hosted runner에서 돌 수 있으므로, 사용자 노트북이 꺼져 있어도 워크플로는 실행될 수 있다.

---

## 2. Claude Code에서 먼저 만들 파일

저장소 루트 기준 권장 파일:

```text
.github/
  workflows/
    publish.yml
    phase20-weekly.yml
scripts/
  publish_daily.sh
  phase20_weekly_report.sh
reports/
  .gitkeep
```

또는 Python 기반이면:

```text
.github/
  workflows/
    publish.yml
    phase20-weekly.yml
scripts/
  publish_daily.py
  phase20_weekly_report.py
reports/
  .gitkeep
```

### Claude Code에 시킬 작업

1. `.github/workflows/publish.yml` 생성
2. `.github/workflows/phase20-weekly.yml` 생성
3. 발행 실행 스크립트 생성
4. Phase 20 점검 리포트 생성 스크립트 생성
5. 결과를 `reports/` 아래 MD로 저장
6. 필요 시 artifact 업로드 step 추가

---

## 3. GitHub에서 직접 해야 하는 설정

## A. Actions 기능 켜기

경로:
- **Repository → Settings → Actions → General**

여기서 확인할 것:
- **Allow all actions and reusable workflows** 또는 조직 정책상 허용된 범위에서 실행 가능 상태
- 저장소에서 GitHub Actions가 비활성화되어 있지 않은지 확인

참고:
- 저장소 단위로 GitHub Actions를 아예 끌 수도 있고, 사용할 수 있는 actions/reusable workflows 범위를 제한할 수도 있다.

---

## B. Workflow permissions 설정

경로:
- **Repository → Settings → Actions → General → Workflow permissions**

권장:
- 기본은 **Read repository contents and packages permissions**
- 그리고 workflow 파일 안에서 필요한 범위만 `permissions:`로 명시

예시:
```yaml
permissions:
  contents: read
```

리포트를 커밋하거나 release/tag를 만들 계획이면 그때만:
```yaml
permissions:
  contents: write
```

주의:
- GitHub의 기본 `GITHUB_TOKEN` 권한은 저장소/조직 생성 시점과 정책에 따라 read-only일 수 있다.
- 저장소 또는 조직 정책이 더 강하면 workflow에서 더 넓게 요청해도 막힐 수 있다.

---

## C. Secrets 등록

경로:
- **Repository → Settings → Secrets and variables → Actions → Secrets**

권장 repository secrets 예시:
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `WP_BASE_URL`
- `WP_USERNAME`
- `WP_APP_PASSWORD`
- `MACROMALT_SITE_URL`

필요 시 추가:
- `SLACK_WEBHOOK_URL`
- `NOTIFY_EMAIL`
- `GH_PAT`  (정말 필요한 경우만)

주의:
- 민감정보는 **Secrets**에 저장
- secret은 workflow에서 `${{ secrets.NAME }}`로 사용
- environment secret이 있으면 repository secret보다 우선한다.

---

## D. Variables 등록

경로:
- **Repository → Settings → Secrets and variables → Actions → Variables**

권장 repository variables 예시:
- `TIMEZONE=Asia/Seoul`
- `PUBLISH_SLOT_1=08:17`
- `PUBLISH_SLOT_2=14:17`
- `PUBLISH_SLOT_3=20:17`
- `PHASE20_WEEKLY_DAY=SUN`
- `PHASE20_WEEKLY_TIME=22:30`
- `REPORT_ARTIFACT_RETENTION_DAYS=14`

비민감 설정값은 **Variables**에 두는 편이 낫다.

---

## E. Environment 사용 여부

권장 environment:
- `production`

경로:
- **Repository → Settings → Environments**

`production` environment를 쓰면:
- environment secrets를 따로 둘 수 있음
- 보호 규칙을 붙일 수 있음
- 배포성 workflow를 environment 기준으로 관리 가능

단, private/internal 저장소에서 environment 기능의 사용 가능 범위는 요금제에 따라 달라질 수 있다.

---

## F. Scheduled workflow 전제

중요:
- `schedule` 이벤트는 **UTC cron** 기준
- **default branch의 workflow 파일**을 기준으로 동작
- 고부하 시간, 특히 **매시 정각** 근처에는 지연될 수 있다

권장:
- 정각 대신 `17`분, `23`분처럼 어긋난 시각 사용

예시:
- KST 08:17 = UTC 23:17 (전날)
- KST 14:17 = UTC 05:17
- KST 20:17 = UTC 11:17

---

## 4. 권장 workflow 분리

## 4-1. publish.yml
역할:
- 하루 3회 발행
- Post1/Post2 생성
- 발행 성공 시 URL 출력
- run summary 작성
- 로그/리포트 artifact 업로드

권장 trigger:
```yaml
on:
  schedule:
    - cron: "17 23 * * *"
    - cron: "17 5 * * *"
    - cron: "17 11 * * *"
  workflow_dispatch:
```

## 4-2. phase20-weekly.yml
역할:
- 최근 발행 로그/결과를 읽어 Phase 20 점검
- `REPORT_PHASE20_*.md` 생성
- artifact 업로드
- 필요 시 저장소에 커밋

권장 trigger:
```yaml
on:
  schedule:
    - cron: "30 13 * * 0"
  workflow_dispatch:
```

설명:
- 위 cron은 **매주 일요일 13:30 UTC = KST 22:30 일요일** 예시

---

## 5. workflow 안에서 꼭 넣을 것

## A. concurrency
중복 실행 방지용:

```yaml
concurrency:
  group: macromalt-publish
  cancel-in-progress: false
```

주간 점검은 별도 그룹:
```yaml
concurrency:
  group: macromalt-phase20-weekly
  cancel-in-progress: false
```

## B. timeout-minutes
무한 대기 방지:
```yaml
timeout-minutes: 30
```

## C. artifact 업로드
리포트와 로그를 남길 것:
```yaml
- name: Upload report artifact
  uses: actions/upload-artifact@v4
  with:
    name: phase20-report
    path: reports/*.md
    retention-days: 14
```

## D. explicit permissions
필요 최소 범위만:
```yaml
permissions:
  contents: read
```

리포트를 repo에 commit/push할 때만:
```yaml
permissions:
  contents: write
```

---

## 6. Claude Code에 바로 줄 수 있는 작업 지시 예시

```text
저장소 루트에서 아래를 생성하라.

1. `.github/workflows/publish.yml`
   - 하루 3회 KST 기준 발행
   - workflow_dispatch 포함
   - concurrency / timeout / artifact 업로드 포함
   - secrets와 vars 사용

2. `.github/workflows/phase20-weekly.yml`
   - 매주 1회 KST 기준 실행
   - 최근 발행 결과를 기준으로 Phase 20 운영 정교화 리포트 생성
   - 결과를 `reports/REPORT_PHASE20_WEEKLY.md`로 저장
   - artifact 업로드 포함

3. `scripts/publish_daily.py` 또는 `.sh`
   - Post1/Post2 생성 및 발행
   - 공개 URL / final_status / slot / post_type 출력

4. `scripts/phase20_weekly_report.py` 또는 `.sh`
   - 최근 발행 로그/결과를 집계
   - opener / fallback / parse_failed / title-dup 회귀 여부 점검
   - Markdown 리포트 생성

5. README 또는 `docs/github-actions-ops.md`
   - 필요한 secrets / vars / 수동 실행법 문서화
```

---

## 7. GitHub 웹에서 실제 클릭 순서

### 1단계
저장소에 workflow 파일 push

### 2단계
**Settings → Actions → General**
- Actions 허용 확인
- Workflow permissions 확인

### 3단계
**Settings → Secrets and variables → Actions**
- Secrets 등록
- Variables 등록

### 4단계
필요 시 **Settings → Environments**
- `production` 생성
- environment secrets 등록

### 5단계
**Actions 탭**
- `publish` workflow가 보이는지 확인
- `phase20-weekly` workflow가 보이는지 확인

### 6단계
각 workflow를 **Run workflow**로 수동 1회 실행
- secrets 누락
- permissions 부족
- path 오류
- dependency 설치 오류
를 먼저 잡는다

### 7단계
수동 실행 성공 후 스케줄 대기

---

## 8. 추천 운영 방식

### 발행
- 자동: GitHub Actions schedule
- 수동 예외: workflow_dispatch

### 주간 운영 정교화
- 자동: GitHub Actions schedule
- 산출물: artifact + 필요 시 repo 커밋

### 장애 대응
- 실패 run은 Actions 탭에서 로그 확인
- 리포트 artifact 다운로드
- 재실행은 Re-run jobs 또는 workflow_dispatch 사용

---

## 9. 가장 중요한 주의점

1. **default branch에 workflow 파일이 있어야 schedule이 동작**
2. **UTC cron으로 입력해야 함**
3. **정각은 피하는 것이 좋음**
4. **Secrets와 Variables를 구분**
5. **`GITHUB_TOKEN` 권한은 최소 권한 원칙**
6. **정상 발행 경로와 주간 점검 경로를 분리**
7. **노트북이 꺼져 있어도 GitHub-hosted runner는 실행 가능**
8. **로컬 파일/브라우저 세션에 의존하는 설계는 피해야 함**

---

## 10. 내가 추천하는 최종 구성

### 즉시 적용형
- GitHub-hosted runner
- `publish.yml`
- `phase20-weekly.yml`
- repository secrets
- repository variables
- artifact 업로드
- workflow_dispatch 포함

### 나중에 확장
- `production` environment
- 리포트 repo 자동 커밋
- Slack/Discord 알림
- 실패 시 GitHub Issue 자동 생성
- 외부 DB/스토리지 연동

---

## 11. 최소 체크리스트

- [ ] workflow 파일 2개 push 완료
- [ ] Actions 허용 확인
- [ ] Workflow permissions 확인
- [ ] Secrets 등록 완료
- [ ] Variables 등록 완료
- [ ] 수동 발행 run 성공
- [ ] 수동 Phase 20 run 성공
- [ ] artifact 생성 확인
- [ ] schedule 대기 상태 확인
