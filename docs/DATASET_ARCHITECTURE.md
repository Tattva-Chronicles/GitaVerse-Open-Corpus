# **GitaVerse Dataset Architecture**

---

## **1. Introduction**

* What is GitaVerse-Open-Corpus
* Why it exists (AI, RAG, LLM finetuning, structured scriptures, QnA corpora)
* Design principles:
  * Transparency
  * Versioned transformations
  * Canonical JSONL formats
  * Multi-lingual readiness
  * Future-proof merging for Upanishads / Vedas

---

## **2. High-Level Architecture Diagram**

Replicate this (ASCII diagram):

```
GitaVerse-Open-Corpus
│
├── datasets/
│   ├── scriptures/
│   │   ├── K1_processed/       # Cleaned Sanskrit–Hindi–English verses
│   │   ├── K2_processed/       # Verse-wise structured transliteration & word meanings
│   │   ├── HF2_HF3_processed/  # Multi-source canonical verse structures
│   │   └── GH3_processed/      # Commentary + multi-author verse mapping
│   │
│   └── qna/
│       ├── hf1_processed/
│       │   ├── hf1_qa.jsonl
│       │   └── hf1_qa_clustered.jsonl
│       ├── k3_processed/
│       │   ├── k3_qa.jsonl
│       │   └── k3_qa_clustered.jsonl
│       └── master_qna/
|	    ├── unified_qna.jsonl
│           └── qa_master.jsonl   
│
└── docs/
```

---

## **3. Overview of Each Dataset Category**

### 📘 **Scripture Datasets**

For each: K1, K2, HF2, HF3/GH1, GH3

Document:

* Source
* License
* Structure
* Transformations applied
* Why this dataset matters
* How it connects to other datasets

Example content:

```
### K1 — Kaggle: Sanskrit/Hindi/English Verse-Wise
- CSV format
- Issues encountered: duplicated verse ranges, inconsistent verse numbering, long commentary blobs inside “meaning” fields.
- Processing applied:
  - normalisation
  - verse_id extraction
  - expansion of multi-verse entries
  - removal of duplicated blocks
```

Do this for each.

---

## **4. QnA Datasets**

### 📗 HF1

* Verse-aligned
* 5 Qs per verse
* High-quality
* Languages: en + hi
* Structure before and after processing

### 📗 K3

* Persona-based
* Modern-life questions
* 7000+ QnA pairs
* Must be canonicalized to match HF1

---

## **5. Canonical Formats (Critical Section)**

Clearly document:

### **5.1 Canonical Verse Format**

(From K2 + HF2 + GH3)

```json
{
  "chapter": 1,
  "verse": 1,
  "verse_id": "1:1",
  "sanskrit": "…",
  "transliteration": "…",
  "translation": { "en": "...", "hi": "..." },
  "word_meanings": { ... },
  "commentary": {
      "Swami Sivananda": "…",
      "Chinmayananda": "…"
  },
  "source": "GH3"
}
```

### **5.2 Canonical QnA Format**

(both HF1 + K3 standardized)

```json
{
  "qid": "HF1-en-1:1-001",
  "source": "HF1",
  "chapter": 1,
  "verse_id": "1:1",
  "question": "...",
  "answer": "..."
}
```

---

## **6. Clustering Architecture**

* Semantic clustering is used.
* Duplicate removal rationale.
* all-MiniLM-L6-v2 Model used.
* Cosine threshold used
* Performance of the clustering
* Final reductions:
  * HF1: 7000 → 3596
  * K3: ~12902 → 7932

---

## **7. Future Merging Layer (NOT DONE NOW)**

Document future steps but mark them “Not executed yet”.

---

## **8. Versioning Policy**

* All processed data regenerated from scripts
* Only transformations stored
* Original datasets not stored (links only)

---

## **9. Credits & Licenses**

See this: `GitaVerse-Open-Corpus\datasets\metadata\data_sources.csv`

---
