# MACROMALT LLM PIPELINE

기준일: 2026-03-16

## 1. 현재 역할 분담

### Gemini
- Step1 분석 재료 생성
- verifier(팩트체크)
- reviser(수정)
- 종목선정 보조

### OpenAI
- Post1 심층분석 작성
- Post2 종목리포트 작성

---

## 2. 파이프라인 구조

1. 뉴스 수집
2. 리서치 수집
3. 분석 재료 생성 (Gemini)
4. Post1 작성 (OpenAI)
5. Post2 작성 (OpenAI)
6. 팩트체크 (Gemini)
7. 수정 (Gemini)
8. WordPress 발행

---

## 3. 실제 확인된 파라미터

### Gemini
| Step | Model | Temperature | Token 상한 |
|---|---|---:|---:|
| Step1 분석재료생성 | `gemini-2.5-flash` | 0.2 | 3000 |
| Step3 팩트체크 | `gemini-2.5-flash` | 0.1 | 3000 |
| Step3 수정 | `gemini-2.5-flash` | 0.3 | 3000 |
| Post2-Step1 종목선정 | `gemini-2.5-flash` | 0.2 | 3000 |

추가 확인:
- `thinking_budget = 0` 실제 전송 확인
- `top_p`, `presence_penalty`, `stop` 등은 현재 미사용

### OpenAI
| Step | Model | Temperature | Token 상한 |
|---|---|---:|---:|
| Step2a 심층분석작성 | `gpt-4o` | 0.7 | 5000 |
| Step2b 종목리포트작성 | `gpt-4o` | 0.65 | 6000 |

---

## 4. DEBUG_LLM 정책

`DEBUG_LLM=1`일 때만 API 호출 직전 payload 요약 로그를 출력한다.

출력 예:
- provider
- model
- temperature
- token 상한
- system_len
- user_len

원칙:
- 기본 동작은 변경하지 않는다
- full payload가 아니라 summary 위주로 남긴다
- 프롬프트 원문 전체 로그는 기본적으로 남기지 않는다

---

## 5. 파라미터 운영 원칙

- 파라미터는 현재 기준값을 유지한다
- 먼저 프롬프트/검수 규칙을 보정한다
- 파라미터 변경은 최후 수단이다
- 품질 이슈가 생기면:
  1. source 문제인지
  2. 규칙 문제인지
  3. 파라미터 문제인지
  를 분리해서 본다

---

## 6. 멀티 LLM 확장 원칙

향후 멀티 LLM 확장 시:
- 기본 운영은 Gemini + OpenAI
- Claude는 선택적 편집 레이어 후보
- Perplexity는 최신성 검색 보강 레이어 후보
- 초기 1개월은 관찰 운영 후 정책 확정

---

## 7. 변경 금지 원칙
현재 운영 단계에서 아래는 금지 또는 보류한다.
- 무분별한 모델 교체
- temperature 잦은 변경
- 파라미터와 프롬프트를 동시에 크게 바꾸는 것
- 문제 원인 분리 없는 튜닝

이 문서는 macromalt의 현재 LLM 구조와 관측 정책 문서다.
