# DOCUMENT AUTHORITY MATRIX

작성일: 2026-03-17
목적: 문서별 최종 권한 소유자 및 수정 허가 주체 정의

---

| 문서 | 경로 | 권한 소유자 | 수정 허가 주체 |
|------|------|-------------|---------------|
| MACROMALT_PRD_MASTER | 00_master/ | 프로젝트 오너 | 프로젝트 오너 |
| MACROMALT_DATA_POLICY | 10_policies/ | Claude Code | 프로젝트 오너 승인 후 |
| MACROMALT_OPERATION_POLICY | 10_policies/ | Claude Code | 프로젝트 오너 승인 후 |
| MACROMALT_WRITING_AND_VERIFICATION_RULES | 10_policies/ | Claude Code | 프로젝트 오너 승인 후 |
| MACROMALT_SLOT_POLICY | 10_policies/ | Claude Code | 프로젝트 오너 승인 후 |
| MACROMALT_LLM_PIPELINE | 10_policies/ | Claude Code | 프로젝트 오너 승인 후 |
| MACROMALT_DEDUP_ENGINE_DESIGN | 10_policies/ | Claude Code | 프로젝트 오너 승인 후 |
| MACROMALT_RESEARCH_POLICY_V3 | 10_policies/ | Claude Code | 프로젝트 오너 승인 후 |
| DESIGN_STYLE_SEPARATION_STRUCTURE | 20_tracks/wordpress_style/ | Claude Code | Antigravity / Codex 참조용 |
| MACROMALT_WORDPRESS_STYLE_TRACK_MASTER_GUIDE | 20_tracks/wordpress_style/ | Claude Code | Antigravity / Codex 수정 가능 |
| macromalt_prd_final | 30_reference/ | 프로젝트 오너 | 참조 전용 (수정 금지) |
| macromalt_prd_final_v2 | 30_reference/ | 프로젝트 오너 | 참조 전용 (수정 금지) |

---

## 에이전트별 수정 허용 범위

| 에이전트 | 수정 허용 범위 |
|----------|---------------|
| Claude Code | 10_policies/, 20_tracks/, 99_meta/ |
| Antigravity / Codex | 20_tracks/wordpress_style/ 만 |
| 프로젝트 오너 | 전체 |
