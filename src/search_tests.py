"""Find the test functions most similar in meaning to a query, in one workspace copy.

Run:    python src/search_tests.py psf__requests-1142 covered "GET requests send no Content-Length"
Needs:  data/index_v1/<id>__<variant>.jsonl (run src/build_index.py first), OPENAI_API_KEY in .env
Use:    from search_tests import search_tests
        search_tests("psf__requests-1142", "covered", "...", k=3)
        -> list of {test_id, file, start_line, end_line, text, score}, best first

Version 1 calls this directly; later the agent's search_tests tool wraps it.
Always returns k results (or every chunk, if the folder has fewer), with no score cut-off.
"""
import json
import sys
from functools import lru_cache

from build_index import INDEX, embed_texts, openai_client


@lru_cache(maxsize=None)
def load_index(instance_id, variant):
    path = INDEX / f"{instance_id}__{variant}.jsonl"
    if not path.exists():
        sys.exit(f"No index at {path}. Run: python src/build_index.py --only {instance_id}")
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


@lru_cache(maxsize=None)
def client():
    return openai_client()


def search_tests(instance_id, variant, query, k=3):
    chunks = load_index(instance_id, variant)
    [q] = embed_texts(client(), [query])
    # OpenAI embeddings have length 1, so the dot product is the cosine similarity
    scored = [(sum(a * b for a, b in zip(q, c["embedding"])), c) for c in chunks]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [{**{key: c[key] for key in ("test_id", "file", "start_line", "end_line", "text")},
             "score": score} for score, c in scored[:k]]


def main():
    if len(sys.argv) != 4:
        sys.exit('Usage: python src/search_tests.py <instance_id> <covered|not_covered> "<query>"')
    for hit in search_tests(*sys.argv[1:4]):
        print(f"{hit['score']:.3f}  {hit['test_id']}")


if __name__ == "__main__":
    main()
