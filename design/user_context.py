"""
UserContext — 멀티유저 파이프라인 실행 컨텍스트 (Phase 24 M0)

파이프라인 함수들이 os.getenv() 대신 이 객체를 통해
사용자별 API 키와 WP 연결 정보를 받는다.

M2 작업 시 이 파일을 참조하여 main.py, generator.py, publisher.py를 수정한다.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UserContext:
    """
    파이프라인 실행에 필요한 사용자별 설정 컨텍스트.

    M1 Backend에서 DB 복호화 후 생성 → pipeline.execute() 에 주입.
    기존 단독 실행(.env 기반)은 from_env() 클래스메서드로 하위 호환 유지.
    """

    # 사용자 식별
    user_id: int
    user_email: str

    # ── AI API 키 ───────────────────────────────────────────
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

    # ── 데이터 수집 API 키 ──────────────────────────────────
    dart_api_key:   Optional[str] = None
    bok_api_key:    Optional[str] = None
    fred_api_key:   Optional[str] = None
    krx_api_key:    Optional[str] = None
    unsplash_access_key: Optional[str] = None

    # ── WordPress 연결 ──────────────────────────────────────
    wp_url:      Optional[str] = None
    wp_username: Optional[str] = None
    wp_password: Optional[str] = None

    # ── WordPress 카테고리 ID ───────────────────────────────
    wp_category_analysis: int = 2
    wp_category_picks:    int = 3
    wp_category_default:  int = 1

    # ── 파이프라인 실행 옵션 ────────────────────────────────
    slot: str = "morning"          # morning | evening
    max_posts: int = 3
    language: str = "ko"

    # ── 실행 추적 (M2에서 run_log_id 주입) ─────────────────
    run_log_id: Optional[int] = None

    @classmethod
    def from_env(cls) -> "UserContext":
        """
        기존 단독 실행 모드 하위 호환.
        .env 파일에서 환경변수를 읽어 UserContext 생성.
        GitHub Actions / 로컬 cron 실행 시 사용.
        """
        import os
        from dotenv import load_dotenv
        load_dotenv()

        return cls(
            user_id=0,
            user_email="operator@local",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            dart_api_key=os.getenv("DART_API_KEY"),
            bok_api_key=os.getenv("BOK_API_KEY"),
            fred_api_key=os.getenv("FRED_API_KEY"),
            krx_api_key=os.getenv("KRX_API_KEY"),
            unsplash_access_key=os.getenv("UNSPLASH_ACCESS_KEY"),
            wp_url=os.getenv("WORDPRESS_SITE_URL"),
            wp_username=os.getenv("WORDPRESS_USERNAME"),
            wp_password=os.getenv("WORDPRESS_PASSWORD"),
            wp_category_analysis=int(os.getenv("WP_CATEGORY_ANALYSIS", "2")),
            wp_category_picks=int(os.getenv("WP_CATEGORY_PICKS", "3")),
            wp_category_default=int(os.getenv("WP_CATEGORY_DEFAULT", "1")),
        )

    def validate(self) -> list[str]:
        """
        필수 항목 누락 여부 확인.
        Returns: 누락된 항목 이름 목록 (빈 리스트 = 모두 정상)
        """
        missing = []
        if not self.openai_api_key:
            missing.append("openai_api_key")
        if not self.gemini_api_key:
            missing.append("gemini_api_key")
        if not self.wp_url:
            missing.append("wp_url")
        if not self.wp_username:
            missing.append("wp_username")
        if not self.wp_password:
            missing.append("wp_password")
        return missing


# ── 사용 예시 (M2 참고용) ──────────────────────────────────────
#
# [기존 단독 실행 — 변경 없음]
# if __name__ == "__main__":
#     ctx = UserContext.from_env()
#     run_pipeline(ctx)
#
# [API 서버에서 사용자별 실행]
# async def execute_pipeline(user_id: int, db: AsyncSession):
#     # DB에서 사용자 키 복호화
#     api_keys = await get_decrypted_api_keys(user_id, db)
#     wp = await get_decrypted_wp_settings(user_id, db)
#     ctx = UserContext(
#         user_id=user_id,
#         user_email=user.email,
#         openai_api_key=api_keys["openai"],
#         gemini_api_key=api_keys["gemini"],
#         wp_url=wp.site_url,
#         wp_username=wp.username,
#         wp_password=wp.password_dec,
#         run_log_id=run_log.id,
#     )
#     missing = ctx.validate()
#     if missing:
#         raise ValueError(f"설정 누락: {missing}")
#     await run_pipeline(ctx)
