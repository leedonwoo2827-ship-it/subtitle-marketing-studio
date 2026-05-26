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

`tsbookmaker`(8610)와 같이 띄울 때 충돌 방지를 위해 별도 포트를 사용합니다.

## LLM 백엔드

사이드바(⚙)에서 둘 중 하나 선택:

### 1) LiteLLM 프록시 (원격, OpenAI 호환)

DeepSeek / OpenAI / Anthropic / 자체 호스팅 등 OpenAI 호환 엔드포인트면 모두 가능.

| 프리셋 | 모델 |
|---|---|
| budget | `deepseek/deepseek-chat` |
| balanced | `openai/gpt-4o-mini` |
| premium | `anthropic/claude-sonnet-4-6` |
| custom | 직접 입력 |

`Base URL` + `API Key` + 모델을 입력하고 `연결 테스트` → 통과하면 `저장`.

### 2) Ollama (로컬)

[ollama.com](https://ollama.com) 설치 후 모델 풀:

```bash
ollama pull llama3.1:8b
# 또는
ollama pull qwen2.5:14b
```

사이드바에서 `Ollama` 선택 → 모델명 입력 → `연결 테스트`.

> 로컬 LLM은 GPU/CPU 경합을 막기 위해 17개 스튜디오를 **순차 실행**(동시성 1)으로 강제합니다. 원격은 사이드바 `병렬 실행` 슬라이더(1~8)로 조정.

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

## 트러블슈팅

- **`설치 실패`** — Python 3.10~3.12 필요. `python --version` 확인.
- **`ollama 연결 실패`** — `ollama serve` 가 실행 중인지, `ollama list`에 해당 모델이 있는지 확인.
- **`LiteLLM 401/403`** — Base URL 끝에 `/v1` 필요한 프로바이더가 있음. 공식 문서 확인.
- **자막 파싱이 깨질 때** — `.srt`/`.vtt`/`.ass`/`.txt` 외 포맷은 미지원. SubRip(.srt)로 변환 후 재시도.
