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

## 2026-11-05 · Identifying relevant tests and instance variants for labelling
- **Tool (model):** ChatGPT (GPT-6) 
- **Files:** data/criteria_test_draft.jsonl
- **Outcome:** Changed

### What I asked for
I asked ChatGPT to help identify relevant tests for the acceptance criteria and determine the different variants associated with each instance_id. 

### How I checked it
I independently ran sanity checks to verify the suggested information and checked that the identified tests and instance variants were relevant to the corresponding criteria.

### What I kept or changed
I used the information provided by ChatGPT as a reference when working on the labels.

---

## 2026-11-06 · Developing presentation slide content and structure
- **Tool (model):** ChatGPT (GPT-6) 
- **Files:** Group 6 traceability evaluation presentation slides
- **Outcome:** Changed

### What I asked for
I asked ChatGPT to help organise the presentation into a logical slide structure and identify the key information that should be included in each section.

### How I checked it
I compared the suggested slide content against our actual project implementation, dataset information and evaluation results. I also checked that the information was consistent with the work completed by my group.

### What I kept or changed
I used the suggested structure and explanations to organise my slides.

---

## 2026-11-08 · Preparing partial repository copies
- **Tool (model):** ChatGPT (GPT-6) 
- **Files:** data/partial_drops.jsonl, src/prepare_repo.py, relevant files under workspace/, proposed entries for labels_dev.jsonl and labels_test.jsonl
- **Outcome:** Changed

### What I asked for
I asked ChatGPT to help organise the partial-coverage instructions for seven selected issues, including identifying which assertions or tests should be removed.

I also asked for assistance formatting the corresponding nine proposed answer-key entries using the required JSONL structure, including the case_id, verdict, tests and note fields.

### How I checked it
I independently reviewed the proposed test removals and ran the repository preparation script:

python src/prepare_repo.py --partial

I checked the terminal output to confirm that all seven partial repository copies were generated successfully.

### What I kept or changed
I used the suggested instructions. The entries were prepared as drafts.

---

## 2026-11-08 · Refining presentation slides
- **Tool (model):** ChatGPT (GPT-6) 
- **Files:** Group 6 traceability evaluation presentation slides
- **Outcome:** Changed

### What I asked for
I asked ChatGPT to review specific slide content, clarify technical explanations and improve the wording of the presentation.

I also asked it to help check the consistency of figures and explanations across different slides, particularly the distinction between partial-coverage cases and the number of partially labelled cases.

### How I checked it
I cross-checked the suggested changes against our evaluation data.

### What I kept or changed
I used the suggestions to improve the clarity and consistency of the slides.