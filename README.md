# learning

AI(Claude Code)를 가이드로 삼아 "겉핥기"를 끝내기 위한 공부 시스템.
처음에 **내 공부 습관을 분석해 처방전을 만들고**, 매 세션은 그 처방대로 진행된다.

## 시작하기

1. 이 저장소를 clone하고 Claude Code로 연다. 처음 열면 프로젝트 hook 승인 안내가 나올 수 있다(세션 기록용).
2. `notes/`는 원작자의 공부 노트다. 내 것으로 쓰려면 비운다.
3. `/onboard`: 인터뷰로 습관·목표·시간을 분석해 개인 파일(`me/`)을 만든다.
4. `/study`: 계획표에서 오늘 할 항목을 골라 시작한다. `/study <주제>`로 계획 밖 주제도 공부할 수 있다.

## 구조

| 경로 | 내용 | git |
| --- | --- | --- |
| `.claude/skills/` | `onboard`(분석), `study`(세션 진행), `git-commit` | 공개 |
| `tools/` | `plan.py`(오늘 할 항목, 진척), `stats.py`(복습 주기, 확신도 통계), `md_log.py`(세션 실시간 기록) | 공개 |
| `notes/<단계>/<개념>.md` | 정리된 개념 노트 | 공개 |
| `me/` | `prescription.md`(처방전), `curriculum.md`, `plan.tsv`, `config.json` | **로컬** |
| `log/` | `quiz.tsv`, `sessions.tsv`, `sessions/`(대화 원문) | **로컬** |

## 방법론

세 사례에서 가져왔다.

| 사례 | 가져온 것 |
| --- | --- |
| [DrCatHicks/learning-opportunities](https://github.com/DrCatHicks/learning-opportunities) | 학습과학 근거. 예측 먼저, 틀리면 **분명히 틀렸다고** 말하기, 세션 시작 시 회상 체크 |
| [amosblomqvist/learn](https://github.com/amosblomqvist/learn) | probe → plan → teach. 퀴즈로 지식의 경계를 위아래로 좁혀 찾기, 개념 의존성 DAG, "어떻게 내가 이걸 발견할 수 있었을까?", 세션 실시간 기록(md-log) |
| [rlaope/estudy](https://github.com/rlaope/estudy) | 노트는 다듬지 않고 쌓는다. 책 → LLM DFS → 온디맨드 프로젝트 |

모든 처방이 기대는 원칙:

- **생성·테스트 효과**: 읽고 보는 것보다 직접 답을 만들고 떠올리는 쪽이 오래 남는다. 그래서 세션은 퀴즈와 teach-back(내 말로 3~5문장) 중심이다.
- **사전 테스트**: 자료를 보기 전에 먼저 추측한다. 틀려도 이후 학습이 강해진다. 순서는 probe 퀴즈 → 자료 → 확인 퀴즈.
- **간격 반복**: 복습은 세션 입장료다. 맞힐 때마다 1 → 3 → 7 → 14 → 30 → 60일, 틀리면 1일.
- **유창성 착각**: 쉽게 읽히면 안다고 착각한다. 퀴즈 직전에 자료를 다시 보지 않는다. 다시 보기는 틀린 뒤, 틀린 부분만.
- **명확한 교정**: 틀리면 바로 틀렸다고 말한다. 흐린 교정은 효과가 없다.
- **캘리브레이션**: 모든 퀴즈에 확신도를 기록해 "아는데 의심하는지 / 모르는데 확신하는지"를 숫자로 본다.
- **온디맨드**: 공부의 종점을 만들고 있는 프로젝트(또는 면접)의 구체적인 지점에 둔다.

## 세션 흐름 (약 50분)

1. 복습 퀴즈 → probe 퀴즈(자료 보기 전)
2. plan: 개념 의존성 DAG 승인
3. 자료 보기(영상·교재, 링크 제공)
4. teach 루프: 노드마다 확인 퀴즈, 틀린 노드만 설명
5. 내 말로 3~5문장 → 개념 노트 정리 → `plan.py log`로 시간·정답률 기록 → commit

`/study` 중에는 대화가 `log/sessions/`에 실시간으로 기록된다. 이 폴더를 Obsidian vault로 열고 그 파일을 옆에 띄워 읽는다. Obsidian은 **읽기만** 한다: 플러그인·테마 없음, `[[위키링크]]` 대신 일반 마크다운 링크(설정 → Files and links → Use [[Wikilinks]] 끄기).
