---
name: git-commit
description: 이 공부 저장소의 변경사항을 논리 단위로 나눠 컨벤션에 맞게 커밋한다. "커밋", "commit", /study 마무리 단계에서 사용.
allowed-tools: Bash
---

개인 공부 저장소라 브랜치 전략 없이 현재 브랜치(`main`)에 바로 커밋한다.

`me/`(처방전·커리큘럼·계획표)와 `log/`(퀴즈·세션 기록)는 gitignore된 개인 파일이라 커밋 대상이 아니다.

## 커밋 메시지 규칙

형식: `type(scope): 설명`

- **type** (영어): `add` 새 노트/파일 · `update` 기존 노트 보강 · `fix` 틀린 내용 정정 · `refactor` 구조/이동 · `docs` README·방법론
- **scope** (영어, kebab-case): 변경 경로로 추론한다. 하드코딩 목록 없음

  | 경로 | scope |
  | --- | --- |
  | `notes/<stage>/...` | 폴더 이름 그대로 (예: `linear-algebra`, `network`) |
  | `tools/` | `tools` |
  | `.claude/skills/<name>/` | `<name>` |
  | 여러 영역에 걸친 변경 | `global` |

- **설명** (한국어): 마침표 없음, 명사형 종결. `~한다/~된다`, `~하기`, `~합니다/~됩니다`, `~했습니다` 금지
  - 좋은 예: `add(linear-algebra): 랭크 정리 노트 추가`, `fix(network): TCP 윈도우 스케일 설명 정정`, `add(notes): 커리큘럼 단계별 폴더 추가`
- 제목 한 줄만 (본문 없음)

## 커밋 흐름

1. `git status`, `git diff`로 변경 확인
2. 논리 단위로 분류: 노트 작성과 퀴즈 로그는 **별도 커밋**
3. 단위마다 관련 파일만 `git add` → `git commit -m "..."`
4. `git log --oneline -n <개수>`로 확인
