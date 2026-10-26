"""Version 1 of the tool: is each acceptance criterion tested?

For each case, search finds the 3 tests most related to the criterion, then the AI reads
the criterion and those tests once and answers covered, partial, not_covered or
needs_review, with a short reason. The answers are saved for scoring.


Run:    python src/run_v1.py                      # every case in data/cases.jsonl
        python src/run_v1.py --case psf__requests-1142__ac1__covered
        python src/run_v1.py --dry-run --limit 1  # print the prompt, no API call
        python src/run_v1.py --ollama             # local Ollama, qwen3:8b (or --ollama <model>)
Needs:  data/cases.jsonl, the case workspaces (src/prepare_repo.py), the embedding index
        (src/build_index.py) and .env with OPENAI_API_KEY.
Defaults: embedding search (search_tests) and the OpenAI model from .env. Fallbacks, each
        with a warning: no key or no index -> keyword search (search_bm25); no key -> local
        Ollama. Every result row records the search and model actually used.
Output: results/results.jsonl by default; use --out results/<split>/<round>/<search>.jsonl,
        e.g. --out results/dev/v2/embedding.jsonl (one line per case; cases already run with the same
        version, model, prompt and search are skipped, so a failed run can be resumed)

Never reads data/labels*.jsonl: scoring is a separate step.
"""
import argparse
import importlib
import inspect
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

VERSION = "v1"
VERDICTS = {"covered", "partial", "not_covered", "needs_review"}
SRC = Path(__file__).parent
OLLAMA_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "qwen3:8b"


def load_cases(path, only=None):
    with open(path, encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]
    for case in cases:
        # cases.jsonl schema is still being agreed: accept a workspace path or build it
        case.setdefault("workspace", f"workspace/{case.get('instance_id')}/{case.get('variant')}")
    return [c for c in cases if not only or c["case_id"] in only]


def format_tests(hits):
    if not hits:
        return "(no tests found)"
    return "\n\n".join(f"### {h['test_id']}\n```python\n{h.get('code') or h['text']}\n```" for h in hits)


def load_search(name):
    """Return search(case, k) for a search module in src/.

    search_tests.py (embedding index) is keyed by issue and variant; search_bm25.py and any
    other module by workspace folder. Both return [{"test_id", ..., "code" or "text"}].
    """
    sys.path.insert(0, str(SRC))
    search_tests = importlib.import_module(name).search_tests
    if list(inspect.signature(search_tests).parameters)[:2] == ["instance_id", "variant"]:
        return lambda case, k: search_tests(case["instance_id"], case["variant"], case["criterion"], k=k)
    return lambda case, k: search_tests(case["workspace"], case["criterion"], k=k)


def build_prompt(template, criterion, hits):
    # str.replace, not str.format: the template contains a literal JSON example
    return template.replace("{criterion}", criterion).replace("{tests}", format_tests(hits))


def parse_reply(text):
    """Return (verdict, reason, tests_used). Bad output becomes needs_review, not a crash."""
    try:
        reply = json.loads(text)
        verdict = str(reply.get("verdict", "")).strip().lower()
        if verdict not in VERDICTS:
            raise ValueError(f"unknown verdict {verdict!r}")
        return verdict, str(reply.get("reason", "")), list(reply.get("tests_used") or [])
    except (ValueError, AttributeError, TypeError) as e:
        return "needs_review", f"Unusable model output ({e}): {text[:300]}", []


def has_openai_key():
    load_dotenv()
    return os.getenv("OPENAI_API_KEY", "").strip() not in ("", "paste-key-here")


def warn(message):
    print(f"NOTE: {message}", file=sys.stderr)


def choose_search(name, cases):
    """The embedding search if it can run for every case, else the keyword search."""
    if name != "search_tests":
        return name
    if not has_openai_key():
        reason = "no OPENAI_API_KEY to embed the criteria"
    else:
        sys.path.insert(0, str(SRC))
        from build_index import INDEX
        missing = [c for c in cases if not (INDEX / f"{c['instance_id']}__{c['variant']}.jsonl").exists()]
        if not missing:
            return name
        reason = (f"no index for {len(missing)} case(s), e.g. {missing[0]['instance_id']} "
                  f"{missing[0]['variant']}; run src/build_index.py")
    warn(f"embedding search unavailable ({reason}), using keyword search (search_bm25)")
    return "search_bm25"


def choose_model(ollama):
    """(model, use_ollama): Ollama with --ollama or when there is no key, else OpenAI."""
    if ollama:
        return ollama, True
    if has_openai_key():
        return os.getenv("OPENAI_MODEL", "gpt-6-luna"), False
    warn(f"no OPENAI_API_KEY, using local Ollama ({OLLAMA_MODEL}); results are for testing only")
    return OLLAMA_MODEL, True


