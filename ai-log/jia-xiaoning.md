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
I made deliberate mistakes to the ground truth file such that I would run into an error, then I implemented the file to check that it works well. 

### What I kept or changed
Kept the main structure of my code for the evaluation, but added in the src/evaluation/sanity_check_labels.py just to be extra safe. Also added the extra portion on the bar graphs for visuals.  

---

## 2026-11-01 · Checking for evaluate.py
- **Tool (model):** Doubao (2.31.4_win)
- **Files:** src\evaluation\evaluate.py, comments from group mates
- **Outcome:** Changed

### What I asked for
Asked to check for any holes in the code outline. Model replied that it was fine but just to change parts on evaluation results. 

### How I checked it
Ran the code again to check for differences.

### What I kept or changed
I changed 
OUTPUT_CSV = "results/evaluation_summary.csv"
AGG_CSV = "results/aggregated_metrics.csv"
to 
file_name = os.path.splitext(os.path.basename(RESULTS_PATH))[0]
OUTPUT_CSV = f"results/{file_name}_evaluation_summary.csv"
AGG_CSV = f"results/{file_name}_aggregated_metrics.csv"

to prevent the evaluation from being overwritten every time I run the evaluator in order to comapre V1, V2, V3 and no-retrieval baseline better. 

---

## 2026-11-02 · Catching key points for dev_answer_keys
- **Tool (model):** ChatGPT (GPT-6) 
- **Files:** data/cases.jsonl, labels_dev.jsonl
- **Outcome:** Changed

### What I asked for
I asked it to pull out the key points for me to draft the answer keys for the different requests from the criteria that were drafted from my teammates.  

### How I checked it
Verified by running checks on sanity. 

### What I kept or changed
Used information given to me 

---

## 2026-11-05 · Catching key points to work on labels from data/criteria_test_draft.jsonl 
- **Tool (model):** ChatGPT (GPT-6) 
- **Files:** data/criteria_test_draft.jsonl
- **Outcome:** Changed

### What I asked for
I asked it for code to check relevant tests and to check the variant of the different instance_id.   

### How I checked it
Verified by running checks on sanity. 

### What I kept or changed
Used information given to me 