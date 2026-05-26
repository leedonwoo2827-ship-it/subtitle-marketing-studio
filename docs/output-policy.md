# 산출물 정책

## 원칙

자막 원문은 외부에 노출하지 않는 **원천 데이터(Raw Data)** 로만 활용합니다. 17개 산출물 모두 **재가공된 텍스트만** 노출됩니다.

## 왜

- 자막은 영상 저작자의 표현물입니다. 그대로 옮기면 저작권·중복 콘텐츠 패널티 위험.
- 채널별 톤이 다른데, 자막 구어체를 그대로 쓰면 블로그·뉴스레터·LinkedIn 어디서도 어색합니다.
- 검색 엔진은 자막 캡션 텍스트와 본문이 동일하면 중복으로 판단해 노출을 누릅니다.

## 적용 방식

- 모든 프롬프트(`prompts/*_ko.md`)에 "자막 원문 그대로 인용 금지, 표현 재가공 필수" 규칙이 들어 있습니다.
- 자막 본문은 LLM에만 전달되고, 산출물(`data/projects/<프로젝트>/<key>/output.md`)에는 직접 노출되지 않습니다.
- `data/projects/<프로젝트>/source.txt`는 사용자 로컬에만 저장되며, 산출물 ZIP에는 포함되지 않습니다.

## 검증

산출물에 자막 원문 표현이 그대로 들어갔는지 점검:

```powershell
# Windows PowerShell — 자막의 임의 구절을 산출물에서 grep
$src = Get-Content "data\projects\<프로젝트>\source.txt" -Raw
Select-String -Path "data\projects\<프로젝트>\*\output.md" -Pattern $src.Substring(0, 80)
```

매칭이 0이어야 정상. 매칭이 있으면 해당 스튜디오 프롬프트의 "재가공" 규칙을 강화하세요.
