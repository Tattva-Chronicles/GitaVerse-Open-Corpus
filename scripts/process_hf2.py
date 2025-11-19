import pandas as pd
import json
from pathlib import Path

# -----------------------------------------------------------
# CONFIG
# -----------------------------------------------------------

INPUT_FILE = "./Bhagavad-Gita_Dataset/geeta_dataset.csv"
OUTPUT_JSONL = "./output/hf2_canonical.jsonl"

# -----------------------------------------------------------
# MAIN PROCESSOR
# -----------------------------------------------------------

def process_hf2():

    Path("./output").mkdir(exist_ok=True)

    df = pd.read_csv(INPUT_FILE)
    df.columns = df.columns.str.strip().str.lower()  # normalize col names

    with open(OUTPUT_JSONL, "w", encoding="utf-8") as outfile:

        for idx, row in df.iterrows():

            try:
                chapter = int(row["chapter"])
                verse = int(row["verse"])
            except:
                continue

            verse_id = f"{chapter}:{verse}"

            # Extract fields
            sanskrit = str(row.get("sanskrit", "")).strip()
            translit = str(row.get("transliteration", "")).strip()
            eng_trans = str(row.get("english", "")).strip()
            hi_trans = str(row.get("hindi", "")).strip()

            canonical = {
                "scripture": "bhagavad_gita",
                "chapter": chapter,
                "verse": verse,
                "verse_id": verse_id,

                "sanskrit": sanskrit,
                "transliteration": translit,

                "translations": [
                    {"language": "en", "text": eng_trans, "source": "HF2"},
                    {"language": "hi", "text": hi_trans, "source": "HF2"}
                ],

                "commentaries": [],
                "word_meanings": []
            }

            outfile.write(json.dumps(canonical, ensure_ascii=False) + "\n")

    print("HF2 canonical dataset saved →", OUTPUT_JSONL)


if __name__ == "__main__":
    process_hf2()
