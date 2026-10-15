"""Build the 'covered' and 'not covered' versions of the code for one issue.

Run:    python src/prepare_repo.py psf__requests-2317
Needs:  data/issues.jsonl (run src/load_swebench.py first) and git installed.
Output: workspace/<instance_id>/covered/      code fix + its tests
        workspace/<instance_id>/not_covered/  code fix only (its tests left out)
"""
import json
import subprocess
import sys
from pathlib import Path

ISSUES = Path("data/issues.jsonl")
WORKSPACE = Path("workspace")


def run(cmd, cwd=None, stdin=None):
    subprocess.run(cmd, cwd=cwd, input=stdin, text=True, check=True)


def load_issue(instance_id):
    with ISSUES.open(encoding="utf-8") as f:
        for line in f:
            issue = json.loads(line)
            if issue["instance_id"] == instance_id:
                return issue
    sys.exit(f"{instance_id} not found in {ISSUES}")


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python src/prepare_repo.py <instance_id>")
    issue = load_issue(sys.argv[1])

    # Download each project once and reuse it (e.g. workspace/_source/requests)
    source = WORKSPACE / "_source" / issue["repo"].split("/")[1]
    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", f"https://github.com/{issue['repo']}.git", str(source)])

    for variant in ["covered", "not_covered"]:
        target = WORKSPACE / issue["instance_id"] / variant
        if target.exists():
            print(f"Already exists, skipping: {target}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--quiet", str(source.resolve()), str(target)])
        run(["git", "checkout", "--quiet", issue["base_commit"]], cwd=target)
        run(["git", "apply", "-"], cwd=target, stdin=issue["patch"])  # the code fix
        if variant == "covered":
            run(["git", "apply", "-"], cwd=target, stdin=issue["test_patch"])  # its tests
        print(f"Ready: {target}")


if __name__ == "__main__":
    main()
