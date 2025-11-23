## GitaVerse-Open-Corpus — Processing Pipeline Documentation

This document explains **every script** used to process the datasets in the repository, what each script does, their inputs/outputs, and their internal logic.

---

# 🔷 1. Overview

The repository uses fully reproducible, modular Python scripts to transform all raw datasets into:

- Canonical verse datasets
- Canonical Q&A datasets
- Clustered deduplicated datasets
- Unified structures used by RAG and LLM pipelines

No manual editing touches the final outputs.
This ensures **100% reproducibility**, **auditability**, and **transparency**.

---

# 🔷 2. Script Index

```
scripts/
│
├── qna/
│ ├── build_hf1_canonical.py
│ ├── build_k3_canonical.py
│ ├── cluster_dataset_hf1.py
│ ├── cluster_dataset_k3.py
│ └── merge_qa_master.py
│
├── scriptures/
│ ├── process_k1.py
│ ├── process_k2.py
│ ├── process_hf2.py
│ ├── process_hf3.py
│ ├── process_gh2.py
│ └── process_gh3.py
│
└── utils/
└── normalize.py
```

---

# 🔷 3. Documentation for Each Script

---

## 🟦 **Q&A Processing Scripts**

---

## **3.1 build_hf1_canonical.py**

### **Purpose**

Converts HF1 Q&A CSV into a **standard JSONL canonical format**.

### **Input**

QnA CSV in English and Hindi


### **Output**

hf1_qa.jsonl


### **Key Features**
- Generates `qid` using formula:  
  `HF1-<language>-<chapter>:<verse>-<nnn>`
- Normalizes English/Hindi text
- Fixes chapter/verse mapping
- Cleans whitespace + artifacts

---

## **3.2 build_k3_canonical.py**

### **Purpose**
Converts the 18-chapter “Gita Applied Q&A” dataset into canonical JSONL.

### **Input**
`Chapter_1_QA.csv` ... `Chapter_18_QA.csv`

### **Output**
`k3_qa.jsonl`

### **Notes**
- Extracts verse numbers from fields like `"1.10–12"`
- Standardizes persona-based inputs
- Ensures uniform schema with HF1

---

## **3.3 cluster_dataset_hf1.py**

### **Purpose**
Clusters HF1 QnA using semantic similarity → removes duplicates.

### **Input**
`hf1_qa.jsonl`

### **Output**
`hf1_qa_clustered.jsonl`

### **Notes**
- Uses SentenceTransformer embeddings
- Clustering threshold: **0.82**
- Preserves the earliest question as the cluster representative
- Adds field:  
  `"cluster_id": <int>`

---

## **3.4 cluster_dataset_k3.py**

### **Purpose**
Clusters K3 QnA dataset.

### **Input**
`k3_qa.jsonl`

### **Output**
`k3_qa_clustered.jsonl`

### **Notes**
Same logic as HF1 clustering.

---

## **3.5 merge_qa_master.py and merge_clustered_qna.py** *(future step, not executed yet)*

### **Purpose**
Will produce:

qa_master.jsonl (Done already)
qa_master_clustered.jsonl


### **Pipeline**
1. Load `hf1_qa_clustered.jsonl`  
2. Load `k3_qa_clustered.jsonl`  
3. Combine  
4. Re-cluster  
5. Rewrite qids using unified scheme

---

# 🟩 **Scripture Processing Scripts**

---

## **3.6 process_k1.py**

### **Purpose**
Processes Kaggle K1 dataset (English/Hindi/Sanskrit).

### **Fixes**
- Multi-verse ranges  
- Duplicates  
- Commentary merged with meaning  
- Normalizes transliteration  

### **Output**
`K1_processed/canonical_ch_*.jsonl`

---

## **3.7 process_k2.py**

### **Purpose**
Processes Kaggle K2 dataset.

### **Fixes**
- Extract word-by-word meanings  
- Standardize structure  
- Clean transliteration  

### **Output**
`K2_processed/*.jsonl`

---

## **3.8 process_hf2.py**

### **Purpose**
Processes multi-lingual CSV dataset.

### **Fixes**
- Unicode normalization  
- Multi-line breaks  
- Clean HTML leftovers  

### **Output**
`HF2_processed/*.jsonl`

---

## **3.9 process_hf3.py / process_gh1.py**

### **Purpose**
Processes GitHub multi-author translations dataset.

### **Output**
`HF3_processed/`  
`GH1_processed/`

---

## **3.10 process_gh2.py**

### **Purpose**
Processes DharmicData multi-chapter JSON verses.

### **Fixes**
- Merge chapter metadata  
- Flatten list structures  

### **Output**
`GH2_processed/*.jsonl`

---

## **3.11 process_gh3.py**

### **Purpose**
Handles gigantic multi-author commentary dataset.

### **Fixes**
- At least 100–300 lines of commentary per verse  
- Unicode Sanskrit  
- Multi-paragraph formatting

### **Output**
`GH3_processed/*.jsonl`

---

# 🔷 4. Utility Scripts (Future Development, If Needed)

---

## **embedding_model.py**
Wraps SentenceTransformer loading, controls:

- model name  
- device selection  
- batch size  
- embedding caching  

---

## **cluster_core.py**
Implements:

- cosine similarity matrix  
- threshold-based grouping  
- cluster assignment  
- cluster representative logic  

---

## **text_cleaning.py**
Handles:

- Unicode fixes  
- Zero-width chars  
- Double spaces  
- HTML cleanups (`<br>`, `&nbsp;`)  

---

## **normalize.py**
- Trim spaces  
- Lowercasing (where needed)  
- Consistent verse IDs  

---

# 🔷 5. Reproducibility

All scripts produce deterministic output when run with the same:

- Raw datasets  
- Script version  
- Model version  

No randomness unless clustering seeds are changed.

---

# 🔷 6. Future Scripts

- `build_canonical_master.py`
- `merge_scriptures.py`
- `build_gita_embeddings.py`
- `rag_pipeline_demo.py`

---
