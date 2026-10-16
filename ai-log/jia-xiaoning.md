# AI Use Log: Your Name

<!--
Starter file. Copy it to ai-log/<first-last>.md (e.g. isis-eka.md) and replace the example.
- One entry per task, not per prompt. Add new entries at the bottom.
- Commit each entry in the same commit as the work it describes, with an
  `Assisted-by: <tool> (<model>)` trailer (a tool's own Co-Authored-By line also counts).
- Outcome is Kept, Changed or Rejected. Rejected entries can be committed with no code.
- "How I checked it" matters most: say what you ran or reviewed, and what you found.
  Write it and "What I kept or changed" yourself. Agents leave both as
  [to fill by <your name>] for you to replace.
Check your file with: python tools/ai_disclosure.py check-logs
-->

## 2026-10-16 · Checking the Asnwer Key
- **Tool (model):** Doubao (2.31.4_win)
- **Files:** data/labels_v1.jsonl, task outline, raw code for evaluation
- **Outcome:** Changed

### What I asked for
I asked it to check if there was anything missing to ensure that the model will work well after passing in the results and ground truth. 

### How I checked it
Using another coding software, after uploading the folders in, I deliberately put some errors into data/labels_v1.jsonl. 

### What I kept or changed
Kept the main structure of my code for the evaluation, but added in the src/evaluation/sanity_check_labels.py just to be extra safe. 
