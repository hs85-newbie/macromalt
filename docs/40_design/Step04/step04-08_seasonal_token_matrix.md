# step04-08. Seasonal Token Matrix (LOCKED v4)

[SSOT] Macromalt의 12개월 계절 변수 매트릭스입니다. 모든 헥사코드는 브랜드 가독성을 보장하도록 설계되었습니다.

## 1. 12-Month Component Matrix

| ID | Season | `--mm-bg` | `--mm-bg-alt` | `--mm-rule` | `--mm-ink-soft` | `--mm-accent` | `--mm-badge-bg` | `--mm-badge-text` |
|:---|:-------|:----------|:--------------|:------------|:----------------|:--------------|:----------------|:------------------|
| **jan** | Frost | `#FBFCFF` | `#F5F7FA` | `#E0E3EB` | `#667085` | `#2D4B75` | `#E8EDF5` | `#1D2D45` |
| **feb** | Ash | `#F8F8F9` | `#F2F2F3` | `#DEDFE0` | `#707070` | `#4A4A4A` | `#ECECED` | `#222222` |
| **mar** | Thaw | `#FCFAF8` | `#F7F2ED` | `#EDE2D9` | `#8C7B6D` | `#8C6D51` | `#F5EBE4` | `#4D3A2B` |
| **apr** | Mist | `#F7FAF9` | `#F0F5F2` | `#D9E5E1` | `#66857A` | `#4D756A` | `#E6F0EE` | `#2B403A` |
| **may** | Sage | `#F9FAF7` | `#F2F5ED` | `#E1E5D9` | `#7A8566` | `#6A754D` | `#EFF2E9` | `#3A402B` |
| **jun** | Haze | `#FFFBF8` | `#FAF5F0` | `#EBE0D5` | `#8C7D6D` | `#8C5E3D` | `#F7EFE9` | `#4D3321` |
| **jul** | Storm | `#F6F7F9` | `#F0F1F5` | `#D5DAE1` | `#667085` | `#3D5475` | `#E9EDF2` | `#212D40` |
| **aug** | Amber | `#FAF9F7` | `#F5F2ED` | `#E6E1D9` | `#857A66` | `#755E3D` | `#F2F0E9` | `#403A2B` |
| **sep** | Harvest| `#FBF9F5` | `#F5F0E9` | `#E1DCCF` | `#857A66` | `#756A3D` | `#F2EEE4` | `#403A21` |
| **oct** | Oak | `#F9F7F5` | `#F2EFEC` | `#E3D8CE` | `#857066` | `#754D2D` | `#F2E9E1` | `#402B1D` |
| **nov** | Smoke | `#F7F7F7` | `#F2F2F2` | `#D9D9D9` | `#707070` | `#4A4A4A` | `#EEEEEE` | `#222222` |
| **dec** | Velvet | `#F6F5F7` | `#F1F0F2` | `#DED9E1` | `#706685` | `#5E3D75` | `#EEE9F2` | `#332140` |

## 2. Global Variable Surface
- **`--mm-bg`**: 메인 페이지 배경.
- **`--mm-bg-alt`**: 사이드바 및 보조 카드 배경.
- **`--mm-rule`**: 모든 `border` 및 `hr` 구분선.
- **`--mm-ink-soft`**: 메타 데이터 및 보조 텍스트 (명도 40% 내외).
- **`--mm-accent`**: 링크 호버, 버튼, 인라인 강조 요소 통합 변수.
- **`--mm-badge-bg`**: 카테고리 배지 배경색.
- **`--mm-badge-text`**: 배지 내 텍스트 색상 (배경 대비 보완).

## 3. Fallback Safety
클래스 매핑 실패 시 Step03의 Default 흑백/그레이 체계로 자동 복귀합니다.
- Default `--mm-bg`: `#FFFFFF`
- Default `--mm-rule`: `#EAEAEA`
