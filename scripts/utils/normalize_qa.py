#!/usr/bin/env python3
"""
normalize_qa.py

Read multiple QA-jsonl/json/csv inputs (HF1-style and K3-style),
auto-detect format, and produce a unified canonical JSONL:
  ./output/unified_qa.jsonl

Usage (example):
  python normalize_qa.py --hf1 ./output/hf1_qa.jsonl --k3 ./output/k3_qa.jsonl --out ./output/unified_qa.jsonl

The script:
 - keeps original IDs in `orig_id`
 - sets `uid` (prefers existing qid; else SOURCE-<line>)
 - copies extra fields into `metadata`
 - tries to coerce chapter -> int where possible
"""

import argparse, json, os
from pathlib import Path

def load_jsonl(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                items.append((i, obj))
            except Exception as e:
                print(f"Skipping invalid JSON at {path}:{i} -> {e}")
    return items

def normalize_record(obj, src, line_idx):
    # Create canonical skeleton
    rec = {
        "uid": None,
        "source": src,
        "orig_id": None,
        "authority": None,
        "language": None,
        "chapter": None,
        "verse": None,
        "verse_id": None,
        "question": None,
        "answer": None,
        "metadata": {},
        "provenance": {"file_line": line_idx}
    }

    # detect HF1-style heuristics: presence of 'qid' or 'verse_id' and numeric chapter int
    if "qid" in obj or ("hf1" in src.lower()) or ("source" in obj and obj.get("source","").upper() == "HF1"):
        # HF1 style
        rec["orig_id"] = obj.get("qid") or obj.get("id") or None
        rec["uid"] = rec["orig_id"] or f"HF1-{line_idx}"
        rec["authority"] = obj.get("authority") or obj.get("cred") or "secondary"
        rec["language"] = obj.get("language") or obj.get("lang") or "en"
        # try chapter / verse
        ch = obj.get("chapter") or obj.get("chap") or obj.get("chapter_num")
        try:
            rec["chapter"] = int(ch) if ch is not None and str(ch).strip() != "" else None
        except:
            rec["chapter"] = None
        # verse id fields
        rec["verse_id"] = obj.get("verse_id") or obj.get("verse") or obj.get("verse_source")
        rec["verse"] = str(obj.get("verse") or obj.get("verse_id") or "") if obj.get("verse") or obj.get("verse_id") else None
        # question/answer
        rec["question"] = obj.get("question") or obj.get("prompt") or obj.get("q") or None
        rec["answer"] = obj.get("answer") or obj.get("generated_explanation") or obj.get("a") or obj.get("response") or None
        # collect other keys into metadata
        for k,v in obj.items():
            if k.lower() in ("qid","id","authority","language","lang","chapter","chap","chapter_num","verse","verse_id","verse_source","question","prompt","q","answer","generated_explanation","a","response","source"):
                continue
            rec["metadata"][k] = v

    else:
        # assume K3-style: Q/A with minimal fields
        rec["orig_id"] = obj.get("qid") or None
        # build uid
        rec["uid"] = obj.get("qid") or (src.upper() + f"-{line_idx}")
        rec["authority"] = obj.get("authority") or "generated"
        rec["language"] = obj.get("language") or obj.get("lang") or "en"
        # chapter / verse
        ch = obj.get("chapter") or obj.get("chapter_number") or None
        try:
            rec["chapter"] = int(ch) if ch is not None and str(ch).strip() != "" else None
        except:
            rec["chapter"] = None
        rec["verse"] = obj.get("verse") or obj.get("verse_id") or None
        rec["verse_id"] = obj.get("verse_id") or obj.get("verse") or None
        # question / answer
        rec["question"] = obj.get("question") or obj.get("prompt") or None
        rec["answer"] = obj.get("answer") or obj.get("generated_explanation") or obj.get("response") or None
        # leftover metadata
        for k,v in obj.items():
            if k.lower() in ("question","prompt","answer","generated_explanation","chapter","verse","verse_id","qid","id","source","language","lang","authority"):
                continue
            rec["metadata"][k] = v

    # final trimming / normalization
    if isinstance(rec["question"], str):
        rec["question"] = rec["question"].strip()
    if isinstance(rec["answer"], str):
        rec["answer"] = rec["answer"].strip()

    return rec

def write_jsonl(items, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hf1", help="Path to hf1_qa.jsonl (optional)", default=None)
    ap.add_argument("--k3", help="Path to k3_qa.jsonl (optional)", default=None)
    ap.add_argument("--out", help="Output unified jsonl", default="./output/unified_qa.jsonl")
    args = ap.parse_args()

    inputs = []
    if args.hf1:
        inputs.append(("HF1", Path(args.hf1)))
    if args.k3:
        inputs.append(("K3", Path(args.k3)))
    if not inputs:
        print("Provide at least one input via --hf1 or --k3")
        return

    unified = []
    for src_name, path in inputs:
        if not path.exists():
            print(f"Warning: input not found: {path} (skipping)")
            continue
        raw = load_jsonl(path)
        print(f"Loaded {len(raw)} lines from {path}")
        for line_idx, obj in raw:
            norm = normalize_record(obj, src_name, line_idx)
            # ensure question & answer exist, otherwise skip but log
            if not norm.get("question") or not norm.get("answer"):
                # still include but flag in metadata
                norm["metadata"]["__incomplete"] = True
                # optional: skip incomplete rows by uncommenting next line
                # continue
            unified.append(norm)

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(unified, outp)
    print(f"Wrote unified dataset with {len(unified)} records to {outp}")

if __name__ == "__main__":
    main()
