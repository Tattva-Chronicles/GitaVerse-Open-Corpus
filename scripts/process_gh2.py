import os
import json
import re
from pathlib import Path
import unicodedata

# -----------------------------
# CONFIG
# -----------------------------
GH2_DIR = r"./DharmicData/SrimadBhagvadGita/"
OUTPUT_FILE = "output/gh2_clean.jsonl"

# -----------------------------
# LANGUAGE DETECTION
# -----------------------------
def detect_language(text: str):
    """
    Detect language based on character ranges.
    Returns: "hi" (Hindi), "sa" (Sanskrit), "en" (English)
    """
    if re.search(r"[\u0900-\u097F]", text):
        # Contains Devanagari → Could be Sanskrit or Hindi
        # Sanskrit tends to contain no spaces or itihasa commentary markers
        # Hindi translations have more modern constructs and punctuation
        if "।" in text or "।।" in text:
            return "hi"   # Most GH2 Hindi uses ।।
        return "sa"       # Rare case: pure Sanskrit commentary
    else:
        return "en"

# -----------------------------
# AUTHOR NORMALIZATION
# -----------------------------
def normalize_author(name: str):
    """
    Normalize authors to a clean canonical form.
    """
    name = name.strip()
    name = name.replace("_", " ")
    name = name.replace("  ", " ")
    name = name.title()

    # Custom normalization rules
    replacements = {
        "Swami Ramsukhdas": "Swami Ramsukhdas",
        "Sri Harikrishnadas Goenka": "Sri Harikrishnadas Goenka",
        "Swami Sivananda": "Swami Sivananda",
        "Swami Tejomayananda": "Swami Tejomayananda",
        "Swami Gambhirananda": "Swami Gambhirananda",
        "Swami Adidevananda": "Swami Adidevananda",
        "Sri Ramanuja": "Sri Ramanuja",
        "Sri Anandgiri": "Sri Anandgiri",
        "Sri Abhinavgupta": "Sri Abhinavagupta",
        "Sri Madhusudan Saraswati": "Sri Madhusudan Saraswati",
        "Sri Dhanpati": "Sri Dhanpati",
        "Dr. S. Sankaranarayan": "Dr. S. Sankaranarayan",
        "Shri Purohit Swami": "Shri Purohit Swami"
    }

    for key, val in replacements.items():
        if name.lower() == key.lower():
            return val

    return name

# -----------------------------
# CLEAN TEXT
# -----------------------------
def clean_text(text: str):
    if not isinstance(text, str):
        return ""

    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r", "").strip()
    return text

# -----------------------------
# MAIN PARSER
# -----------------------------
def parse_gh2():
    output_path = Path(OUTPUT_FILE)
    if output_path.exists():
        os.remove(output_path)

    chapter_files = sorted([f for f in os.listdir(GH2_DIR) if f.endswith(".json")])

    total = 0
    with open(output_path, "a", encoding="utf-8") as outfile:

        for filename in chapter_files:
            full_path = os.path.join(GH2_DIR, filename)
            print(f"Processing: {filename}")

            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            verses = data.get("BhagavadGitaChapter", [])

            for verse_obj in verses:
                chapter = int(verse_obj.get("chapter"))
                verse = int(verse_obj.get("verse"))

                # Base object
                entry = {
                    "chapter": chapter,
                    "verse": verse,
                    "sanskrit": clean_text(verse_obj.get("text", "")),
                    "transliteration": None,   # GH2 doesn't include transliteration
                    "translations": {"en": [], "hi": []},
                    "commentaries": [],
                    "metadata": {
                        "source": "GH2",
                        "source_file": filename,
                        "_id_raw": f"{chapter}.{verse}"
                    }
                }

                # --------------------------
                # Process commentaries
                # --------------------------
                comm = verse_obj.get("commentaries", {})

                for author, content in comm.items():
                    author_clean = normalize_author(author)
                    text_clean = clean_text(content)
                    lang = detect_language(text_clean)

                    entry["commentaries"].append({
                        "author": author_clean,
                        "text": text_clean,
                        "language": lang,
                        "source": "GH2"
                    })

                # --------------------------
                # Process translations
                # --------------------------
                trans = verse_obj.get("translations", {})

                for author, content in trans.items():
                    author_clean = normalize_author(author)
                    text_clean = clean_text(content)
                    lang = detect_language(text_clean)

                    entry["translations"].setdefault(lang, [])

                    entry["translations"][lang].append({
                        "author": author_clean,
                        "text": text_clean,
                        "source": "GH2"
                    })

                # Write to file
                outfile.write(json.dumps(entry, ensure_ascii=False) + "\n")
                total += 1

    print(f"\n✔ GH2 ingestion complete. Total verses processed: {total}")
    print(f"✔ Output written to {OUTPUT_FILE}")

# Run
if __name__ == "__main__":
    parse_gh2()
