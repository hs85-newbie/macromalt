# step04-01. Current State Audit (Step04)

## 1. Fixed Foundations (LOCKED)
Step03 완료 후 사이트는 '제도권 리서치 플랫폼'의 시각적 안정성을 확보했습니다. 다음은 **불변의 영역**으로 관리됩니다.
- **Typography**: Georgia 헤딩 체계 및 Mono-type 유틸리티 폰트.
- **IA/Masthead**: 홈페이지 히로 쉘 및 글로벌 내비게이션 구조.
- **Trust Layer**: Disclosure 박스 물리적 위치 및 푸터 신뢰 레이어.
- **Reading Rhythm**: 본문 폭, 자간, 행간 등 가독성 관련 수치.

## 2. Seasonal Refinement Targets (VARIABLE)
계절성(Seasonal Layer) 주입 시 영향을 받을 수 있는 **허용된 영역**입니다.
- **Tonal Tint**: 배경지(Paper) 톤 및 보조 배경색.
- **Accent Rules**: 텍스트 강조색, 구분선(Rule)의 채도/명도.
- **Badge Nuance**: 카테고리 배지 및 메타데이터 레이블의 배경/텍스트 대비 연동.
- **Subtle Atmosphere**: 미세한 그림자 톤 또는 호버(Hover) 시의 계절별 색온도.

## 3. Risk Assessment
- **Contrast Regression**: 계절별 배경색 변경 시 텍스트 가독성 저하 위험.
- **Brand Dilution**: 색상이 너무 화려해져 기관용 정체성이 훼손될 위험.
- **Logic Fragility**: 자동 전환 로직의 복잡성으로 인한 런타임 오류 위험.

## 4. Audit Conclusion
물리적 구조(Structure)는 100% 고정하되, **CSS 변수(Variable Layer)**만을 통해 매달 '기온'과 '습도'가 변하는 듯한 미세한 톤 변화를 구현하는 것이 가장 안전한 전략입니다.
