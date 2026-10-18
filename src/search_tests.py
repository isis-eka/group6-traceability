"""
This file searches the test file embeddings. 
Given a requirement, it returns the tests in one code copy that are closest in meaning,
even when they use different words. The requirement is turned into numbers the same way
as the tests (see build_index.py), and the closest ones win.

Run:    python src/search_tests.py psf__requests-1142 covered "GET requests send no Content-Length"
        python src/run_v1.py --search search_tests      (version 1 with this search)
Needs:  data/index_v1/<id>__<variant>.jsonl (run src/build_index.py first), OPENAI_API_KEY in .env
Use:    from search_tests import search_tests
        search_tests("workspace/psf__requests-1142/covered", "...", k=3)
        -> list of {test_id, file, start_line, end_line, code, score}, best first

Same interface as src/search_bm25.py, so run_v1.py (and later the agent) can use either.
Always returns k results (or every chunk, if the folder has fewer), with no score cut-off.
"""
import json
import sys
from functools import lru_cache
from pathlib import Path

from build_index import INDEX, embed_texts, openai_client


@lru_cache(maxsize=None)
def load_index(instance_id, variant):
    path = INDEX / f"{instance_id}__{variant}.jsonl"
    if not path.exists():
        # An exception, not sys.exit: callers like run_v1.py import this function
        raise FileNotFoundError(f"No index at {path}. Run: python src/build_index.py --only {instance_id}")
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


@lru_cache(maxsize=None)
def client():
    return openai_client()


def search_tests(workspace, criterion, k=3):
    # workspace/<instance_id>/<variant> names the index file
    instance_id, variant = Path(workspace).parts[-2:]
    chunks = load_index(instance_id, variant)
    [q] = embed_texts(client(), [criterion])
    # OpenAI embeddings have length 1, so the dot product is the cosine similarity
    scored = [(sum(a * b for a, b in zip(q, c["embedding"])), c) for c in chunks]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    # "code" is the test source without the "# file: ... | test: ..." header line
    return [{"test_id": c["test_id"], "file": c["file"], "start_line": c["start_line"],
             "end_line": c["end_line"], "code": c["text"].split("\n", 1)[1], "score": round(score, 3)}
            for score, c in scored[:k]]


def main():
    if len(sys.argv) != 4:
        sys.exit('Usage: python src/search_tests.py <instance_id> <covered|not_covered> "<query>"')
    instance_id, variant, query = sys.argv[1:4]
    for hit in search_tests(f"workspace/{instance_id}/{variant}", query):
        print(f"{hit['score']:.3f}  {hit['test_id']}")


if __name__ == "__main__":
    main()
