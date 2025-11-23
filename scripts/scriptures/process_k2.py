import pandas as pd
import json
import re
from pathlib import Path

# -----------------------------------------------------------
# CONFIG
# -----------------------------------------------------------

INPUT_FILE = "./Bhagavad Gita Dataset-Kaggle K2/Bhagwad_Gita.csv"   # <-- change to your actual file path
OUTPUT_JSONL = "./output/k2_canonical.jsonl"

# -----------------------------------------------------------
# HELPERS
# -----------------------------------------------------------

def extract_commentary(wordmeaning):
    """
    Extract commentary after the word-meaning section.
    Look for the keyword 'Commentary'.
    Return cleaned commentary (EN only).
    If 'No Commentary.' or missing, return empty string.
    """
    if not isinstance(wordmeaning, str):
        return ""

    lowered = wordmeaning.lower()

    if "no commentary" in lowered:
        return ""

    # If the dataset includes commentary after "Commentary"
    match = re.search(r"Commentary(.*)$", wordmeaning, flags=re.DOTALL)
    if match:
        commentary = match.group(1).strip()
        return commentary

    return ""


def extract_word_meanings(wordmeaning):
    """
    Extract structured word-by-word pairs from WordMeaning field.
    The format often: <word> meaning? <word> meaning? etc.
    We create a list of {"sanskrit": word, "meaning": meaning} objects.

    Steps:
    - Remove commentary part
    - Split into lines
    - Each line often contains: <word> <meaning>
    - Remove question marks
    """
    if not isinstance(wordmeaning, str):
        return []

    # Remove commentary part
    word_section = re.split(r"Commentary", wordmeaning)[0]

    lines = [l.strip() for l in word_section.split("\n") if l.strip()]

    word_meanings = []
    for line in lines:
        # Example line:
        # "धर्मक्षेत्रे on the holy plain?"
        # We want: word="धर्मक्षेत्रे", meaning="on the holy plain"

        # Try splitting by space once: first token = word, rest = meaning
        # But ensure there's at least 2 parts
        parts = line.split(" ", 1)
        if len(parts) < 2:
            continue

        word = parts[0].strip()
        meaning = parts[1].strip()

        # Remove trailing ? or ?., ?, punctuation
        meaning = meaning.rstrip("?.! ").strip()

        # Skip lines that start with numbering like "1.1", etc.
        if re.match(r"^\d+(\.\d+)?$", word):
            continue

        # Ignore cases where meaning accidentally begins with Sanskrit
        if re.match(r"^[\u0900-\u097F]+$", meaning):
            continue

        word_meanings.append({
            "sanskrit": word,
            "meaning": meaning
        })

    return word_meanings


# -----------------------------------------------------------
# MAIN PROCESSOR
# -----------------------------------------------------------

def process_k2():
    df = pd.read_csv(INPUT_FILE)

    Path("./output").mkdir(exist_ok=True)

    with open(OUTPUT_JSONL, "w", encoding="utf-8") as outfile:
        for idx, row in df.iterrows():

            try:
                chapter = int(row["Chapter"])
                verse = int(row["Verse"])
            except:
                continue

            verse_id = f"{chapter}:{verse}"

            # Core text
            sanskrit = row.get("Shloka", "").strip()
            translit = row.get("Transliteration", "").strip()

            # English translation
            eng_trans = row.get("EngMeaning", "").strip()

            # Hindi translation
            hin_trans = row.get("HinMeaning", "").strip()

            # WordMeaning parsing
            wm_raw = row.get("WordMeaning", "")

            # Extract commentary (EN-only)
            commentary = extract_commentary(wm_raw)

            # Extract structured word-by-word meanings
            word_meanings = extract_word_meanings(wm_raw)

            canonical = {
                "scripture": "bhagavad_gita",
                "chapter": chapter,
                "verse": verse,
                "verse_id": verse_id,

                "sanskrit": sanskrit,
                "transliteration": translit,

                "translations": [
                    {"language": "en", "text": eng_trans, "source": "K2"},
                    {"language": "hi", "text": hin_trans, "source": "K2"}
                ],

                "commentaries": [
                    {"language": "en", "text": commentary, "source": "K2"}
                ],

                "word_meanings": word_meanings
            }

            outfile.write(json.dumps(canonical, ensure_ascii=False) + "\n")

    print("K2 canonical dataset saved →", OUTPUT_JSONL)


if __name__ == "__main__":
    process_k2()
