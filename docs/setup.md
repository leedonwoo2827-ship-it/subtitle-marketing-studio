# 설치·운영 가이드

## Windows

1. `setup.bat` 더블클릭 — `.venv` 생성 + 의존성 설치 + `.env` 자동 생성
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

## API 설정

[Ubion LiteLLM 프록시](_context/litellm_kit/README.md)를 사용합니다. 모델은 `deepseek-v4-flash` 고정 (저렴 등급, 한국어 OK).

사이드바(⚙)에서:

- **API URL** — 기본값 `http://192.168.50.119:4000` (사내 프록시)
- **API 키** — 사내 LiteLLM 대시보드(`http://192.168.50.119:4000/ui/`)에서 발급받은 virtual key (`sk-...`)

`연결 테스트` → 통과하면 `저장`. 환경변수(`UBION_LITELLM_URL`/`UBION_LITELLM_KEY`)를 미리 설정해두면 자동 인식됩니다.

## 폴더 구조

```
subtitle-marketing-studio/
├── app.py                           # Streamlit 엔트리
├── core/                            # 자막 파서, LLM provider, 러너
├── studio/                          # 17개 스튜디오 + 레지스트리
├── prompts/<key>_ko.md              # <<SYSTEM>> / <<USER>> 프롬프트
├── knowledge/channel-style-research.md  # 채널별 톤·길이 가이드
└── data/
    ├── user_settings.json           # GUI 설정 영속화
    └── projects/<프로젝트>/
        ├── source.txt
        └── <studio_key>/output.md   # 17개 산출물
```

## 17개 스튜디오 라인업

**1부 · 코어 콘텐츠**: 정보성 블로그 · 뉴스레터 · LinkedIn · 미니 전자책 단원
**2부 · SEO·유입**: SEO 메타 · 커뮤니티 게시글 · FAQ · 인스타 카드뉴스
**3부 · 다이렉트 셀링**: PAS 세일즈 · 메타·구글 광고 · 푸시·알림톡 · 랜딩 헤드라인 · 가상 리뷰
**4부 · 마케팅 전략·백오피스**: 페르소나 · 태그·키워드 · 프로모션 · 보도자료

자세한 채널별 톤·길이·해시태그 규칙은 [../knowledge/channel-style-research.md](../knowledge/channel-style-research.md)에 정의되어 있고, 각 스튜디오가 해당 섹션만 발췌해 프롬프트에 주입합니다.

## 새 스튜디오 추가

1. `studio/<key>.py`에 `StudioBase` 상속 클래스 작성 (`key`, `order`, `title`, `section`, `channel_section`)
2. `studio/registry.py`의 `REGISTRY` 리스트에 추가
3. `prompts/<key>_ko.md` 작성 (`<<SYSTEM>>` / `<<USER>>` 구분, `{subtitle}`/`{channel_guide}`/`{target_keyword}`/`{brand_name}` 슬롯)
4. 필요 시 [../knowledge/channel-style-research.md](../knowledge/channel-style-research.md)에 신규 채널 섹션 추가

## 모델 변경

기본 `deepseek-v4-flash` 고정. 다른 모델로 바꾸려면 [../core/user_settings.py](../core/user_settings.py)의 `FIXED_MODEL` 상수를 수정하세요. 사용 가능한 모델 목록은 [Ubion 마이그레이션 키트](../_context/litellm_kit/README.md)의 "신/구 모델 매핑" 표 참조.

## 트러블슈팅

- **`설치 실패`** — Python 3.10~3.12 필요. `python --version` 확인.
- **`401 / 403`** — 사내 대시보드에서 virtual key 발급 여부 확인. URL 끝에 `/v1`을 직접 붙이지 마세요 (자동으로 추가됨).
- **`Connection refused`** — VPN/사내망 접속 확인. `http://192.168.50.119:4000`은 사내 전용.
- **자막 파싱 실패** — `.srt`/`.vtt`/`.ass`/`.txt` 외 포맷은 미지원. SubRip(.srt)로 변환 후 재시도.
