## End-to-End Guide: Using GitaVerse for RAG & LLM Fine-Tuning

This guide helps developers use the GitaVerse dataset to build:

- Chatbots
- Embedding systems
- RAG pipelines
- Fine-tuned LLMs
- Counseling assistants
- Verse-explanation AI

---

# 🔷 1. Understanding the Dataset Types

## 📘 Scriptures

Contain:

- Sanskrit verses
- Translations
- Word meanings
- Multi-author commentaries

Useful for:

- RAG
- Semantic search
- Verse alignment
- Sanskrit linguistic analysis

## 📗 Q&A

Contain:

- Modern questions
- Answers derived from Gita
- Persona-driven wisdom
- Clustered deduplicated entries

Useful for:

- Fine-tuning conversational LLMs
- Dialogue/agent training
- Retrieval answer base

---

# 🔷 2. Building a RAG System

Recommended architecture:

`User Query → Embed → Vector DB (QnA + Commentary + Verses) → Retriever → LLM (Phi-3 / Llama3 / Qwen) → Answer (grounded in Bhagavad Gita)`

## Step 1: Combine all texts

```
scriptures/
qna_clustered/
commentaries/
translations/
word_meanings/
```

## Step 2: Convert to chunked documents

Each chunk should include:

- verse
- translation
- commentary
- qna matches
- source metadata

## Step 3: Produce embeddings

Use a multilingual model: sentence-transformers/paraphrase-multilingual-mpnet-base-v2

## Step 4: Store in vector DB

Recommended choices:

- Milvus
- Pinecone
- Weaviate
- ChromaDB

## Step 5: Build retrieval logic

- Top 5 retrieval for verses
- Top 5 for commentaries
- Top 5 for Q&A

---

# 🔷 3. Fine-Tuning LLMs

## Recommended Models

- Llama 3
- Qwen-2.5
- Mistral 7B
- Gemma
- Phi-3

## What to Fine-Tune On

### For conversational wisdom:

Use:
hf1_qa_clustered.jsonl
k3_qa_clustered.jsonl

### For teaching/explanations:

Use GH3 commentary datasets.

### For translation / Sanskrit:

Use HF2, K1, GH2 scripture sets.

---

# 🔷 4. Example Fine-Tuning Data Format

### Supervised Fine-Tuning (SFT)

```
{"instruction": "How do I handle anxiety?",
"input": "",
"output": "<Gita-based explanation>"}
```

### ChatML Format

```
<|user|> I feel lost in my life.
<|assistant|> My child, know that clarity often begins in confusion...
```

---

# 🔷 5. Best Practices

- Always include verse references
- Use persona-conditioning for K3 data
- Mix commentary + QnA for richer responses
- Avoid overfitting to repetitive questions
- Use clustered datasets only

---

# 🔷 6. Ready-Made Use Cases

- Gita Counseling LLM
- Verse Lookup AI
- Sanskrit Tutor
- Moral Reasoning Engine
- Dharma-based Decision Support Agent
- Voice-based spiritual companion
