"""
generator.py 핵심 유틸 함수 단위 테스트 (HSD-361)

대상 함수 (외부 API 의존 없는 순수 함수):
  - _make_theme_fingerprint
  - _make_axes_fingerprint
  - _make_ticker_buckets
  - _parse_json_response
  - _strip_code_fences
  - _fix_double_typing
  - _strip_all_jeonmang_haeseok_tags
  - parse_picks_from_content
  - extract_title
"""

import sys
import types
import unittest
from unittest.mock import MagicMock


def _mock_heavy_modules() -> None:
    """generator.py 상단의 무거운 외부 의존성을 sys.modules에 mock으로 등록."""
    mocks = [
        "openai",
        "google",
        "google.genai",
        "google.genai.types",
        "yfinance",
        "markdown",
        "requests",
        "bs4",
        "dotenv",
        "pdfplumber",
        "pykrx",
        "pykrx.stock",
        "matplotlib",
        "matplotlib.pyplot",
        "matplotlib.patches",
        "matplotlib.font_manager",
        "PIL",
        "PIL.Image",
    ]
    for name in mocks:
        if name not in sys.modules:
            mod = types.ModuleType(name)
            # google.genai.types 처럼 속성이 필요한 경우 MagicMock으로 처리
            sys.modules[name] = MagicMock()

    # load_dotenv 는 함수로 호출되므로 dotenv 패키지만 mock해도 되지만
    # from dotenv import load_dotenv 패턴을 처리하기 위해 명시 등록
    dotenv_mod = types.ModuleType("dotenv")
    dotenv_mod.load_dotenv = lambda *a, **kw: None  # type: ignore[attr-defined]
    sys.modules["dotenv"] = dotenv_mod


_mock_heavy_modules()

# ── 로컬 모듈도 사전 mock 처리 ───────────────────────────────────────────────
for _local in ("cost_tracker", "scraper", "macro_data", "knowledge_base",
               "editorial_config", "reference_loader", "styles.tokens", "styles"):
    if _local not in sys.modules:
        sys.modules[_local] = MagicMock()

# styles.tokens 에서 import 되는 이름들을 빈 문자열로 등록
_tokens_mock = MagicMock()
for _attr in (
    "_H1_STYLE", "_H3_STYLE", "_P_STYLE", "_HR_STYLE", "_PICKS_DIV_STYLE",
    "_STRONG_STYLE", "_CITE_STYLE", "_FOOTNOTE_SUP_STYLE", "_FOOTNOTE_SECTION_STYLE",
    "_FOOTNOTE_TITLE_STYLE", "_FOOTNOTE_ITEM_STYLE", "BQ_STYLE", "UL_STYLE",
    "OL_STYLE", "LI_STYLE", "A_STYLE", "SOURCE_BOX_STYLE", "SOURCE_H_STYLE",
    "SOURCE_CAT_STYLE", "SOURCE_UL_STYLE", "SOURCE_LI_STYLE",
    "H1_STYLE", "H3_STYLE", "P_STYLE", "HR_STYLE", "PICKS_DIV_STYLE",
):
    setattr(_tokens_mock, _attr, "")
sys.modules["styles.tokens"] = _tokens_mock

import importlib
import os
import sys as _sys

# generator 모듈 import
_gen_path = os.path.join(os.path.dirname(__file__), "..")
if _gen_path not in _sys.path:
    _sys.path.insert(0, _gen_path)

import generator as gen  # noqa: E402


class TestMakeThemeFingerprint(unittest.TestCase):
    """_make_theme_fingerprint — theme 문자열 → macro category fingerprint"""

    def test_empty_string_returns_기타(self):
        assert gen._make_theme_fingerprint("") == "기타"

    def test_none_equivalent_falsy_returns_기타(self):
        # 함수 내부에서 `if not theme_str` 처리
        assert gen._make_theme_fingerprint("   ") == "기타"  # 공백만 있는 경우

    def test_no_matching_keyword_returns_기타(self):
        assert gen._make_theme_fingerprint("날씨 맑음") == "기타"

    def test_single_category_match(self):
        result = gen._make_theme_fingerprint("미국 연준 금리 인상")
        assert result == "금리_통화", f"예상: 금리_통화, 실제: {result}"

    def test_multi_category_match_sorted(self):
        # "중동 지정학 리스크와 국제유가 급등" → 에너지_유가 + 지정학_전쟁
        result = gen._make_theme_fingerprint("중동 지정학 리스크와 국제유가 급등")
        parts = result.split("|")
        assert "에너지_유가" in parts
        assert "지정학_전쟁" in parts

    def test_case_insensitive_english_keyword(self):
        result = gen._make_theme_fingerprint("FOMC 결정 이후 시장 반응")
        assert "금리_통화" in result

    def test_semiconductor_keyword(self):
        result = gen._make_theme_fingerprint("엔비디아 HBM 반도체 공급 이슈")
        assert "반도체_기술" in result


