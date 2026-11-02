"""AI-draft acceptance criteria from issue text only, with prompts/draft_criteria.txt.

Run:    python src/draft_criteria.py                       # every issue in data/issue_text_v1.jsonl
        python src/draft_criteria.py --issue psf__requests-1142
Needs:  .env with the OpenAI key, or --ollama for local testing
Output: data/criteria_draft.jsonl  (one criterion per line, "reviewed": false)

Drafts must be reviewed by the team before they become real cases. Only instance_id and
problem_statement are read from the input: never feed it patches, tests or FAIL_TO_PASS.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_v1 import ask_model, make_client  # noqa: E402

GIVEN = re.compile(r"\bGiven\b.*?(?=\bGiven\b|\Z)", re.S)


def parse_criteria(text):
    """Return the 'Given ..., when ..., then ...' criteria in a reply ([] for UNCLEAR)."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)  # in case thinking leaks into content
    criteria = []
    for chunk in GIVEN.findall(text):
        chunk = re.sub(r"[*_`]", "", chunk)               # markdown bold/italics
        chunk = re.sub(r"\n\s*(\d+[.)]|[-•]|AC\s*\d+:?)\s*$", "", chunk.rstrip())  # next item's number
        chunk = re.sub(r"\s*\n\s*[-•]\s+(?=(when|then|and)\b)", ", ", chunk, flags=re.I)  # bulleted parts
        chunk = " ".join(chunk.split())
        if re.search(r"\bwhen\b", chunk, re.I) and re.search(r"\bthen\b", chunk, re.I):
            criteria.append(chunk)
    return criteria[:2]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--issues", default="data/issue_text_v1.jsonl")
    p.add_argument("--out", default="data/criteria_draft.jsonl")
    p.add_argument("--issue", action="append", help="only this instance_id (repeatable)")
    p.add_argument("--ollama", nargs="?", const="qwen3:8b", metavar="MODEL",
                   help="use the local Ollama server instead of OpenAI (default qwen3:8b)")
    args = p.parse_args()

    client = make_client(ollama=bool(args.ollama))
    model = args.ollama or os.getenv("OPENAI_MODEL", "gpt-6-luna")
    template = Path("prompts/draft_criteria.txt").read_text(encoding="utf-8")
    with open(args.issues, encoding="utf-8") as f:
        issues = [json.loads(line) for line in f if line.strip()]
    issues = [i for i in issues if not args.issue or i["instance_id"] in args.issue]

    with open(args.out, "w", encoding="utf-8") as out:
        for issue in issues:
            prompt = template.replace("{issue_text}", issue["problem_statement"])
            text, _ = ask_model(client, model, prompt, json_mode=False)
            criteria = parse_criteria(text or "")
            if not criteria:
                print(f"{issue['instance_id']}: no criterion (reply: {(text or '')[:120]!r})")
            for n, criterion in enumerate(criteria, 1):
                out.write(json.dumps({"instance_id": issue["instance_id"], "ac_id": f"ac{n}",
                                      "criterion": criterion, "drafted_by": model,
                                      "reviewed": False}) + "\n")
                print(f"{issue['instance_id']} ac{n}: {criterion}")
    print(f"Saved to {args.out}")


if __name__ == "__main__":
    main()
