# AI Use Log: Your Name

<!--
Starter file. Copy it to ai-log/<first-last>.md (e.g. isis-eka.md) and replace the example.
- One entry per task, not per prompt. Add new entries at the bottom.
- Commit each entry in the same commit as the work it describes, with an
  `Assisted-by: <tool> (<model>)` trailer (a tool's own Co-Authored-By line also counts).
- Outcome is Kept, Changed or Rejected. Rejected entries can be committed with no code.
- "How I checked it" matters most: say what you ran or reviewed, and what you found.
Check your file with: python tools/ai_disclosure.py check-logs
-->

## 2026-10-12 · Retrieval pipeline skeleton
- **Tool (model):** Claude Code (Claude Sonnet 4.5)
- **Files:** src/retrieval/pipeline.py, tests/test_chunking.py
- **Outcome:** Changed

### What I asked for
A skeleton for the retrieval pipeline: document loading, chunking, embedding and a top-k
query function.

### How I checked it
Ran the unit tests, which passed. Reviewing the chunking logic by hand showed that the
overlap was measured in characters rather than tokens, so chunks near the limit were cut short.

### What I kept or changed
Kept the structure and the loader. Rewrote the chunk-overlap handling to count tokens and
added a test for chunks at the size limit.
