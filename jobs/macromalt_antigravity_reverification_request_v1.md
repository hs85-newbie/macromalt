# MACROMALT / Antigravity 재증빙 요청서 v1

## 0. 문서 목적
본 문서는 `step01-08_VERIFICATION_PROOF.md` 검토 결과에 따라,
현재 제출본이 **프리뷰 검증 보고서로는 유효하지만 최종 운영 반영 증빙으로는 부족**하다는 판단에 근거하여,
Antigravity 측에 추가 제출이 필요한 산출물과 최종 승인 조건을 명확히 전달하기 위한 요청서다.

본 요청서는 **WordPress 스타일 표현 트랙 전용**이며,
생성 로직, temporal SSOT, verifier, gate, publishing workflow, research/content policy는 본 요청 범위에 포함되지 않는다.

---

## 1. 현재 판정
현재 `step01-08_VERIFICATION_PROOF.md`에 대한 판정은 다음과 같다.

- **판정:** `PARTIAL PASS / 재증빙 필요`
- **의미:**
  - 스타일 개선 방향 자체는 유효하다.
  - 프리뷰 수준 검증은 어느 정도 성립한다.
  - 그러나 실제 운영 반영 완료를 최종 승인하기 위한 증빙은 아직 부족하다.

즉, 이번 단계는 **실패가 아니라 보완 제출 요구 단계**로 이해하면 된다.

---

## 2. 재증빙이 필요한 이유
아래 사유로 인해 현재 제출본만으로는 최종 acceptance를 내릴 수 없다.

### 2.1 Proof image가 deployed-state인지 확정되지 않음
현재 첨부된 이미지 파일명과 경로는 `injected` preview 성격으로 읽힌다.
따라서 이것이 실제 서버/실반영 상태인지, 아니면 브라우저 임시 주입 프리뷰인지 명확하지 않다.

### 2.2 변경 파일 실증이 없음
이번 트랙은 변경 대상 파일이 사전에 명확히 고정되어 있었으므로,
실제로 어떤 파일이 어떻게 바뀌었는지에 대한 **diff 또는 변경 요약**이 필요하다.

### 2.3 안전성 증빙이 선언형에 머물러 있음
`generator.py`, `styles/tokens.py` 무수정이 서술되어 있으나,
리뷰어가 재검증 가능한 증빙 자료가 함께 제출되지 않았다.

### 2.4 Operator scope와 Antigravity scope의 완료 여부가 분리되어 있지 않음
menu / logo / home shell / WordPress setting 성격의 항목은
Antigravity CSS 작업과 운영자 설정 작업을 구분해서 보고해야 한다.
현재 제출본은 이 경계가 최종 완료 보고 수준에서 충분히 분리되지 않았다.

---

## 3. Antigravity 재제출 요청 항목
아래 4개는 **필수 추가 제출 항목**이다.
누락 시 최종 승인은 보류한다.

### 3.1 Deployed-state screenshot package
다음 실제 반영 상태 캡처를 다시 제출하라.
`injected preview`가 아니라, **실제 반영 후 브라우저에서 다시 촬영한 캡처**여야 한다.

필수 항목:
- Homepage / Desktop
- Homepage / Mobile
- Single Post / Desktop
- Single Post / Mobile
- Archive / Desktop
- Archive / Mobile

필수 규칙:
- 파일명에 `deployed` 또는 `live`를 포함할 것
- URL 또는 화면 상단 정보로 live-state임을 식별 가능하게 할 것
- 가능하면 동일 페이지의 전/후 비교 캡처를 함께 제출할 것

### 3.2 Modified file diff summary
아래 파일의 실제 변경 내용을 요약 또는 diff 형태로 제출하라.

대상 파일:
- `styles/wordpress/base.css`
- `styles/wordpress/typography.css`
- `styles/wordpress/components.css`
- `theme/child-theme/style.css`
- `theme/child-theme/style.css` 내 `Template:` 헤더 관련 변경 여부

필수 규칙:
- 파일별로 `변경 목적 / 핵심 변경점 / 영향 범위 / 롤백 용이성`을 함께 적을 것
- 단순 “modified” 표기만으로는 인정하지 않음
- 가능하면 unified diff 또는 before/after block을 포함할 것

### 3.3 Zero-edit safety proof
다음 파일이 실제로 변경되지 않았음을 증빙하라.

