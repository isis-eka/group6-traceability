# AI Use Log: Gabriel Tan

## 2026-10-16 · Version 1 runner and keyword test search
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** src/run_v1.py, src/search_bm25.py, .githooks/commit-msg, tools/ai_disclosure.py, README.md, CLAUDE.md, AGENTS.md
- **Outcome:** Kept

### What I asked for
Review the repo against our revised proposal, then build the version 1 script: criterion ->
top 3 similar tests -> one LLM call with prompts/verdict_v1.txt -> a line in
results/results.jsonl. Add a BM25 keyword search over test functions as a stand-in until the
embedding index is ready (and as the BM25 baseline later). Fix the commit hook, which picked the
Windows Store python3 stub, and the log check, which read staged files as cp1252 on Windows;
both blocked every commit on my machine.

### How I checked it
ran python src/run_v1.py --dry-run --limit 1 and read the printed prompt to check it held the criterion, the top 3 tests and the verdict_v1 instructions. ran search_bm25.py on a few criteria and checked the returned tests were relevant. then I made a commit to confirm the hook and ai_disclosure.py no longer blocked it.

### What I kept or changed
kept the runner, the BM25 search and both Windows fixes as written. BM25 is only a stand-in until the embedding index is ready, and it’ll be the baseline later.

## 2026-10-16 · Local testing on Ollama (qwen3:8b)
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** src/run_v1.py, README.md, CLAUDE.md, AGENTS.md
- **Outcome:** Kept

### What I asked for
Run version 1 on qwen3:8b through my local Ollama instead of the OpenAI API while testing,
switched on with an --ollama flag rather than settings in .env, with a clear error when no
key is set and a long timeout for slow local calls.

### How I checked it
ran python src/run_v1.py --ollama on the dev cases (results in results/results_qwen_test.jsonl, 16 rows). checked that every row had a valid verdict, a reason and the tests it used, and that each row recorded qwen3:8b as the model. I also ran it without a key to see the error message.

### What I kept or changed
Kept. These rows are for testing only

## 2026-10-16 · Resolve merge with the embedding search
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** AGENTS.md, CLAUDE.md, README.md
- **Outcome:** Kept

### What I asked for
Fix the merge conflicts after pulling Isis's embedding search and dev-set changes: keep her
AGENTS.md-as-single-instructions-file change (CLAUDE.md is now just @AGENTS.md) and add my
run_v1.py commands and notes alongside her build_index.py and search_tests.py ones.

### How I checked it
looked through the merged AGENTS.md, CLAUDE.md and README.md to confirm Isis’s change was kept, my run_v1.py notes were there, and no conflict markers were left.

### What I kept or changed
kept the merge as is

## 2026-10-17 · Embedding search by default, keyword search and Ollama as fallbacks
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** src/run_v1.py, AGENTS.md, README.md
- **Outcome:** Kept

### What I asked for
Let run_v1.py use Isis's embedding search (src/search_tests.py, called with instance_id and
variant) as well as the keyword search (called with the workspace folder). Make the embedding
search the default, with keyword search as the fallback when there is no OpenAI key or index,
and Ollama as a flag or the fallback when there is no OpenAI key.

### How I checked it
ran run_v1.py with the index in data/index_v1/ and confirmed it used search_tests. I then ran it with no OpenAI key (or no index) and checked it printed the message and fell back to BM25 or Ollama. I also checked each result row recorded the search and model actually used.

### What I kept or changed
Kept. works as intended

## 2026-10-17 · Show the model at the start of run_v1.py
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** src/run_v1.py
- **Outcome:** Kept

### What I asked for
When run_v1.py starts, print the model being used, so it is clear whether a run is on OpenAI
or the Ollama fallback.

### How I checked it
ran run_v1.py --dry-run with and without --ollama and checked the first line showed the right model, provider, search, prompt and number of cases.

### What I kept or changed
kept all

## 2026-10-17 · Fix non-ASCII characters in patches in prepare_repo.py
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** src/prepare_repo.py
- **Outcome:** Kept

### What I asked for
Fix build_index.py --dry-run failing on the workspaces. prepare_repo.py sent patches to
git apply as text in the Windows codepage (cp1252), so the u"ööö" test in
psf__requests-2931's covered copy was written as invalid UTF-8 and the index builder could
not read it. Patches now go in as UTF-8 bytes; the 2931 workspace was rebuilt.

### How I checked it
deleted workspace/psf__requests-2931 and reran prepare_repo.py. The u"ööö" test then read as valid UTF-8, and build_index.py --dry-run finished without the crash.

### What I kept or changed
kept. told the team to rebuild their 2931 workspace

## 2026-10-31 · Version 3: the agent (run_agent.py)
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** src/run_agent.py, prompts/agent_v1.txt, results/dev/v3/embedding.jsonl, docs/decisions.md, AGENTS.md
- **Outcome:** Kept

