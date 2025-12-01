# 📂 Dataset Architecture

## GitaVerse-Open-Corpus

This document describes the **internal dataset architecture** used in the GitaVerse-Open-Corpus.

It explains:

- dataset categories
- file formats
- canonical schemas
- processing logic
- naming conventions
- relationships between datasets

---

# 🏛️ 1. Dataset Categories

All processed datasets fall into two major groups:

```
1. Scriptures
2. Question & Answer (QnA)
```

---

# 📘 2. Scriptures Category

These datasets contain:

- Sanskrit verse text
- translations (Hindi / English)
- transliteration
- optional commentary
- metadata

## Included Source Sets:

```
K1  (Kaggle – Verse dataset)
K2  (Kaggle – Verse + transliteration + meaning)
HF2 (HuggingFace – Sanskrit/Hindi/English aligned)
HF3/GH1 (Structured JSON with commentaries)
GH2 (DharmicData Gita subset JSON)
GH3 (Full commentary dataset)
```

---

# 📗 2.1 Canonical Scriptures Output Format (JSONL)

Each verse is stored as:

```
{
  "chapter": 1,
  "verse": 1,
  "verse_id": "1:1",
  "sanskrit": "...",
  "english": "...",
  "hindi": "...",
  "transliteration": "...",
  "commentaries": [
      {
        "author": "Swami Ramsukhdas",
        "language": "hindi",
        "text": "..."
      },
      ...
  ],
  "sources": ["K1","K2","HF2","GH3"]
}
```

Notes:

- fields populated only if present in the source
- commentaries may be empty
- verse_id always normalized `"chapter:verse"`

---

# 💬 3. QnA Category

These datasets contain:

- modern or classical questions
- answers
- aligned to verses
- multiple languages depending on source

## Included Sources:

```
HF1 – Verse-based Q&A (English/Hindi)
K3 – Modern Life Problem Q&A with personas
```

---

# 💡 3.1 Canonical QnA Format

All Q&A datasets are normalized to:

```
{
  "qid": "HF1-en-1:1-001",
  "source": "HF1",
  "chapter": 1,
  "verse": "1:1",
  "question": "...",
  "answer": "..."
}
```

For K3:

```
{
  "qid": "K3-10.1-024",
  "source": "K3",
  "chapter": 10,
  "verse": "10.1",
  "question": "...",
  "answer": "..."
}
```

---

# 🧹 4. Clustered Dataset Outputs

Semantic deduplication produces:

```
datasets/qna/clustered_qna/
  hf1_qa_clustered.jsonl
  k3_qa_clustered.jsonl
```

Format identical to canonical QnA, but:

- duplicates removed
- representative question kept
- unique cluster ids assigned

Example:

```
{
  "cluster_id": 1023,
  "questions": ["Why am I anxious?", "How do I stop worrying?"],
  "answer": "... representative answer ...",
  "chapter": 2,
  "verse": "2:47",
  "source": ["HF1","K3"]
}
```

---

# 🔗 5. Dataset Relationship Overview

```
RAW DATASETS
   |
   v
canonicalization scripts
   |
   v
canonical_* outputs
   |
   v
clustering pipeline
   |
   v
clustered_* outputs
```

---

# 🏷️ 6. Metadata Files

```
datasets/metadata/
    DataSources.csv
```

Contains:

- dataset names
- licenses
- links
- provenance

---

# 🧪 7. Naming Conventions

```
source identifiers:
K1  Kaggle Dataset 1
K2  Kaggle Dataset 2
HF1 HuggingFace QnA
HF2 HuggingFace scripture translation
HF3 HuggingFace commentary
GH1 GitHub same as HF3
GH2 DharmicData
GH3 Commentary dataset
K3  Modern Life Q&A
```

See Also: `datasets\metadata\data_sources.csv`

---

# Master Verse Schema (Post-Normalization)

```
{
  "scripture": "bhagavad_gita",
  "chapter": 11,
  "verse": 16,
  "verse_id": "11.16",  "sanskrit": "...",
  "transliteration": "...",  "translations": [
    {
      "language": "en",
      "author": "...",
      "text": "...",
      "source": "GH3"
    }
  ],  "commentaries": [
    {
      "author": "...",
      "language": "hi",
      "text": "...",
      "source": "GH3"
    }
  ],  "sources": ["K1", "HF2", "GH2", "GH3"]
}
```

All verse ingestion for RAG and LLM training should now use: `datasets/scriptures/master_verses/master_verses.jsonl`
