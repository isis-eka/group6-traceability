"""
Keyword (BM25) search over a repo's test functions.

Given a requirement, it returns the tests that share the most words with it. BM25 is the
standard formula for this: rare words (like "Content-Length") count more than common ones.
It needs no API key or index, so it is the baseline we compare the embedding search
(search_tests.py) against, and run_v1.py falls back to it when there is no key or index.
Any search module used by run_v1.py must provide the same function:

    search_tests(workspace, criterion, k=3) -> [{"test_id", "file", "code", "score"}]

Try:    python src/search_bm25.py workspace/psf__requests-1142/covered "GET sends no Content-Length"
"""
import math
import re
import sys
from collections import Counter
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__", ".tox", ".venv", "venv", "build", "dist"}
DEF = re.compile(r"^(\s*)(?:async\s+)?def\s+(test\w*)\s*\(")
CLASS = re.compile(r"^(\s*)class\s+(\w+)")
WORD = re.compile(r"[a-z0-9]+")
# Criterion boilerplate that matches nothing useful in test code
STOPWORDS = {"given", "when", "then", "the", "a", "an", "and", "or", "is", "are", "be", "to",
             "of", "in", "on", "it", "its", "that", "this", "with", "should", "for", "as", "by"}
K1, B = 1.5, 0.75


def test_files(workspace):
    for path in sorted(Path(workspace).rglob("*.py")):
        if SKIP_DIRS & set(path.parts):
            continue
        if path.name.startswith("test_") or path.name.endswith("_test.py"):
            yield path


def decorator_start(lines, def_line, indent):
    """First line of the decorators above def_line, including multi-line ones such as
    @pytest.mark.parametrize(...), which hold the test inputs."""
    start = j = def_line
    while j > 0:
        line = lines[j - 1]
        if not line.strip():
            break
        line_indent = len(line) - len(line.lstrip())
        if line_indent == indent and line.lstrip().startswith("@"):
            start = j - 1
        elif not (line_indent > indent or line.lstrip()[0] in ")]}"):
            break
        j -= 1
    return start


def split_tests(path, workspace):
    """Yield one chunk per test function, with its decorators and class.

    Uses indentation, not ast, because older requests tests are Python 2 code.
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    rel = path.relative_to(workspace).as_posix()
    classes = []  # (indent, name) of enclosing classes
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        classes = [c for c in classes if c[0] < indent]
        if m := CLASS.match(line):
            classes.append((indent, m.group(2)))
            continue
        m = DEF.match(line)
        if not m:
            continue
        start = decorator_start(lines, i, indent)
        end = i + 1
        while end < len(lines) and (not lines[end].strip()
                                    or len(lines[end]) - len(lines[end].lstrip()) > indent):
            end += 1
        while end > i + 1 and not lines[end - 1].strip():
            end -= 1
        test_id = "::".join([rel, *(c[1] for c in classes), m.group(2)])
        yield {"test_id": test_id, "file": rel, "code": "\n".join(lines[start:end])}


def tokens(text):
    return [w for w in WORD.findall(text.lower()) if w not in STOPWORDS]


def search_tests(workspace, criterion, k=3):
    tests = [t for f in test_files(workspace) for t in split_tests(f, workspace)]
    if not tests:
        return []
    docs = [Counter(tokens(t["test_id"] + " " + t["code"])) for t in tests]
    avg_len = sum(sum(d.values()) for d in docs) / len(docs)
    df = Counter(w for d in docs for w in d)
    query = set(tokens(criterion))
    for t, d in zip(tests, docs):
        length = sum(d.values())
        t["score"] = round(sum(
            math.log(1 + (len(docs) - df[w] + 0.5) / (df[w] + 0.5))
            * d[w] * (K1 + 1) / (d[w] + K1 * (1 - B + B * length / avg_len))
            for w in query if w in d), 3)
    return sorted(tests, key=lambda t: -t["score"])[:k]


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python src/search_bm25.py <workspace> <criterion>")
    for hit in search_tests(sys.argv[1], sys.argv[2]):
        print(f"{hit['score']:>7}  {hit['test_id']}")