### What I asked for
Build version 3, the agent: the AI gets three read-only tools (search_tests, grep, read_file)
and decides what to read, up to 10 tool calls per case, then gives a verdict. The limits are
enforced in code (tool-call limit, paths kept inside the case folder, no .git, 200-line reads).
Written as our own loop on the OpenAI Responses API, reusing run_v1.py's helpers and result
format, with prompt agent_v1.txt based on verdict_v2's rules. Then run it on the 24 dev cases.

### How I checked it
ran the new agent version on 1 case to first verify the tool calling loop. it had a bug that caused it to not complete the call and got stuck.
reprompt with what i observed to fined the issue, claude pointed out the issue and fixed it. reran the 1 case then with the full
dev set after confirming it worked with the 1 case.

### What I kept or changed
changed the tool calling loop to fix the bug and kept the updated code.

## 2026-11-02 · No-retrieval baseline
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** prompts/no_retrieval_v1.txt, src/run_v1.py, results/dev/no_retrieval/none.jsonl, docs/decisions.md, AGENTS.md
- **Outcome:** Kept

### What I asked for
Build the no-retrieval baseline from the plan: the AI sees only the acceptance criterion, no
tests or code, and must pick covered, partial or not_covered. Added `--search none` to
run_v1.py and the prompt no_retrieval_v1.txt, then ran it on the 24 dev cases.

### How I checked it
ran and skimmed through code to verify it did not read the tests or code.

### What I kept or changed
correctly implemented, ran as expected, kept

## 2026-11-02 · End-user command trace.py (repo link + issue -> traceability report)
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** src/trace.py, README.md, docs/decisions.md, AGENTS.md
- **Outcome:** Kept

### What I asked for
An end-user command so the tool works on any project, not only our prepared SWE-bench copies.
It takes a GitHub repo link or a local folder, and a GitHub issue (link or number), a text file
or typed criteria. It drafts acceptance criteria from the issue text, runs the agent on each one
and writes a Markdown traceability report (verdict, tests cited, reason, summary, next step).
Also a README section with runnable examples.

### How I checked it
ran it with python src/trace.py --repo https://github.com/pallets/flask --issue 5014
checked results correct in the reports/pallets__flask__5014.md

### What I kept or changed
worked well results as expected, kept

## 2026-11-09 · Test-set runs (V3 agent + no-retrieval baseline) and false all-clear fix in evaluate.py
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** results/test/v3/, results/test/no_retrieval/, src/evaluation/evaluate.py
- **Outcome:** Kept

### What I asked for
Check that the test-set setup was complete, then run the agent (V3) and the no-retrieval
baseline on gpt-6-luna: the 44 covered/not_covered cases, and the 4 partial cases into
separate files (partial_*.jsonl). Score them with evaluate.py against labels_test.jsonl.
Then fix a bug the scoring showed: false all-clear only counted `covered` when the key says
`not_covered`; it now also counts `covered` when the key says `partial` (line 113), matching
the plan's definition. All four test results files were rescored.

### How I checked it
checked throught he results, looked through the code for the bug pointed out in evaluate.
reran results to verify bug fix

### What I kept or changed
implemented fix and kept updated changes

## 2026-11-09 · trace.py: numbered report files and the agent_v2 prompt
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** src/trace.py, README.md
- **Outcome:** Kept

### What I asked for
Stop trace.py replacing an existing report: a rerun now saves the next free number
(`reports/<repo>__<issue>_2.md`, `_3.md`, ...), also for `--out`. Switch its agent prompt from
`agent_v1` to `prompts/agent_v2.txt`, with a `--prompt` option to pick another, and show the
prompt name in the report header. The evaluation (run_agent.py, results/) is unchanged.

### How I checked it
ran trace multiple times to ensure no overwriting, checked the code changes to verify calls to agent_v1 were changed to v2

### What I kept or changed
worked as expectedf, kept

## 2026-11-10 · Dev reruns with the new prompts, and trace.py back to agent_v1
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** src/trace.py, README.md
- **Outcome:** Changed

### What I asked for
Rerun the dev set with the new prompts (V1 and V2 with verdict_v3, V3 with agent_v2) on
gpt-6-luna and compare them with the frozen prompts. All three scored lower on the 24 main
cases (V1 0.46 -> 0.42, V2 0.58 -> 0.46, V3 0.83 -> 0.54), so switch trace.py's default agent
prompt back to agent_v1, the one evaluated (--prompt agent_v2 still picks the new one). The
dev index and the psf__requests-4718 copies had to be rebuilt first.

### How I checked it
reran trace on dev set, compared results

### What I kept or changed
results were worse off with the new prompts, switched back to agent_v1 and verdict_v2

## 2026-11-10 · README: demo video link and sample reports
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** README.md, reports/demo-shop.md, reports/demo-shop_2.md, reports/pallets__flask__5014.md
- **Outcome:** Kept

### What I asked for
Update the README with the YouTube demo video (https://youtu.be/DDAHtk_iD8k) and the other
demo results: a table of the three reports from the demo runs, and a note that the two
demo-shop runs differ on AC1. The 397 MB video file is left out of the repo (over GitHub's
100 MB limit); the README links to YouTube instead.

### How I checked it
read through updated section, verified youtube link worked

### What I kept or changed
kept most, edited sections to mention the different in the 2nd demorepo run.