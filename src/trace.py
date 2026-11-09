"""The tool for a team: which of an issue's acceptance criteria are tested in a repo?

Give it a repo (GitHub link or local folder) and an issue (GitHub link, number, or text file),
or your own acceptance criteria. It drafts the criteria from the issue text if needed, runs the
agent (version 3) on each one, and writes a traceability report: per criterion the verdict,
the tests it relied on and why, a summary ("2 of 3 covered, 1 partial") and what to do next.

Run:    python src/trace.py --repo https://github.com/psf/requests --issue https://github.com/psf/requests/issues/1142
        python src/trace.py --repo https://github.com/pallets/flask --issue 4602     # issue number in that repo
        python src/trace.py --repo ../myproject --issue story.txt                   # local folder, text file
        python src/trace.py --repo ../myproject --criterion "Given ..., when ..., then ..."   (repeatable)
        python src/trace.py --repo ../myproject --criteria criteria.txt             # one criterion per line
Needs:  .env with OPENAI_API_KEY (or --ollama), git for GitHub links. Set GITHUB_TOKEN in .env
        if GitHub's rate limit for issue downloads is hit.
Output: reports/<repo>__<issue number>.md (or --out), also printed; an existing report is never
        replaced: the new one gets the next free number (..._2.md, ..._3.md). GitHub repos are cloned (shallow) into
        workspace/_trace/<owner>__<repo>/; the test index is cached next to them.

Same agent and limits as run_agent.py (prompt agent_v1 by default, --prompt to change): read-only, at most 10 tool calls per criterion, never
outside the repo folder or inside .git. The report is the AI's judgment: check before acting.
This is the product, not the evaluation: it never reads data/ and saves nothing to results/.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import run_agent
import run_v1
from build_index import chunks_for_file, embed_texts, openai_client, test_files, text_hash, write_jsonl
from draft_criteria import parse_criteria

TRACE = Path("workspace/_trace")
REPO_URL = re.compile(r"https?://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?(?:/tree/([^?#]+))?/?$")
ISSUE_URL = re.compile(r"https?://github\.com/([\w.-]+)/([\w.-]+)/issues/(\d+)")
NEXT_STEP = {
    "covered": "Nothing to do.",
    "partial": "Add the missing checks to the test (the reason says what is unchecked).",
    "not_covered": "Write a test for this criterion; related tests do not check it.",
    "needs_review": "A person should check: the agent could not tell.",
}


# ---- inputs ----------------------------------------------------------------------------------

def get_repo(repo, ref):
    """(folder, info) for a GitHub link (cloned into workspace/_trace/) or a local folder."""
    m = REPO_URL.match(repo.strip())
    if not m:
        folder = Path(repo).resolve()
        if not folder.is_dir():
            sys.exit(f"--repo {repo!r} is neither a GitHub repo link nor a folder")
        return folder, {"name": folder.name, "label": str(folder), "owner_repo": None}
    owner, name, tree_ref = m.groups()
    ref = ref or tree_ref
    folder = TRACE / f"{owner}__{name}" / (re.sub(r"[^\w.-]", "_", ref) if ref else "default")
    if not folder.is_dir():
        print(f"Cloning github.com/{owner}/{name}{' @ ' + ref if ref else ''} into {folder} ...")
        cmd = ["git", "clone", "--depth", "1", "--quiet"] + (["--branch", ref] if ref else []) + \
              [f"https://github.com/{owner}/{name}.git", str(folder)]
        if subprocess.run(cmd).returncode != 0:
            sys.exit("git clone failed (check the link, or --ref for a branch or tag)")
    sha = subprocess.run(["git", "-C", str(folder), "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    return folder.resolve(), {"name": f"{owner}__{name}", "label": f"github.com/{owner}/{name}",
                              "owner_repo": f"{owner}/{name}", "sha": sha}


def fetch_issue(owner_repo, number):
    """Title and body of a GitHub issue (no comments: criteria come from the issue text only)."""
    req = urllib.request.Request(f"https://api.github.com/repos/{owner_repo}/issues/{number}",
                                 headers={"Accept": "application/vnd.github+json"})
    if os.getenv("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.getenv('GITHUB_TOKEN')}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            issue = json.load(resp)
    except OSError as e:
        sys.exit(f"Could not download issue {owner_repo}#{number}: {e}")
    return {"title": issue["title"], "text": f"{issue['title']}\n\n{issue.get('body') or ''}",
            "link": issue["html_url"]}


def get_issue(issue, repo_info):
    m = ISSUE_URL.match(issue.strip())
    if m:
        return fetch_issue(f"{m.group(1)}/{m.group(2)}", m.group(3))
    if re.fullmatch(r"#?\d+", issue.strip()):
        if not repo_info["owner_repo"]:
            sys.exit("An issue number needs a GitHub --repo link; give a link or a text file instead")
        return fetch_issue(repo_info["owner_repo"], issue.strip().lstrip("#"))
    path = Path(issue)
    if not path.is_file():
        sys.exit(f"--issue {issue!r} is not a GitHub issue link, an issue number or a file")
    text = path.read_text(encoding="utf-8")
    return {"title": text.strip().splitlines()[0][:100] if text.strip() else path.name,
            "text": text, "link": str(path)}


def draft(client, model, issue_text):
    template = Path("prompts/draft_criteria.txt").read_text(encoding="utf-8")
    text, _ = run_v1.ask_model(client, model, template.replace("{issue_text}", issue_text), json_mode=False)
    criteria = parse_criteria(text or "")
    if not criteria:
        sys.exit("The issue is too vague to draft a testable criterion. Give --criterion yourself.")
    return criteria


# ---- search over the repo's tests --------------------------------------------------------------

def build_index(folder, path):
    """One embedded chunk per test function, cached at `path` for this commit/folder."""
    if path.exists():
        with path.open(encoding="utf-8") as f:
            return [json.loads(line) for line in f]
    chunks = []
    for f in test_files(folder):
        try:
            chunks += chunks_for_file(f, folder)
        except (SystemExit, UnicodeDecodeError):  # unparsable file (e.g. Python 2): skip it
            print(f"  skipped {f.relative_to(folder).as_posix()} (cannot parse)", file=sys.stderr)
    if not chunks:
        sys.exit(f"No test functions (test_*.py / *_test.py) found in {folder}")
    print(f"Indexing {len(chunks)} test functions ...")
    vectors = {}
    todo = list({text_hash(c["text"]): c["text"] for c in chunks}.items())
    for (h, _), v in zip(todo, embed_texts(openai_client(), [t for _, t in todo])):
        vectors[h] = v
    rows = [{**c, "embedding": vectors[text_hash(c["text"])]} for c in chunks]
    write_jsonl(path, rows)
    return rows


def make_search(index):
    client = openai_client()

    def search(case, k):
        [q] = embed_texts(client, [case["criterion"]])
        scored = sorted(((sum(a * b for a, b in zip(q, c["embedding"])), c) for c in index),
                        key=lambda pair: pair[0], reverse=True)
        return [{"test_id": c["test_id"], "file": c["file"], "start_line": c["start_line"],
                 "end_line": c["end_line"], "code": c["text"].split("\n", 1)[1]} for _, c in scored[:k]]
    return search


# ---- report ----------------------------------------------------------------------------------

def test_link(test_id, lines, repo_info):
    file = test_id.split("::")[0]
    start = lines.get(test_id)
    if repo_info.get("sha") and start:
        return f"[`{test_id}`](https://github.com/{repo_info['owner_repo']}/blob/{repo_info['sha']}/{file}#L{start})"
    return f"`{test_id}`" + (f" (line {start})" if start else "")


def summary(results):
    counts = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    parts = [f"{counts.pop('covered', 0)} of {len(results)} covered"]
    parts += [f"{n} {v.replace('_', ' ')}" for v, n in counts.items()]
    return ", ".join(parts)


def free_path(path):
    """path itself if it does not exist yet, else the first free path_2, path_3, ... (never overwrite a report)."""
    new, n = path, 2
    while new.exists():
        new = path.with_name(f"{path.stem}_{n}{path.suffix}")
        n += 1
    return new


def report(repo_info, issue, results, model, prompt_name, drafted, lines):
    out = [f"# Traceability report: {repo_info['label']}", ""]
    commit = f" @ `{repo_info['sha'][:10]}`" if repo_info.get("sha") else ""
    out += [f"- **Repo:** {repo_info['label']}{commit}"]
    if issue:
        out += [f"- **Issue:** [{issue['title']}]({issue['link']})"]
    out += [f"- **Checked:** {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC with `{model}`, prompt `{prompt_name}` "
            f"(agent, at most {run_agent.MAX_CALLS} read-only tool calls per criterion)",
            "", f"## Summary: {summary(results)}", "",
            "| # | Acceptance criterion | Verdict | Tests cited |", "|---|---|---|---|"]
    for n, r in enumerate(results, 1):
        tests = "<br>".join(f"`{t.split('::')[-1]}`" for t in r["tests_used"]) or "none"
        out += [f"| AC{n} | {r['criterion']} | **{r['verdict'].replace('_', ' ')}** | {tests} |"]
    out += ["", "## Details", ""]
    for n, r in enumerate(results, 1):
        out += [f"### AC{n}: {r['verdict'].replace('_', ' ')}", "", f"> {r['criterion']}", "",
                f"**Why:** {r['reason']}", ""]
        if r["tests_used"]:
            out += ["**Tests:** " + ", ".join(test_link(t, lines, repo_info) for t in r["tests_used"]), ""]
        out += [f"**Next step:** {NEXT_STEP[r['verdict']]}", "",
                f"<sub>Agent steps ({len(r['steps'])}): " +
                "; ".join(f"{s['tool']}({', '.join(str(v) for v in s['args'].values())[:60]})"
                          for s in r["steps"]) + "</sub>", ""]
    out += ["---", "Generated by an AI agent: check a verdict before acting on it."
            + (" The acceptance criteria were AI-drafted from the issue text; review them too." if drafted else "")]
    return "\n".join(out) + "\n"


# ---- main ------------------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", required=True, help="GitHub repo link or local folder")
    p.add_argument("--ref", help="branch or tag to clone (GitHub links only; default: the default branch)")
    p.add_argument("--issue", help="GitHub issue link, issue number in --repo, or a text file")
    p.add_argument("--criterion", action="append", help="an acceptance criterion (repeatable)")
    p.add_argument("--criteria", help="text file, one acceptance criterion per line")
    p.add_argument("--out", help="report file (default reports/<repo>__<issue number>.md); "
                                 "if it exists, _2, _3, ... is added instead of replacing it")
    p.add_argument("--prompt", default="agent_v1", help="agent prompt in prompts/, without .txt (default agent_v1)")
    p.add_argument("--k", type=int, default=3, help="tests per search_tests call")
    p.add_argument("--ollama", nargs="?", const=run_v1.OLLAMA_MODEL, metavar="MODEL",
                   help="use the local Ollama server instead of OpenAI, for testing only")
    args = p.parse_args()
    if not (args.issue or args.criterion or args.criteria):
        p.error("give --issue, --criterion or --criteria")

    folder, repo_info = get_repo(args.repo, args.ref)
    model, use_ollama = run_v1.choose_model(args.ollama)
    client = run_v1.make_client(ollama=use_ollama)

    issue = get_issue(args.issue, repo_info) if args.issue else None
    criteria = list(args.criterion or [])
    if args.criteria:
        criteria += [l.strip() for l in Path(args.criteria).read_text(encoding="utf-8").splitlines() if l.strip()]
    drafted = not criteria
    if drafted:
        print(f"Drafting acceptance criteria from: {issue['title']}")
        criteria = draft(client, model, issue["text"])
    for n, c in enumerate(criteria, 1):
        print(f"  AC{n}: {c}")

    index_path = TRACE / f"{repo_info['name']}__{repo_info.get('sha') or 'local'}.index.jsonl"
    index = build_index(folder, index_path)
    lines = {c["test_id"]: c["start_line"] for c in index}
    search = make_search(index)
    template = Path(f"prompts/{args.prompt}.txt").read_text(encoding="utf-8")

    results = []
    for n, criterion in enumerate(criteria, 1):
        print(f"Checking AC{n} ...")
        case = {"workspace": str(folder), "criterion": criterion}
        ws = run_agent.Workspace(case, search, args.k)
        prompt = template.replace("{criterion}", criterion).replace("{max_calls}", str(run_agent.MAX_CALLS))
        verdict, reason, used, steps, _, _ = run_agent.run_case(client, model, prompt, ws)
        results.append({"criterion": criterion, "verdict": verdict, "reason": reason,
                        "tests_used": used, "steps": steps})
        print(f"  {verdict}  ({len(steps)} tool calls)")

    text = report(repo_info, issue, results, model, args.prompt, drafted, lines)
    number = re.search(r"/(?:issues|pull)/(\d+)", issue["link"]) if issue else None
    out = free_path(Path(args.out or f"reports/{repo_info['name']}{'__' + number.group(1) if number else ''}.md"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"\n{text}\nSaved to {out}")


if __name__ == "__main__":
    main()
