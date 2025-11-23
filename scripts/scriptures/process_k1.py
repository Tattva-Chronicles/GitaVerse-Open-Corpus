import pandas as pd
import json
import re
from pathlib import Path

# -----------------------------------------------------------
# CONFIG
# -----------------------------------------------------------

INPUT_FILE = "./Bhagavad Gita verse-wise(English,Hindi,Sanskrit)-YashNarnaware-Kaggle K1/bhagavad_gita.csv"
OUTPUT_JSONL = "./output/k1_canonical.jsonl"

# -----------------------------------------------------------
# HELPERS
# -----------------------------------------------------------

def parse_verse_number(text):
    """
    Extract chapter and verse(s).
    Examples:
        "Chapter 1, Verse 1"       → (1, [1])
        "Chapter 1, Verse 4-6"     → (1, [4,5,6])
    """
    match = re.search(r"Chapter\s+(\d+),\s*Verse\s+([\d-]+)", text)
    if not match:
        return None, []

    chapter = int(match.group(1))
    verse_part = match.group(2)

    if "-" in verse_part:
        start, end = verse_part.split("-")
        verses = list(range(int(start), int(end) + 1))
    else:
        verses = [int(verse_part)]

    return chapter, verses


def clean_commentary(text):
    """Convert 'Not available' → ''"""
    if isinstance(text, str) and text.strip().lower() in ["not available", "na", "none", ""]:
        return ""
    return text.strip() if isinstance(text, str) else ""


# -----------------------------------------------------------
# MAIN PROCESSOR
# -----------------------------------------------------------

def process_k1():
    df = pd.read_csv(INPUT_FILE)

    # Remove the first column if it's unnamed (index column)
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])

    # Deduplicate rows based on Sanskrit + English translation + Hindi translation
    df = df.drop_duplicates(
        subset=[
            "verse_in_sanskrit",
            "translation_in_english",
            "translation_in_hindi",
            "meaning_in_english",
            "meaning_in_hindi"
        ],
        keep="first"
    )

    Path("./output").mkdir(exist_ok=True)

    with open(OUTPUT_JSONL, "w", encoding="utf-8") as outfile:
        for idx, row in df.iterrows():

            chapter, verses = parse_verse_number(row['verse_number'])
            if chapter is None or len(verses) == 0:
                continue  # skip malformed rows

            # Prepare base fields
            sanskrit = row["verse_in_sanskrit"]
            translit = row["sanskrit_verse_transliteration"]

            # Clean translations
            en_trans = row["translation_in_english"]
            hi_trans = row["translation_in_hindi"]

            # Clean commentaries
            en_comment = clean_commentary(row["meaning_in_english"])
            hi_comment = clean_commentary(row["meaning_in_hindi"])

            for verse in verses:
                verse_id = f"{chapter}:{verse}"

                canonical = {
                    "scripture": "bhagavad_gita",
                    "chapter": chapter,
                    "verse": verse,
                    "verse_id": verse_id,

                    "sanskrit": sanskrit,
                    "transliteration": translit,

                    "translations": [
                        {"language": "en", "text": en_trans, "source": "K1"},
                        {"language": "hi", "text": hi_trans, "source": "K1"}
                    ],

                    "commentaries": [
                        {"language": "en", "text": en_comment, "source": "K1"},
                        {"language": "hi", "text": hi_comment, "source": "K1"}
                    ]
                }

                outfile.write(json.dumps(canonical, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    process_k1()
    print("K1 canonical dataset saved →", OUTPUT_JSONL)
