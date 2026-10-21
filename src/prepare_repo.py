"""Build the 'covered' and 'not covered' versions of the code for one issue.

Run:    python src/prepare_repo.py psf__requests-2317
        python src/prepare_repo.py --all       # every dev issue in data/chosen_issues.json
        python src/prepare_repo.py --test      # every test-set issue in data/chosen_issues.json
Needs:  data/issues.jsonl (run src/load_swebench.py first) and git installed.
Output: workspace/<instance_id>/covered/      code fix + its tests
        workspace/<instance_id>/not_covered/  code fix only (its tests left out)

The copies have no git history (.git is deleted): the history holds the real fix and its
tests, which the agent must never find. Re-running on an existing copy also deletes its .git.
workspace/_source/ keeps its history, because the copies are cloned from it.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ISSUES = Path("data/issues.jsonl")
CHOSEN = Path("data/chosen_issues.json")
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


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python src/prepare_repo.py <instance_id>  or  --all  or  --test")
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
