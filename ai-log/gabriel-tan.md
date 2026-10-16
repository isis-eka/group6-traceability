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
[to fill by Gabriel Tan]

### What I kept or changed
[to fill by Gabriel Tan]

## 2026-10-16 · Local testing on Ollama (qwen3:8b)
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** src/run_v1.py, README.md, CLAUDE.md, AGENTS.md
- **Outcome:** Kept

### What I asked for
Run version 1 on qwen3:8b through my local Ollama instead of the OpenAI API while testing,
switched on with an --ollama flag rather than settings in .env, with a clear error when no
key is set and a long timeout for slow local calls.

### How I checked it
[to fill by Gabriel Tan]

### What I kept or changed
[to fill by Gabriel Tan]

## 2026-10-16 · Resolve merge with the embedding search
- **Tool (model):** Claude Code (Claude Opus 5.5)
- **Files:** AGENTS.md, CLAUDE.md, README.md
- **Outcome:** Kept

### What I asked for
Fix the merge conflicts after pulling Isis's embedding search and dev-set changes: keep her
AGENTS.md-as-single-instructions-file change (CLAUDE.md is now just @AGENTS.md) and add my
run_v1.py commands and notes alongside her build_index.py and search_tests.py ones.

### How I checked it
[to fill by Gabriel Tan]

### What I kept or changed
[to fill by Gabriel Tan]

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
[to fill by Gabriel Tan]

### What I kept or changed
[to fill by Gabriel Tan]