def make_client(ollama=False):
    """OpenAI client, or with ollama=True the local Ollama server (same API, no key)."""
    from openai import OpenAI
    if ollama:
        try:
            urllib.request.urlopen(OLLAMA_URL.removesuffix("/v1") + "/api/version", timeout=5)
        except OSError:
            sys.exit(f"Ollama is not running at {OLLAMA_URL}: start it, or put OPENAI_API_KEY in .env")
        return OpenAI(base_url=OLLAMA_URL, api_key="ollama", timeout=600)  # local calls can take minutes
    if not has_openai_key():
        sys.exit("No OPENAI_API_KEY: copy .env.example to .env and paste the key "
                 "(or use --ollama / --dry-run)")
    return OpenAI()


def ask_model(client, model, prompt, json_mode=True):
    extra = {"response_format": {"type": "json_object"}} if json_mode else {}
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **extra,
            )
            return resp.choices[0].message.content, resp.usage
        except Exception as e:  # rate limits, timeouts: retry, then give up on this case
            if attempt == 2:
                raise
            print(f"  API error ({e}), retrying", file=sys.stderr)
            time.sleep(5 * (attempt + 1))


def default_build(template, case, hits):
    """(prompt, extra fields for the result row). run_v2.py passes its own."""
    return build_prompt(template, case["criterion"], hits), {}


def main(version=VERSION, build=default_build, doc=__doc__):
    p = argparse.ArgumentParser(description=doc, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cases", default="data/cases.jsonl")
    p.add_argument("--out", default="results/results.jsonl")
    p.add_argument("--prompt", default="verdict_v1", help="file name in prompts/, without .txt")
    p.add_argument("--search", default="search_tests",
                   help="search module in src/: search_tests (embedding index, default; falls back "
                        "to search_bm25 without an OpenAI key or index) or search_bm25 (keyword)")
    p.add_argument("--k", type=int, default=3)
    p.add_argument("--case", action="append", help="run only this case_id (repeatable)")
    p.add_argument("--limit", type=int)
    p.add_argument("--dry-run", action="store_true", help="print prompts, call no API, save nothing")
    p.add_argument("--ollama", nargs="?", const=OLLAMA_MODEL, metavar="MODEL",
                   help=f"use the local Ollama server instead of OpenAI, for testing only "
                        f"(default model {OLLAMA_MODEL}; also used when there is no OpenAI key)")
    args = p.parse_args()

    template = Path(f"prompts/{args.prompt}.txt").read_text(encoding="utf-8")
    cases = load_cases(args.cases, args.case)[:args.limit]
    search_name = choose_search(args.search, cases)
    search = load_search(search_name)
    model, use_ollama = choose_model(args.ollama)

    out = Path(args.out)
    run = {"version": version, "model": model, "prompt": args.prompt, "search": search_name}
    done = set()
    if out.exists() and not args.dry_run:
        with out.open(encoding="utf-8") as f:
            done = {r["case_id"] for r in map(json.loads, filter(str.strip, f))
                    if all(r.get(k) == v for k, v in run.items())}

    client = None
    if not args.dry_run:
        client = make_client(ollama=use_ollama)
        out.parent.mkdir(exist_ok=True)
    print(f"Model: {model} ({'Ollama' if use_ollama else 'OpenAI'}), search: {search_name}, "
          f"prompt: {args.prompt}, cases: {len(cases)}")

    counts = {}
    for case in cases:
        if case["case_id"] in done:
            print(f"skip (already run): {case['case_id']}")
            continue
        if not Path(case["workspace"]).is_dir():
            print(f"skip (no workspace, run prepare_repo.py): {case['workspace']}", file=sys.stderr)
            continue
        hits = search(case, args.k)
        prompt, extra = build(template, case, hits)
        if args.dry_run:
            print(f"===== {case['case_id']}\n{prompt}\n")
            continue

        text, usage = ask_model(client, model, prompt)
        verdict, reason, tests_used = parse_reply(text)
        row = {
            "case_id": case["case_id"],
            "verdict": verdict,
            "reason": reason,
            "tests_found": [h["test_id"] for h in hits],
            "tests_used": tests_used,
            **extra,
            **run,
            "tool_calls": 0,
            "tokens_in": usage.prompt_tokens,
            "tokens_out": usage.completion_tokens,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        with out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        counts[verdict] = counts.get(verdict, 0) + 1
        print(f"{verdict:<13} {case['case_id']}")

    if counts:
        print(f"Saved to {out}: " + ", ".join(f"{v} {n}" for v, n in sorted(counts.items())))


if __name__ == "__main__":
    main()
