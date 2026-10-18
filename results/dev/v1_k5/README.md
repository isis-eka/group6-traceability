# Dev set, version 1 with 5 tests shown (2026-10-18)

> **A one-off variation of [`dev/v1`](../v1/README.md).** Same 24 cases, model (`gpt-6-luna`), prompt
> (`verdict_v1`) and embedding search. The only change: search shows the AI **5 tests instead of 3**
> (`--k 5`). Like `dev/v1`, this is a pipeline test: the answer key has no `partial` cases yet.

The question: if the right test is often missed in the top 3, does showing 5 help?

```bash
python src/run_v1.py --k 5 --out results/dev/v1_k5/embedding.jsonl
python src/evaluation/evaluate.py results/dev/v1_k5/embedding.jsonl
```

## Results

| Metric | 3 tests (`dev/v1`) | 5 tests (this run) |
|---|---|---|
| Verdict accuracy | 0.375 (9 / 24) | 0.375 (9 / 24) |
| Test recall | 0.778 | 0.806 |
| Test precision | 0.278 | 0.183 |
| False alarm rate | 0.042 (1 case) | 0.000 |
| False all-clear rate | 0.000 | **0.042 (1 case)** |
| `partial` answers | 14 | 14 |

Only 5 of 24 cases came out differently:

| Case | Right answer | 3 tests | 5 tests |
|---|---|---|---|
| 1537 ac1, not_covered | not_covered | partial | not_covered ✅ |
| 1635 ac1, covered | covered | not_covered | partial (right test still not found) |
| 4718, not_covered | not_covered | not_covered | partial ❌ |
| 3718, not_covered | not_covered | partial | **covered** ❌ (false all-clear) |
| 4106, covered | covered | partial | partial (one more right test found) |

## What we learned

- **Showing more tests barely helps.** The right test is usually in the top 3 or not found at all:
  1635 ac1's right test is still missing at 5. Recall rose by one test (4106).
- **More tests add noise.** Accuracy stayed the same, `partial` stayed at 14, and one case became a
  false all-clear. **We keep k = 3.** Fixing the prompt's definition of `partial` matters more.
- **3718 may show a gap in the answer key.** On the not_covered copy, the AI said `covered` because of
  `test_response_json_when_content_is_None`, an older test that is not part of the fix. It sets the raw
  stream to `None` and reads `response.content`, so it may partly check this criterion. Our rule
  "the fix's tests removed means not covered" doesn't hold when older tests overlap. Xiaoning to check
  this case when adding `partial` labels.
