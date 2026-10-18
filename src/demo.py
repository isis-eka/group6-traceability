"""A step-by-step walkthrough of version 1 on one case, for a live presentation.

It shows each step of version 1 and waits for Enter between them:
  1. the acceptance criterion
  2. the 3 tests the embedding search finds (id, score, first lines of code)
  3. the AI's verdict, reason and the tests it relied on (one real call, prompt verdict_v1)
  4. the right answer from the answer key, and whether the AI got it right

The answer key is opened only in step 4, after the AI has answered, and is never put in the
prompt. The demo saves nothing: it uses run_v1.py's own functions, so it behaves like a real run.

Run:    python src/demo.py --list                                  # case ids to choose from
        python src/demo.py psf__requests-1142__ac1__covered
        python src/demo.py psf__requests-1142__ac1__covered --no-pause   # no Enter prompts
Needs:  the same as run_v1.py (workspaces, embedding index, OPENAI_API_KEY in .env), plus
        data/labels_v1.jsonl for step 4.
"""
import argparse
import json
import sys
import textwrap
from pathlib import Path

from run_v1 import ask_model, build_prompt, choose_model, load_cases, load_search, make_client, parse_reply

CASES = "data/cases.jsonl"
LABELS = "data/labels_v1.jsonl"
PROMPT = "verdict_v1"
K = 3
CODE_LINES = 15
WIDTH = 88


def heading(step, title):
    print(f"\n{'=' * WIDTH}\n STEP {step}: {title}\n{'=' * WIDTH}")


def wrap(text, indent="  "):
    print(textwrap.fill(text, WIDTH, initial_indent=indent, subsequent_indent=indent))


def pause(enabled):
    if enabled:
        input("\n  (press Enter to continue) ")


def short_name(test_id):
    """tests/test_requests.py::TestRequests::test_x[...] -> test_x"""
    return test_id.split("::")[-1].split("[")[0]


def correct_answer(case):
    """The answer key's row for this case. Labels are per issue and copy for now:
    psf__requests-1142__ac1__covered -> psf__requests-1142-covered (as in evaluate.py)."""
    key = f"{case['instance_id']}-{case['variant']}"
    with open(LABELS, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                if row["case_id"] == key:
                    return row
    return None


def list_cases():
    for case in load_cases(CASES):
        print(case["case_id"])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("case_id", nargs="?")
    p.add_argument("--list", action="store_true", help="show the case ids and exit")
    p.add_argument("--no-pause", action="store_true", help="don't wait for Enter between steps")
    args = p.parse_args()
    if args.list:
        return list_cases()
    if not args.case_id:
        p.error("give a case id, or --list to see them")

    found = load_cases(CASES, [args.case_id])
    if not found:
        sys.exit(f"Unknown case {args.case_id!r}. Run: python src/demo.py --list")
    case = found[0]
    stop = not args.no_pause

    # 1. The requirement
    heading(1, "The requirement")
    print(f"  Issue:  {case['instance_id']}")
    print(f"  Code:   {case['variant']} copy "
          + ("(the fix and its tests)" if case["variant"] == "covered" else "(the fix, its tests removed)"))
    print("  Acceptance criterion:")
    wrap(case["criterion"], "    ")
    pause(stop)

    # 2. Search
    heading(2, f"Search: the {K} tests closest in meaning to the requirement")
    hits = load_search("search_tests")(case, K)
    for n, hit in enumerate(hits, 1):
        print(f"\n  [{n}] {hit['test_id']}   (similarity {hit['score']:.3f})")
        lines = hit["code"].splitlines()
        for line in lines[:CODE_LINES]:
            print(f"      {line}")
        if len(lines) > CODE_LINES:
            print(f"      ... ({len(lines) - CODE_LINES} more lines)")
    pause(stop)

    # 3. The AI's verdict (one call; the prompt holds only the criterion and these tests)
    heading(3, "The AI's verdict")
    model, use_ollama = choose_model(None)
    print(f"  Asking {model} (prompt {PROMPT}) ...")
    template = Path(f"prompts/{PROMPT}.txt").read_text(encoding="utf-8")
    text, usage = ask_model(make_client(ollama=use_ollama), model, build_prompt(template, case["criterion"], hits))
    verdict, reason, tests_used = parse_reply(text)
    print(f"\n  Verdict:  {verdict.upper()}")
    print("  Reason:")
    wrap(reason, "    ")
    print("  Tests relied on: " + (", ".join(short_name(t) for t in tests_used) or "none"))
    print(f"  ({usage.prompt_tokens} tokens in, {usage.completion_tokens} out)")
    pause(stop)

    # 4. The answer key, opened only now
    heading(4, "The right answer (answer key)")
    if not Path(LABELS).exists():
        print(f"  {LABELS} is not here: the answer key is shared privately, not on GitHub.")
        return
    label = correct_answer(case)
    if label is None:
        print(f"  No answer key row for {case['instance_id']} {case['variant']}.")
        return
    right = label["verdict"]
    print(f"  Right answer:  {right.upper()}")
    if label["tests"]:
        print("  Tests that check it: " + ", ".join(short_name(t) for t in label["tests"]))
        found_ids = {short_name(h["test_id"]) for h in hits}
        hit_count = sum(short_name(t) in found_ids for t in label["tests"])
        print(f"  Search found {hit_count} of {len(label['tests'])} of them.")
    print()
    if verdict == right:
        print("  RESULT: the AI got it RIGHT.")
    elif verdict == "covered" and right == "not_covered":
        print("  RESULT: WRONG. False all-clear: the AI said the requirement is tested when it isn't.")
    else:
        print(f"  RESULT: WRONG. The AI said {verdict}, the answer is {right}.")


if __name__ == "__main__":
    main()
