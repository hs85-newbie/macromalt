# 06. Rollback Plan (Step02)

Step02 구현 중 문제가 발생할 경우의 복구 절차입니다.

## 1. Quick Rollback (Site Icons & CSS)
- **Method**: 워드프레스 테마를 기존 `macromalt-child` (Step01 버전)로 재활성화하거나, 스타일 시트만 이전 버전으로 롤백합니다.
- **Time**: 즉시 반영 가능.

## 2. Structural Rollback (Hooks / Functions)
- **Functions**: `theme/child-theme/functions.php` 파일을 삭제하거나 리네임하여 원본 `generatepress` 테마의 로직으로 즉시 환원합니다.
- **Command**:
  ```bash
  mv theme/child-theme/functions.php theme/child-theme/functions.php.bak
  ```

## 3. Emergency Restoration
- 모든 작업은 `wordpress_upload/` 내의 ZIP 백업본을 기반으로 관리되므로, 시스템 오류 시 해당 ZIP 파일을 재업로드하여 가장 안정적인 상태(Step01)로 복구할 수 있습니다.
