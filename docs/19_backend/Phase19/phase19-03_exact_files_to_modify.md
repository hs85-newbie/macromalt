# phase19-03. Exact Files to Modify (Phase 19 Logging)

## 1. Backend Pipeline
- [MODIFY] `generator.py`: `_calculate_quality_metrics` 함수 신설 및 성공 경로 주입.
- [MODIFY] `main.py`: 최종 로그 요약 블록에 JSON 형식의 4-pass Audit 데이터 추가.

## 2. Safety Boundary
- 오직 로깅과 지표 수집 레이어만 수정합니다.
- Verifier의 판정 로직, 프롬프트, 발행 과정, 그리고 Step04 스타일 레이어는 일체 수정하지 않습니다.
