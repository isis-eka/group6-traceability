"""Version 3 of the tool: an agent decides what to read.

Instead of always being shown the same 3 tests, the AI gets three read-only tools and decides
for itself where to look, up to 10 tool calls per case, then answers covered, partial,
not_covered or needs_review with a short reason.

Tools (all limited to the case's own folder, workspace/<instance_id>/<variant>/):
  search_tests(query)            version 1's search, with the agent's own query (top 3 tests)
  grep(pattern)                  regular expression over the folder's files, at most 40 matches
  read_file(path, start_line)    at most 200 lines of one file, with line numbers

Run:    python src/run_agent.py --out results/dev/v3/embedding.jsonl
        python src/run_agent.py --case psf__requests-1142__ac1__covered --verbose
        python src/run_agent.py --dry-run --limit 1   # print the first prompt, no API call
        (same --cases, --prompt, --search, --k, --limit, --ollama and resume as run_v1.py)
Needs:  the same as run_v1.py.
Output: like run_v1.py, with version "v3", "tool_calls" and "steps" (each call's tool and
        arguments). "tests_found" is every test search_tests returned to the agent.

The limits are enforced here, not just asked for in the prompt (AGENTS.md hard rules):
  - at most MAX_CALLS tool calls; asking for more after that gives needs_review
  - every path must stay inside the case folder; .git and paths outside it are refused
  - read_file returns at most 200 lines, grep at most 40 matches, search at most 3 tests
A plain tool-calling loop on the Responses API rather than the Agents SDK: it reuses run_v1.py's
client and Ollama fallback and needs no new package. Not Chat Completions: there gpt-6-luna
allows tools only with reasoning switched off, which would make v3 reason less than v1 and v2.
Never reads data/labels*.jsonl.
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import run_v1

VERSION = "v3"
MAX_CALLS = 10
MAX_READ_LINES = 200
MAX_GREP_MATCHES = 40
MAX_LINE_CHARS = 200
SKIP_DIRS = {".git", "__pycache__"}

TOOLS = [
    {"type": "function",
        "name": "search_tests",
        "description": "Find the test functions closest in meaning to the query. Returns their ids and code.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "What the tests should check, in plain words"},
        }, "required": ["query"]},
    },
    {"type": "function",
        "name": "grep",
        "description": f"Search the project's files for a Python regular expression. Returns up to "
                       f"{MAX_GREP_MATCHES} matches as path:line: text.",
        "parameters": {"type": "object", "properties": {
            "pattern": {"type": "string"},
            "path": {"type": "string", "description": "Folder or file to search, relative to the project root (default: all)"},
        }, "required": ["pattern"]},
    },
    {"type": "function",
        "name": "read_file",
        "description": f"Read up to {MAX_READ_LINES} lines of a file, with line numbers.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Relative to the project root, e.g. requests/models.py"},
            "start_line": {"type": "integer", "description": "First line to show (default 1)"},
        }, "required": ["path"]},
    },
]


class Refused(Exception):
    """A tool call the rules don't allow; the agent is told why and can try something else."""


class Workspace:
    """Read-only access to one case folder. Every path is checked before it is opened."""

    def __init__(self, case, search, k):
        self.root = Path(case["workspace"]).resolve()
        self.case, self.search, self.k = case, search, k
        self.tests_found = []

    def path(self, rel):
        rel = (rel or ".").replace("\\", "/")
        target = (self.root / rel).resolve()
        if Path(rel).is_absolute() or not target.is_relative_to(self.root):
            raise Refused(f"{rel!r} is outside the project folder")
        if SKIP_DIRS & set(target.relative_to(self.root).parts):
            raise Refused(f"{rel!r} is not readable")
        if not target.exists():
            raise Refused(f"{rel!r} does not exist")
        return target

    def files(self, under):
        paths = [under] if under.is_file() else sorted(under.rglob("*"))
        for p in paths:
            if p.is_file() and not SKIP_DIRS & set(p.relative_to(self.root).parts):
                yield p

    def search_tests(self, query):
        hits = self.search({**self.case, "criterion": query}, self.k)
        self.tests_found += [h["test_id"] for h in hits if h["test_id"] not in self.tests_found]
        return "\n\n".join(f"### {h['test_id']} ({h['file']} lines {h['start_line']}-{h['end_line']})\n"
                           f"{h.get('code') or h['text']}" for h in hits) or "(no tests found)"

    def grep(self, pattern, path="."):
        try:
            regex = re.compile(pattern)
        except re.error:
            regex = re.compile(re.escape(pattern))  # not a valid regex: search the text as typed
        out = []
        for f in self.files(self.path(path)):
            try:
                lines = f.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, OSError):
                continue  # binary file
            for i, line in enumerate(lines, 1):
                if regex.search(line):
                    out.append(f"{f.relative_to(self.root).as_posix()}:{i}: {line.strip()[:MAX_LINE_CHARS]}")
                    if len(out) == MAX_GREP_MATCHES:
                        return "\n".join(out) + f"\n(stopped at {MAX_GREP_MATCHES} matches: narrow the pattern or path)"
        return "\n".join(out) or "(no matches)"

    def read_file(self, path, start_line=1):
        target = self.path(path)
        if target.is_dir():
            return "Directory: " + ", ".join(sorted(p.name for p in target.iterdir() if p.name not in SKIP_DIRS))
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(int(start_line or 1), 1)
        shown = lines[start - 1:start - 1 + MAX_READ_LINES]
        body = "\n".join(f"{n:5}  {line}" for n, line in enumerate(shown, start))
        if start - 1 + len(shown) < len(lines):
            body += f"\n(file has {len(lines)} lines; read more with start_line={start + len(shown)})"
        return body or f"(file has {len(lines)} lines)"

    def call(self, name, args):
        if name not in ("search_tests", "grep", "read_file"):
            raise Refused(f"unknown tool {name!r}")
        try:
            return getattr(self, name)(**args)
        except TypeError as e:
            raise Refused(f"bad arguments: {e}")


