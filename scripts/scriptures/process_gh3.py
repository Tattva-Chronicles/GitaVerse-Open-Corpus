#!/usr/bin/env python3
"""
build_gh3.py

Process GH3 dataset pieces into normalized JSONL outputs.

Outputs (in ./output by default):
 - gh3_translations.jsonl    (one translation per line)
 - gh3_commentaries.jsonl    (one commentary per line)
 - gh3_verses_normalized.jsonl (one verse record per line; contains pointers/summary to translations/commentaries)

Usage:
    python build_gh3.py \
      --input-folder ./gh3_raw \
      --output-folder ./output

Defaults assume files are in current dir or /mnt/data (adjust as required).
"""

import os
import json
import argparse
from collections import defaultdict
from typing import Dict, List, Any
from tqdm import tqdm

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def ensure_dir(d: str):
    os.makedirs(d, exist_ok=True)

def safe_str(x):
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    return str(x)

def main(args):
    input_folder = args.input_folder
    out_folder = args.output_folder
    ensure_dir(out_folder)

    # Expecting files (some may be named slightly differently — try common names)
    candidates = {
        "authors": ["authors.json", "author.json", "authors.txt"],
        "chapters": ["chapters.json", "chapter.json"],
        "languages": ["languages.json", "language.json"],
        "verses": ["verse.json", "verses.json", "bhagavadgita_chapter_1.json"],
        "translations": ["translation.json", "translations.json", "translation_list.json"],
        "commentaries": ["commentary.json", "commentaries.json", "commentary_sample.json"],
        "summary": ["summary.md", "README.md"]
    }

    found = {}
    for key, names in candidates.items():
        for n in names:
            p = os.path.join(input_folder, n)
            if os.path.exists(p):
                found[key] = p
                break
        else:
            found[key] = None

    # Load what exists
    authors = {}
    if found["authors"]:
        print(f"Loading authors from {found['authors']}")
        raw = load_json(found["authors"])
        # Accept either list or dict
        if isinstance(raw, list):
            for a in raw:
                # expect keys: id or author_id, authorName/name
                aid = a.get("id") or a.get("author_id") or a.get("authorId") or a.get("authorID")
                if aid is None:
                    # try name as key
                    continue
                authors[int(aid)] = a
        elif isinstance(raw, dict):
            authors = raw
    else:
        print("Warning: authors file not found. continuing without author lookup.")

    chapters = {}
    if found["chapters"]:
        print(f"Loading chapters from {found['chapters']}")
        raw = load_json(found["chapters"])
        if isinstance(raw, list):
            for c in raw:
                cid = c.get("id") or c.get("chapter") or c.get("chapter_id")
                if cid is not None:
                    chapters[int(cid)] = c
        elif isinstance(raw, dict):
            chapters = raw

    languages = {}
    if found["languages"]:
        print(f"Loading languages from {found['languages']}")
        raw = load_json(found["languages"])
        if isinstance(raw, list):
            for l in raw:
                lid = l.get("id") or l.get("language_id") or l.get("code")
                if lid is None:
                    continue
                languages[lid] = l
        elif isinstance(raw, dict):
            languages = raw

    verses_raw = []
    if found["verses"]:
        print(f"Loading verses from {found['verses']}")
        verses_raw = load_json(found["verses"])
        # allow object with key "verses"
        if isinstance(verses_raw, dict) and "verses" in verses_raw:
            verses_raw = verses_raw["verses"]
    else:
        print("Error: verse file not found. Exiting.")
        return

    translations_raw = []
    if found["translations"]:
        print(f"Loading translations from {found['translations']}")
        translations_raw = load_json(found["translations"])
        if isinstance(translations_raw, dict) and "translations" in translations_raw:
            translations_raw = translations_raw["translations"]
    else:
        print("Warning: translation file not found. continuing.")

    commentaries_raw = []
    if found["commentaries"]:
        print(f"Loading commentaries from {found['commentaries']}")
        commentaries_raw = load_json(found["commentaries"])
        # Some commentary file may be a dict with 'rows' or similar
        if isinstance(commentaries_raw, dict):
            # try common keys
            for k in ("commentaries","items","rows","data"):
                if k in commentaries_raw:
                    commentaries_raw = commentaries_raw[k]
                    break
    else:
        print("Warning: commentary file not found. continuing.")

    # Build verse lookup keyed by verse_id (prefer "verse_id" or "id_raw" or composed chapter:verse)
    verse_by_vid: Dict[str, Dict[str, Any]] = {}
    for v in verses_raw:
        # keys may include 'verse_id', 'id', '_id_raw', 'verse_id' string like "10:1", or numeric fields chapter/verse
        vid = None
        for k in ("verse_id", "_id_raw", "id", "verseId"):
            if k in v and v[k]:
                vid = safe_str(v[k])
                break
        if not vid:
            # try compose from chapter + verse
            ch = v.get("chapter") or v.get("chapter_id") or v.get("chapterNumber") or v.get("chapter_no")
            vs = v.get("verse") or v.get("verseNumber") or v.get("verse_id_num")
            if ch is not None and vs is not None:
                vid = f"{int(ch)}:{int(vs)}"
        if not vid:
            # fallback to index-based id
            vid = f"unknown:{len(verse_by_vid)+1}"
        # normalize basic verse entry
        normalized = {
            "verse_id": vid,
            "chapter": v.get("chapter"),
            "verse_number": v.get("verse") or v.get("verseNumber") or v.get("verse_id"),
            "sanskrit": v.get("sanskrit") or v.get("text") or v.get("original_text"),
            "transliteration": v.get("transliteration") or v.get("transliteration_text"),
            "raw": v  # keep raw for traceability
        }
        verse_by_vid[vid] = normalized

    # Index translations by verse_id
    translations_by_vid: Dict[str, List[Dict[str,Any]]] = defaultdict(list)
    for t in translations_raw:
        # t may already have language, verse_id etc.
        # try to find verse id
        vid = None
        for k in ("verse_id", "_id_raw", "id", "verseId", "verseIdRaw"):
            if k in t and t[k]:
                vid = safe_str(t[k])
                break
        if not vid:
            # try chapter + verse
            ch = t.get("chapter") or t.get("chapter_id")
            vs = t.get("verse") or t.get("verse_number") or t.get("verseNumber")
            if ch is not None and vs is not None:
                vid = f"{int(ch)}:{int(vs)}"
        if not vid:
            # maybe translation entries include a 'source_file' or 'source' with filename containing verse id
            vid = t.get("source_file") or t.get("source")
            if vid and ":" not in str(vid):
                vid = None
        if not vid:
            vid = f"unknown_translation:{len(translations_by_vid)+1}"

        translations_by_vid[vid].append(t)

    # Index commentaries by verse_id
    commentaries_by_vid: Dict[str, List[Dict[str,Any]]] = defaultdict(list)
    for c in commentaries_raw:
        vid = None
        for k in ("verse_id", "_id_raw", "verseId", "id", "verseIdRaw"):
            if k in c and c[k]:
                vid = safe_str(c[k])
                break
        if not vid:
            ch = c.get("chapter") or c.get("chapter_id") or c.get("verseNumber")
            vs = c.get("verse") or c.get("verseNumber")
            if ch is not None and vs is not None:
                try:
                    vid = f"{int(ch)}:{int(vs)}"
                except Exception:
                    vid = None
        if not vid:
            # maybe commentary lists verse id in other key names
            if "verse_id" in c:
                vid = safe_str(c["verse_id"])
        if not vid:
            vid = f"unknown_commentary:{len(commentaries_by_vid)+1}"
        commentaries_by_vid[vid].append(c)

    # Write translations JSONL
    translations_out = os.path.join(out_folder, "gh3_translations.jsonl")
    commentaries_out = os.path.join(out_folder, "gh3_commentaries.jsonl")
    verses_out = os.path.join(out_folder, "gh3_verses_normalized.jsonl")

    print(f"Writing translations -> {translations_out}")
    with open(translations_out, "w", encoding="utf-8") as fout:
        total = 0
        for vid, tl in translations_by_vid.items():
            for entry in tl:
                # canonicalize translation record
                rec = {
                    "verse_id": vid,
                    "language": entry.get("language") or entry.get("lang") or (entry.get("translations") and entry.get("translations")[0].get("language")) if isinstance(entry.get("translations"), list) else None, # type: ignore
                    "text": entry.get("text") or entry.get("translations") or entry.get("translation") or entry,
                    "source": entry.get("source") or entry.get("source_file"),
                    "raw": entry
                }
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                total += 1
        print(f"Wrote {total} translation records.")

    # Write commentaries JSONL
    print(f"Writing commentaries -> {commentaries_out}")
    with open(commentaries_out, "w", encoding="utf-8") as fout:
        total = 0
        for vid, clist in commentaries_by_vid.items():
            for c in clist:
                # canonicalize commentary record
                rec = {
                    "verse_id": vid,
                    "author_id": c.get("author_id") or c.get("id") or c.get("author_id_raw"),
                    "author_name": c.get("authorName") or c.get("author") or c.get("author_name"),
                    "language": c.get("lang") or c.get("language") or c.get("language_id"),
                    "commentary": c.get("description") or c.get("text") or c.get("commentary") or c,
                    "raw": c
                }
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                total += 1
        print(f"Wrote {total} commentary records.")

    # Build normalized verse records (pointers to counts and lists of translation/commentary ids)
    print(f"Writing normalized verses -> {verses_out}")
    with open(verses_out, "w", encoding="utf-8") as fout:
        total = 0
        for vid, verse in verse_by_vid.items():
            trans = translations_by_vid.get(vid, [])
            comms = commentaries_by_vid.get(vid, [])
            rec = {
                "verse_id": vid,
                "chapter": verse.get("chapter"),
                "verse_number": verse.get("verse_number"),
                "sanskrit": safe_str(verse.get("sanskrit")),
                "transliteration": safe_str(verse.get("transliteration")),
                "translation_count": len(trans),
                "commentary_count": len(comms),
                # list small metadata for quick lookup (author names, languages, short snippet)
                "translations_meta": [
                    {
                        "language": (t.get("language") or t.get("lang")) if isinstance(t, dict) else None,
                        "source": (t.get("source") if isinstance(t, dict) else None),
                        "snippet": (safe_str(t.get("text") if isinstance(t, dict) else t)[:200])
                    }
                    for t in trans
                ],
                "commentaries_meta": [
                    {
                        "author_id": (c.get("author_id") or c.get("id")),
                        "author_name": (c.get("authorName") or c.get("author") or c.get("author_name")),
                        "language": (c.get("lang") or c.get("language")),
                        "snippet": safe_str(c.get("description") or c.get("text") or c.get("commentary"))[:200]
                    }
                    for c in comms
                ],
                "raw_verse": verse.get("raw")
            }
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            total += 1
        print(f"Wrote {total} normalized verse records.")

    print("GH3 processing complete.")
    print("Outputs:")
    print(" -", translations_out)
    print(" -", commentaries_out)
    print(" -", verses_out)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build GH3 canonical JSONL files.")
    parser.add_argument("--input-folder", default="./", help="Folder with GH3 raw files (authors.json, verse.json, translation.json, commentary.json, chapters.json, languages.json)")
    parser.add_argument("--output-folder", default="./output", help="Output folder for JSONL files")
    args = parser.parse_args()
    main(args)
