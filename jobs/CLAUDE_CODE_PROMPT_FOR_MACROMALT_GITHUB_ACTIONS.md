# CLAUDE_CODE_PROMPT_FOR_MACROMALT_GITHUB_ACTIONS.md

아래 프롬프트를 Claude Code에 그대로 붙여넣어 실행하라.

---

# Macromalt GitHub Actions 자동 운영 구성 작업

현재 Macromalt 프로젝트는 다음 상태다.

- 스타일 가이드는 완료 상태다.
- 운영 정교화 게이트는 Phase 19 GO로 종료된 상태로 본다.
- Phase 20은 구조 개편이 아니라 **상시 운영 정교화 / 운영 해석 정밀화 / 후속 모니터링** 트랙으로 본다.
- 앞으로는 **노트북을 상시 켜두지 않고** 운영 가능해야 한다.
- 목표는 아래 2개다.

## 목표
1. **하루 3회 자동 발행**
2. **주 1회 Phase 20 운영 정교화 리포트 자동 생성**

중요:
- 실행 환경은 **GitHub Actions** 기준으로 설계하라.
- 사용자의 맥북 로컬 환경에 상시 의존하지 말라.
- GitHub-hosted runner에서 동작 가능한 구조를 우선 설계하라.
- 로컬 GUI, 브라우저 세션, 수동 개입 전제 설계를 피하라.

---

## 절대 유지할 프로젝트 원칙

아래는 이번 작업에서 변경 금지다.

1. Post2 pick-angle opener 구조
2. generic opener 금지 규칙
3. fallback WARN 허용 정책
4. PARSE_FAILED TYPE_A~TYPE_UNKNOWN 체계
5. 기존 기준1 / 기준5 판정 원칙
6. 정상 발행 경로 품질로그 구조
   - slot
   - post_type
   - opener_pass
   - criteria_1_pass
   - criteria_5_pass
   - source_structure_pass
7. 공개 URL 기준 검증 원칙

즉, 이번 작업은 **콘텐츠 구조나 발행 품질 로직 수정이 아니라 자동 운영 실행 환경 구성**이다.

---

## 해야 할 일

저장소 안에 아래를 생성 또는 수정하라.

### 1. GitHub Actions workflow 파일 생성
다음 두 파일을 만들어라.

- `.github/workflows/publish.yml`
- `.github/workflows/phase20-weekly.yml`

### 2. 실행 스크립트 생성
프로젝트 기술 스택에 맞게 아래 둘 중 적절한 방식으로 구성하라.

권장:
- `scripts/publish_daily.py`
- `scripts/phase20_weekly_report.py`

또는 기존 런타임이 쉘 스크립트 기반이면:
- `scripts/publish_daily.sh`
- `scripts/phase20_weekly_report.sh`

### 3. 리포트 출력 경로 준비
다음 폴더를 준비하라.

- `reports/`

필요하면 `.gitkeep`를 넣어라.

### 4. 문서 생성
다음 운영 문서를 생성하라.

- `docs/github-actions-ops.md`

여기에는 아래를 반드시 문서화하라.
- 필요한 GitHub Secrets 목록
- 필요한 GitHub Variables 목록
- 수동 실행 방법
- 장애 시 확인 위치
- artifact 확인 위치
- cron 시간의 KST/UTC 대응표

---

## workflow 요구사항

## A. publish.yml

역할:
- 하루 3회 자동 발행
- workflow_dispatch 수동 실행 지원
- Post1 / Post2 생성 및 발행
- 최종 URL / final_status / slot / post_type / 품질로그 요약 출력
- 실패 시 로그를 남기고 종료
- 결과 리포트 또는 로그 artifact 업로드

필수 요구사항:
1. `schedule` + `workflow_dispatch` 포함
2. UTC cron 사용
3. 정각 피해서 분 단위 어긋나게 설정
4. `concurrency` 설정
5. `timeout-minutes` 설정
6. 최소 권한 `permissions` 명시
7. GitHub Secrets / Variables 사용
8. 실행 결과를 artifact로 업로드
9. default branch 기준으로 작동하도록 일반적인 workflow 구조 사용

권장 스케줄:
- KST 08:17
- KST 14:17
- KST 20:17

UTC cron으로 환산해서 넣어라.

## B. phase20-weekly.yml

역할:
- 매주 1회 Phase 20 운영 정교화 점검
- 최근 발행 결과/로그 기준 리포트 생성
- 리포트를 `reports/REPORT_PHASE20_WEEKLY.md`로 저장
- artifact 업로드
- workflow_dispatch 수동 실행 지원

필수 요구사항:
1. `schedule` + `workflow_dispatch`
2. UTC cron
3. `concurrency`
4. `timeout-minutes`
5. 최소 권한 `permissions`
6. GitHub Secrets / Variables 사용 가능 구조
7. 결과 MD artifact 업로드

권장 스케줄:
- 일요일 KST 22:30

