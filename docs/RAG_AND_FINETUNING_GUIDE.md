# RAG and Fine-tuning Guide for O Capistaine

This guide explains how to build the knowledge base for **O Capistaine**, the AI assistant for the Audierne2026 campaign.

## Overview: Two-Step Process

Building an effective AI assistant requires two complementary approaches:

| Step | Purpose | Data | Output |
|------|---------|------|--------|
| **1. RAG** | Provide context/knowledge | Full documents | `documents.jsonl` |
| **2. Fine-tuning** | Teach style/behavior | Q&A pairs | `dataset_train.jsonl` |

```
┌─────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE PIPELINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Source Documents]                                          │
│       │                                                      │
│       ├──► README.md (7 category pages)                      │
│       ├──► contributions/ (issues & discussions)             │
│       └──► pdf_extracts/ (OCR from official PDFs)            │
│                    │                                         │
│         ┌─────────┴─────────┐                                │
│         ▼                   ▼                                │
│   ┌───────────┐      ┌─────────────┐                         │
│   │    RAG    │      │ Fine-tuning │                         │
│   │ (Context) │      │   (Style)   │                         │
│   └─────┬─────┘      └──────┬──────┘                         │
│         │                   │                                │
│         ▼                   ▼                                │
│   Full documents       Q&A pairs                             │
│   for retrieval        for training                          │
│         │                   │                                │
│         └─────────┬─────────┘                                │
│                   ▼                                          │
│            O Capistaine                                      │
│         (Knowledgeable +                                     │
│          Correct style)                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Prepare Source Documents

### 1.1 Extract PDFs (Local only)

PDF extraction uses Mistral OCR API and must run locally (not in CI/CD).

```bash
# Set API key
export MISTRAL_OCR_API_KEY='your-key'

# List available PDFs
python scripts/extract_pdf_with_mistral.py --list-only

# Extract all PDFs (2s delay between requests)
python scripts/extract_pdf_with_mistral.py

# Extract specific category
python scripts/extract_pdf_with_mistral.py -c economie

# Force re-extraction
python scripts/extract_pdf_with_mistral.py --force
```

**Output:** `docs/<category>/pdf_extracts/*.md`

### 1.2 Export GitHub Contributions

This can run in GitHub Actions or locally.

```bash
# Export all issues and discussions to markdown
python scripts/export_contributions_to_md.py
```

**Output:** `docs/<category>/contributions/*.md`

---

## Step 2: Generate RAG Dataset (Full Documents)

The RAG dataset contains **complete document content** for semantic search and context retrieval.

```bash
python scripts/prepare_rag_dataset.py --output data/rag/documents.jsonl
```

### RAG Document Format

```json
{
  "id": "pdf-economie-rapport-2024",
  "category": "economie",
  "category_title": "Économie locale",
  "source_type": "pdf_extract",
  "title": "Rapport économique 2024",
  "url": "https://example.com/rapport.pdf",
  "content": "[FULL DOCUMENT CONTENT - NOT TRUNCATED]",
  "metadata": {
    "filepath": "docs/economie/pdf_extracts/rapport-2024.md",
    "char_count": 15420,
    "word_count": 2341,
    "pages": 12
  }
}
```

### Upload to Mistral for RAG

```bash
curl -X POST "https://api.mistral.ai/v1/files" \
  -H "Authorization: Bearer $MISTRAL_API_KEY" \
  -F "file=@data/rag/documents.jsonl" \
  -F "purpose=retrieval"
```

---

## Step 3: Generate Fine-tuning Dataset (Q&A Pairs)

The fine-tuning dataset teaches the model **how to respond** (tone, format, persona).

```bash
python scripts/prepare_mistral_dataset.py --output data/mistral/dataset.jsonl
```

### Fine-tuning Format (Mistral)

```json
{
  "messages": [
    {"role": "system", "content": "Tu es O Capistaine, l'assistant IA..."},
    {"role": "user", "content": "Que contient le document X ?"},
    {"role": "assistant", "content": "Le document X présente..."}
  ]
}
```

### Upload for Fine-tuning

```bash
# Upload training set
curl -X POST "https://api.mistral.ai/v1/files" \
  -H "Authorization: Bearer $MISTRAL_API_KEY" \
  -F "file=@data/mistral/dataset_train.jsonl" \
  -F "purpose=fine-tune"

# Upload validation set
curl -X POST "https://api.mistral.ai/v1/files" \
  -H "Authorization: Bearer $MISTRAL_API_KEY" \
  -F "file=@data/mistral/dataset_val.jsonl" \
  -F "purpose=fine-tune"
```

---

## Complete Workflow

### Option A: Manual (Local)

```bash
# 1. Extract PDFs (requires MISTRAL_OCR_API_KEY)
python scripts/extract_pdf_with_mistral.py

# 2. Export contributions (requires gh CLI authenticated)
python scripts/export_contributions_to_md.py

# 3. Generate RAG dataset
python scripts/prepare_rag_dataset.py

# 4. Generate fine-tuning dataset
python scripts/prepare_mistral_dataset.py

# 5. Upload to Mistral (manual or via API)
```

### Option B: GitHub Actions + Local

1. **Local:** Extract PDFs (OCR requires response)
   ```bash
   python scripts/extract_pdf_with_mistral.py
   git add docs/*/pdf_extracts/
   git commit -m "Add PDF extracts"
   git push
   ```

2. **GitHub Actions:** Run "Feed Mistral RAG" workflow
   - Exports contributions
   - Generates both datasets
   - Optionally uploads to Mistral

---

## Dataset Comparison

| Dataset | Purpose | Content | Typical Size |
|---------|---------|---------|--------------|
| `documents.jsonl` | RAG retrieval | Full documents | ~400 KB |
| `dataset_train.jsonl` | Fine-tuning | Q&A pairs (truncated) | ~300 KB |
| `dataset_val.jsonl` | Validation | Q&A pairs (10%) | ~40 KB |

---

## File Structure

```
data/
├── rag/
│   ├── documents.jsonl          # Full documents for RAG
│   └── documents_metadata.json  # Statistics
│
└── mistral/
    ├── dataset_train.jsonl      # Q&A pairs for training
    ├── dataset_val.jsonl        # Q&A pairs for validation
    └── dataset_metadata.json    # Statistics

docs/
├── <category>/
│   ├── README.md                # Main category content
│   ├── contributions/           # GitHub issues/discussions
│   └── pdf_extracts/            # OCR-extracted PDFs
```

---

## Updating the Knowledge Base

When new content is added:

1. **New PDFs referenced in docs:**
   ```bash
   python scripts/extract_pdf_with_mistral.py  # Only processes new ones
   ```

2. **New GitHub contributions:**
   ```bash
   python scripts/export_contributions_to_md.py --clean
   ```

3. **Regenerate datasets:**
   ```bash
   python scripts/prepare_rag_dataset.py
   python scripts/prepare_mistral_dataset.py
   ```

4. **Re-upload to Mistral** (if using their hosted solution)

---

## Troubleshooting

### PDF extraction fails
- Check `MISTRAL_OCR_API_KEY` is set
- Some PDFs may be protected or corrupted
- Use `--delay 5` if rate limited

### Dataset too small
- Ensure all categories have README.md files
- Run `export_contributions_to_md.py` to get latest issues
- Check `docs/.pdf_extracts_index.json` for processed PDFs

### Fine-tuning not learning correctly
- Increase Q&A pairs diversity
- Check system prompt consistency
- Ensure RAG context is being retrieved properly

---

*Last updated: February 2026*