대상 파일:
- `generator.py`
- `styles/tokens.py`

허용 증빙 방식:
- git diff 0 결과
- change log 상 untouched evidence
- file hash comparison
- execution log 상 no-change evidence

필수 규칙:
- 단순 문장 선언만으로는 부족함
- 리뷰어가 재검증 가능한 형태여야 함

### 3.4 Operator-scope completion status report
다음 항목은 Antigravity CSS 작업과 분리하여 상태를 제출하라.

대상 항목 예시:
- Navigation menu
- Site title visibility
- Logo upload / replacement
- Homepage shell / WordPress front-page setting
- 기타 WP Admin 설정성 작업

각 항목별 상태값:
- `DONE_BY_OPERATOR`
- `NOT_DONE_OPERATOR_PENDING`
- `NOT_REQUIRED`
- `PARTIAL`

필수 규칙:
- CSS로 해결된 것과 운영자 설정으로 해결된 것을 혼합 서술하지 말 것
- “시각적으로는 보임”과 “실운영 설정 완료”를 구분할 것

---

## 4. 재제출 패키지 권장 구조
재제출 시 아래 구조를 권장한다.

### 4.1 문서 세트
- `step01-08A_DEPLOYED_SCREENSHOT_INDEX.md`
- `step01-08B_MODIFIED_FILE_DIFF_SUMMARY.md`
- `step01-08C_ZERO_EDIT_SAFETY_PROOF.md`
- `step01-08D_OPERATOR_SCOPE_STATUS.md`
- `step01-08E_FINAL_ACCEPTANCE_READY_NOTE.md`

### 4.2 최소 첨부 자산
- live/deployed screenshots
- diff text or patch summary
- zero-edit evidence capture/log
- operator status table

---

## 5. 최종 승인 기준
아래 조건이 모두 충족되어야 최종 승인 가능하다.

### 5.1 Hard Pass 조건
- live/deployed screenshot이 제출되었다.
- 변경 파일 diff 또는 파일별 변경 요약이 제출되었다.
- `generator.py`, `styles/tokens.py` 무수정 증빙이 제출되었다.
- operator scope 상태가 분리 보고되었다.
- 기존 스타일 트랙의 금지선 위반이 없다.

### 5.2 Fail 조건
다음 중 하나라도 해당하면 최종 승인 불가다.

- injected preview만 있고 live/deployed proof가 없음
- 변경 파일이 무엇인지 확인 불가
- `generator.py` 또는 `styles/tokens.py` 변경 흔적 존재
- WordPress 설정 작업과 CSS 작업이 뒤섞여 있어 완료 상태 판별 불가
- rollback 불가능 또는 rollback 경로 불명확

---

## 6. Antigravity 전달용 재지시 문구
아래 문구를 그대로 전달해도 된다.

> `step01-08_VERIFICATION_PROOF.md`는 프리뷰 검증 보고서로는 유효하나, 최종 운영 반영 증빙으로는 부족하다.
> 따라서 아래 4개를 추가 제출하라.
> 1) deployed-state desktop/mobile screenshots
> 2) modified file diff summary
> 3) zero-edit proof for `generator.py` and `styles/tokens.py`
> 4) operator-scope completion status for menu/logo/home shell and related WP settings
> 
> 제출물은 injected preview와 live/deployed state를 구분해야 하며,
> 파일별 변경 목적과 영향 범위를 확인 가능해야 한다.
> 위 4개가 확인되면 final acceptance review를 진행한다.

---

## 7. 리뷰어 메모
이번 요청은 디자인 방향 자체를 부정하는 것이 아니다.
현재 상태는 **실행 자체는 상당 부분 진척되었으나, 최종 승인용 증빙 패키지가 아직 부족한 상태**다.
따라서 Antigravity는 새로 설계할 필요 없이,
기존 작업을 **운영 반영 기준으로 다시 증빙하는 일**에 집중하면 된다.

---

## 8. 운영 원칙 고정
앞으로 스타일 트랙은 아래 순서를 기본 운영으로 고정한다.

1. Antigravity 계획 수립
2. 계획 검증
3. 리뷰 + 평가표 작성
4. Antigravity 실제 업무 수행
5. 실행 증빙 제출
6. 최종 acceptance review

그리고 관련 문서는 항상 가능한 한 **pair**로 관리한다.
- 스타일 프롬프트 MD
- 평가표 / 검수표 MD

