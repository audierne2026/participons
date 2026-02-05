# PDF Extracts (Mistral Document AI)

This directory contains text extracted from PDF documents referenced in the Audierne2026 documentation, using Mistral's Document AI OCR service.

## Overview

| Category | PDF Count |
|----------|-----------|
| Logement & Urbanisme | 19 |
| Économie locale | 18 |
| Environnement | 7 |
| Alimentation, bien-être et soins | 4 |
| École & Jeunesse | 2 |
| Autre | 2 |
| Associations & Vie locale | 1 |
| Culture & Patrimoine | 1 |
| **Total** | **54** |

## Files

- `PDF_LIST.md` - Complete list of all PDF URLs found
- `pdf_index.json` - Index of processed PDFs with metadata
- `<category>/<filename>.md` - Extracted content per PDF

## Usage

### List all PDFs (no API call)
```bash
python scripts/extract_pdf_with_mistral.py --list-only
```

### Extract all PDFs
```bash
export MISTRAL_API_KEY="your-key"
python scripts/extract_pdf_with_mistral.py
```

### Extract by category
```bash
python scripts/extract_pdf_with_mistral.py --category logement
```

### Limit processing
```bash
python scripts/extract_pdf_with_mistral.py --limit 5
```

### Force re-extraction
```bash
python scripts/extract_pdf_with_mistral.py --force
```

## Mistral OCR API

The script uses the Mistral OCR endpoint:
- **Model:** `mistral-ocr-latest`
- **Endpoint:** `https://api.mistral.ai/v1/ocr`
- **Input:** Public PDF URLs
- **Output:** Markdown text with page separators

### API Requirements
- `MISTRAL_API_KEY` environment variable
- PDFs must be publicly accessible URLs
- Supported formats: PDF, PPTX, DOCX

## Integration with RAG

Extracted PDFs can be added to the fine-tuning dataset:
```bash
# After extraction
python scripts/prepare_mistral_dataset.py --include-pdf-extracts
```

## GitHub Secret

Add `MISTRAL_API_KEY` to repository secrets for CI/CD workflows.
