import json
import os
from sentence_transformers import SentenceTransformer, util
import torch
from tqdm import tqdm

# ------------ CONFIG ------------
INPUT_FILE = "./output/hf1_qa.jsonl"
OUTPUT_FILE = "./output/hf1_qa_clustered.jsonl"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
THRESHOLD = 0.86  # High similarity required for clustering duplicates
BATCH_SIZE = 64
# --------------------------------

device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer(MODEL_NAME, device=device)

def load_jsonl(path):
    data = []
    with open(path, "r", encoding="utf8") as f:
        for line in f:
            data.append(json.loads(line))
    return data

def save_jsonl(path, data):
    with open(path, "w", encoding="utf8") as f:
        for row in data:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

def cluster_questions(entries):
    print("[INFO] Encoding questions...")
    questions = [e["question"] for e in entries]
    embeddings = model.encode(questions, convert_to_tensor=True, batch_size=BATCH_SIZE)

    clusters = []
    assigned = set()

    print("[INFO] Clustering...")
    for i in tqdm(range(len(entries))):
        if i in assigned:
            continue

        cluster = [i]
        assigned.add(i)

        sims = util.cos_sim(embeddings[i], embeddings)[0]

        for j in range(i + 1, len(entries)):
            if j not in assigned and float(sims[j]) >= THRESHOLD:
                cluster.append(j)
                assigned.add(j)

        clusters.append(cluster)

    print(f"[INFO] Total clusters formed: {len(clusters)}")

    # choose representative + merge
    merged_output = []
    for cid, indices in enumerate(clusters):
        rep = entries[indices[0]].copy()
        rep["cluster_id"] = cid
        rep["merged_count"] = len(indices)
        merged_output.append(rep)

    return merged_output

def main():
    print("[INFO] Loading HF1 data...")
    entries = load_jsonl(INPUT_FILE)
    print(f"[INFO] Total HF1 records: {len(entries)}")

    clustered = cluster_questions(entries)

    print(f"[INFO] Saving clustered HF1 → {OUTPUT_FILE}")
    save_jsonl(OUTPUT_FILE, clustered)

    print("[DONE] HF1 clustering complete.")

if __name__ == "__main__":
    main()
