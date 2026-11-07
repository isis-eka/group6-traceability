"""Build the 'covered' and 'not covered' versions of the code for one issue.

Run:    python src/prepare_repo.py psf__requests-2317
        python src/prepare_repo.py --all       # every dev issue in data/chosen_issues.json
        python src/prepare_repo.py --test      # every test-set issue in data/chosen_issues.json
        python src/prepare_repo.py --partial   # partial copies for every issue in data/partial_drops.jsonl
Needs:  data/issues.jsonl (run src/load_swebench.py first) and git installed.
Output: workspace/<instance_id>/covered/      code fix + its tests
        workspace/<instance_id>/not_covered/  code fix only (its tests left out)
        workspace/<instance_id>/partial/      the covered copy minus the tests named in
                                              data/partial_drops.jsonl (git-ignored: it names the
                                              right tests, so treat it like an answer key)
                                              {"instance_id": "...", "drop": ["tests/test_x.py::test_y"],
                                               "remove_lines": {"tests/test_x.py": [171, "340-348"]}}
                                              drop removes whole tests; remove_lines removes single
                                              lines (e.g. one assert) by their number in the covered
                                              copy. Either may be left out.

The copies have no git history (.git is deleted): the history holds the real fix and its
tests, which the agent must never find. Re-running on an existing copy also deletes its .git.
workspace/_source/ keeps its history, because the copies are cloned from it.
"""
import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path

ISSUES = Path("data/issues.jsonl")
CHOSEN = Path("data/chosen_issues.json")
DROPS = Path("data/partial_drops.jsonl")
WORKSPACE = Path("workspace")


def run(cmd, cwd=None, stdin=None):
    # Patches go in as UTF-8 bytes: text mode would use the system codepage (cp1252 on
    # Windows) and write non-ASCII characters in a patch as the wrong bytes.
    data = stdin.encode("utf-8") if stdin is not None else None
    subprocess.run(cmd, cwd=cwd, input=data, check=True)


def load_issue(instance_id):
    with ISSUES.open(encoding="utf-8") as f:
        for line in f:
            issue = json.loads(line)
            if issue["instance_id"] == instance_id:
                return issue
    sys.exit(f"{instance_id} not found in {ISSUES}")


def remove_history(target):
    # onerror: git marks its object files read-only, which stops rmtree on Windows
    def make_writable(func, path, _):
        Path(path).chmod(0o700)
        func(path)
    shutil.rmtree(target / ".git", onerror=make_writable)


def prepare(instance_id):
    issue = load_issue(instance_id)

    # Download each project once and reuse it (e.g. workspace/_source/requests)
    source = WORKSPACE / "_source" / issue["repo"].split("/")[1]
    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", f"https://github.com/{issue['repo']}.git", str(source)])

    for variant in ["covered", "not_covered"]:
        target = WORKSPACE / issue["instance_id"] / variant
        if target.exists():
            if (target / ".git").exists():
                remove_history(target)
                print(f"Already exists, removed its git history: {target}")
            else:
                print(f"Already exists, skipping: {target}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--quiet", str(source.resolve()), str(target)])
        run(["git", "checkout", "--quiet", issue["base_commit"]], cwd=target)
        run(["git", "apply", "-"], cwd=target, stdin=issue["patch"])  # the code fix
        if variant == "covered":
            run(["git", "apply", "-"], cwd=target, stdin=issue["test_patch"])  # its tests
        remove_history(target)
        print(f"Ready: {target}")


def find_test(tree, names):
    """The node for a test id's names (e.g. ["TestX", "test_y"]), or None."""
    body = tree.body
    for name in names:
        node = next((n for n in body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                     and n.name == name), None)
        if node is None:
            return None
        body = node.body
    return node


def line_span(item):
    """171 -> (171, 171); "340-348" -> (340, 348)."""
    first, _, last = str(item).partition("-")
    return int(first), int(last or first)


def make_partial(folder, test_ids, remove_lines):
    """Delete the named tests (decorators included) and the listed lines from the copy's test files.
    Line numbers are the covered copy's, so everything is worked out before anything is deleted."""
    by_file = {}
    for test_id in test_ids:
        path, *names = test_id.split("[")[0].split("::")
        by_file.setdefault(path, {"tests": [], "lines": []})["tests"].append((test_id, names))
    for path, items in remove_lines.items():
        by_file.setdefault(path, {"tests": [], "lines": []})["lines"] += [line_span(i) for i in items]
    for path, todo in by_file.items():
        file = folder / path
        if not file.is_file():
            sys.exit(f"{path}: no file {file}")
        lines = file.read_text(encoding="utf-8").splitlines(keepends=True)
        tree = ast.parse("".join(lines))
        spans = list(todo["lines"])
        for test_id, names in todo["tests"]:
            node = find_test(tree, names)
            if node is None:
                sys.exit(f"{test_id}: not found in {file}")
            spans.append((min([node.lineno] + [d.lineno for d in node.decorator_list]), node.end_lineno))
        spans.sort()
        for (s1, e1), (s2, _) in zip(spans, spans[1:]):
            if s2 <= e1:
                sys.exit(f"{file}: overlapping removals at lines {s1}-{e1} and {s2}")
        if spans and (spans[0][0] < 1 or spans[-1][1] > len(lines)):
            sys.exit(f"{file}: line numbers outside 1-{len(lines)}")
        for start, end in reversed(spans):
            del lines[start - 1:end]
        source = "".join(lines)
        try:
            ast.parse(source)
        except SyntaxError as e:  # e.g. a class or block left empty
            sys.exit(f"Removing {spans} from {file} breaks it: {e}")
        file.write_text(source, encoding="utf-8")


def prepare_partial(instance_id, test_ids, remove_lines):
    covered = WORKSPACE / instance_id / "covered"
    target = WORKSPACE / instance_id / "partial"
    if not covered.is_dir():
        sys.exit(f"Missing {covered}: run python src/prepare_repo.py {instance_id} first")
    if target.exists():
        shutil.rmtree(target)  # rebuilt every time, so an edited drop list always applies
    shutil.copytree(covered, target)
    make_partial(target, test_ids, remove_lines)
    n_lines = sum(e - s + 1 for items in remove_lines.values() for s, e in map(line_span, items))
    print(f"Ready: {target} ({len(test_ids)} test(s) dropped, {n_lines} line(s) removed)")


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python src/prepare_repo.py <instance_id>  or  --all  or  --test  or  --partial")
    if sys.argv[1] == "--partial":
        rows = [json.loads(line) for line in DROPS.open(encoding="utf-8") if line.strip()]
        for row in rows:
            prepare_partial(row["instance_id"], row.get("drop", []), row.get("remove_lines", {}))
        return
    # --all is the dev set only, so nobody downloads the test set's tests by accident
    splits = {"--all": "dev", "--test": "test"}
    if sys.argv[1] in splits:
        for row in json.loads(CHOSEN.read_text(encoding="utf-8")):
            if row["split"] == splits[sys.argv[1]]:
                prepare(row["instance_id"])
    else:
        prepare(sys.argv[1])


if __name__ == "__main__":
    main()
