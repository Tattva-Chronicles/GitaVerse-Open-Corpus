#!/usr/bin/env python3
"""
parallel_cluster.py

Greedy parallel fuzzy clustering for question deduplication / representative clustering.
Designed for ~20k records. Uses rapidfuzz + ThreadPoolExecutor for fast similarity checks.

Outputs a JSONL file with cluster_id, rep_text, and original row.

Usage:
    python parallel_cluster.py --input hf1_qa.jsonl --output clustered_hf1.jsonl

Supports JSONL (line-delimited JSON) and CSV input. Requires a 'question' field/column.
"""

import argparse
import json
import csv
import os
import sys
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from rapidfuzz import fuzz
from rapidfuzz import utils as rutils
from tqdm import tqdm
from functools import lru_cache
from typing import List, Dict, Any, Tuple
from dateutil import parser as dateparser

# ---------------------------
# Configurable parameters
# ---------------------------
DEFAULT_TOKEN_SORT_THRESHOLD = 88   # token_sort_ratio threshold (recommended ~88)
DEFAULT_PARTIAL_THRESHOLD = 94      # partial_ratio threshold (recommended ~94)
MAX_COMPARE_DEFAULT = 2500          # max representatives to check per question (None => all)
MAX_WORKERS = max(4, (os.cpu_count() or 2) * 2)  # threadpool size
NORMALIZE_MIN_LEN = 3               # skip normalization trimming below this length
# ---------------------------


# ---------------------------
# Helpers: normalization + caching
# ---------------------------
@lru_cache(maxsize=65536)
def normalize_text(s: str) -> str:
    """Lightweight stable normalization for clustering."""
    if s is None:
        return ""
    s2 = s.strip().lower()
    # minimal punctuation normalization (keeps meaning, reduces noise)
    # Keep letters, digits and common punctuation, replace others with space
    # But avoid heavy tokenization — rapidfuzz token_sort_ratio handles tokens
    s2 = s2.replace("\n", " ").replace("\r", " ")
    # collapse whitespace
    s2 = " ".join(s2.split())
    return s2


