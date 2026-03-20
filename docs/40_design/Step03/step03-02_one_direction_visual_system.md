# step03-02. One Direction Visual System (Step03)

Step03의 유일한 시각적 방향성인 **"The Institutional Utility Layer (제도권 유틸리티 레이어)"**를 확정합니다.

## 1. Core Concept: "Quiet Maturity"
불필요한 장식을 배제하고, 정보의 출처와 신뢰도를 담백하게 전달하는 '차분한 성숙함'을 지향합니다.

## 2. Locked Trust Surface Copy (LOCKED)

### A. Disclosure Box (기사 상단 고지 사항)
- **Heading**: `DISCLOSURE & METHODOLOGY`
- **Body Content (Locked)**: 
  > Macromalt provides institutional-grade market research and analysis for information purposes only. Our methodology prioritizes data-driven insights and verified global macro trends. All information is subject to change without notice. No investment advice is implied or provided.
- **Scope**: 오직 `single` 기사 페이지에만 노출.
- **Exclusion**: Home, About, Category, Archive, Search, Static Pages에서는 절대 노출하지 않음.

### B. About Page Skeleton (Locked Structure)
워드프레스 관리자에서 운영자가 편집 가능하도록 초기화하되, 아래 구조와 최소 카피를 유지합니다.
1. **The Mission**: `INSTITUTIONAL RESEARCH FOR THE GLOBAL MACRO` (Macromalt의 존재 이유)
2. **Methodology**: `DATA-DRIVEN & VERIFIED` (검증 프로세스 및 정보 원천)
3. **Coverage Area**: `GLOBAL EQUITY, MACRO TRENDS, & CURATED PICKS` (주요 분석 영역)
4. **Continuity**: `EDITORIAL STANDARDS & OBJECTIVITY` (독자가 기대할 점)
5. **Contact & Closure**: `OFFICIAL CHANNELS & IDENTITY` (문의 및 정체성 요약)

### C. Footer Append Strategy
기존 GeneratePress 푸터 정체성(Site Title)을 삭제하지 않고, 그 하단에 **Trust Micro-layer**를 추가(Append)합니다.
- **Text**: `© 2026 MACROMALT. ALL RIGHTS RESERVED. INSTITUTIONAL RESEARCH FOR THE GLOBAL MACRO.`

### D. Search Result Header
- **Search Header Label**: `SEARCHING THE MACROMALT ARCHIVE:`
- **Empty State Label**: `NO RESULTS FOUND IN THE MACROMALT ARCHIVE.`
- **Condition**: `is_search()` 시에만 상단 훅으로 주입.

## 3. Visual Rules
- **Typography**: 
  - 메타데이터, 배지, 푸터 링크, Disclosure 헤딩에 **Mono-type stack** 적용.
  - 사이즈: `11px~13px`.
- **Disclosure Detail**: 
  - Background: `#F8F9FA`, Border: `1px solid var(--color-rule)`.
