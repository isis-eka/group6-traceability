"""Version 2 of the tool: version 1 plus the code the tests call.

Same as run_v1.py (same search, model, prompt file, output and resume), but before the AI
call it finds the functions and classes each retrieved test calls in the project's own
source code, and adds their code under the tests in the prompt. No agent: a fixed script
decides what code is shown, so comparing v2 with the agent (v3) tells us whether the agent
helps by choosing what to read or just by seeing more code.

Run:    python src/run_v2.py --out results/dev/v2/embedding.jsonl
        python src/run_v2.py --dry-run --limit 1  # print the prompt, no API call
        (every run_v1.py option works: --prompt, --search, --case, --k, --ollama)
Needs:  the same as run_v1.py.
Output: like run_v1.py, with version "v2" and "code_added": the definitions shown, e.g.
        "requests/models.py::PreparedRequest.prepare_content_length".

How the code is found (one level deep, no imports are followed):
  1. the names each test calls: f(...) and obj.f(...), minus builtins and test helpers
  2. their definitions (def / class) in the case folder's source files: not test files,
     tests/, docs/, examples/, setup.py, or vendored copies (requests/packages/)
  3. names with fewer definitions first (less ambiguous), then in the order the tests use
     them; at most 2 definitions per name, 60 lines each and 250 lines in all
Reads only inside the case's workspace folder. Never reads data/labels*.jsonl.
"""
import builtins
import keyword
import re
from pathlib import Path

import run_v1

VERSION = "v2"
MAX_PER_NAME = 2
MAX_DEF_LINES = 60
MAX_TOTAL_LINES = 250

SKIP_DIRS = {".git", "__pycache__", "tests", "test", "testing", "docs", "examples", "packages",
             ".tox", ".venv", "venv", "build", "dist"}
SKIP_FILES = {"setup.py", "conftest.py"}
DEF = re.compile(r"^(\s*)(?:async\s+)?(def|class)\s+(\w+)")
CALL = re.compile(r"(?:\.|\b)([A-Za-z_]\w*)\s*\(")
# Names every test calls that say nothing about the code under test
NOT_CODE = (set(dir(builtins)) | set(keyword.kwlist) | {
    "self", "cls", "super", "assert_", "assertEqual", "assertTrue", "assertFalse", "assertIn",
    "assertNotIn", "assertIs", "assertIsNone", "assertIsNotNone", "assertRaises", "assertRaisesRegex",
    "assertAlmostEqual", "assertNotEqual", "fail", "skip", "raises", "warns", "mark", "parametrize",
    "fixture", "approx", "Mock", "MagicMock", "patch", "monkeypatch", "setattr", "httpbin",
})


def source_files(workspace):
    for path in sorted(Path(workspace).rglob("*.py")):
        rel = path.relative_to(workspace)
        if SKIP_DIRS & set(rel.parts[:-1]) or path.name in SKIP_FILES:
            continue
        if path.name.startswith("test_") or path.name.endswith("_test.py"):
            continue
        yield path, rel.as_posix()


def definitions(workspace):
    """{name: [{"id", "code"}]} for every def and class in the source files.

    Indentation-based like search_bm25.split_tests, because older requests code is Python 2.
    """
    found = {}
    for path, rel in source_files(workspace):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        classes = []  # (indent, name) of enclosing classes
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip())
            classes = [c for c in classes if c[0] < indent]
            m = DEF.match(line)
            if not m:
                continue
            end = i + 1
            while end < len(lines) and (not lines[end].strip()
                                        or len(lines[end]) - len(lines[end].lstrip()) > indent):
                end += 1
            body = lines[i:end]
            if m.group(2) == "class":
                # header, docstring and __init__ only: called methods are shown on their own
                for j, inner in enumerate(body[1:], 1):
                    d = DEF.match(inner)
                    if d and d.group(3) != "__init__":
                        body = body[:j]
                        break
            while body and not body[-1].strip():
                body.pop()
            if len(body) > MAX_DEF_LINES:
                body = body[:MAX_DEF_LINES] + [f"    # ... ({len(body) - MAX_DEF_LINES} more lines)"]
            qualname = ".".join([c[1] for c in classes] + [m.group(3)])
            found.setdefault(m.group(3), []).append({"id": f"{rel}::{qualname}", "code": "\n".join(body)})
            if m.group(2) == "class":
                classes.append((indent, m.group(3)))
    return found


def called_names(hits):
    """Names the tests call, in order of first use (top search hit first)."""
    names = []
    for hit in hits:
        for name in CALL.findall(hit.get("code") or hit["text"]):
            if name not in NOT_CODE and not name.startswith(("test", "assert")) and name not in names:
                names.append(name)
    return names


def called_code(workspace, hits):
    defs = definitions(workspace)
    names = [n for n in called_names(hits) if n in defs]
    names.sort(key=lambda n: len(defs[n]))  # stable: ties keep the tests' order
    chosen, total = [], 0
    for name in names:
        for d in defs[name][:MAX_PER_NAME]:
            size = d["code"].count("\n") + 1
            if total + size > MAX_TOTAL_LINES:
                return chosen
            chosen.append(d)
            total += size
    return chosen


def format_code(code):
    if not code:
        return "\n\n## Code these tests call\n(none found in the project's source)"
    return "\n\n## Code these tests call\n\n" + "\n\n".join(
        f"### {d['id']}\n```python\n{d['code']}\n```" for d in code)


def build(template, case, hits):
    code = called_code(case["workspace"], hits)
    tests = run_v1.format_tests(hits) + format_code(code)
    # str.replace, not str.format: the template contains a literal JSON example
    prompt = template.replace("{criterion}", case["criterion"]).replace("{tests}", tests)
    return prompt, {"code_added": [d["id"] for d in code]}


if __name__ == "__main__":
    run_v1.main(version=VERSION, build=build, doc=__doc__)
