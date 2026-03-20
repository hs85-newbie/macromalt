# step04-09. PHASE19 Logging Plan (Backend Audit)

## 1. Objective
정상 발행 경로(Normal Success Path)에서 4개 핵심 Pass 필드를 로그에 남겨, Phase 19 Route B의 최종 GO 판정을 위한 근거 데이터를 확보합니다.

## 2. Technical Implementation

### 2.1 Quality Logic Centralization (`generator.py`)
현재 `_log_parse_failed_event` 내부에 파편화되어 있는 품질 계산 로직을 독립된 함수로 분리합니다.
- **New Function**: `_calculate_quality_metrics(raw_output: str) -> dict`
- **Output Fields**:
    - `opener_pass`: Pick-angle 도입부 구조 유지 여부.
    - `criteria_1_pass`: 시점 혼합(과거형) 부재 여부.
    - `criteria_5_pass`: 투자 권유 표현 부재 여부.
    - `source_structure_pass`: 출처/리서치 블록 구조 여부.

### 2.2 Success Path Integration
- `generate_deep_analysis` 및 `generate_stock_picks_report` 함수 내부에서, `verify_draft` 통과 후 최종 `final_content`에 대해 `_calculate_quality_metrics`를 실행합니다.
- 추출된 지표를 `quality_metrics`라는 키로 결과 딕셔너리에 포함시켜 `main.py`로 전달합니다.

### 2.3 Dashboard Logging (`main.py`)
- `main.py`의 `logger.info("=" * 60)` 요약 블록 직전에, Phase 19 전용 Audit JSON 로그를 출력하도록 보강합니다.
- **Log Format**:
  ```json
  {
    "run_id": "...",
    "slot": "...",
    "post_type": "post1/post2",
    "final_status": "GO",
    "opener_pass": true,
    "criteria_1_pass": true,
    "criteria_5_pass": true,
    "source_structure_pass": true
  }
  ```

## 3. Scope Protection
- 기존 PARSE_FAILED 로그 구조(`_log_parse_failed_event`)는 그대로 유지하여 하위 호환성을 보장합니다.
- Verifier/Reviser의 판정 알고리즘이나 프롬프트는 수정하지 않습니다. (순수 로깅 보강)
