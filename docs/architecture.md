# Architecture

How the project fits together: which script makes which file, and who owns each step.
It covers the evaluation (no-retrieval baseline and versions 1–3 on the dev and test sets) and the
end-user tool `trace.py`. The diagrams are [Mermaid](https://mermaid.js.org/): GitHub draws them
from the text below, so edit the text to change them.

## Pipeline

```mermaid
flowchart TB
    swe[("SWE-bench<br/>requests + flask")]

    subgraph data["Data (Isis Eka)"]
        load["load_swebench.py"] --> issues["issues.jsonl<br/>(not uploaded)"]
        issues --> pick["pick_test_set.py"]
        pick --> chosen["chosen_issues.json<br/>10 dev + 18 test"]
        chosen --> prep["prepare_repo.py"]
        issues --> prep
        prep --> ws["workspace/ id /<br/>covered, not_covered, partial<br/>(no git history)"]
        drops["partial_drops.jsonl<br/>(private, not uploaded)"] --> prep
        issues --> export["export_issue_text.py"]
        export --> text["issue_text.jsonl<br/>issue_text_test.jsonl"]
        ws --> build["build_index.py"]
        build --> index["index_v1/<br/>(not uploaded)"]
    end

    subgraph criteria["Criteria (Sammi)"]
        text --> draft["AI draft + human review<br/>prompts/draft_criteria.txt"]
    end

    subgraph engine["Engine (Gabriel; version 2: Isis)"]
        draft --> mk["make_cases.py"]
        mk --> cases["cases.jsonl (dev)<br/>cases_test.jsonl (test)"]
        search["search_tests.py (embedding)<br/>or search_bm25.py"]
        index --> search
        ws --> search
        cases --> base["baseline: run_v1.py --search none<br/>criterion only"]
        cases --> v1["V1: run_v1.py<br/>top 3 tests"]
        cases --> v2["V2: run_v2.py<br/>V1 + the code the tests call"]
        cases --> v3["V3: run_agent.py<br/>agent: search_tests, grep, read_file<br/>max 10 calls"]
        search --> v1
        search --> v2
        search --> v3
        ws --> v2
        ws --> v3
        base --> results["results/ split / round /<br/>search.jsonl"]
        v1 --> results
        v2 --> results
        v3 --> results
    end

    subgraph scoring["Scoring (Xiaoning)"]
        labels["labels_dev.jsonl, labels_test.jsonl<br/>(private, not uploaded)"] --> eval["src/evaluation/evaluate.py"]
        results --> eval
        eval --> scores["summary + aggregated metrics CSVs<br/>next to the results; plot_metrics.py charts"]
    end

    swe --> load
    ws -. "the fix's own tests" .-> labels
```

The answer keys (`labels_dev.jsonl`, `labels_test.jsonl`) and the partial drop list only flow into
scoring and `prepare_repo.py`. They never reach the criteria step, the search or the model. Prompts
live in `prompts/` (`no_retrieval_v1`, `verdict_v1`, `verdict_v2`, `agent_v1`) and are frozen since
31 Oct.

## The end-user tool

`trace.py` reuses version 3 on any repository, outside the evaluation (decision 15). It never
reads `data/` and writes nothing to `results/`.

```mermaid
flowchart LR
    repo["--repo<br/>GitHub link or local folder"] --> clone["shallow clone into<br/>workspace/_trace/"]
    issue["--issue<br/>link, number or text file"] --> crit{"criteria given?"}
    crit -- "no" --> draft["draft criteria<br/>prompts/draft_criteria.txt"]
    crit -- "yes" --> agent
    draft --> agent["V3 agent per criterion<br/>(same prompt and limits)"]
    clone --> agent
    agent --> report["reports/ repo __ issue .md"]
```

## Data model

One row per line in each `.jsonl` file. `case_id` links a case, its answer and its results.

```mermaid
erDiagram
    CHOSEN_ISSUES ||--|| ISSUE_TEXT : "instance_id"
    CHOSEN_ISSUES ||--|{ CASES : "instance_id"
    CHOSEN_ISSUES ||--o| PARTIAL_DROPS : "instance_id"
    CASES ||--|| LABELS : "case_id"
    CASES ||--o{ RESULTS : "case_id"
    CHOSEN_ISSUES ||--|{ INDEX_CHUNKS : "instance_id + variant"

    CHOSEN_ISSUES {
        string instance_id PK "psf__requests-1142"
        string split "dev or test"
    }
    ISSUE_TEXT {
        string instance_id PK
        string problem_statement "the GitHub issue text"
    }
    CASES {
        string case_id PK "psf__requests-1142__ac1__covered"
        string instance_id FK
        string variant "covered, not_covered or partial"
        string criterion "Given ... when ... then ..."
        string workspace "workspace/id/variant"
    }
    PARTIAL_DROPS {
        string instance_id PK "private"
        list drop "test ids removed from the covered copy"
        dict remove_lines "file to line numbers or ranges"
    }
    LABELS {
        string case_id PK "private answer key"
        string verdict "covered, partial or not_covered"
        list tests "pytest ids that check it"
        string note
    }
    RESULTS {
        string case_id FK
        string verdict "covered, partial, not_covered or needs_review"
        string reason
        list tests_found "what search returned"
        list tests_used "what the model cited"
        string version "v1, v2 or v3"
        string model
        string prompt
        string search
        int tool_calls
        list code_added "version 2 only"
        list steps "version 3 only"
        int tokens_in
        int tokens_out
        string timestamp
    }
    INDEX_CHUNKS {
        string test_id "tests/file.py::Class::test_name"
        string file
        int start_line
        int end_line
        string text
        list embedding
    }
```

`LABELS` replaced the first key, `labels_v1.jsonl` (one row per issue and copy), on the dev set
(decision 17); the test set uses `labels_test.jsonl` in the same format. `INDEX_CHUNKS` is one file
per issue and variant: `data/index_v1/<id>__<variant>.jsonl`.
