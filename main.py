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


def step_publish(post: dict, category_ids: list, step_label: str,
                 featured_media_id: int = None, scheduled_at: str = "") -> dict:
    """Step 3A/3B: WordPress Draft 업로드"""
    from publisher import publish_draft

    logger.info(f"▶ [{step_label}] WordPress 업로드 시작: '{post['title']}'")
    result = publish_draft(
        title=post["title"],
        content=post["content"],
        category_ids=category_ids,
        featured_media_id=featured_media_id,
        seo_title=post.get("seo_title", ""),  # [Phase 21] SEO slug 소스
        scheduled_at=scheduled_at,
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

    import cost_tracker as _ct
    _ct.record_run_start()

    logger.info("=" * 60)
    logger.info(f"macromalt Phase 22 다중 테마 파이프라인 시작 [run_id: {run_id}]")
    logger.info(f"[Phase 22] 슬롯: {slot} | run_id: {run_id}")
    logger.info("=" * 60)

    # ── 발행 시간 스케줄 (실행 시점 기준 상대 오프셋, 단위: 분) ──
    # 절대 시각 방식은 크론 실행 시간과 역전될 수 있어 상대 방식으로 변경.
    # Post1 5개: +10, +40, +70, +100, +130분 후
    # Post2 2개: +160, +190분 후
    _POST1_OFFSETS = [10, 40, 70, 100, 130]
    _POST2_OFFSETS = [160, 190]

    def _make_scheduled_at(offset_min: int) -> str:
        """실행 시점(now) 기준 offset_min분 후 ISO 8601 문자열 반환."""
        target = now + timedelta(minutes=offset_min)
        return target.strftime("%Y-%m-%dT%H:%M:%S")

    # ── 카테고리 ID ─────────────────────────────────────────────
    _WP_ANALYSIS_PARENT = 2   # Phase 22: ANALYSIS 부모 ID
    _WP_PICKS_PARENT    = 3   # Phase 22: PICKS 부모 ID

    # ── Step 1: 수집 (1회 — 모든 테마 공유) ─────────────────────
    try:
        news     = step_scrape_news()
        research = step_scrape_research()
    except RuntimeError as e:
        logger.error(f"❌ [Step 1] 수집 실패: {e}")
        sys.exit(1)

    # ── Step 0: 테마 선정 ────────────────────────────────────────
    try:
        from generator import gemini_select_themes, format_articles_for_prompt, format_research_for_prompt, _build_history_context
        _news_txt    = format_articles_for_prompt(news)
        _res_txt     = format_research_for_prompt(research)
        _history_ctx = _build_history_context(slot)   # 최근 발행 이력 → 중복 테마 방지
        themes = gemini_select_themes(
            news_text=_news_txt,
            research_text=_res_txt,
            slot=slot,
            n=5,
            history_context=_history_ctx,
        )
    except Exception as e:
        logger.warning(f"⚠ [Step 0] 테마 선정 실패 — 단일 테마 fallback: {e}")
        themes = [{"priority": 1, "theme": "", "picks_priority": 1, "reason": "fallback"}]

    logger.info(f"[Phase 22] 선정 테마 {len(themes)}개:")
    for t in themes:
        logger.info(f"   [{t.get('priority')}] {t.get('theme','')[:60]} (픽 우선순위: {t.get('picks_priority')})")

    # ── Step 2A: Post1 생성 루프 (테마별) ───────────────────────
    from generator import generate_deep_analysis
    posts1 = []
    for i, theme_info in enumerate(themes):
        theme_name = theme_info.get("theme", "")
        try:
            logger.info(f"▶ [Step 2A-{i+1}] Post1 생성: '{theme_name[:50]}'")
            post1 = generate_deep_analysis(news, research, slot=slot,
                                           forced_theme=theme_name)
            post1["_theme_info"] = theme_info  # 메타 보존
            posts1.append(post1)
            logger.info(f"✅ [Step 2A-{i+1}] Post1 완료: '{post1['title'][:50]}'")
        except Exception as e:
            logger.error(f"❌ [Step 2A-{i+1}] Post1 생성 실패 — 건너뜀: {e}")

    if not posts1:
        logger.error("❌ 모든 Post1 생성 실패 — 파이프라인 중단")
        sys.exit(1)

    # ── Step 2B: Post2 생성 (picks_priority 상위 2개) ───────────
    from generator import generate_stock_picks_report
    # picks_priority 낮은 순으로 정렬 (1=최우선)
    picks_candidates = sorted(
        [t for t in themes if t.get("picks_priority", 99) <= 2],
        key=lambda x: x.get("picks_priority", 99)
    )[:2]

    posts2 = []
    for i, theme_info in enumerate(picks_candidates):
        theme_name = theme_info.get("theme", "")
        # 해당 테마의 post1 찾기
        matching_post1 = next(
            (p for p in posts1 if p.get("_theme_info", {}).get("theme") == theme_name),
            posts1[0]  # fallback: 첫 번째 post1
        )
        try:
            logger.info(f"▶ [Step 2B-{i+1}] Post2 생성: '{theme_name[:50]}'")
            post2 = generate_stock_picks_report(
                theme=matching_post1.get("theme", theme_name),
                key_data=matching_post1.get("key_data", []),
                post1_content=matching_post1.get("content", ""),
                news=news,
                research=research,
                materials=matching_post1.get("materials"),
                slot=slot,
            )
            post2["_theme_info"] = theme_info
            posts2.append(post2)
            logger.info(f"✅ [Step 2B-{i+1}] Post2 완료: '{post2['title'][:50]}'")
        except Exception as e:
            logger.error(f"❌ [Step 2B-{i+1}] Post2 생성 실패 — 건너뜀: {e}")

    # ── Step 2C: 이미지 준비 ─────────────────────────────────────
    from images import attach_post1_image, attach_post2_image, inject_chart_into_content
    from publisher import _strip_leading_h1
    import re as _re

    for post1 in posts1:
        try:
            media_id, img_url, attribution = attach_post1_image(post1.get("theme", ""))
            if img_url:
                _img_figure = (
                    f'\n<figure class="mm-featured-figure" style="margin:1.5em 0;text-align:center;">'
                    f'<img src="{img_url}" alt="{post1.get("theme","")}" '
                    f'style="max-width:100%;height:auto;" /></figure>\n'
                )
                _h1_m = _re.search(r"</h1>", post1.get("content", ""))
                if _h1_m:
                    _pos = _h1_m.end()
                    post1["content"] = post1["content"][:_pos] + _img_figure + post1["content"][_pos:]
                else:
                    post1["content"] = _img_figure + post1.get("content", "")
            if attribution:
                post1["content"] += (
                    f'\n<p class="mm-image-credit" style="font-size:11px;color:#aaa;text-align:right;margin-top:2em;">'
                    f'[출처: {attribution}]</p>'
                )
        except Exception as e:
            logger.warning(f"⚠ Post1 이미지 준비 실패 (비치명): {e}")

    for post2 in posts2:
        try:
            _, img_html, chart_src = attach_post2_image(post2.get("picks", []))
            if img_html:
                _url_m = _re.search(r'src="([^"]+)"', img_html)
                _alt_m = _re.search(r'alt="([^"]+)"', img_html)
                if _url_m:
                    post2["content"] = _strip_leading_h1(post2["content"])
                    post2["content"] = inject_chart_into_content(
                        post2["content"], _url_m.group(1),
                        _alt_m.group(1) if _alt_m else "", source=chart_src,
                    )
        except Exception as e:
            logger.warning(f"⚠ Post2 이미지 준비 실패 (비치명): {e}")

    # ── Step 3: 발행 ─────────────────────────────────────────────
    from publisher import get_or_create_wp_category

    post1_results = []
    for i, post1 in enumerate(posts1):
        try:
            theme_name = post1.get("_theme_info", {}).get("theme") or post1.get("theme", "")
            cat_id = get_or_create_wp_category(theme_name, _WP_ANALYSIS_PARENT)
            sched  = _make_scheduled_at(_POST1_OFFSETS[i]) if i < len(_POST1_OFFSETS) else ""
            result = step_publish(
                post1, [_WP_ANALYSIS_PARENT, cat_id], f"Step 3A-{i+1}",
                scheduled_at=sched,
            )
            post1_results.append(result)
        except Exception as e:
            logger.error(f"❌ [Step 3A-{i+1}] Post1 발행 실패: {e}")

    if not post1_results:
        logger.error("❌ Post1 발행 전체 실패")
        sys.exit(1)

    for i, post2 in enumerate(posts2):
        try:
            theme_name = post2.get("_theme_info", {}).get("theme") or post2.get("theme", "")
            cat_id = get_or_create_wp_category(theme_name, _WP_PICKS_PARENT)
            sched  = _make_scheduled_at(_POST2_OFFSETS[i]) if i < len(_POST2_OFFSETS) else ""
            step_publish(
                post2, [_WP_PICKS_PARENT, cat_id], f"Step 3B-{i+1}",
                scheduled_at=sched,
            )
        except Exception as e:
            logger.error(f"⚠ [Step 3B-{i+1}] Post2 발행 실패: {e}")

    # ── Phase 19: 정상 발행 품질 로그 (다중 포스트) ──────────────
    try:
        from generator import _log_normal_publish_event
        for i, (post1, result) in enumerate(zip(posts1, post1_results)):
            _log_normal_publish_event(
                run_id=run_id, slot=slot, post_type=f"post1_{i+1}",
                content=post1.get("content", ""), final_status="GO",
                public_url=result.get("post_url", ""),
            )
        for i, post2 in enumerate(posts2):
            _log_normal_publish_event(
                run_id=run_id, slot=slot, post_type=f"post2_{i+1}",
                content=post2.get("content", ""), final_status="GO",
                public_url="",
            )
    except Exception as e:
        logger.warning(f"⚠ Phase 19 품질로그 실패 (비치명): {e}")

    # ── Phase 10: 발행 이력 저장 ─────────────────────────────────
    if post1_results:
        try:
            from generator import save_publish_history
            # 대표 post1/post2 (첫 번째)로 이력 저장
            save_publish_history(
                slot=slot,
                post1=posts1[0],
                post2=posts2[0] if posts2 else None,
            )
        except Exception as e:
            logger.warning(f"⚠ 발행 이력 저장 실패 (비치명): {e}")

    # ── 비용 요약 ─────────────────────────────────────────────────
    try:
        run_summary = _ct.get_run_summary()
        logger.info(
            f"[비용] 런 합계 | GPT: ${run_summary.get('gpt',{}).get('cost_usd',0):.4f} "
            f"(₩{run_summary.get('gpt',{}).get('cost_krw',0):,}) | "
            f"Gemini: ₩{run_summary.get('gemini',{}).get('cost_krw',0):,} | "
            f"총: ₩{run_summary.get('total_krw',0):,}"
        )
    except Exception:
        pass

    logger.info("=" * 60)
    logger.info(f"✅ macromalt Phase 22 파이프라인 완료 [run_id: {run_id}]")
    logger.info(f"   Post1: {len(post1_results)}개 발행 | Post2: {len(posts2)}개 발행")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