def read_input_rows(input_path: str) -> List[Dict[str, Any]]:
    """Read JSONL or CSV and return list of dict rows."""
    rows = []
    ext = os.path.splitext(input_path)[1].lower()
    if ext in [".jsonl", ".ndjson", ".json"]:
        with open(input_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
    elif ext in [".csv"]:
        with open(input_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                rows.append(dict(r))
    else:
        raise ValueError(f"Unsupported input extension: {ext}")
    return rows


def write_jsonl(output_path: str, rows: List[Dict[str, Any]]):
    with open(output_path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


# ---------------------------
# Similarity worker
# ---------------------------
def compare_pair(args: Tuple[int, str, str]) -> Tuple[int, float, float]:
    """
    Compare candidate string to a representative string.

    Returns (rep_index, token_sort_score, partial_score)
    """
    rep_idx, rep_text, cand_text = args
    # Candidate and rep are normalized, so call rapidfuzz on them directly
    token_sort_score = fuzz.token_sort_ratio(cand_text, rep_text)
    partial_score = fuzz.partial_ratio(cand_text, rep_text)
    return (rep_idx, float(token_sort_score), float(partial_score))


# ---------------------------
# Clustering function
# ---------------------------
def parallel_greedy_cluster(
    rows: List[Dict[str, Any]],
    question_field: str = "question",
    token_sort_threshold: int = DEFAULT_TOKEN_SORT_THRESHOLD,
    partial_threshold: int = DEFAULT_PARTIAL_THRESHOLD,
    max_compare: int = MAX_COMPARE_DEFAULT,
    show_progress: bool = True,
) -> Tuple[List[Dict[str, Any]], Dict]:
    """
    Main greedy clustering loop with parallel comparisons.
    Returns (annotated_rows, stats)
    """

    n = len(rows)
    # Representatives list: list of strings (normalized rep text)
    reps: List[str] = []
    # mapping rep index -> cluster id
    rep_cluster_ids: List[int] = []
    # cluster sizes
    cluster_sizes: Dict[int, int] = {}
    # result rows (augment each row with cluster info)
    out_rows: List[Dict[str, Any]] = []

    # Thread pool for parallel comparisons (rapidfuzz releases GIL while computing)
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    # We'll iterate across records in input order. This tends to produce stable reps.
    it = range(n)
    if show_progress:
        it = tqdm(range(n), desc="Clustering", unit="rows")

    next_cluster_id = 0
    for idx in it:
        row = rows[idx]
        raw_q = row.get(question_field, "")
        norm_q = normalize_text(raw_q)

        # trivial short cases -> make new cluster
        if len(norm_q) < NORMALIZE_MIN_LEN:
            cluster_id = next_cluster_id
            next_cluster_id += 1
            reps.append(norm_q)
            rep_cluster_ids.append(cluster_id)
            cluster_sizes[cluster_id] = 1
            out = dict(row)
            out.update({"cluster_id": cluster_id, "rep_text": norm_q, "rep_index": len(reps)-1})
            out_rows.append(out)
            continue

        # if no reps yet -> create first
        if not reps:
            cluster_id = next_cluster_id
            next_cluster_id += 1
            reps.append(norm_q)
            rep_cluster_ids.append(cluster_id)
            cluster_sizes[cluster_id] = 1
            out = dict(row)
            out.update({"cluster_id": cluster_id, "rep_text": norm_q, "rep_index": 0})
            out_rows.append(out)
            continue

        # Prepare reps to check (sample if too many)
        total_reps = len(reps)
        if (max_compare is None) or (max_compare >= total_reps):
            reps_to_check = list(enumerate(reps))
        else:
            # sampling strategy: pick a deterministic sample biased to recent reps + some spread
            # take last chunk + uniform sample from earlier reps
            recent_take = min(800, max(100, int(0.2 * max_compare)))
            idx_start = max(0, total_reps - recent_take)
            candidates = list(enumerate(reps[idx_start:]))
            # adjust indices for enumerating from 0
            candidates = [(i + idx_start, r) for (i, r) in candidates]

            remaining = max_compare - len(candidates)
            if remaining > 0 and idx_start > 0:
                # uniform sample from [0, idx_start)
                step = max(1, idx_start // remaining)
                sampled = [(i, reps[i]) for i in range(0, idx_start, step)]
                candidates.extend(sampled[:remaining])
            reps_to_check = candidates

        # Build args for parallel compare
        args_iter = ((i, rep_text, norm_q) for (i, rep_text) in reps_to_check)

        # Submit compare tasks in the threadpool in chunks to avoid massive futures queue
        futures = []
        CHUNK = 2000  # internal chunk size for submission
        # because args_iter is a generator of tuples, we convert to list for chunking
        args_list = list(args_iter)
        matches = []  # collect candidate matches (rep_idx, token_sort, partial)
        # Use map in one go for faster run (ThreadPoolExecutor.map returns iterator)
        # Build parameter list for compare_pair
        if args_list:
            try:
                # Using executor.map is efficient and avoids pickling overhead for each job
                for res in executor.map(compare_pair, args_list, chunksize=64):
                    matches.append(res)
            except Exception as e:
                # fallback to sequential if something odd happens
                matches = [compare_pair(a) for a in args_list]

        # Evaluate best match (by token_sort primarily, but also consider partial)
        best = None  # (rep_idx, token_sort, partial)
        for rep_idx, ts, pr in matches:
            # quick early accept if above high thresholds
            if ts >= token_sort_threshold and pr >= partial_threshold:
                best = (rep_idx, ts, pr)
                break
            # keep best token_sort if we don't break early
            if best is None or ts > best[1] or (ts == best[1] and pr > best[2]):
                best = (rep_idx, ts, pr)

        # Decide assignment
        assigned_cluster = None
        if best:
            rep_idx, best_ts, best_pr = best
            # Accept if either metric crosses its threshold
            if (best_ts >= token_sort_threshold) or (best_pr >= partial_threshold):
                assigned_cluster = rep_cluster_ids[rep_idx]

        if assigned_cluster is None:
            # new cluster
            cluster_id = next_cluster_id
            next_cluster_id += 1
            reps.append(norm_q)
            rep_cluster_ids.append(cluster_id)
            cluster_sizes[cluster_id] = 1
            out = dict(row)
            out.update({"cluster_id": cluster_id, "rep_text": norm_q, "rep_index": len(reps)-1})
            out_rows.append(out)
        else:
            # assign to existing cluster; do NOT change rep (keeps rep stable)
            cluster_sizes[assigned_cluster] = cluster_sizes.get(assigned_cluster, 0) + 1
            out = dict(row)
            # find rep index for assigned cluster
            rep_index = rep_cluster_ids.index(assigned_cluster)
            out.update({"cluster_id": assigned_cluster, "rep_text": reps[rep_index], "rep_index": rep_index})
            out_rows.append(out)

    # shutdown executor
    executor.shutdown(wait=True)

    stats = {
        "n_input": n,
        "n_reps": len(reps),
        "n_clusters": len(cluster_sizes),
        "cluster_sizes": cluster_sizes,
    }
    return out_rows, stats


# ---------------------------
# CLI
# ---------------------------
def main():
    parser = argparse.ArgumentParser(description="Parallel fuzzy greedy clustering for Q/A dedupe")
    parser.add_argument("--input", "-i", required=True, help="Input JSONL or CSV file with a 'question' column")
    parser.add_argument("--output", "-o", required=True, help="Output JSONL path (clustered rows)")
    parser.add_argument("--question-field", default="question", help="Field name containing the question")
    parser.add_argument("--token-sort-threshold", type=int, default=DEFAULT_TOKEN_SORT_THRESHOLD)
    parser.add_argument("--partial-threshold", type=int, default=DEFAULT_PARTIAL_THRESHOLD)
    parser.add_argument("--max-compare", type=int, default=MAX_COMPARE_DEFAULT,
                        help="Max number of representatives to compare per question (use 0 or -1 to disable cap)")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bar")
    parser.add_argument("--preview", action="store_true", help="Only cluster first 200 rows for quick preview")
    args = parser.parse_args()

    max_compare = None if (args.max_compare is None or args.max_compare <= 0) else args.max_compare

    print("Reading input...")
    rows = read_input_rows(args.input)
    if args.preview:
        rows = rows[:200]
        print("Preview mode: clustering first 200 rows only.")

    print(f"Records: {len(rows)}. Workers: {MAX_WORKERS}. token_sort_threshold={args.token_sort_threshold}, partial_threshold={args.partial_threshold}, max_compare={max_compare}")
    clustered_rows, stats = parallel_greedy_cluster(
        rows,
        question_field=args.question_field,
        token_sort_threshold=args.token_sort_threshold,
        partial_threshold=args.partial_threshold,
        max_compare=max_compare, # type: ignore
        show_progress=not args.no_progress,
    )

    # Save
    print(f"Clusters created: {stats['n_clusters']}. Representatives: {stats['n_reps']}. Saving to {args.output} ...")
    write_jsonl(args.output, clustered_rows)
    print("Saved.")

    # print top clusters
    sizes = sorted(stats["cluster_sizes"].items(), key=lambda x: x[1], reverse=True)[:30]
    print("Top clusters (cluster_id -> size):")
    for cid, sz in sizes:
        print(f"  {cid:4d} -> {sz}")

    print("Done.")


if __name__ == "__main__":
    main()
