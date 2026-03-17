# MACROMALT DEDUP ENGINE DESIGN

기준일: 2026-03-16  
상태: Phase 11 설계 기준 문서 (구현 진행 중)

## 1. 목적

- 같은 theme가 강한 날에도 같은 질문 구조 반복을 줄인다
- theme / sub_axes / 종목군 수준의 반복 완화 규칙을 만든다
- 완전 차단보다 회전 지시와 감점을 우선한다
- 신규 데이터 소스 없이 현재 파이프라인 기준으로 최소 구현한다

---

## 2. 현재 문제

Phase 10의 반복 감지는 아래 한계가 있었다.
- `sub_axes[0]` 문자열 완전 일치 중심
- 같은 슬롯 48시간 규칙 위주
- theme 유사도 비교 없음
- 종목군 반복 감지 없음
- 감지 결과가 단순 ON/OFF 성격

따라서 같은 테마가 강한 날,
- 유사 topic
- 유사 질문 구조
- 유사 종목군
으로 수렴하는 것을 더 줄일 필요가 있다

---

## 3. 반복 판단 단위

### 3.1 theme fingerprint
키워드 카테고리 매핑 기반 문자열 fingerprint

예시:
- `"중동 지정학적 리스크와 국제유가 급등"` → `에너지_유가|지정학_전쟁`
- `"중동 긴장 고조와 유가 상승"` → `에너지_유가|지정학_전쟁`
- `"미국 연준 금리 인상 우려"` → `금리_통화`

매칭 실패 시:
- `기타`
- 감점 없음
- 로그는 남김

### 3.2 sub_axes fingerprint
각 sub_axes 항목을 핵심 질문 축 id로 매핑

예시:
- `"미국장 마감 이후 반응"` → `미국장_마감`
- `"한국 수출 타격"` → `수출_무역`

### 3.3 종목군 fingerprint
티커 → 버킷 매핑

예시:
- `XLE / XOM / CVX` → `에너지`
- `005930 / 000660 / NVDA` → `반도체_기술`

미매핑은 `기타`.

---

## 4. 반복 감점 규칙

### MILD
- 같은 `theme_fingerprint`
- 같은 `slot`
- 48시간 이내

처리:
- sub_axes 전환 권고

### STRONG
- 같은 `theme_fingerprint`
- 같은 `sub_axes_fingerprint[0]`
- 24시간 이내

처리:
- sub_axes 전체 교체 강제 지시

### BUCKET
- 같은 `theme_fingerprint`
- 같은 종목군 교집합
- 24시간 이내

처리:
- Post2 대체 종목군 지시

### 허용 규칙
- 같은 theme라도 slot이 다르고 질문 구조가 다르면 허용
- 같은 theme라도 종목군이 다르면 부분 허용
- `theme_fingerprint = 기타`는 감점 없음

복수 규칙 동시 발동 시 우선순위:
- `STRONG > BUCKET > MILD`

---

## 5. 우회/회전 규칙

### STRONG
- theme_sub_axes 전체 교체
- 이전과 다른 인과 경로(축) 3개 선택 지시

### BUCKET
- 이전 버킷 외 섹터에서 선정 지시
- 대안 종목군 제시

### MILD
- 같은 테마라면 하위 관점 최소 2개 이상 교체 지시

### Fallback
- 최근 5건 모두 같은 `theme_fingerprint`
- STRONG + BUCKET 동시 지시
- 완전 차단은 하지 않음

---

## 6. Post1 / Post2 역할 차이 유지

### Post1
- 매크로 메커니즘
- 파급 경로
- 시장 구조
- 정책 연결고리

### Post2
- 종목/섹터 민감도
- 트리거 조건
- 구체 티커 선정 이유

반복이 감지되면:
- Post1은 원인 구조
- Post2는 종목 트리거
에 더 집중하도록 지시를 강화한다

---

## 7. publish_history 확장안

예시 구조:

```json
{
  "published_at": "2026-03-16T18:00:00+09:00",
  "slot": "evening",
  "theme": "중동 긴장 고조와 유가 상승",
  "theme_fingerprint": "에너지_유가|지정학_전쟁",
  "sub_axes": ["미국장 마감 반응", "한국 정유주 영향"],
  "sub_axes_fingerprint": ["미국장_마감", "업종_차별화"],
  "post1_title": "...",
  "post2_title": "...",
  "tickers": ["XLE", "XOM", "010950.KS"],
  "stock_buckets": ["에너지"]
}
```

---

## 8. 로그 정책

예시:
- `[Phase 11] theme fingerprint: "에너지_유가|지정학_전쟁"`
- `[Phase 11] sub_axes fingerprint: ["미국장_마감", "업종_차별화"]`
- `[Phase 11] stock_buckets: ["에너지"]`
- `[Phase 11] 반복 감지 — STRONG ...`
- `[Phase 11] 반복 감지 — BUCKET ...`
- `[Phase 11] 회전 지시 삽입: STRONG`
- `[Phase 11] 이력 저장 완료 ...`

추가 권장 로그:
- `theme_fp=기타`
- `stock bucket unmapped`
- fallback 발동 여부

---

## 9. 범위 밖
- 임베딩/벡터DB
- 신규 데이터 소스
- scraper/main 구조 변경
- 파라미터 변경
- 대규모 리팩토링

이 문서는 Phase 11 구현 기준 설계 문서다.
