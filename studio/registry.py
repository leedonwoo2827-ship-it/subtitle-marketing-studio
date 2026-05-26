"""All 17 studios registered here. Order = display order in UI."""
from studio._base import StudioBase

CORE = "1부 · 코어 콘텐츠"
SEO = "2부 · SEO·유입"
SELL = "3부 · 다이렉트 셀링"
BACK = "4부 · 마케팅 전략·백오피스"


class BlogEditorStudio(StudioBase):
    key = "blog_editor"
    order = 1
    title = "01. 정보성 블로그 에디터"
    section = CORE
    channel_section = "블로그 (네이버 / 티스토리 / Medium)"
    description = "구어체 자막을 서론-본론-결론·H2/H3 구조의 2,000~4,000자 칼럼으로 재가공"


class NewsletterStudio(StudioBase):
    key = "newsletter"
    order = 2
    title = "02. 스토리텔링 뉴스레터 에디터"
    section = CORE
    channel_section = "뉴스레터 (스티비 / 메일리 / Substack)"
    description = "핵심 에피소드를 추출해 친근한 이메일 뉴스레터 본문(Title + Body)"


class LinkedInStudio(StudioBase):
    key = "linkedin"
    order = 3
    title = "03. 비즈니스 인사이트 LinkedIn"
    section = CORE
    channel_section = "LinkedIn"
    description = "Lesson Learned 1개를 격식 있는 네트워킹 글 800~1,500자로 추출"


class EbookChapterStudio(StudioBase):
    key = "ebook_chapter"
    order = 4
    title = "04. 미니 전자책 단원 집필기"
    section = CORE
    channel_section = "블로그 (네이버 / 티스토리 / Medium)"
    description = "책 한 단원처럼 문맥을 다듬어 체계적으로 서술한 전자책 텍스트"


class SEOMetaStudio(StudioBase):
    key = "seo_meta"
    order = 5
    title = "05. SEO 메타 타이틀·디스크립션"
    section = SEO
    channel_section = "블로그 (네이버 / 티스토리 / Medium)"
    description = "검색 엔진 노출용 제목(50자) + 2줄 설명(150자) 후보 5세트"


class CommunityPostStudio(StudioBase):
    key = "community_post"
    order = 6
    title = "06. 정보 공유형 커뮤니티 게시글"
    section = SEO
    channel_section = "커뮤니티 (네이버 카페 / 밴드 / 디시 / 클리앙)"
    description = "광고 티 없는 정보 공유형 게시글로 재구성"


class FAQStudio(StudioBase):
    key = "faq"
    order = 7
    title = "07. FAQ 및 Q&A 생성기"
    section = SEO
    channel_section = "블로그 (네이버 / 티스토리 / Medium)"
    description = "소비자 예상 질문 5개 + 명쾌한 답변 세트"


class InstagramCardsStudio(StudioBase):
    key = "instagram_cards"
    order = 8
    title = "08. 인스타그램 카드뉴스 텍스트"
    section = SEO
    channel_section = "인스타그램 카드뉴스 (텍스트 only)"
    description = "1~5장 슬라이드별 핵심 카피 + 캡션 + 해시태그"


class PASCopyStudio(StudioBase):
    key = "pas_copy"
    order = 9
    title = "09. PAS 세일즈 카피"
    section = SELL
    channel_section = "메타·구글 광고 (피드·검색)"
    description = "Problem-Agitate-Solution 구조의 강력한 판매 문구"


class AdCopyStudio(StudioBase):
    key = "ad_copy"
    order = 10
    title = "10. 메타·구글 타겟 광고 카피"
    section = SELL
    channel_section = "메타·구글 광고 (피드·검색)"
    description = "후킹 헤드라인 3종 + 본문 2종 (피드용 짧은 텍스트)"


class PushMessageStudio(StudioBase):
    key = "push_message"
    order = 11
    title = "11. 푸시·알림톡 메시지"
    section = SELL
    channel_section = "푸시 알림 / 카카오 알림톡"
    description = "30자 이내 호기심 유발 카피 5종 + 오픈율 가설"


class LandingHeadlineStudio(StudioBase):
    key = "landing_headline"
    order = 12
    title = "12. 랜딩페이지 헤드라인"
    section = SELL
    channel_section = "메타·구글 광고 (피드·검색)"
    description = "가치 제안을 한 줄로 압축한 메인 카피 + 서브카피 5세트"


class ReviewsStudio(StudioBase):
    key = "reviews"
    order = 13
    title = "13. 가상 고객 리뷰·후기"
    section = SELL
    channel_section = "커뮤니티 (네이버 카페 / 밴드 / 디시 / 클리앙)"
    description = "타겟 페르소나별 자연스러운 텍스트 리뷰 5종"


class PersonaStudio(StudioBase):
    key = "persona"
    order = 14
    title = "14. 마케팅 타겟 페르소나 정의"
    section = BACK
    channel_section = None
    description = "자막의 주제·어조 분석으로 도출한 핵심 소비자 페르소나 3종 (나이·직업·고민)"


class TagsKeywordsStudio(StudioBase):
    key = "tags_keywords"
    order = 15
    title = "15. 태그·연관 키워드 발굴"
    section = BACK
    channel_section = None
    description = "메인 키워드 5개 + 해시태그 20개 + 롱테일 키워드 10개"


class PromotionStudio(StudioBase):
    key = "promotion"
    order = 16
    title = "16. 연관 프로모션 아이디어"
    section = BACK
    channel_section = "커뮤니티 (네이버 카페 / 밴드 / 디시 / 클리앙)"
    description = "댓글 참여·퀴즈·이벤트 등 텍스트 기반 프로모션 기획 3종"


class PressReleaseStudio(StudioBase):
    key = "press_release"
    order = 17
    title = "17. 보도자료 텍스트"
    section = BACK
    channel_section = "보도자료"
    description = "5단 구성(헤드라인·부제·리드·본문·회사소개)의 정형 보도자료"


REGISTRY = [
    BlogEditorStudio(),
    NewsletterStudio(),
    LinkedInStudio(),
    EbookChapterStudio(),
    SEOMetaStudio(),
    CommunityPostStudio(),
    FAQStudio(),
    InstagramCardsStudio(),
    PASCopyStudio(),
    AdCopyStudio(),
    PushMessageStudio(),
    LandingHeadlineStudio(),
    ReviewsStudio(),
    PersonaStudio(),
    TagsKeywordsStudio(),
    PromotionStudio(),
    PressReleaseStudio(),
]
