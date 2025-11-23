# build_k3_canonical.py
import os, json, glob, csv
from pathlib import Path

K3_FOLDER = r"./Bhagavad Gita Q&A Dataset for Modern Life Problem K3"
OUTPUT_FOLDER = r"./output"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
OUT_PATH = Path(OUTPUT_FOLDER) / "k3_qa.jsonl"

# heuristics: try common column names
PREFERRED_COLS = [
    ("question","question"),
    ("Question","question"),
    ("prompt","question"),
    ("answer","answer"),
    ("Answer","answer"),
    ("chapter","chapter"),
    ("verse_source","verse"),
    ("verse","verse"),
    ("source","source"),
]

def pick_field(row, keys):
    for k in keys:
        if k in row and row[k] not in (None,"", "nan"):
            return row[k]
    return None

def normalize_row(row):
    # best-effort normalization
    q = pick_field(row, ["question","Question","generated_question","prompt"])
    a = pick_field(row, ["answer","Answer","generated_explanation","generated_answer"])
    chapter = pick_field(row, ["chapter","Chapter"])
    verse = pick_field(row, ["verse","verse_source","verse_id"])
    source = pick_field(row, ["source","source_file"]) or "K3"
    # fallback: try to combine fields if missing
    if (not q) and "sanskrit_shloka" in row and "english_translation" in row:
        # a naive QA pair: english as answer, short question from verse
        q = f"How does this verse apply to modern life? ({row.get('verse_source') or ''})"
    if not a:
        # try english_translation or generated_explanation
        a = pick_field(row, ["generated_explanation","english_translation","english_answer","answer"])
    return {
        "question": (q or "").strip(),
        "answer": (a or "").strip(),
        "chapter": chapter or "",
        "verse": verse or "",
        "source": source,
    }

def read_csv_file(path):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        # try flexible CSV read
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(normalize_row(r))
    return rows

def main():
    files = sorted(glob.glob(os.path.join(K3_FOLDER, "*.csv")))
    total = 0
    written = 0
    with open(OUT_PATH, "w", encoding="utf-8") as out:
        for p in files:
            print("Reading:", p)
            rows = read_csv_file(p)
            for r in rows:
                total += 1
                # skip empty questions / answers
                if not r["question"] or not r["answer"]:
                    continue
                out.write(json.dumps(r, ensure_ascii=False) + "\n")
                written += 1
    print(f"Done. CSV files read: {len(files)}; rows read: {total}; written canonical: {written}")
    print("Saved:", OUT_PATH)

if __name__ == "__main__":
    main()
