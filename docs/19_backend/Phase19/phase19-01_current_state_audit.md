# phase19-01. Current State Audit (Phase 19 Logging)

## 1. Quality Analytics Gap
현재 `generator.py`는 `PARSE_FAILED` 발생 시에만 `_log_parse_failed_event`를 통해 심층적인 품질 지표(Opener pass, Criteria pass 등)를 기록합니다. 정상 발행 경로(GO)에서는 이러한 세부 지표가 로그에 남지 않아, 실제로 발행된 글의 품질이 기준을 충족하는지에 대한 운영 증적이 부족한 상태입니다.

## 2. Technical Context
- **Target Fields**: `opener_pass`, `criteria_1_pass`, `criteria_5_pass`, `source_structure_pass`.
- **Target Path**: `generator.py` -> `generate_deep_analysis` 및 `generate_stock_picks_report`.
- **Log Sink**: `macromalt_daily.log` 및 표준 출력(stdout).

## 3. Objective
정상 발행 성공 시에도 4개 지표를 계산하여 로그에 남김으로써, Route B 최종 GO 판정 및 Phase 19 클로저를 위한 데이터를 확보하는 것입니다.