class TestMakeAxesFingerprint(unittest.TestCase):
    """_make_axes_fingerprint — sub_axes 리스트 → axis_id 리스트"""

    def test_empty_list(self):
        assert gen._make_axes_fingerprint([]) == []

    def test_none_input(self):
        assert gen._make_axes_fingerprint(None) == []

    def test_known_keyword_match(self):
        result = gen._make_axes_fingerprint(["어젯밤 미국장 마감 분석"])
        assert result == ["미국장_마감"]

    def test_no_match_returns_기타(self):
        result = gen._make_axes_fingerprint(["날씨와 경제의 관계"])
        assert result == ["기타"]

    def test_multiple_axes(self):
        axes = ["나스닥 선물 움직임", "원달러 환율 동향", "날씨"]
        result = gen._make_axes_fingerprint(axes)
        assert result[0] == "미국장_개장"
        assert result[1] == "환율_달러"
        assert result[2] == "기타"

    def test_case_insensitive(self):
        result = gen._make_axes_fingerprint(["Overnight 금리 변동"])
        assert result == ["미국장_마감"]


class TestMakeTickerBuckets(unittest.TestCase):
    """_make_ticker_buckets — 티커 → 섹터 버킷 집합"""

    def test_empty_list(self):
        assert gen._make_ticker_buckets([]) == []

    def test_none_input(self):
        assert gen._make_ticker_buckets(None) == []

    def test_known_us_ticker(self):
        result = gen._make_ticker_buckets(["NVDA"])
        assert result == ["반도체_기술"]

    def test_known_kr_ticker(self):
        result = gen._make_ticker_buckets(["005930"])  # 삼성전자
        assert result == ["반도체_기술"]

    def test_ks_suffix_stripped(self):
        # .KS 접미사 제거 후 조회
        result = gen._make_ticker_buckets(["005930.KS"])
        assert result == ["반도체_기술"]

    def test_unknown_ticker_returns_기타(self):
        result = gen._make_ticker_buckets(["ZZZZ"])
        assert result == ["기타"]

    def test_dedup_and_sorted(self):
        # 같은 버킷에 속하는 두 티커 → 중복 제거
        result = gen._make_ticker_buckets(["NVDA", "AMD"])
        assert result == ["반도체_기술"]

    def test_multiple_buckets_sorted(self):
        result = gen._make_ticker_buckets(["NVDA", "JPM"])
        assert "반도체_기술" in result
        assert "금융" in result
        assert result == sorted(result)


class TestParseJsonResponse(unittest.TestCase):
    """_parse_json_response — LLM raw 출력에서 JSON 추출"""

    def test_empty_string_returns_none(self):
        assert gen._parse_json_response("") is None

    def test_plain_json(self):
        result = gen._parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_code_block(self):
        raw = '```json\n{"theme": "반도체"}\n```'
        result = gen._parse_json_response(raw)
        assert result == {"theme": "반도체"}

    def test_plain_code_block(self):
        raw = '```\n{"a": 1}\n```'
        result = gen._parse_json_response(raw)
        assert result == {"a": 1}

    def test_json_list(self):
        raw = '[{"ticker": "NVDA"}, {"ticker": "AMD"}]'
        result = gen._parse_json_response(raw)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_json_embedded_in_text(self):
        raw = '결과는 다음과 같습니다. {"score": 99} 끝.'
        result = gen._parse_json_response(raw)
        assert result == {"score": 99}

    def test_invalid_json_returns_none(self):
        result = gen._parse_json_response("이것은 JSON이 아닙니다.")
        assert result is None


