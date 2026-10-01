"""md-log: 공부 세션을 마크다운 파일로 실시간 미러링 (amosblomqvist/learn 의 md-log 이식).

터미널은 수식·mermaid 를 못 그리니, 같은 내용을 파일에 써서 Obsidian 에서 렌더링해 읽는다.
담는 것: 사용자 입력, Claude 의 글, AskUserQuestion 질문과 답. 다른 도구 호출은 뺀다.

세션 로그는 log/sessions/ 에 따로 쓴다. notes/ 는 마무리 때 정리한 개념만 둔다.
link 한 세션(CLAUDE_CODE_SESSION_ID)의 hook 만 쓴다. 다른 세션이 덮어쓰지 않게.

usage:
  python3 tools/md_log.py link <file.md>   # 이 세션의 기록을 이 파일로 시작
  python3 tools/md_log.py unlink           # 기록 중지
  python3 tools/md_log.py hook             # Claude Code hook (stdin: hook JSON)
  python3 tools/md_log.py test
"""
import json, os, re, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = ROOT / ".claude" / "md-log.json"
START = "<command-name>/study</command-name>"  # 마지막 /study 호출부터 기록


def quote(kind, title, lines):
    return "\n".join([f"> [!{kind}] {title}"] + [f"> {l}" if l else ">" for l in lines])


def command_text(s):
    name = re.search(r"<command-name>(.*?)</command-name>", s)
    args = re.search(r"<command-args>(.*?)</command-args>", s, re.S)
    return f"`{name.group(1)} {args.group(1).strip() if args else ''}`".replace(" `", "`")


def question_block(questions):
    lines = []
    for q in questions:
        if lines:
            lines.append("")
        lines.append(f"**{q['question']}**")
        lines += [f"{i}. {o['label']}" for i, o in enumerate(q.get("options", []), 1)]
    return quote("question", "QUIZ", lines)


def answer_block(result):
    answers = (result or {}).get("answers") if isinstance(result, dict) else None
    if not answers:
        return quote("warning", "건너뜀", ["(답하지 않음)"])
    return quote("example", "ANSWER", [f"{q} → **{a}**" for q, a in answers.items()])


def render(rows, pending=None):
    start = 0
    for i, r in enumerate(rows):
        c = r.get("message", {}).get("content")
        if r.get("type") == "user" and isinstance(c, str) and START in c:
            start = i
    out, seen = [], set()
    for r in rows[start:]:
        if r.get("isMeta") or r.get("isSidechain") or r.get("type") not in ("user", "assistant"):
            continue
        c = r["message"]["content"]
        if isinstance(c, str):
            if "<command-name>" in c:
                out.append(quote("quote", "YOU", [command_text(c)]))
            elif not c.startswith("<"):
                out.append(quote("quote", "YOU", c.splitlines()))
            continue
        for b in c:
            if b["type"] == "text" and r["type"] == "assistant" and b["text"].strip():
                out.append("> [!abstract] CLAUDE\n\n" + b["text"].strip())
            elif b["type"] == "text" and r["type"] == "user" and not b["text"].startswith(("<", "[Request")):
                out.append(quote("quote", "YOU", b["text"].splitlines()))
            elif b["type"] == "tool_use" and b["name"] == "AskUserQuestion":
                seen.add(b["id"])
                out.append(question_block(b["input"].get("questions", [])))
            elif b["type"] == "tool_result" and b.get("tool_use_id") in seen:
                seen.discard(b["tool_use_id"])
                seen.add("done:" + b["tool_use_id"])
                out.append(answer_block(r.get("toolUseResult")))
    # hook 시점에 transcript 에 아직 안 써진 질문/답을 보충
    if pending and pending.get("tool_name") == "AskUserQuestion":
        tid = pending.get("tool_use_id")
        if pending.get("hook_event_name") == "PreToolUse" and tid not in seen and "done:" + str(tid) not in seen:
            out.append(question_block(pending.get("tool_input", {}).get("questions", [])))
        if pending.get("hook_event_name") == "PostToolUse" and "done:" + str(tid) not in seen:
            out.append(answer_block(pending.get("tool_response")))
    return "\n\n".join(out) + "\n"


def hook():
    if not LINK.exists():
        return
    event = json.load(sys.stdin)
    rows = []
    for line in open(event["transcript_path"]):
        try:
            rows.append(json.loads(line))
        except ValueError:
            pass  # 쓰는 중인 마지막 줄
    link = json.loads(LINK.read_text())
    if not mine(link, event):
        return
    target = ROOT / link["file"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"# 세션 기록 ({link['date']})\n\n" + render(rows, event))


def mine(link, event):
    return link.get("session") == event.get("session_id")


def demo():
    q = {"questions": [{"question": "3·(1,0)+2·(0,1)?", "options": [{"label": "(3, 2)"}, {"label": "모르겠음"}]}]}
    rows = [
        {"type": "user", "message": {"content": "이전 대화"}},
        {"type": "user", "message": {"content": START + "<command-args>선형대수</command-args>"}},
        {"type": "user", "isMeta": True, "message": {"content": [{"type": "text", "text": "skill body"}]}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "벡터 $v$ 부터"}]}},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "t1", "name": "AskUserQuestion", "input": q}]}},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "t2", "name": "Bash", "input": {}}]}},
    ]
    md = render(rows)
    assert "이전 대화" not in md and "skill body" not in md and "Bash" not in md
    assert "`/study 선형대수`" in md and "벡터 $v$ 부터" in md and "1. (3, 2)" in md
    assert "ANSWER" not in md
    post = {"hook_event_name": "PostToolUse", "tool_name": "AskUserQuestion", "tool_use_id": "t1",
            "tool_response": {"answers": {"3·(1,0)+2·(0,1)?": "(3, 2)"}}}
    assert "→ **(3, 2)**" in render(rows, post)
    rows.append({"type": "user", "toolUseResult": post["tool_response"],
                 "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": "..."}]}})
    assert render(rows, post).count("ANSWER") == 1  # transcript 에 이미 있으면 중복 없음
    pre = {"hook_event_name": "PreToolUse", "tool_name": "AskUserQuestion", "tool_use_id": "t9", "tool_input": q}
    assert render(rows, pre).count("QUIZ") == 2
    assert mine({"session": "a"}, {"session_id": "a"})
    assert not mine({"session": "a"}, {"session_id": "b"}) and not mine({}, {"session_id": "b"})


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "link":
        sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
        LINK.write_text(json.dumps({"file": sys.argv[2], "date": date.today().isoformat(), "session": sid}, ensure_ascii=False))
        print(f"md-log → {sys.argv[2]}")
    elif cmd == "unlink":
        LINK.unlink(missing_ok=True)
    elif cmd == "hook":
        try:
            hook()
        except Exception as e:  # 기록 실패가 세션을 막으면 안 된다
            print(f"md-log: {e}", file=sys.stderr)
    elif cmd == "test":
        demo(); print("ok")
    else:
        print(__doc__)