def respond(client, model, items):
    for attempt in range(3):
        try:
            return client.responses.create(model=model, input=items, tools=TOOLS)
        except Exception as e:  # rate limits, timeouts: retry, then give up on this case
            if attempt == 2:
                raise
            print(f"  API error ({e}), retrying", file=sys.stderr)
            time.sleep(5 * (attempt + 1))


def final_json(text):
    """The JSON object in the agent's last reply (it may wrap it in a code fence)."""
    m = re.search(r"\{.*\}", text or "", re.S)
    return m.group(0) if m else (text or "")


def run_case(client, model, prompt, ws, verbose=False):
    """(verdict, reason, tests_used, steps, tokens_in, tokens_out)"""
    items = [{"role": "user", "content": prompt}]
    steps, tokens_in, tokens_out = [], 0, 0
    while True:
        resp = respond(client, model, items)
        tokens_in += resp.usage.input_tokens
        tokens_out += resp.usage.output_tokens
        calls = [o for o in resp.output if o.type == "function_call"]
        if not calls:
            verdict, reason, used = run_v1.parse_reply(final_json(resp.output_text))
            return verdict, reason, used, steps, tokens_in, tokens_out
        if len(steps) >= MAX_CALLS:
            reason = f"Reached the limit of {MAX_CALLS} tool calls without deciding."
            return "needs_review", reason, [], steps, tokens_in, tokens_out
        items += resp.output  # the model's reasoning and calls go back with the results
        for c in calls:
            try:
                args = json.loads(c.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            if len(steps) >= MAX_CALLS:
                result = f"Refused: the limit of {MAX_CALLS} tool calls is used up. Answer now."
            else:
                steps.append({"tool": c.name, "args": args})
                try:
                    result = ws.call(c.name, args)
                except Refused as e:
                    result = f"Refused: {e}"
                left = MAX_CALLS - len(steps)
                result += f"\n\n[{left} tool call{'s' if left != 1 else ''} left]" if left else \
                    "\n\n[No tool calls left: answer now in JSON]"
            if verbose:
                print(f"  {c.name}({json.dumps(args)[:120]}) -> {len(result)} chars")
            items.append({"type": "function_call_output", "call_id": c.call_id, "output": result})


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cases", default="data/cases.jsonl")
    p.add_argument("--out", default="results/results.jsonl")
    p.add_argument("--prompt", default="agent_v1", help="file name in prompts/, without .txt")
    p.add_argument("--search", default="search_tests",
                   help="search module behind the search_tests tool: search_tests (embedding) or search_bm25")
    p.add_argument("--k", type=int, default=3)
    p.add_argument("--case", action="append", help="run only this case_id (repeatable)")
    p.add_argument("--limit", type=int)
    p.add_argument("--dry-run", action="store_true", help="print the first prompt, call no API, save nothing")
    p.add_argument("--verbose", action="store_true", help="print each tool call")
    p.add_argument("--ollama", nargs="?", const=run_v1.OLLAMA_MODEL, metavar="MODEL",
                   help="use the local Ollama server instead of OpenAI, for testing only")
    args = p.parse_args()

    template = Path(f"prompts/{args.prompt}.txt").read_text(encoding="utf-8")
    cases = run_v1.load_cases(args.cases, args.case)[:args.limit]
    search_name = run_v1.choose_search(args.search, cases)
    search = run_v1.load_search(search_name)
    model, use_ollama = run_v1.choose_model(args.ollama)

    out = Path(args.out)
    run = {"version": VERSION, "model": model, "prompt": args.prompt, "search": search_name}
    done = set()
    if out.exists() and not args.dry_run:
        with out.open(encoding="utf-8") as f:
            done = {r["case_id"] for r in map(json.loads, filter(str.strip, f))
                    if all(r.get(k) == v for k, v in run.items())}

    client = None
    if not args.dry_run:
        client = run_v1.make_client(ollama=use_ollama)
        out.parent.mkdir(parents=True, exist_ok=True)
    print(f"Model: {model} ({'Ollama' if use_ollama else 'OpenAI'}), search: {search_name}, "
          f"prompt: {args.prompt}, cases: {len(cases)}, max tool calls: {MAX_CALLS}")

    counts = {}
    for case in cases:
        if case["case_id"] in done:
            print(f"skip (already run): {case['case_id']}")
            continue
        if not Path(case["workspace"]).is_dir():
            print(f"skip (no workspace, run prepare_repo.py): {case['workspace']}", file=sys.stderr)
            continue
        # str.replace, not str.format: the template contains a literal JSON example
        prompt = template.replace("{criterion}", case["criterion"]).replace("{max_calls}", str(MAX_CALLS))
        if args.dry_run:
            print(f"===== {case['case_id']}\n{prompt}\n")
            continue

        ws = Workspace(case, search, args.k)
        verdict, reason, tests_used, steps, tokens_in, tokens_out = run_case(
            client, model, prompt, ws, verbose=args.verbose)
        row = {
            "case_id": case["case_id"],
            "verdict": verdict,
            "reason": reason,
            "tests_found": ws.tests_found,
            "tests_used": tests_used,
            **run,
            "tool_calls": len(steps),
            "steps": steps,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        with out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        counts[verdict] = counts.get(verdict, 0) + 1
        print(f"{verdict:<13} {case['case_id']}  ({len(steps)} tool calls)")

    if counts:
        print(f"Saved to {out}: " + ", ".join(f"{v} {n}" for v, n in sorted(counts.items())))


if __name__ == "__main__":
    main()
