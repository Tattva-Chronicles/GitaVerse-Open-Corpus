# 📚 GitaVerse — Bhagavad Gita Open Dataset Suite

*A comprehensive, multi-source, multi-language scripture & Q&A corpus for LLM training, RAG systems, research, and spiritual applications.*

---

## 🌟 Overview

**GitaVerse** is an open-source, carefully structured dataset suite built from publicly available Bhagavad Gita datasets across Kaggle, HuggingFace, GitHub, and DharmicData.

We **do not redistribute** any copyrighted or proprietary datasets.
We only publish:

* **Processed and normalized datasets**
* **Unified canonical JSONL formats**
* **Documentation of transformations**
* **Processing scripts used to create them**
* **Metadata & citations**
* **Links to original datasets**

This repo is designed for:

✔ LLM fine-tuning (SFT / instruction tuning)
✔ RAG pipelines with scripture + commentaries
✔ Sanskrit/Hindi/English NLP
✔ App & API development
✔ Philosophical, ethical, & spiritual AI
✔ Academic and devotional study

---

## 📁 Repository Structure

```
/
├── datasets/
│   ├── scriptures/
│   │   ├── K1_original/
│   │   ├── K1_processed/
│   │   ├── K2_original/
│   │   ├── K2_processed/
│   │   ├── HF2_original/
│   │   ├── HF2_processed/
│   │   ├── HF3_original/      (GH1 same)
│   │   ├── HF3_processed/
│   │   ├── GH2_original/
│   │   ├── GH2_processed/
│   │   ├── GH3_original/
│   │   └── GH3_processed/
│   │
│   ├── qna/
│   │   ├── HF1_original/
│   │   ├── HF1_processed/
│   │   ├── K3_original/
│   │   ├── K3_processed/
│   │   ├── clustered_qna/
│   │   └── master_qna/        (future)
│   │
│   └── metadata/
│       ├── data_sources.csv
│       └── LICENSES.md
│
├── scripts/
│   ├── k1_process.py
│   ├── k2_process.py
│   ├── hf1_build.py
│   ├── k3_build.py
│   ├── cluster_qna.py
│   ├── gh3_build.py
│   └── utils/
│       ├── text_cleaning.py
│       ├── sem_cluster_utils.py
│       └── loaders.py
│
├── docs/
│   ├── DATASET_ARCHITECTURE.md
│   ├── SCRIPT_DOCUMENTATION.md
│   ├── USE_CASES.md
│   ├── RAG_AND_LLMS_GUIDE.md
│   └── ROADMAP.md
│
├── LICENSE
├── README.md
└── CONTRIBUTING.md
```

---

# 📦 Dataset Categories

## 1️⃣ **Scripture Datasets**

| Code          | Source      | Description                                                 |
| ------------- | ----------- | ----------------------------------------------------------- |
| **K1**        | Kaggle      | Sanskrit + English meanings                                 |
| **K2**        | Kaggle      | Sanskrit + Transliteration + Hindi + English                |
| **HF2**       | HuggingFace | Fully aligned Sanskrit–Hindi–English verses                 |
| **HF3 / GH1** | GitHub      | Modular dataset (chapter, verse, translation, commentaries) |
| **GH2**       | DharmicData | Chapter-wise structured JSON                                |
| **GH3**       | GitHub      | Multi-author commentary dataset (extensive)                 |

All these are processed into **canonical JSONL formats** ideal for LLM work.

---

## 2️⃣ **Q&A Datasets**

| Code              | Source          | Description                                    |
| ----------------- | --------------- | ---------------------------------------------- |
| **HF1**           | HuggingFace     | Verse-wise Q&A (Hindi + English)               |
| **K3**            | Modern Life Q&A | Persona-based, verse-aligned, deep reflections |
| **Clustered QnA** | Our processing  | Semantic deduplication of 19,902 Q&A pairs     |

These datasets form the backbone of:

* semantic search
* “Did you mean this?” suggestions
* user question enrichment
* training specialized Gita philosophical models

---

# 🧠 Canonical Dataset Schemas

### 📘 **Canonical Verse JSONL**

```
{
  "verse_id": "1:1",
  "chapter": 1,
  "verse_number": 1,
  "sanskrit": "...",
  "transliteration": "...",
  "translations": [...],
  "commentaries": [...],
  "sources": [...],
  "metadata": {...}
}
```

### 💬 **Canonical Q&A JSONL**

```
{
  "qid": "k3_00123",
  "chapter": 2,
  "verse_source": "2.47",
  "question": "...",
  "answer": "...",
  "language": "en",
  "source_dataset": "K3"
}
```

---

# 💡 What You Can Build with This Suite

### 🔹 **RAG Systems**

* Scripture-level retrieval
* Commentary-aware retrieval
* Modern-question similarity retrieval
* Sanskrit/Hindi/English cross-language retrieval

### 🔹 **Fine-Tuned Gita Models**

* SFT models on pure Q&A
* Commentary-aware LLM
* Persona-based (18 personas from K3) “Chapter-specialist” models
* Verse-expansion generator

### 🔹 **Apps & Agents**

* “Ask Krishna” chatbot
* Dharma-based life guidance assistant
* Leadership lessons explainer
* Spiritual journaling & reflection app
* Anxiety/depression support (within ethical limits)

### 🔹 **Educational Tools**

* Quiz generators
* Flashcards
* Sanskrit learning helpers
* Commentary comparison tools

### 🔹 **Research**

* Cross-dataset variance study
* Commentary lineage analysis
* Semantic clustering of verses
* Tropes & theme modeling

This suite is arguably the most complete *open Bhagavad Gita machine-learning dataset collection* currently available.

---

# 🎓 Academic Value

The unified design enables:

* multi-dataset triangulation
* reduction of hallucination
* citation-ready canonical format
* stable IDs for verse, Q&A, commentary
* future expansion to Upanishads, Vedas, Ramayana, Mahabharata

---

# 🔐 Licensing

We publish:

* **only processed files we created**
* **only transformation scripts**
* **no original datasets**

All original datasets remain under their **original licenses** (CC0, CC-BY 4.0, MIT, etc.).
See `datasets/metadata/LICENSES.md`.

---

# 🤝 Contributing

Contributions are welcome!
See `CONTRIBUTING.md` for:

* coding standards
* dataset addition guidelines
* review process

---

# 🚀 Roadmap

Found in `docs/ROADMAP.md`, but highlights include:

* Unified Master Gita Dataset (Scriptures + Commentary + QA)
* Full Gita RAG Pipeline
* iOS & Android App Export
* API Gateway for Verse/Q&A/Commentary
* Multi-language Embedding Index
* Real-time question suggestion engine

---

# 🙏 Acknowledgements

We acknowledge and thank every original dataset creator.
This repository stands entirely on their open-source contributions.

