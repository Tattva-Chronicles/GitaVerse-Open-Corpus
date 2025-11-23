import json

HF1_PATH = "./output/hf1_qa_clustered.jsonl"
K3_PATH = "./output/k3_qa_clustered.jsonl"
OUTPUT_PATH = "./qa_master.jsonl"

def load_jsonl(path):
    data = []
    with open(path, "r", encoding="utf8") as f:
        for line in f:
            data.append(json.loads(line))
    return data

def save_jsonl(path, rows):
    with open(path, "w", encoding="utf8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

def normalize_hf1(row):
    return {
        "qid": row["qid"],
        "source": "HF1",
        "cluster_id": row.get("cluster_id"),
        "merged_count": row.get("merged_count"),
        "chapter": row["chapter"],
        "verse": row["verse"],
        "verse_id": f"{row['chapter']}:{row['verse']}",
        "aligned": True,
        "question": row["question"],
        "answer": row["answer"]
    }

def normalize_k3(row):
    # K3 has no qid → create one
    qid = f"K3-{row['chapter']}-{row['verse']}-{row['cluster_id']}"
    return {
        "qid": qid,
        "source": "K3",
        "cluster_id": row.get("cluster_id"),
        "merged_count": row.get("merged_count"),
        "chapter": int(row["chapter"]),
        "verse": str(row["verse"]),
        "verse_id": f"{row['chapter']}:{row['verse']}",
        "aligned": False,
        "question": row["question"],
        "answer": row["answer"]
    }

def main():
    print("[INFO] Loading clustered datasets...")
    hf1 = load_jsonl(HF1_PATH)
    k3 = load_jsonl(K3_PATH)

    print(f"[INFO] HF1 entries: {len(hf1)}")
    print(f"[INFO] K3 entries: {len(k3)}")

    print("[INFO] Normalizing...")
    final = []

    for r in hf1:
        final.append(normalize_hf1(r))

    for r in k3:
        final.append(normalize_k3(r))

    print("[INFO] Saving qa_master.jsonl...")
    save_jsonl(OUTPUT_PATH, final)

    print(f"[DONE] Saved {len(final)} Q&A entries.")

if __name__ == "__main__":
    main()
