"""
process_hf3.py
Ingest Bhagwat-Gita-Infinity (HF3) modular JSON files into canonical JSONL.

- Reads:
    ./Bhagwat-Gita-Infinity/chapters/*.json
    ./Bhagavad-Gita-Infinity/sloks/*.json

- Writes:
    ./output/hf3_canonical.jsonl     -> verse-level canonical objects
    ./output/hf3_chapters.json       -> array of chapter metadata
"""

import json
import re
from pathlib import Path
from glob import glob

BASE_DIR = "./Bhagwat-Gita-Infinity"   # adjust if necessary
CHAPTERS_GLOB = f"{BASE_DIR}/chapter/*.json"
SLOKS_GLOB = f"{BASE_DIR}/slok/*.json"
OUT_DIR = Path("./output")
OUT_DIR.mkdir(exist_ok=True, parents=True)
OUT_FILE = OUT_DIR / "hf3_canonical.jsonl"
CHAPTERS_OUT = OUT_DIR / "hf3_chapters.json"

DEVANAGARI_RE = re.compile(r'[\u0900-\u097F]')  # detect devanagari

def detect_language(text: str) -> str:
    """Heuristic: Devanagari present -> hi (Hindi), else en."""
    if not text or not isinstance(text, str):
        return "en"
    if DEVANAGARI_RE.search(text):
        return "hi"
    # fallback: if long ascii with many english words -> en
    return "en"

def flatten_commentary_fields(commentator_obj):
    """
    Given a dictionary like {"author": "Swami X", "et": "...", "ec": "...", "ht": "..."},
    return a list of (subfield_key, subfield_text) in a reasonable order.
    """
    texts = []
    if not isinstance(commentator_obj, dict):
        return texts

    # prefer ordering: et, ec, etc..., ht/hc/sc
    order = ["et", "ec", "ht", "hc", "sc", "htc", "et0", "et1"]
    # add any other keys deterministically after author
    for key in order:
        if key in commentator_obj and isinstance(commentator_obj[key], str) and commentator_obj[key].strip():
            texts.append((key, commentator_obj[key].strip()))
    # add remaining string fields
    for k,v in commentator_obj.items():
        if k in ("author",) or k in order:
            continue
        if isinstance(v, str) and v.strip():
            texts.append((k, v.strip()))
    return texts

def collect_commentaries(slok_json: dict):
    """
    Walk through the slok JSON and collect commentator blocks.
    Return list of {"author":..., "text":..., "language":..., "source":"HF3", "raw_key":...}
    """
    commentaries = []
    # keys that are definitely metadata - ignore
    meta_keys = {"_id", "chapter", "verse", "slok", "transliteration", "translation", "translation_en", "translation_hi", "slok_id", "id"}
    for key, val in slok_json.items():
        if key in meta_keys:
            continue
        # typical commentator blocks are dicts
        if isinstance(val, dict):
            # attempt to extract author
            author = val.get("author") if "author" in val else None
            parts = flatten_commentary_fields(val)
            # if there is nothing in parts, skip
            if not parts:
                continue
            # join parts preserving order; but also keep track of field types for language inference
            texts = []
            for fld, txt in parts:
                texts.append(txt)
            text_combined = "\n\n".join(texts).strip()

            # language detection: prefer using presence of devanagari in the combined text; otherwise look at subkeys
            lang = detect_language(text_combined)

            # fallback: if author field is Devanagari -> hi
            if not author and isinstance(val.get("author", ""), str) and DEVANAGARI_RE.search(val.get("author", "")):
                lang = "hi"

            commentary_obj = {
                "author": author if author else key,
                "text": text_combined,
                "language": lang,
                "source": "HF3",
                "raw_key": key
            }
            commentaries.append(commentary_obj)
        else:
            # If val is a direct string but key looks like a commentator (heuristic: short key)
            if isinstance(val, str) and len(val.strip()) > 0 and len(key) <= 30:
                lang = detect_language(val)
                commentaries.append({
                    "author": key,
                    "text": val.strip(),
                    "language": lang,
                    "source": "HF3",
                    "raw_key": key
                })
    return commentaries

