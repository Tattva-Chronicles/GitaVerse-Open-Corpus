#!/usr/bin/env python3
"""
GitaVerse Master Builder

Reads all canonical/normalized verse datasets from ./output and produces:
  1) output/master_verses.jsonl       – unified master verse file
  2) output/authors_index.json        – canonical author registry
  3) output/chapters_master.json      – chapter metadata with verse counts

Input files used (if present in ./output):

  - k1_canonical.jsonl
  - k2_canonical.jsonl
  - hf2_canonical.jsonl
  - hf3_canonical.jsonl
  - gh2_clean.jsonl
  - gh3_verses_normalized.jsonl
  - gh3_translations.jsonl
  - gh3_commentaries.jsonl
  - hf3_chapters.json
"""

import os
import json
from collections import defaultdict, Counter

# ---------- CONFIG ----------

SCRIPTURE_NAME = "bhagavad_gita"

# Priority order for picking the "primary" sanskrit/transliteration text
SOURCE_PRIORITY = ["GH3", "GH2", "HF2", "K2", "K1", "HF3"]

# Input file names inside ./output
INPUT_FILES = {
    "K1": "k1_canonical.jsonl",
    "K2": "k2_canonical.jsonl",
    "HF2": "hf2_canonical.jsonl",
    "HF3_CANON": "hf3_canonical.jsonl",
    "GH2": "gh2_clean.jsonl",
    "GH3_VERSES": "gh3_verses_normalized.jsonl",
    "GH3_TRANSLATIONS": "gh3_translations.jsonl",
    "GH3_COMMENTARIES": "gh3_commentaries.jsonl",
    "HF3_CHAPTERS": "hf3_chapters.json",
}

# Output paths (all under ./output)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

MASTER_VERSES_PATH = os.path.join(OUTPUT_DIR, "master_verses.jsonl")
AUTHORS_INDEX_PATH = os.path.join(OUTPUT_DIR, "authors_index.json")
CHAPTERS_MASTER_PATH = os.path.join(OUTPUT_DIR, "chapters_master.json")


# ---------- UTILITIES ----------

