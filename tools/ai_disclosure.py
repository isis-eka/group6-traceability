"""Check AI use disclosure (SE201 AI Use Disclosure Policy, section 4).

Any commit with AI-assisted work must carry an `Assisted-by: <tool> (<model>)`
trailer (or the tool's own AI `Co-Authored-By:` line) AND add an entry to
ai-log/<member>.md in the same commit.

Run:
    python tools/ai_disclosure.py check-logs             # validate every ai-log/*.md
    python tools/ai_disclosure.py check-range BASE HEAD  # CI: every AI commit in BASE..HEAD logs its work
    python tools/ai_disclosure.py summary                # tools and outcomes per member, for the declaration
    python tools/ai_disclosure.py commit-msg FILE        # used by .githooks/commit-msg
"""
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, check=True).stdout.strip())
LOG_DIR = "ai-log"
TEMPLATE = "your-name.md"

ASSISTED_BY = re.compile(r"^Assisted-by:\s*(.*)$", re.I | re.M)
ASSISTED_BY_VALUE = re.compile(r"^[^()]+\([^()]+\)\s*$")  # <tool> (<model>)
AI_CO_AUTHOR = re.compile(
    r"^Co-Authored-By:.*(claude|anthropic|openai|codex|gpt|copilot|gemini|cursor)", re.I | re.M)

ENTRY_HEADING = re.compile(r"^## (\d{4}-\d{2}-\d{2}) [·\-–—] \S.*$")
FIELDS = {
    "Tool (model)": re.compile(r"^- \*\*Tool \(model\):\*\* \S.*\(.+\)\s*$"),
    "Files": re.compile(r"^- \*\*Files:\*\* \S"),
    "Outcome": re.compile(r"^- \*\*Outcome:\*\* (Kept|Changed|Rejected)\s*$"),
}
SECTIONS = ["What I asked for", "How I checked it", "What I kept or changed"]


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout


def is_log_file(path):
    p = Path(path)
    return p.parts[:1] == (LOG_DIR,) and p.suffix == ".md" and p.name != TEMPLATE


def trailer_errors(message):
    """Return (has_ai_trailer, errors) for a commit message."""
    errors = []
    values = ASSISTED_BY.findall(message)
    for value in values:
        if not ASSISTED_BY_VALUE.match(value.strip()):
            errors.append(f"Bad trailer 'Assisted-by: {value.strip()}'. "
                          "Use: Assisted-by: <tool> (<model>), e.g. Assisted-by: Codex (gpt-6-luna)")
    return bool(values) or bool(AI_CO_AUTHOR.search(message)), errors


def check_log(path, text):
    """Return a list of 'file:line: problem' strings for one ai-log file."""
    errors = []
    lines = text.splitlines()
    first = next((i for i, l in enumerate(lines) if l.strip()), None)
    if first is None or not lines[first].startswith("# AI Use Log: "):
        errors.append(f"{path}:1: first line must be '# AI Use Log: <your name>'")

    starts = [i for i, l in enumerate(lines) if l.startswith("## ")]
    if not starts:
        errors.append(f"{path}: no entries yet (each starts with '## YYYY-MM-DD · Title')")
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        body = lines[start:end]
        where = f"{path}:{start + 1}"
        if not ENTRY_HEADING.match(body[0]):
            errors.append(f"{where}: heading must be '## YYYY-MM-DD · Short title'")
        for name, pattern in FIELDS.items():
            if not any(pattern.match(l) for l in body):
                hint = " (Kept, Changed or Rejected)" if name == "Outcome" else ""
                errors.append(f"{where}: missing or malformed '- **{name}:**' field{hint}")
        for section in SECTIONS:
            idx = next((i for i, l in enumerate(body) if l.strip() == f"### {section}"), None)
            if idx is None:
                errors.append(f"{where}: missing '### {section}' section")
                continue
            nxt = next((i for i in range(idx + 1, len(body)) if body[i].startswith("#")), len(body))
            if not any(l.strip() for l in body[idx + 1:nxt]):
                errors.append(f"{where}: '### {section}' is empty")
    return errors


def cmd_check_logs():
    errors = []
    for path in sorted((ROOT / LOG_DIR).glob("*.md")):
        if path.name != TEMPLATE:
            errors += check_log(path.relative_to(ROOT), path.read_text(encoding="utf-8"))
    return errors


def cmd_commit_msg(msg_file):
    message = Path(msg_file).read_text(encoding="utf-8")
    # Ignore comment lines git strips from the final message
    message = "\n".join(l for l in message.splitlines() if not l.startswith("#"))
    has_ai, errors = trailer_errors(message)
    staged = [f for f in git("diff", "--cached", "--name-only").splitlines() if is_log_file(f)]
    if has_ai and not staged:
        errors.append(
            "This commit is marked as AI-assisted but adds no ai-log entry.\n"
            "  Add an entry to ai-log/<your-name>.md (see ai-log/your-name.md) and stage it.\n"
            "  (Amending a commit that already has its entry? Re-run with --no-verify.)")
    for f in staged:
        staged_text = git("show", f":{f}")
        errors += check_log(f, staged_text)
    return errors


def cmd_check_range(base, head):
    errors = []
    if not base or set(base) == {"0"}:  # new branch: check just the head commit
        revs = [head]
    else:
        revs = git("rev-list", "--no-merges", f"{base}..{head}").split()
    for sha in revs:
        message = git("log", "-1", "--format=%B", sha)
        has_ai, trailer_errs = trailer_errors(message)
        short = f"{sha[:7]} {message.splitlines()[0] if message else ''}"
        errors += [f"{short}: {e}" for e in trailer_errs]
        files = git("diff-tree", "--no-commit-id", "--name-only", "-r", "--root", sha).splitlines()
        if has_ai and not any(is_log_file(f) for f in files):
            errors.append(f"{short}: AI-assisted commit with no ai-log entry in the same commit")
    return errors


def cmd_summary():
    for path in sorted((ROOT / LOG_DIR).glob("*.md")):
        if path.name == TEMPLATE:
            continue
        text = path.read_text(encoding="utf-8")
        tools = Counter(m.strip() for m in re.findall(r"^- \*\*Tool \(model\):\*\* (.+)$", text, re.M))
        outcomes = Counter(re.findall(r"^- \*\*Outcome:\*\* (\w+)", text, re.M))
        print(f"{path.name}: {sum(outcomes.values())} entries")
        for tool, n in tools.most_common():
            print(f"  {n} x {tool}")
        print("  outcomes: " + ", ".join(f"{k} {v}" for k, v in outcomes.items()))
    return []


def main():
    commands = {"check-logs": (cmd_check_logs, 0), "commit-msg": (cmd_commit_msg, 1),
                "check-range": (cmd_check_range, 2), "summary": (cmd_summary, 0)}
    if len(sys.argv) < 2 or sys.argv[1] not in commands \
            or len(sys.argv) - 2 != commands[sys.argv[1]][1]:
        sys.exit(__doc__)
    func, _ = commands[sys.argv[1]]
    errors = func(*sys.argv[2:])
    if errors:
        print("AI use disclosure check failed (SE201 policy, section 4):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
