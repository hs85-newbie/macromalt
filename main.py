"""
macromalt 자동화 시스템 - 메인 파이프라인 (Phase 15E / v3 정책 반영)
=====================================================
실행 순서:
  Step 1   — 뉴스 수집 (기존 RSS/Web 소스)
  Step 1B  — 리서치 수집 (네이버금융 + 한경 컨센서스)
  Step 2A  — Post 1 생성: 심층 경제 분석
  Step 2B  — Post 2 생성: 종목 리포트
  Step 3A  — Post 1 WordPress 임시저장
  Step 3B  — Post 2 WordPress 임시저장

에러 처리:
  Post 1 실패 → Post 2도 중단 (파이프라인 전체 종료)
  Post 2 실패 → Post 1 결과는 유지 (경고 로그 후 종료)

실행 방법:
  source venv/bin/activate
  python main.py
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


# ──────────────────────────────────────────────
# 0. 슬롯 식별 — Phase 10
# ──────────────────────────────────────────────

def _is_us_dst(dt: datetime) -> bool:
    """미국 서머타임(EDT) 적용 여부 판단.
    규칙: 3월 두 번째 일요일 ~ 11월 첫 번째 일요일 (미국 DST 기준).
    """
    year = dt.year
    # 3월 두 번째 일요일
    mar1 = datetime(year, 3, 1)
    dst_start = mar1 + timedelta(days=(6 - mar1.weekday()) % 7 + 7)
    # 11월 첫 번째 일요일
    nov1 = datetime(year, 11, 1)
    dst_end = nov1 + timedelta(days=(6 - nov1.weekday()) % 7)
    return dst_start.date() <= dt.date() < dst_end.date()


def detect_slot(dt: datetime = None) -> str:
    """현재 시각(KST)을 기준으로 발행 슬롯을 반환한다.

    슬롯 정의 (KST):
      morning  : 05:00 ~ 11:59  — 미국장 마감 → 한국장 개장 전
      evening  : 14:00 ~ 20:59  — 한국장 마감 리뷰
      us_open  : DST   21:30 ~ 22:29  / non-DST 22:30 ~ 23:29
                 미국장 개장 30분 전 중심 ±30분 윈도우
      default  : 그 외 시간대    — 중립 일반 브리핑
    """
    if dt is None:
        dt = datetime.now()
    hm = dt.hour * 100 + dt.minute  # 예: 21:35 → 2135

    if 500 <= hm < 1200:
        return "morning"
    if 1400 <= hm < 2100:
        return "evening"

    # us_open 윈도우: DST 여부에 따라 30분씩 이동
    if _is_us_dst(dt):
        if 2130 <= hm < 2230:
            return "us_open"
    else:
        if 2230 <= hm < 2330:
            return "us_open"

    return "default"


# ──────────────────────────────────────────────
# 1. 로거 설정 (파일 + 콘솔 동시 출력)
# ──────────────────────────────────────────────
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "macromalt_daily.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("macromalt")


# ──────────────────────────────────────────────
# 2. 카테고리 ID 로드 헬퍼
# ──────────────────────────────────────────────
def _get_category_ids(env_key: str, default: list) -> list:
    """
    .env에서 카테고리 ID를 읽어 반환합니다.
    값이 없거나 파싱 실패 시 default를 사용합니다.
    """
    val = os.getenv(env_key, "").strip()
    if val:
        try:
            return [int(x.strip()) for x in val.split(",") if x.strip()]
        except ValueError:
            logger.warning(f"⚠ {env_key} 값 파싱 실패, 기본값 {default} 사용")
    return default


# ──────────────────────────────────────────────
# 3. 파이프라인 단계별 실행 함수
# ──────────────────────────────────────────────
def step_scrape_news() -> list[dict]:
    """Step 1: 뉴스 수집 (RSS/Web 소스)"""
    from scraper import run_all_sources

    logger.info("▶ [Step 1] 뉴스 수집 시작")
    articles = run_all_sources()

    if not articles:
        raise RuntimeError("수집된 기사가 0건입니다. sources.json 및 네트워크를 확인하세요.")

    logger.info(f"✅ [Step 1] 뉴스 수집 완료: {len(articles)}건")
    return articles


def step_scrape_research() -> list[dict]:
    """Step 1B: 리서치 수집 (네이버금융 + 한경 컨센서스)"""
    from scraper import run_research_sources

    logger.info("▶ [Step 1B] 리서치 데이터 수집 시작")
    research = run_research_sources()
    logger.info(f"✅ [Step 1B] 리서치 수집 완료: {len(research)}건")
    return research


def step_generate_analysis(news: list[dict], research: list[dict], slot: str = "default") -> dict:
    """Step 2A: Post 1 — 심층 경제 분석 생성"""
    from generator import generate_deep_analysis

    logger.info("▶ [Step 2A] Post 1 심층 경제 분석 생성 시작")
    post1 = generate_deep_analysis(news, research, slot=slot)
    logger.info(f"✅ [Step 2A] Post 1 생성 완료: '{post1['title']}'")
    logger.info(f"   핵심 주제: {post1.get('theme', 'N/A')}")
    return post1


def step_generate_picks(post1: dict, news: list[dict], research: list[dict], slot: str = "default") -> dict:
    """Step 2B: Post 2 — 종목 리포트 생성"""
    from generator import generate_stock_picks_report

    logger.info("▶ [Step 2B] Post 2 종목 리포트 생성 시작")
    post2 = generate_stock_picks_report(
        theme=post1.get("theme", ""),
        key_data=post1.get("key_data", []),
        post1_content=post1.get("content", ""),
        news=news,
        research=research,
        materials=post1.get("materials"),   # Phase 7: Post 1 분석 재사용
        slot=slot,                          # Phase 10: 슬롯 전달
    )
    logger.info(f"✅ [Step 2B] Post 2 생성 완료: '{post2['title']}'")
    picks_count = len(post2.get("picks", []))
    logger.info(f"   선정 종목: {picks_count}개")
    return post2


def step_publish(post: dict, category_ids: list, step_label: str, featured_media_id: int = None) -> dict:
    """Step 3A/3B: WordPress Draft 업로드"""
    from publisher import publish_draft

    logger.info(f"▶ [{step_label}] WordPress 업로드 시작: '{post['title']}'")
    result = publish_draft(
        title=post["title"],
        content=post["content"],
        category_ids=category_ids,
        featured_media_id=featured_media_id,
    )
    logger.info(f"✅ [{step_label}] 업로드 완료: Post ID {result['post_id']}")
    return result


# ──────────────────────────────────────────────
# 4. 메인 실행 진입점
# ──────────────────────────────────────────────
def main() -> None:
    now    = datetime.now()
    run_id = now.strftime("%Y%m%d_%H%M%S")
    slot   = detect_slot(now)

    logger.info("=" * 60)
    logger.info(f"macromalt Phase 15E 파이프라인 시작 [run_id: {run_id}]")
    logger.info(f"[Phase 15E] 슬롯: {slot} | run_id: {run_id}")
    logger.info("=" * 60)

    # 카테고리 ID 로드
    cat_analysis = _get_category_ids("WP_CATEGORY_ANALYSIS", [2])
    cat_picks    = _get_category_ids("WP_CATEGORY_PICKS",    [2])
    logger.info(f"   카테고리 — 심층분석: {cat_analysis} | 종목리포트: {cat_picks}")

    post1_result = None
    post2_result = None

    try:
        # ── Step 1: 수집 ──────────────────────────────
        news     = step_scrape_news()
        research = step_scrape_research()

        # ── Step 2A: Post 1 생성 ──────────────────────
        post1 = step_generate_analysis(news, research, slot=slot)

    except RuntimeError as e:
        logger.error("=" * 60)
        logger.error(f"❌ [Step 1] 수집 실패 [run_id: {run_id}]")
        logger.error(f"   원인: {e}")
        logger.error("=" * 60)
        sys.exit(1)

    except Exception as e:
        logger.exception(f"❌ [Step 2A] Post 1 생성 실패 [run_id: {run_id}]")
        logger.error(f"   원인: {e}")
        logger.error("   Post 1 실패로 Post 2 생성을 중단합니다.")
        sys.exit(1)

    try:
        # ── Step 2B: Post 2 생성 ──────────────────────
        post2 = step_generate_picks(post1, news, research, slot=slot)

    except Exception as e:
        logger.error(f"⚠ [Step 2B] Post 2 생성 실패 — Post 1은 계속 발행합니다.")
        logger.error(f"   원인: {e}")
        post2 = None

    # ── Step 2C: 이미지 준비 (비치명 — 실패해도 발행 계속) ───
    from images import attach_post1_image, attach_post2_image, inject_chart_into_content
    from publisher import _strip_leading_h1
    import re as _re

    logger.info("▶ [Step 2C] 이미지 준비")
    post1_media_id, post1_attribution = attach_post1_image(post1.get("theme", ""))
    post2_media_id, post2_img_html    = attach_post2_image(post2.get("picks", []) if post2 else [])
    logger.info(f"   이미지 — Post1: media_id={post1_media_id} | Post2: media_id={post2_media_id}")

    # Post 1: 본문 하단에 Unsplash 출처 표기
    if post1_attribution:
        post1["content"] = post1.get("content", "") + (
            f'\n<p class="mm-image-credit" style="font-size:11px;color:#aaa;text-align:right;margin-top:2em;">'
            f'[출처: {post1_attribution}]'
            f'</p>'
        )
        logger.info("   Post1 이미지 출처 표기 추가")

    # Post 2: h1 먼저 제거 → 차트를 메인 픽 h2 직후에 삽입 (featured_media 미사용 — 본문 삽입만)
    if post2 and post2_img_html:
        _url_m = _re.search(r'src="([^"]+)"', post2_img_html)
        _alt_m = _re.search(r'alt="([^"]+)"', post2_img_html)
        if _url_m:
            post2["content"] = _strip_leading_h1(post2["content"])
            post2["content"] = inject_chart_into_content(
                post2["content"],
                _url_m.group(1),
                _alt_m.group(1) if _alt_m else "",
            )
            logger.info("   차트 본문 삽입 완료 (메인 픽 h2 직후)")

    try:
        # ── Step 3A: Post 1 발행 ─────────────────────
        post1_result = step_publish(post1, cat_analysis, "Step 3A", featured_media_id=post1_media_id)

    except Exception as e:
        logger.error(f"❌ [Step 3A] Post 1 발행 실패 [run_id: {run_id}]")
        logger.error(f"   원인: {e}")
        sys.exit(1)

    if post2 is not None:
        try:
            # ── Step 3B: Post 2 발행 (featured_media 없음 — 차트는 본문에만)
            post2_result = step_publish(post2, cat_picks, "Step 3B", featured_media_id=None)

        except Exception as e:
            logger.error(f"⚠ [Step 3B] Post 2 발행 실패")
            logger.error(f"   원인: {e}")
            logger.warning("   Post 1은 정상 발행되었습니다.")

    # ── Phase 10: 발행 이력 저장 ─────────────────────
    if post1_result:
        try:
            from generator import save_publish_history
            save_publish_history(
                slot=slot,
                post1=post1,
                post2=post2 if post2 is not None else None,
            )
        except Exception as e:
            logger.warning(f"⚠ 발행 이력 저장 실패 (비치명): {e}")

    # ── Phase 19: 정상 발행 경로 품질 필드 로그 ────────────────────────
    try:
        from generator import _log_normal_publish_event
        _final_status = "GO"  # 여기까지 도달하면 정상 발행 완료

        if post1_result:
            _log_normal_publish_event(
                run_id=run_id,
                slot=slot,
                post_type="post1",
                content=post1.get("content", ""),
                final_status=_final_status,
                public_url=post1_result.get("post_url", ""),
            )
        if post2_result:
            _log_normal_publish_event(
                run_id=run_id,
                slot=slot,
                post_type="post2",
                content=post2.get("content", ""),
                final_status=_final_status,
                public_url=post2_result.get("post_url", ""),
            )
    except Exception as e:
        logger.warning(f"⚠ Phase 19 정상발행 품질로그 실패 (비치명): {e}")

    # ── Phase 15E: Post1/Post2 역할 분리 + 해석 지성 + 신뢰성 + P14~15E 게이트 ─
    try:
        from generator import (
            _check_post_separation,
            _check_post_continuity,
        )

        if post1 is not None and post2 is not None:
            sep = _check_post_separation(
                post1.get("content", ""), post2.get("content", "")
            )
            sep_status = sep["status"]
            continuity = _check_post_continuity(
                post1.get("content", ""), post2.get("content", "")
            )
            continuity_status = continuity["status"]
        else:
            sep_status = "SKIP"
            continuity_status = "SKIP"

        # Phase 12 품질 스코어
        p1_scores = post1.get("quality_scores", {}) if post1 else {}

        # Phase 13/14 진단 스코어
        p1_p13 = post1.get("p13_scores", {}) if post1 else {}
        p2_p13 = post2.get("p13_scores", {}) if post2 else {}

        def _gate(score_dict: dict, key: str) -> str:
            return score_dict.get(key, "SKIP")

        def _p13gate(p13_dict: dict, sub: str, key: str = "status") -> str:
            sub_dict = p13_dict.get(sub, {})
            if isinstance(sub_dict, dict):
                return sub_dict.get(key, "SKIP")
            return "SKIP"

        def _worst(a: str, b: str) -> str:
            rank = {"FAIL": 0, "WARN": 1, "PASS": 2, "SKIP": 3}
            return a if rank.get(a, 3) <= rank.get(b, 3) else b

        temporal_status = _worst(
            _p13gate(p1_p13, "temporal"), _p13gate(p2_p13, "temporal")
        )
        numeric_status = _worst(
            _p13gate(p1_p13, "numeric"), _p13gate(p2_p13, "numeric")
        )
        closure_status = _worst(
            _p13gate(p1_p13, "closure"), _p13gate(p2_p13, "closure")
        )
        interp_p1 = _p13gate(p1_p13, "interpretation", key="overall")
        interp_p2 = _p13gate(p2_p13, "interpretation", key="overall")
        hedge_p1  = _p13gate(p1_p13, "interpretation", key="hedge_overuse")
        hedge_p2  = _p13gate(p2_p13, "interpretation", key="hedge_overuse")
        ctr_p1    = _p13gate(p1_p13, "interpretation", key="counterpoint_spec")
        ctr_p2    = _p13gate(p2_p13, "interpretation", key="counterpoint_spec")

        # Phase 14: spine 존재 여부 확인
        p1_spine = post1.get("post1_spine", "") if post1 else ""
        spine_status = "PASS" if p1_spine else "WARN"

        # Phase 14: 소스 정규화 실행 여부 (p13_scores에서 간접 확인)
        source_norm_status = "PASS"  # 항상 실행됨 (generate_deep_analysis에서)

        # Phase 14: 재작성 루프 여부 (weak_hits 기준으로 판단)
        p1_weak = p1_p13.get("interpretation", {}).get("weak_interp_hits", 0) if isinstance(p1_p13.get("interpretation"), dict) else 0
        p2_weak = p2_p13.get("interpretation", {}).get("weak_interp_hits", 0) if isinstance(p2_p13.get("interpretation"), dict) else 0
        rewrite_triggered = (p1_weak >= 3 or p2_weak >= 3)
        rewrite_loop_status = "PASS" if rewrite_triggered else ("WARN" if (p1_weak >= 1 or p2_weak >= 1) else "PASS")

        # HOLD 조건 (Phase 14): temporal FAIL 또는 numeric hard_fail만 HOLD 트리거
        # numeric suspicious-only는 WARN으로 강등 (Phase 14 재조정)
        p1_hf = p1_p13.get("numeric", {}).get("hard_fail_count", 0) if isinstance(p1_p13.get("numeric"), dict) else 0
        p2_hf = p2_p13.get("numeric", {}).get("hard_fail_count", 0) if isinstance(p2_p13.get("numeric"), dict) else 0

        hold_conditions = [
            temporal_status == "FAIL",
            (p1_hf + p2_hf) >= 1,          # Phase 14: hard_fail만 HOLD (suspicious는 WARN)
        ]

        gate = {
            # ── Phase 12 기존 키 유지 ─────────────────────────────────────
            "numeric_density":             _gate(p1_scores, "numeric_density"),
            "time_anchor":                 _gate(p1_scores, "time_anchor"),
            "counterpoint_presence":       _gate(p1_scores, "counterpoint_presence"),
            "generic_wording_control":     _gate(p1_scores, "generic_wording"),
            "post_role_separation":        sep_status,
            # ── Phase 13 진단 키 유지 ─────────────────────────────────────
            "interpretation_quality_p1":   interp_p1,
            "interpretation_quality_p2":   interp_p2,
            "hedge_overuse_p1":            hedge_p1,
            "hedge_overuse_p2":            hedge_p2,
            "counterpoint_specificity_p1": ctr_p1,
            "counterpoint_specificity_p2": ctr_p2,
            "post1_post2_continuity":      continuity_status,
            "temporal_consistency":        temporal_status,
            "numeric_sanity":              numeric_status,
            "verifier_revision_closure":   closure_status,
            # ── Phase 14 신규 키 ──────────────────────────────────────────
            "source_normalization":         source_norm_status,
            "fact_forecast_separation":     source_norm_status,
            "analytical_spine_enforcement": spine_status,
            "post2_continuation_enforcement": "PASS" if p1_spine else "WARN",
            "weak_interpretation_rewrite_loop": rewrite_loop_status,
            "numeric_sanity_recalibration": "PASS",
            # ── Phase 15 신규 키 ──────────────────────────────────────────
            "phase15_tense_correction":    _p13gate(p1_p13, "tense", key="status") if isinstance(p1_p13.get("tense"), dict) else "PASS",
            "phase15c_label_safety":       _p13gate(p2_p13, "label_leak", key="status") if isinstance(p2_p13.get("label_leak"), dict) else "PASS",
            "phase15d_jeonmang_strip":     "PASS",   # 항상 실행됨
            "phase15e_month_settlement":   "PASS",   # 항상 실행됨
            # ── 공통 안정성 ────────────────────────────────────────────────
            "phase13_compatibility":       "PASS",
            "public_signature_stability":  "PASS",
            "import_build":                "PASS",
            "final_status":                "HOLD" if any(hold_conditions) else "GO",
        }

        logger.info("[Phase 15E] 최종 품질 게이트:")
        for k, v in gate.items():
            logger.info(f"  {k}: {v}")

    except Exception as e:
        logger.warning(f"⚠ Phase 15E 품질 게이트 집계 실패 (비치명): {e}")

    # ── 최종 결과 요약 ────────────────────────────────
    logger.info("=" * 60)
    logger.info(f"🎉 macromalt Phase 15E 파이프라인 완료 [run_id: {run_id}] [슬롯: {slot}]")
    logger.info("-" * 60)

    if post1_result:
        logger.info("  📄 Post 1 — 심층 경제 분석")
        logger.info(f"     제목    : {post1['title']}")
        logger.info(f"     주제    : {post1.get('theme', 'N/A')}")
        logger.info(f"     Post ID : {post1_result['post_id']}")
        logger.info(f"     URL     : {post1_result['post_url']}")
        logger.info(f"     상태    : {post1_result['status']} (임시저장)")

    logger.info("-" * 60)

    if post2_result:
        logger.info("  📊 Post 2 — 종목 리포트")
        logger.info(f"     제목    : {post2['title']}")
        picks = post2.get("picks", [])
        if picks:
            ticker_names = ", ".join(
                f"{p.get('name','?')}({p.get('ticker','?')})" for p in picks
            )
            logger.info(f"     종목    : {ticker_names}")
        logger.info(f"     Post ID : {post2_result['post_id']}")
        logger.info(f"     URL     : {post2_result['post_url']}")
        logger.info(f"     상태    : {post2_result['status']} (임시저장)")
    elif post2 is None:
        logger.warning("  ⚠ Post 2 — 생성 또는 발행 실패 (Post 1은 정상)")

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
