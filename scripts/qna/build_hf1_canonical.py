import pandas as pd
import json
from pathlib import Path

# -----------------------------------------------------------
# CONFIG
# -----------------------------------------------------------

EN_INPUT = "./Bhagavad-Gita-QA/English/english.csv"
HI_INPUT = "./Bhagavad-Gita-QA/Hindi/hindi.csv"

OUTPUT_JSONL = "./output/hf1_qa.jsonl"

# -----------------------------------------------------------
# HELPER: AUTO QID GENERATOR
# -----------------------------------------------------------

def make_qid(lang, chapter, verse, index):
    """
    Example:
    HF1-en-1:1-001
    HF1-hi-2:14-003
    """
    return f"HF1-{lang}-{chapter}:{verse}-{index:03d}"

# -----------------------------------------------------------
# PROCESSOR
# -----------------------------------------------------------

def process_hf1():

    Path("./output").mkdir(exist_ok=True)

    # Load English & Hindi datasets
    df_en = pd.read_csv(EN_INPUT)
    df_hi = pd.read_csv(HI_INPUT)

    # Normalize columns (make sure exact naming)
    df_en.columns = df_en.columns.str.strip().str.lower()
    df_hi.columns = df_hi.columns.str.strip().str.lower()

    # Required columns: chapter_no, verse_no, question, answer
    required = {"chapter_no", "verse_no", "question", "answer"}
    if not required.issubset(df_en.columns):
        raise Exception("English HF1 CSV missing required columns.")

    if not required.issubset(df_hi.columns):
        raise Exception("Hindi HF1 CSV missing required columns.")

    # Output file
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as outfile:

        # -----------------------------------------------------------
        # PROCESS ENGLISH QA
        # -----------------------------------------------------------
        for idx, row in df_en.iterrows():

            chapter = int(row["chapter_no"])
            verse = int(row["verse_no"])
            verse_id = f"{chapter}:{verse}"

            qid = make_qid("en", chapter, verse, idx + 1) # type: ignore

            canonical = {
                "qid": qid,
                "source": "HF1",
                "authority": "secondary",

                "language": "en",
                "chapter": chapter,
                "verse": verse,
                "verse_id": verse_id,

                "question": str(row.get("question", "")).strip(),
                "answer": str(row.get("answer", "")).strip()
            }

            outfile.write(json.dumps(canonical, ensure_ascii=False) + "\n")

        # -----------------------------------------------------------
        # PROCESS HINDI QA
        # -----------------------------------------------------------
        for idx, row in df_hi.iterrows():

            chapter = int(row["chapter_no"])
            verse = int(row["verse_no"])
            verse_id = f"{chapter}:{verse}"

            qid = make_qid("hi", chapter, verse, idx + 1) # type: ignore

            canonical = {
                "qid": qid,
                "source": "HF1",
                "authority": "secondary",

                "language": "hi",
                "chapter": chapter,
                "verse": verse,
                "verse_id": verse_id,

                "question": str(row.get("question", "")).strip(),
                "answer": str(row.get("answer", "")).strip()
            }

            outfile.write(json.dumps(canonical, ensure_ascii=False) + "\n")

    print("HF1 canonical QA dataset saved →", OUTPUT_JSONL)


# -----------------------------------------------------------
# RUN
# -----------------------------------------------------------

if __name__ == "__main__":
    process_hf1()
