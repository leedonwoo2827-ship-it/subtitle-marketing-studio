"""16 channel-centric studios.

Section grouping (UI):
- 카드뉴스·기타 (6): Threads x2, Instagram x2, KakaoTalk, 보도자료
- 블로그 (10): Naver x3, Tistory, Medium, Brunch, Velog, Personal, Column, WordPress EN
"""
from studio._base import StudioBase

CARD = "카드뉴스·기타"
BLOG = "블로그"


# ─────────────────── 카드뉴스 + 보도자료 (1~6) ───────────────────

class ThreadsQuickStudio(StudioBase):
    key = "threads_quick"
    order = 1
    title = "01. Threads 간결형 카드뉴스"
    section = CARD
    channel_section = "Threads 간결형 카드뉴스"
    description = "PNG 3장 (1080×1350) · 빠른 소비, 짧은 카피"
    html_renderer = "cards_threads_quick"
    png_renderer = "cards_threads_quick"


class ThreadsInsightStudio(StudioBase):
    key = "threads_insight"
    order = 2
    title = "02. Threads 인사이트형 카드뉴스"
    section = CARD
    channel_section = "Threads 인사이트형 카드뉴스"
    description = "PNG 5장 (1080×1350) · 한 주제 deep-dive"
    html_renderer = "cards_threads_insight"
    png_renderer = "cards_threads_insight"


class InstagramInfoStudio(StudioBase):
    key = "instagram_info"
    order = 3
    title = "03. Instagram 정보형 카드뉴스"
    section = CARD
    channel_section = "Instagram 정보형 카드뉴스"
    description = "PNG 5장 (1080×1350) · 캡션·해시태그 5장 카드 내 내장"
    html_renderer = "cards_instagram_info"
    png_renderer = "cards_instagram_info"


class InstagramStoryStudio(StudioBase):
    key = "instagram_story"
    order = 4
    title = "04. Instagram 스토리텔링형 카드뉴스"
    section = CARD
    channel_section = "Instagram 스토리텔링형 카드뉴스"
    description = "PNG 7장 (1080×1350) · 서사·에피소드, 7장 카드 내 캡션"
    html_renderer = "cards_instagram_story"
    png_renderer = "cards_instagram_story"


class KakaoCardsStudio(StudioBase):
    key = "kakao_cards"
    order = 5
    title = "05. 카카오톡 카드뉴스"
    section = CARD
    channel_section = "카카오톡 카드뉴스 (친구톡 / 채널톡)"
    description = "PNG 1~3장 (800×800) · 친구톡·채널톡 시안"
    html_renderer = "cards_kakao"
    png_renderer = "cards_kakao"


class PressReleaseStudio(StudioBase):
    key = "press_release"
    order = 6
    title = "06. 보도자료"
    section = CARD
    channel_section = "보도자료"
    description = "DOCX · 5단 구성, 기자 메일 첨부용"
    html_renderer = "generic"
    docx_renderer = "press_release"


# ─────────────────── 블로그 10종 (7~16) ───────────────────

class BlogNaverInfoStudio(StudioBase):
    key = "blog_naver_info"
    order = 7
    title = "07. 블로그 네이버 정보형"
    section = BLOG
    channel_section = "블로그 네이버 정보형"
    description = "2,500자 · 결론 먼저, H2/H3 정보 칼럼"
    max_tokens = 8192


class BlogNaverDailyStudio(StudioBase):
    key = "blog_naver_daily"
    order = 8
    title = "08. 블로그 네이버 일상형"
    section = BLOG
    channel_section = "블로그 네이버 일상형"
    description = "1,500자 · 1인칭 일기·체험 톤"
    max_tokens = 6144


class BlogNaverReviewStudio(StudioBase):
    key = "blog_naver_review"
    order = 9
    title = "09. 블로그 네이버 리뷰형"
    section = BLOG
    channel_section = "블로그 네이버 리뷰형"
    description = "2,000자 · 별점·장단점·총평·추천 대상"
    max_tokens = 7168


class BlogTistorySEOStudio(StudioBase):
    key = "blog_tistory_seo"
    order = 10
    title = "10. 블로그 티스토리 SEO형"
    section = BLOG
    channel_section = "블로그 티스토리 SEO형"
    description = "3,500자 · 키워드 밀도·메타·FAQ 섹션"
    max_tokens = 12288


class BlogMediumEssayStudio(StudioBase):
    key = "blog_medium_essay"
    order = 11
    title = "11. 블로그 Medium 에세이형"
    section = BLOG
    channel_section = "블로그 Medium 에세이형"
    description = "2,500자 · 인사이트·통찰, 격식 1인칭"
    max_tokens = 8192


class BlogBrunchEmotionalStudio(StudioBase):
    key = "blog_brunch_emotional"
    order = 12
    title = "12. 블로그 브런치 감성형"
    section = BLOG
    channel_section = "블로그 브런치 감성형"
    description = "2,500자 · 문학적·사색·감성"
    max_tokens = 8192


class BlogPersonalRetroStudio(StudioBase):
    key = "blog_personal_retro"
    order = 13
    title = "13. 블로그 개인 기술블로그 회고형"
    section = BLOG
    channel_section = "블로그 개인 기술블로그 회고형"
    description = "1,500자 · 회고·다이어리, 짧고 정직"
    max_tokens = 6144


class BlogColumnOpStudio(StudioBase):
    key = "blog_column_op"
    order = 14
    title = "14. 블로그 칼럼 시사형"
    section = BLOG
    channel_section = "블로그 칼럼 시사형"
    description = "2,500자 · 시사·날카로움, 논거·반증"
    max_tokens = 8192


class BlogWordpressENStudio(StudioBase):
    key = "blog_wordpress_en"
    order = 15
    title = "15. 블로그 워드프레스 영문 SEO"
    section = BLOG
    channel_section = "블로그 워드프레스 영문 SEO"
    description = "~3,000 words (English) · WordPress SEO"
    max_tokens = 10240


REGISTRY = [
    ThreadsQuickStudio(),
    ThreadsInsightStudio(),
    InstagramInfoStudio(),
    InstagramStoryStudio(),
    KakaoCardsStudio(),
    PressReleaseStudio(),
    BlogNaverInfoStudio(),
    BlogNaverDailyStudio(),
    BlogNaverReviewStudio(),
    BlogTistorySEOStudio(),
    BlogMediumEssayStudio(),
    BlogBrunchEmotionalStudio(),
    BlogPersonalRetroStudio(),
    BlogColumnOpStudio(),
    BlogWordpressENStudio(),
]