UTC cron으로 환산해서 넣어라.

---

## 스크립트 요구사항

## A. publish_daily.*

해야 할 일:
- 기존 generator / publish 진입점을 GitHub Actions에서 호출할 수 있게 감싸라.
- run_id를 출력하라.
- Post1 / Post2의 결과를 구분해서 출력하라.
- 최소한 아래를 stdout 또는 저장 로그에 남겨라.

필수 출력 항목:
- run_id
- slot
- post_type
- final_status
- public_url
- opener_pass
- criteria_1_pass
- criteria_5_pass
- source_structure_pass

가능하면 JSONL 또는 파싱 가능한 형식으로 남겨라.

## B. phase20_weekly_report.*

해야 할 일:
- 최근 발행 로그 또는 결과를 읽어서 주간 운영 정교화 리포트를 생성하라.
- 아래 항목을 최소 포함하라.

필수 포함 항목:
1. 기간
2. 총 발행 run 수
3. 총 실발행 수
4. 공개 URL 수
5. final_status 분포
6. opener 회귀 여부
7. generic opener 재발 여부
8. fallback_used 발생 건수
9. PARSE_FAILED TYPE별 건수
10. title duplication 회귀 여부
11. 수동 확인 필요 항목
12. 최종 판정
   - GO
   - CONDITIONAL GO
   - HOLD

리포트는 Markdown으로 생성하라.

출력 파일:
- `reports/REPORT_PHASE20_WEEKLY.md`

---

## GitHub 설정을 고려한 구현 조건

아래 조건을 반드시 반영하라.

1. 민감정보는 코드에 하드코딩하지 말 것
2. 아래 값은 GitHub Secrets 또는 Variables로 읽는 구조로 만들 것

예시 Secrets:
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `WP_BASE_URL`
- `WP_USERNAME`
- `WP_APP_PASSWORD`

예시 Variables:
- `TIMEZONE`
- `PUBLISH_SLOT_1`
- `PUBLISH_SLOT_2`
- `PUBLISH_SLOT_3`
- `PHASE20_WEEKLY_CRON`

3. GitHub-hosted runner에서 fresh VM 기준으로 실행 가능해야 한다
4. 로컬 파일에만 남는 상태 의존을 최소화하라
5. 필요한 의존성 설치 step을 workflow에 넣어라
6. 리포트 artifact 업로드 step을 포함하라

---

## 권장 구현 방식

가능하면 아래 방향으로 구현하라.

### 공통 유틸
- workflow와 스크립트가 공유하는 설정 로더 분리
- time zone / cron 설명 / env parsing 유틸 분리 가능하면 수행

### 로그 포맷
- 가능한 한 JSON 또는 key=value 형식으로 일관되게 출력
- 주간 리포트 스크립트가 재활용할 수 있어야 한다

### artifact
- 발행 로그
- 주간 리포트
- 필요 시 에러 로그
를 artifact로 업로드하라.

---

## workflow 안에 반드시 넣을 것

예시 수준이 아니라 실제로 반영하라.

### permissions
최소 권한 원칙 적용:
- 기본은 `contents: read`
- 리포트 파일을 repo에 commit하는 구조가 아니라면 `write` 권한 불필요

### concurrency
발행 workflow:
- 같은 종류의 중복 실행 방지

주간 리포트 workflow:
- 별도 group 사용

### timeout
- 발행 workflow: 적절한 실행 시간 제한
- 주간 리포트 workflow: 적절한 실행 시간 제한

### artifact upload
- `actions/upload-artifact@v4` 사용
- 보존일수도 합리적으로 설정

---

## 산출물

작업 완료 후 아래를 제출하라.

1. 생성/수정 파일 목록
2. 각 파일의 역할 설명
3. GitHub Secrets 목록
4. GitHub Variables 목록
5. 수동 테스트 절차
6. 예상되는 첫 실행 체크포인트
7. 위험 요소
   - cron 시간대 실수
   - secrets 누락
   - runner 환경 차이
   - default branch 이슈
8. 권장 후속 작업
   - Slack/Discord 알림
   - 실패 시 issue 생성
   - weekly report repo 커밋 여부 검토

---

## 출력 방식

답변은 아래 순서로 하라.

1. 작업 해석
2. 생성/수정 예정 파일 트리
3. 각 파일의 전체 내용
4. GitHub 웹에서 사용자가 직접 해야 하는 설정 체크리스트
5. 수동 테스트 순서
6. 위험 요소
7. 최종 요약

중요:
- placeholder만 던지지 말고, 실제로 돌아갈 수 있는 수준의 workflow 초안을 작성하라.
- 프로젝트 구조를 모르면 합리적인 가정을 분명히 적고 진행하라.
- GitHub Actions에서 바로 적용 가능한 수준의 YAML과 스크립트 골격을 제공하라.
- 기존 발행 로직을 깨지 않도록 최소 침습 방식으로 구성하라.
