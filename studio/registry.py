"""15 channel-centric studios.

Section grouping (UI):
- 📝 텍스트 (▶ 일괄 실행 대상): 블로그 9 + 보도자료 1 = 10 (저비용 텍스트)
- 🖼 카드뉴스 (개별 실행 · 이미지 비용): Threads x2, Instagram x2, KakaoTalk = 5
"""
from studio._base import StudioBase

CARD = "🖼 카드뉴스 (Jinja2 + Playwright)"
BLOG = "📝 블로그·보도자료 (텍스트)"


# ─────────────────── 블로그 9종 (1~9) ───────────────────

class BlogNaverInfoStudio(StudioBase):
    key = "blog_naver_info"
    order = 1
    title = "01. 블로그 네이버 정보형"
    section = BLOG
    channel_section = "블로그 네이버 정보형"
    description = "2,500자 · 결론 먼저, H2/H3 정보 칼럼"
    max_tokens = 8192


class BlogNaverDailyStudio(StudioBase):
    key = "blog_naver_daily"
    order = 2
    title = "02. 블로그 네이버 일상형"
    section = BLOG
    channel_section = "블로그 네이버 일상형"
    description = "1,500자 · 1인칭 일기·체험 톤"
    max_tokens = 6144


class BlogNaverReviewStudio(StudioBase):
    key = "blog_naver_review"
    order = 3
    title = "03. 블로그 네이버 리뷰형"
    section = BLOG
    channel_section = "블로그 네이버 리뷰형"
    description = "2,000자 · 별점·장단점·총평·추천 대상"
    max_tokens = 7168


class BlogTistorySEOStudio(StudioBase):
    key = "blog_tistory_seo"
    order = 4
    title = "04. 블로그 티스토리 SEO형"
    section = BLOG
    channel_section = "블로그 티스토리 SEO형"
    description = "3,500자 · 키워드 밀도·메타·FAQ 섹션"
    max_tokens = 12288


class BlogMediumEssayStudio(StudioBase):
    key = "blog_medium_essay"
    order = 5
    title = "05. 블로그 Medium 에세이형"
    section = BLOG
    channel_section = "블로그 Medium 에세이형"
    description = "2,500자 · 인사이트·통찰, 격식 1인칭"
    max_tokens = 8192


class BlogBrunchEmotionalStudio(StudioBase):
    key = "blog_brunch_emotional"
    order = 6
    title = "06. 블로그 브런치 감성형"
    section = BLOG
    channel_section = "블로그 브런치 감성형"
    description = "2,500자 · 문학적·사색·감성"
    max_tokens = 8192


class BlogPersonalRetroStudio(StudioBase):
    key = "blog_personal_retro"
    order = 7
    title = "07. 블로그 개인 기술블로그 회고형"
    section = BLOG
    channel_section = "블로그 개인 기술블로그 회고형"
    description = "1,500자 · 회고·다이어리, 짧고 정직"
    max_tokens = 6144


class BlogColumnOpStudio(StudioBase):
    key = "blog_column_op"
    order = 8
    title = "08. 블로그 칼럼 시사형"
    section = BLOG
    channel_section = "블로그 칼럼 시사형"
    description = "2,500자 · 시사·날카로움, 논거·반증"
    max_tokens = 8192


class BlogWordpressENStudio(StudioBase):
    key = "blog_wordpress_en"
    order = 9
    title = "09. 블로그 워드프레스 영문 SEO"
    section = BLOG
    channel_section = "블로그 워드프레스 영문 SEO"
    description = "~3,000 words (English) · WordPress SEO"
    max_tokens = 10240


# ─────────────────── 보도자료 (10) ───────────────────

class PressReleaseStudio(StudioBase):
    key = "press_release"
    order = 10
    title = "10. 보도자료"
    section = BLOG  # text-only, included in bulk run
    channel_section = "보도자료"
    description = "DOCX · 5단 구성, 기자 메일 첨부용"
    html_renderer = "generic"
    docx_renderer = "press_release"


# ─────────────────── 카드뉴스 5종 (11~15) — 개별 실행 ───────────────────

class ThreadsQuickStudio(StudioBase):
    key = "threads_quick"
    order = 11
    title = "11. Threads 간결형 카드뉴스"
    section = CARD
    channel_section = "Threads 간결형 카드뉴스"
    description = "PNG 3장 (1080×1350) · Jinja2 템플릿 + Playwright"
    html_renderer = "cards_threads_quick"
    png_renderer = "cards_threads_quick"
    max_tokens = 10240  # 3 cards × 2~3 blocks × 2~3 sentences + tagline


class ThreadsInsightStudio(StudioBase):
    key = "threads_insight"
    order = 12
    title = "12. Threads 인사이트형 카드뉴스"
    section = CARD
    channel_section = "Threads 인사이트형 카드뉴스"
    description = "PNG 5장 (1080×1350) · 한 주제 deep-dive"
    html_renderer = "cards_threads_insight"
    png_renderer = "cards_threads_insight"
    max_tokens = 14336  # 5 cards × 2~3 blocks (+ stat + tagline) — JSON overhead


class InstagramInfoStudio(StudioBase):
    key = "instagram_info"
    order = 13
    title = "13. Instagram 정보형 카드뉴스"
    section = CARD
    channel_section = "Instagram 정보형 카드뉴스"
    description = "PNG 5장 (1080×1350) · 캡션 5장 카드 내 내장"
    html_renderer = "cards_instagram_info"
    png_renderer = "cards_instagram_info"
    max_tokens = 14336  # 5 cards × 2~3 blocks + tags + caption + hashtags


class InstagramStoryStudio(StudioBase):
    key = "instagram_story"
    order = 14
    title = "14. Instagram 스토리텔링형 카드뉴스"
    section = CARD
    channel_section = "Instagram 스토리텔링형 카드뉴스"
    description = "PNG 7장 (1080×1350) · 서사·에피소드"
    html_renderer = "cards_instagram_story"
    png_renderer = "cards_instagram_story"
    max_tokens = 16384  # 7 cards × 2 blocks + caption — most output of all card studios


class KakaoCardsStudio(StudioBase):
    key = "kakao_cards"
    order = 15
    title = "15. 카카오톡 카드뉴스"
    section = CARD
    channel_section = "카카오톡 카드뉴스 (친구톡 / 채널톡)"
    description = "PNG 1~3장 (800×800) · 노란 외곽 + 흰 내부"
    html_renderer = "cards_kakao"
    png_renderer = "cards_kakao"
    max_tokens = 8192  # 1~3 cards, short — default budget plenty


REGISTRY = [
    BlogNaverInfoStudio(),
    BlogNaverDailyStudio(),
    BlogNaverReviewStudio(),
    BlogTistorySEOStudio(),
    BlogMediumEssayStudio(),
    BlogBrunchEmotionalStudio(),
    BlogPersonalRetroStudio(),
    BlogColumnOpStudio(),
    BlogWordpressENStudio(),
    PressReleaseStudio(),
    ThreadsQuickStudio(),
    ThreadsInsightStudio(),
    InstagramInfoStudio(),
    InstagramStoryStudio(),
    KakaoCardsStudio(),
]
