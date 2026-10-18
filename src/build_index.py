"""Get the tests ready for meaning-based search (the embedding search in search_tests.py).

For each code copy in workspace/, cut every test file into pieces, one per test function
("chunks"), turn each piece into a list of numbers that captures its meaning ("embedding",
made by OpenAI), and save them on this laptop. Identical tests share one embedding, so
nothing is paid for twice.

Run:    python src/build_index.py                 embed all issues in data/chosen_issues.json
        python src/build_index.py --dry-run       chunks only, no API calls (free)
        python src/build_index.py --only psf__requests-1142
Needs:  workspace/<id>/covered and workspace/<id>/not_covered (run src/prepare_repo.py first),
        OPENAI_API_KEY in .env (not needed for --dry-run)
Output: data/index_v1/<id>__<variant>.jsonl  one line per test function:
        test_id, file, start_line, end_line, text, embedding
        --dry-run writes workspace/_chunks/<id>/<variant>/chunks.jsonl instead (no embedding)

The index comes only from the code in the workspace folders. It never reads labels or
issues.jsonl, and chunk text never names the issue, the variant or the workspace path.
"""
import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

CHOSEN = Path("data/chosen_issues.json")
WORKSPACE = Path("workspace")
INDEX = Path("data/index_v1")
CHUNKS = WORKSPACE / "_chunks"
VARIANTS = ["covered", "not_covered"]
EMBED_MODEL = "text-embedding-3-small"
BATCH = 100  # chunks per embeddings request


def test_files(folder):
    files = set(folder.rglob("test_*.py")) | set(folder.rglob("*_test.py"))
    return sorted(f for f in files if ".git" not in f.relative_to(folder).parts)


def chunks_for_file(path, folder):
    """One chunk per test function, decorators included. Stops on a parse error."""
    rel = path.relative_to(folder).as_posix()
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=rel)
    except SyntaxError as e:
        sys.exit(f"Could not parse {path}: {e}")
    lines = source.splitlines()
    chunks = []

    def visit(nodes, classes):
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                visit(node.body, classes + [node.name])
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                start = min([node.lineno] + [d.lineno for d in node.decorator_list])
                end = node.end_lineno
                test_id = "::".join([rel] + classes + [node.name])
                # No line numbers in the text: tests shifted down by new tests in covered
                # keep the same text, so they share one embedding with not_covered.
                header = f"# file: {rel} | test: {test_id}"
                text = "\n".join([header] + lines[start - 1:end])
                chunks.append({"test_id": test_id, "file": rel, "start_line": start,
                               "end_line": end, "text": text})

    visit(tree.body, [])
    return chunks


def build_chunks(folder):
    files = test_files(folder)
    chunks = [c for f in files for c in chunks_for_file(f, folder)]
    return files, chunks


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def openai_client():
    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv()
    return OpenAI()  # reads OPENAI_API_KEY from the environment


def embed_texts(client, texts):
    vectors = []
    for i in range(0, len(texts), BATCH):
        response = client.embeddings.create(model=EMBED_MODEL, input=texts[i:i + BATCH])
        vectors += [item.embedding for item in response.data]
    return vectors


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")  # write then rename, so a crash never leaves a half file
    with tmp.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    tmp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="build chunks only, no API calls")
    parser.add_argument("--only", metavar="INSTANCE_ID", help="index one issue")
    args = parser.parse_args()

    ids = [c["instance_id"] for c in json.loads(CHOSEN.read_text())]
    if args.only:
        if args.only not in ids:
            sys.exit(f"{args.only} is not in {CHOSEN}")
        ids = [args.only]

    folders = [(i, v, WORKSPACE / i / v) for i in ids for v in VARIANTS]
    missing = [str(f) for _, _, f in folders if not f.is_dir()]
    if missing:
        sys.exit("Missing workspace folders (run src/prepare_repo.py):\n  " + "\n  ".join(missing))

    if args.dry_run:
        print(f"{'folder':<36} {'test files':>10} {'chunks':>7}")
        unique = set()
        for i, v, folder in folders:
            files, chunks = build_chunks(folder)
            write_jsonl(CHUNKS / i / v / "chunks.jsonl", chunks)
            unique |= {text_hash(c["text"]) for c in chunks}
            print(f"{i + '/' + v:<36} {len(files):>10} {len(chunks):>7}")
        print(f"\nChunks written to {CHUNKS}/. Unique chunk texts to embed: {len(unique)}")
        return

    client = openai_client()
    cache = {}  # text hash -> embedding, shared across folders in this run
    for path in INDEX.glob("*.jsonl"):  # reuse embeddings from earlier runs
        for line in path.open(encoding="utf-8"):
            row = json.loads(line)
            cache[text_hash(row["text"])] = row["embedding"]

    for i, v, folder in folders:
        out = INDEX / f"{i}__{v}.jsonl"
        if out.exists():
            print(f"Already indexed, skipping: {out}")
            continue
        _, chunks = build_chunks(folder)
        todo = list({text_hash(c["text"]): c["text"] for c in chunks
                     if text_hash(c["text"]) not in cache}.items())
        for (h, _), vector in zip(todo, embed_texts(client, [t for _, t in todo])):
            cache[h] = vector
        write_jsonl(out, [{**c, "embedding": cache[text_hash(c["text"])]} for c in chunks])
        print(f"Indexed {out}: {len(chunks)} chunks, {len(todo)} newly embedded")


if __name__ == "__main__":
    main()