class TestStripCodeFences(unittest.TestCase):
    """_strip_code_fences — 코드펜스 및 래퍼 제거"""

    def test_empty_string_passthrough(self):
        assert gen._strip_code_fences("") == ""

    def test_html_code_block_removed(self):
        raw = "```html\n<h1>제목</h1>\n```"
        assert gen._strip_code_fences(raw) == "<h1>제목</h1>"

    def test_plain_code_block_removed(self):
        raw = "```\n<p>본문</p>\n```"
        assert gen._strip_code_fences(raw) == "<p>본문</p>"

    def test_plain_html_unchanged(self):
        html = "<h1>제목</h1><p>내용</p>"
        assert gen._strip_code_fences(html) == html

    def test_double_quotes_wrapper_removed(self):
        raw = '"<p>내용</p>"'
        assert gen._strip_code_fences(raw) == "<p>내용</p>"

    def test_single_quotes_wrapper_removed(self):
        raw = "'<p>내용</p>'"
        assert gen._strip_code_fences(raw) == "<p>내용</p>"

    def test_prefix_description_removed(self):
        raw = "다음은 HTML 출력입니다:\n<h1>제목</h1>"
        result = gen._strip_code_fences(raw)
        assert result.startswith("<h1>")


class TestFixDoubleTyping(unittest.TestCase):
    """_fix_double_typing — 중복 타이핑 패턴 교정"""

    def test_tag_duplicate_해해석_removed(self):
        assert "[해해석]" not in gen._fix_double_typing("[해해석] 분석")

    def test_tag_duplicate_전전망_removed(self):
        assert "[전전망]" not in gen._fix_double_typing("[전전망] 전망")

    def test_spaced_tag_해_해석_removed(self):
        assert "[해 해석]" not in gen._fix_double_typing("[해 해석] 내용")

    def test_double_space_collapsed(self):
        result = gen._fix_double_typing("텍스트  이중  공백")
        assert "  " not in result

    def test_normal_text_unchanged(self):
        text = "정상적인 한국어 텍스트입니다."
        assert gen._fix_double_typing(text) == text


class TestStripJeonmangHaeseokTags(unittest.TestCase):
    """_strip_all_jeonmang_haeseok_tags — [전망]/[해석] 태그 일괄 제거"""

    def test_전망_tag_removed(self):
        result = gen._strip_all_jeonmang_haeseok_tags("[전망] 긍정적 시그널")
        assert "[전망]" not in result
        assert "긍정적 시그널" in result

    def test_해석_tag_removed(self):
        result = gen._strip_all_jeonmang_haeseok_tags("[해석] 상승 원인")
        assert "[해석]" not in result
        assert "상승 원인" in result

    def test_multiple_tags_all_removed(self):
        text = "[전망] 상승 [해석] 원인 [전망] 예상"
        result = gen._strip_all_jeonmang_haeseok_tags(text)
        assert "[전망]" not in result
        assert "[해석]" not in result

    def test_no_tags_unchanged(self):
        text = "일반 텍스트"
        assert gen._strip_all_jeonmang_haeseok_tags(text) == text


class TestParsePicksFromContent(unittest.TestCase):
    """parse_picks_from_content — <!-- PICKS: [...] --> 블록에서 티커 추출"""

    def test_valid_picks_extracted(self):
        content = '<!-- PICKS: [{"ticker": "NVDA"}, {"ticker": "AMD"}] -->'
        result = gen.parse_picks_from_content(content)
        assert len(result) == 2
        assert result[0]["ticker"] == "NVDA"

    def test_no_picks_block_returns_empty(self):
        content = "<h1>제목</h1><p>내용</p>"
        assert gen.parse_picks_from_content(content) == []

    def test_malformed_json_returns_empty(self):
        content = "<!-- PICKS: [{broken json}] -->"
        assert gen.parse_picks_from_content(content) == []

    def test_empty_array_returns_empty(self):
        content = "<!-- PICKS: [] -->"
        assert gen.parse_picks_from_content(content) == []

    def test_spaces_in_block_handled(self):
        content = "<!--  PICKS:  [{"  + '"ticker": "005930"}]  -->'
        result = gen.parse_picks_from_content(content)
        assert len(result) == 1
        assert result[0]["ticker"] == "005930"


class TestExtractTitle(unittest.TestCase):
    """extract_title — 마크다운 H1 제목 추출"""

    def test_h1_title_extracted(self):
        md = "# 오늘의 시장 브리핑\n\n## 섹션1\n내용"
        result = gen.extract_title(md)
        assert result == "오늘의 시장 브리핑"

    def test_no_h1_returns_default(self):
        md = "## 부제목\n\n내용"
        result = gen.extract_title(md)
        assert result.startswith("[오늘의 캐시픽]")

    def test_h1_with_extra_hashes(self):
        md = "## 부제목\n# 진짜 제목\n내용"
        result = gen.extract_title(md)
        assert result == "진짜 제목"

    def test_empty_content_returns_default(self):
        result = gen.extract_title("")
        assert result.startswith("[오늘의 캐시픽]")


if __name__ == "__main__":
    unittest.main()
