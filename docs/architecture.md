# Architecture

How version 1 fits together: which script makes which file, and who owns each step.
The diagrams are [Mermaid](https://mermaid.js.org/): GitHub draws them from the text below, so
edit the text to change them.

## Pipeline

```mermaid
flowchart TB
    swe[("SWE-bench<br/>requests + flask")]

    subgraph data["Data (Isis Eka)"]
        load["load_swebench.py"] --> issues["issues.jsonl<br/>(not uploaded)"]
        issues --> prep["prepare_repo.py"]
        prep --> ws["workspace/ id /<br/>covered + not_covered"]
        issues --> export["export issue text"]
        export --> text["issue_text_v1.jsonl"]
        ws --> build["build_index.py"]
        build --> index["index_v1/<br/>(not uploaded)"]
    end

    subgraph criteria["Criteria (Sammi)"]
        text --> draft["draft + review<br/>acceptance criteria"]
    end

    subgraph engine["Engine (Gabriel)"]
        draft --> cases["cases.jsonl"]
        cases --> run["run_v1.py"]
        search["search_bm25.py<br/>or search_tests.py"] --> run
        index --> search
        ws --> search
        prompt["prompts/verdict_v1.txt"] --> run
        run --> results["results/results.jsonl"]
    end

    subgraph scoring["Scoring (Xiaoning)"]
        labels["labels_v1.jsonl<br/>(private, not uploaded)"] --> eval["src/evaluation/"]
        results --> eval
        eval --> scores["scores + charts<br/>in results/"]
    end

    swe --> load
    issues -. "FAIL_TO_PASS tests" .-> labels
```

The answer key (`labels_v1.jsonl`) only flows into scoring. It never reaches the criteria
step, the search or the model.

## Data model

One row per line in each `.jsonl` file. `case_id` links a case, its answer and its results.

```mermaid
erDiagram
    CHOSEN_ISSUES ||--|| ISSUE_TEXT : "instance_id"
    CHOSEN_ISSUES ||--|{ CASES : "instance_id"
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
        string variant "covered or not_covered"
        string criterion "Given ... when ... then ..."
        string workspace "workspace/id/variant"
        bool reviewed
    }
    LABELS {
        string case_id PK "private answer key"
        string label "covered, partial or not_covered"
        list tests "pytest ids that check it"
        string labeler
        string note
    }
    RESULTS {
        string case_id FK
        string verdict "covered, partial, not_covered or needs_review"
        string reason
        list tests_found "what search returned"
        list tests_used "what the model cited"
        string model
        string prompt
        string search
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

`LABELS` shows the planned one-row-per-criterion format. Until Sammi's criteria are in,
`labels_v1.jsonl` still has one row per issue and variant (`psf__requests-1142-covered`).
`INDEX_CHUNKS` is one file per issue and variant: `data/index_v1/<id>__<variant>.jsonl`.
