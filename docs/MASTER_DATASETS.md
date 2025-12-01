# Master Canonical Datasets

This document defines the **final authoritative datasets** of the GitaVerse Open Corpus after full normalization, deduplication, author-indexing, and chapter alignment.

These master datasets are the **single source of truth** for:

- RAG pipelines
- LLM fine-tuning
- API serving
- Search & retrieval
- Scholarly analysis
- Multi-author commentary synthesis

All future downstream systems MUST rely on these files instead of raw or partially processed sources.

---

## 1. Master Verse Dataset

### 📄 File Location

```

datasets/scriptures/master_verses/master_verses.jsonl.7z

````

(Stored as a compressed archive)

---

### ✅ Purpose

This file contains the **fully merged, normalized, multi-source canonical version of every Bhagavad Gita verse**, with:

- Clean verse alignment
- Unified verse IDs
- All available translations
- All available commentaries
- Cross-source provenance

This completely eliminates the need to manually stitch together:

- K1 / K2
- HF2 / HF3
- GH2 / GH3

---

### ✅ Guarantees

Each record guarantees:

- One canonical `verse_id`
- One normalized Sanskrit text
- Best-available transliteration
- All translations mapped by:
  - Language
  - Author
  - Source
- All commentaries mapped by:
  - Author
  - Language
  - Source
- Full data lineage via `sources[]`

---

### ✅ Canonical Schema (Authoritative)

```json
{
  "scripture": "bhagavad_gita",
  "chapter": 11,
  "verse": 16,
  "verse_id": "11.16",

  "sanskrit": "अनेकबाहूदरवक्त्रनेत्रं...",
  "transliteration": "aneka-bāhūdara-vaktra-netram...",

  "translations": [
    {
      "language": "en",
      "author": "Swami Sivananda",
      "text": "...",
      "source": "GH3"
    }
  ],

  "commentaries": [
    {
      "author": "Sri Shankaracharya",
      "language": "hi",
      "text": "...",
      "source": "GH3"
    }
  ],

  "sources": ["K1", "K2", "HF2", "GH2", "GH3"]
}
````

---

### ✅ Usage Mandate

All of the following must now use **only this file**:

* RAG ingestion pipelines
* Embedding generation
* API verse endpoints
* LLM fine-tuning datasets
* Verse search engines
* Multilingual comparison tools

Raw datasets are now considered **upstream sources only**.

---

## 2. Canonical Author Index

### 📄 File Location

```
datasets/scriptures/master_verses/authors_index.json
```

---

### ✅ Purpose

This file provides a **stable global registry of all authors** appearing across:

* Translations
* Commentaries
* Multi-source datasets

It guarantees:

* No duplicate author identities
* Stable IDs for embeddings and analytics
* Language coverage tracking
* Source coverage tracking

---

### ✅ Canonical Schema

```json
{
  "author_id": 17,
  "author_name": "Swami Chinmayananda",
  "languages": ["hi", "en"],
  "roles": ["commentary", "translation"],
  "sources": ["GH2", "GH3", "HF3"]
}
```

---

### ✅ Why This Matters

This enables:

* Attribution-safe AI responses
* Author-specific embeddings
* Per-author fine-tuning datasets
* Scholarly analysis by commentator
* Multi-perspective synthesis by LLMs

---

## 3. Chapter Metadata Index

### 📄 File Location

```
datasets/scriptures/master_verses/chapters_master.json
```

---

### ✅ Purpose

Provides structured metadata for each chapter to support:

* Chapter-level search
* Thematic navigation
* UI rendering
* Curriculum design
* Semantic grouping

---

### ✅ Canonical Schema

```json
{
  "scripture": "bhagavad_gita",
  "chapter": 11,
  "chapter_title": "Vishwarupa Darshana Yoga",
  "verse_count": 55,
  "themes": ["cosmic form", "divine vision", "bhakti", "awe"]
}
```

---

## 4. Data Authority Hierarchy

This defines the full authority chain of the repository:

```
Raw Sources
   ↓
Cleaned Datasets (GH2, HF2, K2)
   ↓
Normalized Datasets (GH3)
   ↓
MASTER DATASETS
   ├── master_verses.jsonl
   ├── canonical_authors.json
   └── chapters_metadata.json
```

Only the **MASTER DATASETS** should be considered **production-grade**.

---

## 5. Compression & Distribution Policy

Due to GitHub size limits:

* `master_verses.jsonl` may be stored as:

  * `master_verses.jsonl.7z`


When compressed, a checksum **must** be included:

```
master_verses.jsonl.7z.sha256
```

This guarantees:

* Data integrity
* Reproducibility
* Trusted redistribution

---

## 6. Long-Term Stability Policy

Once published:

* `verse_id` values are **immutable**
* `author_id` values are **immutable**
* Structural fields may only be extended, never broken
* Deprecated fields must be preserved for backward compatibility

This ensures:

* Stable embeddings across releases
* Safe fine-tuning upgrades
* API backward compatibility
* Academic citation reliability

---

## 7. Future Expansion Compatibility

The master dataset architecture fully supports:

* Additional scriptures
* Cross-text parallels
* Commentary sentiment layers
* Voice-aligned narration datasets
* Concept graphs
* Knowledge tracing for AI tutors

No schema redesign will be required.

---