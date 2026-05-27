# 설치·운영 가이드

## Windows

1. `setup.bat` 더블클릭 — `.venv` 생성 + 의존성 설치 + Playwright Chromium 다운로드 + `.env` 자동 생성
2. `run.bat` 더블클릭 — http://localhost:8620

## macOS / Linux

```bash
./setup.sh
./run.sh
```

## 포트 변경

기본 8620. `.env`에서 변경:

```
STREAMLIT_SERVER_PORT=9000
```

`tsbookmaker`(8610)와 같이 띄울 때 충돌 방지를 위해 별도 포트를 사용합니다.

## API 설정

[Ubion LiteLLM 프록시](https://github.com/leedonwoo2827-ship-it/subtitle-marketing-studio)를 사용합니다. 모델은 `deepseek-v4-flash` 고정 (저렴 등급, 한국어 OK).

사이드바(⚙)에서:

- **API URL** — 기본값 `http://192.168.50.119:4000` (사내 프록시)
- **API 키** — 사내 LiteLLM 대시보드(`http://192.168.50.119:4000/ui/`)에서 발급받은 virtual key (`sk-...`)

`연결 테스트` → 통과하면 `저장`. 환경변수(`UBION_LITELLM_URL`/`UBION_LITELLM_KEY`)를 미리 설정해두면 자동 인식됩니다.

## 폴더 구조

```
subtitle-marketing-studio/
├── app.py                           # Streamlit 엔트리
├── core/                            # 자막 파서, LLM provider, 러너, 렌더러
│   ├── subtitle.py                  # .srt/.vtt/.ass/.txt 파서
│   ├── llm.py                       # Ubion LiteLLM provider (OpenAI SDK)
│   ├── runner.py                    # 15개 일괄/개별 실행 오케스트레이터
│   ├── html_render.py               # Markdown → HTML
│   ├── card_templates.py            # Jinja2 카드뉴스 템플릿 + JSON 파서
│   ├── png_render.py                # Playwright HTML → PNG 캡처
│   ├── docx_render.py               # python-docx (보도자료)
│   └── image_render.py              # (opt-in) Nano Banana 이미지 LLM — 기본 비활성
├── studio/                          # 15개 스튜디오 + 레지스트리
├── prompts/<key>_ko.md              # <<SYSTEM>> / <<USER>> 프롬프트
├── knowledge/channel-style-research.md  # 채널별 톤·길이 가이드
└── data/
    ├── user_settings.json           # GUI 설정 영속화
    └── projects/<프로젝트>/
        ├── source.txt
        └── <NN_studio_key>/
            ├── output.md            # 텍스트: 본문 / 카드: SNS 본문 초안
            ├── output.html          # Jinja2 + Google Fonts 렌더
            ├── output.json          # (카드 전용) LLM JSON 원본
            ├── output.docx          # (보도자료 전용) Word 문서
            └── cards/card_*.png     # (카드 전용) Playwright 캡처
```

## 15개 스튜디오 라인업

**📝 블로그·보도자료 (텍스트, 1~10)**
- 01 블로그 네이버 정보형 (2,500자)
- 02 블로그 네이버 일상형 (1,500자)
- 03 블로그 네이버 리뷰형 (2,000자)
- 04 블로그 티스토리 SEO형 (3,500자)
- 05 블로그 Medium 에세이형 (2,500자)
- 06 블로그 브런치 감성형 (2,500자)
- 07 블로그 개인 기술블로그 회고형 (1,500자)
- 08 블로그 칼럼 시사형 (2,500자)
- 09 블로그 워드프레스 영문 SEO (~3,000 words)
- 10 보도자료 (800~1,500자, **DOCX**)

**🖼 카드뉴스 (Jinja2 + Playwright, 11~15)**
- 11 Threads 간결형 카드뉴스 (3장, 1080×1350)
- 12 Threads 인사이트형 카드뉴스 (5장, 1080×1350)
- 13 Instagram 정보형 카드뉴스 (5장, 1080×1350)
- 14 Instagram 스토리텔링형 카드뉴스 (7장, 1080×1350)
- 15 카카오톡 카드뉴스 (1~3장, 800×800)

자세한 채널별 톤·길이·해시태그 규칙은 [../knowledge/channel-style-research.md](../knowledge/channel-style-research.md)에 정의되어 있고, 각 스튜디오가 해당 섹션만 발췌해 프롬프트에 주입합니다.

## 카드뉴스 렌더링 파이프라인

```
자막 → DeepSeek LLM → JSON (5장 구조)
                         ↓
        Jinja2 채널 템플릿 + Google Fonts (Noto Sans KR · Nanum Myeongjo)
                         ↓
                       HTML (.studio-card div N개)
                         ↓
        Playwright headless Chromium (로컬, 추가 API 비용 없음)
                         ↓
                  cards/card_1.png ~ card_N.png
```

이미지 LLM(Nano Banana 등)은 사용하지 않습니다. 한글 텍스트가 깨지지 않고 디자인이 일관됩니다.

## 새 스튜디오 추가

1. `studio/<key>.py`에 `StudioBase` 상속 클래스 작성 (`key`, `order`, `title`, `section`, `channel_section`, `max_tokens`, `html_renderer`, `png_renderer`, `docx_renderer`)
2. `studio/registry.py`의 `REGISTRY` 리스트에 추가
3. `prompts/<key>_ko.md` 작성 (`<<SYSTEM>>` / `<<USER>>` 구분, `{subtitle}`/`{channel_guide}`/`{target_keyword}`/`{brand_name}` 슬롯)
4. 필요 시 [../knowledge/channel-style-research.md](../knowledge/channel-style-research.md)에 신규 채널 섹션 추가
5. 카드뉴스 신규 채널이면 [../core/card_templates.py](../core/card_templates.py)에 Jinja2 템플릿 + `_TEMPLATES` 등록 + [../core/png_render.py](../core/png_render.py) `_CHANNEL_SIZES` 등록

## 모델 변경

기본 `deepseek-v4-flash` 고정. 다른 모델로 바꾸려면 [../core/user_settings.py](../core/user_settings.py)의 `FIXED_MODEL` 상수를 수정하세요. 사용 가능한 모델 목록은 Ubion LiteLLM 마이그레이션 키트 참조.

## 트러블슈팅

- **설치 실패** — Python 3.10~3.12 필요. `python --version` 확인.
- **Playwright Chromium 다운로드 실패** — 수동 설치:
  ```
  .venv\Scripts\activate
  python -m playwright install chromium
  ```
- **401 / 403** — 사내 대시보드에서 virtual key 발급 여부 확인. URL 끝에 `/v1`을 직접 붙이지 마세요 (자동으로 추가됨).
- **Connection refused** — VPN/사내망 접속 확인. `http://192.168.50.119:4000`은 사내 전용.
- **카드뉴스 JSON 파싱 실패** — LLM이 가끔 토큰 한도에 부딪혀 잘림. 재실행하면 됨. 잘린 경우에도 완성된 카드까지는 자동 복구돼서 표시됨.
- **자막 파싱 실패** — `.srt`/`.vtt`/`.ass`/`.txt` 외 포맷은 미지원. SubRip(.srt)로 변환 후 재시도.