def extract_translations(slok_json):
    """
    Try to find canonical english/hindi translations:
    - check for explicit fields 'translation_en', 'translation_hi', 'translation', 'et' etc.
    - also check common commentator fields that look like translations
    Returns translations list of {"language","text","source"}
    """
    translations = []
    # direct fields
    for cand in ("translation_en", "translation", "translation_en_text", "translationEn"):
        if cand in slok_json and isinstance(slok_json[cand], str) and slok_json[cand].strip():
            translations.append({"language": "en", "text": slok_json[cand].strip(), "source": "HF3"})
            break
    for cand in ("translation_hi", "translation_hi_text", "translationHi"):
        if cand in slok_json and isinstance(slok_json[cand], str) and slok_json[cand].strip():
            translations.append({"language": "hi", "text": slok_json[cand].strip(), "source": "HF3"})
            break

    # fallback: look into common commentator entries for fields like 'et' or 'ht' which may be translations
    if not any(t["language"] == "en" for t in translations):
        # scan nested commentators for 'et' fields
        for v in slok_json.values():
            if isinstance(v, dict) and "et" in v and isinstance(v["et"], str) and v["et"].strip():
                translations.append({"language": "en", "text": v["et"].strip(), "source": "HF3"})
                break

    if not any(t["language"] == "hi" for t in translations):
        for v in slok_json.values():
            if isinstance(v, dict) and any(k in v for k in ("ht","hc","sc")):
                # take concatenation of those fields if present
                parts = []
                for k in ("ht","hc","sc"):
                    if k in v and isinstance(v[k], str) and v[k].strip():
                        parts.append(v[k].strip())
                if parts:
                    translations.append({"language": "hi", "text": "\n\n".join(parts), "source": "HF3"})
                    break

    return translations

def process_hf3():
    # load chapters metadata
    chapters = []
    for chapter_file in sorted(glob(CHAPTERS_GLOB)):
        with open(chapter_file, "r", encoding="utf-8") as fh:
            try:
                chap = json.load(fh)
                chapters.append(chap)
            except Exception as e:
                print("WARN: failed to parse chapter:", chapter_file, e)

    # write chapters metadata
    with open(CHAPTERS_OUT, "w", encoding="utf-8") as fh:
        json.dump(chapters, fh, ensure_ascii=False, indent=2)

    # process sloks
    slok_files = sorted(glob(SLOKS_GLOB))
    if not slok_files:
        print("WARN: no slok files found under", SLOKS_GLOB)

    with open(OUT_FILE, "w", encoding="utf-8") as outfh:
        for slok_file in slok_files:
            with open(slok_file, "r", encoding="utf-8") as fh:
                try:
                    s = json.load(fh)
                except Exception as e:
                    print("WARN: failed to parse:", slok_file, e)
                    continue

            # core fields
            chapter = s.get("chapter") or s.get("ch") or None
            verse = s.get("verse") or s.get("slok_number") or None
            try:
                chapter_i = int(chapter)
            except Exception:
                chapter_i = None
            try:
                verse_i = int(verse)
            except Exception:
                verse_i = None

            slok_id = s.get("_id") or s.get("id") or Path(slok_file).stem
            sanskrit = s.get("slok") or s.get("sanskrit") or s.get("slok_text") or ""
            translit = s.get("transliteration") or s.get("transliteration_text") or ""

            translations = extract_translations(s)
            commentaries = collect_commentaries(s)

            canonical = {
                "scripture": "bhagavad_gita",
                "chapter": chapter_i,
                "verse": verse_i,
                "verse_id": f"{chapter_i}:{verse_i}" if chapter_i and verse_i else slok_id,
                "sanskrit": sanskrit,
                "transliteration": translit,
                "translations": translations,
                "commentaries": commentaries,
                "source": "HF3",
                "source_file": Path(slok_file).name,
                "_id_raw": slok_id
            }

            outfh.write(json.dumps(canonical, ensure_ascii=False) + "\n")

    print("HF3 ingestion complete.")
    print("Wrote:", OUT_FILE, "and", CHAPTERS_OUT)

if __name__ == "__main__":
    process_hf3()
