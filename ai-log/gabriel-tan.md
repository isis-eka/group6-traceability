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
