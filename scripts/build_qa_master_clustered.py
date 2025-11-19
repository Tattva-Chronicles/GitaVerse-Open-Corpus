import os
import json
import csv
from concurrent.futures import ThreadPoolExecutor
from rapidfuzz import fuzz
from tqdm import tqdm
from functools import lru_cache

# ---------------- CONFIG ----------------
HF1_PATH = r"./output/hf1_qa.jsonl"
K3_FOLDER = r"./Bhagavad Gita Q&A Dataset for Modern Life Problem K3"
OUTPUT_FOLDER = r"./output"

OUTPUT_PATH = os.path.join(OUTPUT_FOLDER, "qa_master_clustered.jsonl")

TOKEN_SORT_THRESHOLD = 88
PARTIAL_THRESHOLD = 94
MAX_COMPARE = 2500
MAX_WORKERS = 12
NORMALIZE_MIN_LEN = 3
# -----------------------------------------


@lru_cache(maxsize=65536)
def normalize_text(s: str) -> str:
    if not s:
        return ""
    s2 = s.lower().strip().replace("\n", " ").replace("\r", " ")
    s2 = " ".join(s2.split())
    return s2


def load_hf1():
    rows = []
    with open(HF1_PATH, "r", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            row["source"] = "hf1"
            rows.append(row)
    return rows


def load_k3():
    rows = []
    for file in os.listdir(K3_FOLDER):
        if not file.lower().endswith(".csv"):
            continue
        chapter_path = os.path.join(K3_FOLDER, file)
        chapter_name = os.path.splitext(file)[0]

        with open(chapter_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                r["source"] = f"k3_{chapter_name}"
                rows.append(r)
    return rows


def compare_pair(args):
    rep_idx, rep_text, cand_text = args
    ts = fuzz.token_sort_ratio(cand_text, rep_text)
    pr = fuzz.partial_ratio(cand_text, rep_text)
    return rep_idx, ts, pr


def cluster_records(rows):
    reps = []
    rep_cluster_ids = []
    cluster_sizes = {}

    out_rows = []
    next_cluster_id = 0

    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    for row in tqdm(rows, desc="Clustering", unit="row"):
        q = row.get("question", "")
        norm_q = normalize_text(q)

        if len(norm_q) < NORMALIZE_MIN_LEN or not reps:
            # new cluster
            cid = next_cluster_id
            next_cluster_id += 1

            reps.append(norm_q)
            rep_cluster_ids.append(cid)
            cluster_sizes[cid] = 1

            row["cluster_id"] = cid
            row["rep_text"] = norm_q
            out_rows.append(row)
            continue

        # sample representatives
        total_reps = len(reps)
        if MAX_COMPARE >= total_reps:
            reps_to_check = list(enumerate(reps))
        else:
            # last 800 reps + uniform sample
            recent_take = min(800, MAX_COMPARE)
            start = max(0, total_reps - recent_take)
            reps_to_check = [(i + start, reps[i + start]) for i in range(recent_take)]

            remaining = MAX_COMPARE - recent_take
            if remaining > 0 and start > 0:
                step = max(1, start // remaining)
                for i in range(0, start, step):
                    reps_to_check.append((i, reps[i]))

        # parallel compare
        args_list = [(idx, rep, norm_q) for idx, rep in reps_to_check]

        matches = []
        for res in executor.map(compare_pair, args_list):
            matches.append(res)

        # choose best
        best = None
        for rep_idx, ts, pr in matches:
            if ts >= TOKEN_SORT_THRESHOLD and pr >= PARTIAL_THRESHOLD:
                best = (rep_idx, ts, pr)
                break
            if not best or ts > best[1] or (ts == best[1] and pr > best[2]):
                best = (rep_idx, ts, pr)

        rep_idx, ts, pr = best # type: ignore
        if ts >= TOKEN_SORT_THRESHOLD or pr >= PARTIAL_THRESHOLD:
            cid = rep_cluster_ids[rep_idx]
        else:
            cid = next_cluster_id
            next_cluster_id += 1
            reps.append(norm_q)
            rep_cluster_ids.append(cid)
            cluster_sizes[cid] = 0

        cluster_sizes[cid] = cluster_sizes.get(cid, 0) + 1
        row["cluster_id"] = cid
        row["rep_text"] = reps[rep_cluster_ids.index(cid)]
        out_rows.append(row)

    executor.shutdown(wait=True)
    return out_rows, cluster_sizes


def main():
    print("[INFO] Loading HF1...")
    hf1_rows = load_hf1()
    print(f"  Loaded {len(hf1_rows)} HF1 entries")

    print("[INFO] Loading K3 (18 files)...")
    k3_rows = load_k3()
    print(f"  Loaded {len(k3_rows)} K3 entries")

    print("[INFO] Merging datasets...")
    all_rows = hf1_rows + k3_rows
    print(f"[INFO] Total combined rows: {len(all_rows)}")

    clustered, sizes = cluster_records(all_rows)

    print(f"[INFO] Total clusters formed: {len(sizes)}")

    print(f"[INFO] Saving → {OUTPUT_PATH}")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        for r in clustered:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("[DONE] Clustering complete.")


if __name__ == "__main__":
    main()