def iter_jsonl(path):
    """Yield JSON objects line by line from a .jsonl file."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def safe_load_json(path, default=None):
    """Load a JSON file safely."""
    if not os.path.exists(path):
        print(f"[WARN] Missing JSON file: {path}")
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def slugify_author(name: str) -> str:
    """Turn a raw author name into a simple slug id."""
    name = name.strip().lower()
    # remove honorifics that show up often, but keep fairly conservative
    for prefix in ["srimad ", "shri ", "sri ", "swami ", "acharya ", "ācārya "]:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    # collapse non-alnum to single hyphen
    out = []
    last_sep = False
    for ch in name:
        if ch.isalnum():
            out.append(ch)
            last_sep = False
        else:
            if not last_sep:
                out.append("-")
                last_sep = True
    slug = "".join(out).strip("-")
    return slug or "unknown"


# Manual alias mapping for obvious duplicates across datasets.
# Extend this as you discover more.
AUTHOR_ALIASES = {
    # Ramanuja
    "Sri Ramanujacharya": "ramanuja",
    "Sri Ramanuja": "ramanuja",
    "Ramanuja": "ramanuja",

    # Shankara
    "Sri Shankaracharya": "shankara",
    "Adi Shankaracharya": "shankara",

    # Prabhupada
    "A.C. Bhaktivedanta Swami Prabhupada": "prabhupada",
    "Srila Prabhupada": "prabhupada",

    # Gambirananda
    "Swami Gambirananda": "gambirananda",

    # Sivananda
    "Swami Sivananda": "sivananda",

    # Chinmayananda
    "Swami Chinmayananda": "chinmayananda",

    # Ramsukhdas
    "Swami Ramsukhdas": "ramsukhdas",

    # Tejomayananda
    "Swami Tejomayananda": "tejomayananda",
}


def normalize_author(raw_name: str):
    """
    Normalize an author name to (author_id, display_name).
    raw_name: original string from dataset.
    """
    if not raw_name:
        return None, None
    raw_name = raw_name.strip()
    canonical_id = AUTHOR_ALIASES.get(raw_name)
    if canonical_id is None:
        canonical_id = slugify_author(raw_name)
    display_name = raw_name
    return canonical_id, display_name


def normalize_lang(lang: str):
    """Normalize language strings to simple codes: en, hi, sa etc."""
    if not lang:
        return None
    l = lang.strip().lower()
    # Common mappings
    mapping = {
        "english": "en",
        "en": "en",
        "hindi": "hi",
        "hi": "hi",
        "sanskrit": "sa",
        "sa": "sa",
        "sanskrit (devanagari)": "sa",
    }
    return mapping.get(l, l)


# ---------- GLOBAL STATE ----------

# (chapter, verse) -> master verse record
master_verses = {}

# GH3 verse_id -> (chapter, verse)
gh3_verse_id_to_cv = {}

# Author index accumulator:
# author_id -> dict(display_name:str, raw_names:set, sources:set, languages:set, roles:set)
authors_index_acc = defaultdict(lambda: {
    "display_name": None,
    "raw_names": set(),
    "sources": set(),
    "languages": set(),
    "roles": set(),
})


def get_master_key(chapter: int, verse: int):
    return f"{chapter}:{verse}"


def upsert_master_verse(chapter: int, verse: int):
    """Ensure a master verse entry exists and return it."""
    key = get_master_key(chapter, verse)
    if key not in master_verses:
        verse_id = f"{chapter}:{verse}"
        verse_uid = f"BG-{chapter}-{verse}"
        master_verses[key] = {
            "scripture": SCRIPTURE_NAME,
            "chapter": chapter,
            "verse": verse,
            "verse_id": verse_id,
            "verse_uid": verse_uid,
            "sanskrit": None,                 # primary, filled later
            "transliteration": None,          # primary, filled later
            "sanskrit_variants": [],          # [{text, source}]
            "transliteration_variants": [],   # [{text, source}]
            "translations": [],               # [{language, text, source, author_id?, author_name?, author_name_raw?}]
            "commentaries": [],               # [{language, text, source, author_*...}]
            "word_meanings": [],              # arbitrary list of objects/strings tagged with source
            "sources": set(),                 # converted to list later
            "provenance": [],                 # [{source, source_file?, raw_id?}]
        }
    return master_verses[key]


def add_author_entry(raw_name, source, language, role):
    """Record author info into authors_index_acc."""
    if not raw_name:
        return
    author_id, display_name = normalize_author(raw_name)
    if not author_id:
        return
    entry = authors_index_acc[author_id]
    # Prefer the longest / richest display name
    if entry["display_name"] is None or len(display_name) > len(entry["display_name"]):
        entry["display_name"] = display_name
    entry["raw_names"].add(raw_name)
    if source:
        entry["sources"].add(source)
    if language:
        entry["languages"].add(language)
    if role:
        entry["roles"].add(role)
    return author_id, display_name


# ---------- PROCESSORS FOR EACH DATASET ----------

def process_k1(path):
    if not os.path.exists(path):
        print(f"[INFO] K1 file not found: {path}")
        return
    print(f"[INFO] Processing K1: {path}")
    source = "K1"
    for row in iter_jsonl(path):
        chapter = row.get("chapter")
        verse = row.get("verse")
        if chapter is None or verse is None:
            continue
        mv = upsert_master_verse(chapter, verse)

        s = row.get("sanskrit")
        if s:
            mv["sanskrit_variants"].append({"text": s, "source": source})

        tr = row.get("transliteration")
        if tr:
            mv["transliteration_variants"].append({"text": tr, "source": source})

        # Translations (no explicit author)
        for t in row.get("translations", []):
            lang = normalize_lang(t.get("language"))
            mv["translations"].append({
                "language": lang,
                "text": t.get("text"),
                "source": source,
            })

        # Commentaries (anonymous)
        for c in row.get("commentaries", []):
            lang = normalize_lang(c.get("language"))
            mv["commentaries"].append({
                "language": lang,
                "text": c.get("text"),
                "source": source,
            })

        mv["sources"].add(source)
        # Basic provenance
        mv["provenance"].append({"source": source})


def process_k2(path):
    if not os.path.exists(path):
        print(f"[INFO] K2 file not found: {path}")
        return
    print(f"[INFO] Processing K2: {path}")
    source = "K2"
    for row in iter_jsonl(path):
        chapter = row.get("chapter")
        verse = row.get("verse")
        if chapter is None or verse is None:
            continue
        mv = upsert_master_verse(chapter, verse)

        s = row.get("sanskrit")
        if s:
            mv["sanskrit_variants"].append({"text": s, "source": source})

        tr = row.get("transliteration")
        if tr:
            mv["transliteration_variants"].append({"text": tr, "source": source})

        for t in row.get("translations", []):
            lang = normalize_lang(t.get("language"))
            mv["translations"].append({
                "language": lang,
                "text": t.get("text"),
                "source": source,
            })

        for c in row.get("commentaries", []):
            lang = normalize_lang(c.get("language"))
            mv["commentaries"].append({
                "language": lang,
                "text": c.get("text"),
                "source": source,
            })

        # word_meanings could be [] or more structured
        for wm in row.get("word_meanings", []):
            entry = {"source": source, "value": wm}
            mv["word_meanings"].append(entry)

        mv["sources"].add(source)
        mv["provenance"].append({"source": source})


def process_hf2(path):
    if not os.path.exists(path):
        print(f"[INFO] HF2 file not found: {path}")
        return
    print(f"[INFO] Processing HF2: {path}")
    source = "HF2"
    for row in iter_jsonl(path):
        chapter = row.get("chapter")
        verse = row.get("verse")
        if chapter is None or verse is None:
            continue
        mv = upsert_master_verse(chapter, verse)

        s = row.get("sanskrit")
        if s:
            mv["sanskrit_variants"].append({"text": s, "source": source})

        tr = row.get("transliteration")
        if tr:
            mv["transliteration_variants"].append({"text": tr, "source": source})

        for t in row.get("translations", []):
            lang = normalize_lang(t.get("language"))
            mv["translations"].append({
                "language": lang,
                "text": t.get("text"),
                "source": source,
            })

        for c in row.get("commentaries", []):
            lang = normalize_lang(c.get("language"))
            mv["commentaries"].append({
                "language": lang,
                "text": c.get("text"),
                "source": source,
            })

        for wm in row.get("word_meanings", []):
            entry = {"source": source, "value": wm}
            mv["word_meanings"].append(entry)

        mv["sources"].add(source)
        mv["provenance"].append({"source": source})


def process_hf3_canonical(path):
    if not os.path.exists(path):
        print(f"[INFO] HF3 canonical file not found: {path}")
        return
    print(f"[INFO] Processing HF3 canonical: {path}")
    source = "HF3"
    for row in iter_jsonl(path):
        chapter = row.get("chapter")
        verse = row.get("verse")
        if chapter is None or verse is None:
            continue
        mv = upsert_master_verse(chapter, verse)

        s = row.get("sanskrit")
        if s:
            mv["sanskrit_variants"].append({"text": s, "source": source})

        tr = row.get("transliteration")
        if tr:
            mv["transliteration_variants"].append({"text": tr, "source": source})

        for t in row.get("translations", []):
            lang = normalize_lang(t.get("language"))
            mv["translations"].append({
                "language": lang,
                "text": t.get("text"),
                "source": source,
            })

        for c in row.get("commentaries", []):
            lang = normalize_lang(c.get("language"))
            raw_name = c.get("author")
            author_id, display_name = add_author_entry(raw_name, source, lang, role="commentary")
            mv["commentaries"].append({
                "author_id": author_id,
                "author_name": display_name,
                "author_name_raw": raw_name,
                "language": lang,
                "text": c.get("text"),
                "source": source,
                "meta": {
                    "raw_key": c.get("raw_key"),
                },
            })

        mv["sources"].add(source)
        mv["provenance"].append({
            "source": source,
            "source_file": row.get("source_file"),
            "raw_id": row.get("_id_raw"),
        })


def process_gh2(path):
    if not os.path.exists(path):
        print(f"[INFO] GH2 file not found: {path}")
        return
    print(f"[INFO] Processing GH2: {path}")
    source = "GH2"
    for row in iter_jsonl(path):
        chapter = row.get("chapter")
        verse = row.get("verse")
        if chapter is None or verse is None:
            continue
        mv = upsert_master_verse(chapter, verse)

        s = row.get("sanskrit")
        if s:
            mv["sanskrit_variants"].append({"text": s, "source": source})

        tr = row.get("transliteration")
        if tr:
            mv["transliteration_variants"].append({"text": tr, "source": source})

        translations = row.get("translations", {})
        # translations is dict: lang -> [ {author, text, source} ]
        for lang_key, entries in translations.items():
            for t in entries:
                lang = normalize_lang(t.get("language") or lang_key)
                raw_name = t.get("author")
                author_id, display_name = add_author_entry(raw_name, source, lang, role="translation")
                mv["translations"].append({
                    "language": lang,
                    "text": t.get("text"),
                    "source": source,
                    "author_id": author_id,
                    "author_name": display_name,
                    "author_name_raw": raw_name,
                })

        for c in row.get("commentaries", []):
            lang = normalize_lang(c.get("language"))
            raw_name = c.get("author")
            author_id, display_name = add_author_entry(raw_name, source, lang, role="commentary")
            mv["commentaries"].append({
                "author_id": author_id,
                "author_name": display_name,
                "author_name_raw": raw_name,
                "language": lang,
                "text": c.get("text"),
                "source": source,
            })

        metadata = row.get("metadata", {})
        mv["sources"].add(source)
        mv["provenance"].append({
            "source": metadata.get("source", source),
            "source_file": metadata.get("source_file"),
            "raw_id": metadata.get("_id_raw"),
        })


def process_gh3_verses(path):
    """First pass of GH3: verse spine + word_meanings + verse_id mapping."""
    if not os.path.exists(path):
        print(f"[INFO] GH3 verses file not found: {path}")
        return
    print(f"[INFO] Processing GH3 verses: {path}")
    source = "GH3"
    for row in iter_jsonl(path):
        raw = row.get("raw_verse", {}) or {}
        chapter = raw.get("chapter_number") or row.get("chapter")
        verse_num = raw.get("verse_number") or row.get("verse_number")
        verse_id = str(row.get("verse_id"))
        if chapter is None or verse_num is None:
            continue
        chapter = int(chapter)
        verse_num = int(verse_num)
        mv = upsert_master_verse(chapter, verse_num)

        # Map GH3 verse_id -> (chapter, verse)
        if verse_id:
            gh3_verse_id_to_cv[verse_id] = (chapter, verse_num)

        # Sanskrit / transliteration
        s = row.get("sanskrit") or raw.get("text")
        if s:
            mv["sanskrit_variants"].append({"text": s, "source": source})

        tr = row.get("transliteration") or raw.get("transliteration")
        if tr:
            mv["transliteration_variants"].append({"text": tr, "source": source})

        wm = raw.get("word_meanings")
        if wm:
            # word_meanings is a string here
            mv["word_meanings"].append({
                "source": source,
                "value": wm,
                "format": "string",
            })

        mv["sources"].add(source)
        mv["provenance"].append({
            "source": source,
            "raw_id": raw.get("externalId") or raw.get("id") or verse_id,
        })


def process_gh3_translations(path):
    """Attach GH3 translations based on verse_id mapping."""
    if not os.path.exists(path):
        print(f"[INFO] GH3 translations file not found: {path}")
        return
    print(f"[INFO] Processing GH3 translations: {path}")
    source = "GH3"
    for row in iter_jsonl(path):
        verse_id = str(row.get("verse_id"))
        if verse_id not in gh3_verse_id_to_cv:
            continue
        chapter, verse = gh3_verse_id_to_cv[verse_id]
        mv = upsert_master_verse(chapter, verse)

        t = row.get("text") or {}
        raw_name = t.get("authorName")
        lang = normalize_lang(t.get("lang") or row.get("language"))
        description = t.get("description")

        author_id, display_name = add_author_entry(raw_name, source, lang, role="translation")
        mv["translations"].append({
            "language": lang,
            "text": description,
            "source": source,
            "author_id": author_id,
            "author_name": display_name,
            "author_name_raw": raw_name,
        })

        mv["sources"].add(source)


def process_gh3_commentaries(path):
    """Attach GH3 commentaries based on verse_id mapping."""
    if not os.path.exists(path):
        print(f"[INFO] GH3 commentaries file not found: {path}")
        return
    print(f"[INFO] Processing GH3 commentaries: {path}")
    source = "GH3"
    for row in iter_jsonl(path):
        verse_id = str(row.get("verse_id"))
        if verse_id not in gh3_verse_id_to_cv:
            continue
        chapter, verse = gh3_verse_id_to_cv[verse_id]
        mv = upsert_master_verse(chapter, verse)

        raw_name = row.get("author_name")
        lang = normalize_lang(row.get("language"))
        text = row.get("commentary")

        author_id, display_name = add_author_entry(raw_name, source, lang, role="commentary")
        mv["commentaries"].append({
            "author_id": author_id,
            "author_name": display_name,
            "author_name_raw": raw_name,
            "language": lang,
            "text": text,
            "source": source,
            "meta": {
                "author_id": row.get("author_id"),
            },
        })

        mv["sources"].add(source)


# ---------- FINALIZATION ----------

def finalize_master_texts():
    """Choose primary sanskrit/transliteration based on SOURCE_PRIORITY."""
    for mv in master_verses.values():
        # Primary Sanskrit
        chosen_s = None
        for src in SOURCE_PRIORITY:
            for v in mv["sanskrit_variants"]:
                if v.get("source") == src:
                    chosen_s = v.get("text")
                    break
            if chosen_s:
                break
        if not chosen_s and mv["sanskrit_variants"]:
            chosen_s = mv["sanskrit_variants"][0].get("text")
        mv["sanskrit"] = chosen_s

        # Primary transliteration
        chosen_tr = None
        for src in SOURCE_PRIORITY:
            for v in mv["transliteration_variants"]:
                if v.get("source") == src:
                    chosen_tr = v.get("text")
                    break
            if chosen_tr:
                break
        if not chosen_tr and mv["transliteration_variants"]:
            chosen_tr = mv["transliteration_variants"][0].get("text")
        mv["transliteration"] = chosen_tr

        # Convert sources set to sorted list
        mv["sources"] = sorted(mv["sources"])


def write_master_verses():
    print(f"[INFO] Writing master verses -> {MASTER_VERSES_PATH}")
    with open(MASTER_VERSES_PATH, "w", encoding="utf-8") as f:
        # sort by (chapter, verse)
        for key in sorted(master_verses.keys(), key=lambda k: (int(k.split(":")[0]), int(k.split(":")[1]))):
            mv = master_verses[key]
            # Make sure sets in provenance entries are not present; all values are JSON-serializable
            f.write(json.dumps(mv, ensure_ascii=False) + "\n")


def write_authors_index():
    print(f"[INFO] Writing authors index -> {AUTHORS_INDEX_PATH}")
    out = []
    for author_id, data in authors_index_acc.items():
        entry = {
            "author_id": author_id,
            "display_name": data["display_name"] or author_id,
            "raw_names": sorted(data["raw_names"]),
            "sources": sorted(data["sources"]),
            "languages": sorted(data["languages"]),
            "roles": sorted(data["roles"]),
        }
        out.append(entry)
    # sort alphabetically
    out.sort(key=lambda x: x["author_id"])
    with open(AUTHORS_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


def write_chapters_master():
    hf3_chapters_path = os.path.join(OUTPUT_DIR, INPUT_FILES["HF3_CHAPTERS"])
    chapters = safe_load_json(hf3_chapters_path, default=[])
    # Build counts from master verses
    chapter_counts = Counter()
    for mv in master_verses.values():
        chapter_counts[mv["chapter"]] += 1

    # Index by chapter_number if present
    by_num = {}
    for ch in chapters or []:
        num = ch.get("chapter_number") or ch.get("chapter") or ch.get("number")
        if num is not None:
            by_num[int(num)] = ch

    # Build unified chapter metadata
    all_ch_nums = set(chapter_counts.keys()) | set(by_num.keys())
    out = []
    for num in sorted(all_ch_nums):
        base = by_num.get(num, {"chapter_number": num})
        cm = dict(base)
        cm["chapter_number"] = num
        cm["master_verse_count"] = chapter_counts.get(num, 0)
        out.append(cm)

    print(f"[INFO] Writing chapters master -> {CHAPTERS_MASTER_PATH}")
    with open(CHAPTERS_MASTER_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


# ---------- MAIN ----------

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Process all verse sources
    process_k1(os.path.join(OUTPUT_DIR, INPUT_FILES["K1"]))
    process_k2(os.path.join(OUTPUT_DIR, INPUT_FILES["K2"]))
    process_hf2(os.path.join(OUTPUT_DIR, INPUT_FILES["HF2"]))
    process_hf3_canonical(os.path.join(OUTPUT_DIR, INPUT_FILES["HF3_CANON"]))
    process_gh2(os.path.join(OUTPUT_DIR, INPUT_FILES["GH2"]))

    # GH3 is relational: verses first, then translations, then commentaries
    process_gh3_verses(os.path.join(OUTPUT_DIR, INPUT_FILES["GH3_VERSES"]))
    process_gh3_translations(os.path.join(OUTPUT_DIR, INPUT_FILES["GH3_TRANSLATIONS"]))
    process_gh3_commentaries(os.path.join(OUTPUT_DIR, INPUT_FILES["GH3_COMMENTARIES"]))

    # 2. Finalize and write outputs
    finalize_master_texts()
    write_master_verses()
    write_authors_index()
    write_chapters_master()

    print("[INFO] Done.")


if __name__ == "__main__":
    main()
