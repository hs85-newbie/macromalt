# step03-06. Rollback Plan (Step03)

Step03 작업 중 문제가 발생할 경우 Step02 완료 시점으로 복구하는 절차입니다.

## 1. Structural Rollback (Hooks)
`functions.php`에서 다음 Step03 전용 훅 코드를 제거합니다.
- `DISCLOSURE & METHODOLOGY` 주입 훅
- `SEARCHING THE MACROMALT ARCHIVE` 주입 훅
- `Footer Trust Micro-layer` 주입 훅

## 2. Visual Rollback (CSS)
다음 파일들에서 Step03를 위해 추가된 스타일 선언 및 임포트를 제거합니다.
- `theme/child-theme/style.css`
- `styles/wordpress/base.css`
- `styles/wordpress/typography.css`
- `styles/wordpress/components.css`

## 3. Atomic Recovery
- 가장 권장되는 방식은 보관된 `macromalt-step02.zip`을 다시 테마 업로드를 통해 설치하고 활성화하는 것입니다.

---

## 4. Verification Check
롤백 완료 후, Step02의 에디토리얼 마스트헤드와 Step01의 읽기 최적화 Typography가 그대로 작동하는지 최종 확인합니다.
