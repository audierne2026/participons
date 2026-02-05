# Mistral Fine-tuning Dataset

This directory contains the JSONL datasets for fine-tuning Mistral models with Audierne2026 documentation.

## Files

- `dataset_train.jsonl` - Training dataset (90% of data)
- `dataset_val.jsonl` - Validation dataset (10% of data)
- `dataset_metadata.json` - Dataset statistics and metadata

## Format

Each line in the JSONL files follows Mistral's fine-tuning format:

```json
{
  "messages": [
    {"role": "system", "content": "Tu es O Capistaine..."},
    {"role": "user", "content": "Question about Audierne2026"},
    {"role": "assistant", "content": "Factual answer with sources"}
  ]
}
```

## Regenerating the Dataset

```bash
# From repository root
python scripts/prepare_mistral_dataset.py

# With custom options
python scripts/prepare_mistral_dataset.py --split 0.85 --output data/mistral/custom.jsonl
```

## Uploading to Mistral

### Via CLI (if mistral-cli installed)
```bash
mistral files upload data/mistral/dataset_train.jsonl
mistral files upload data/mistral/dataset_val.jsonl
```

### Via API
```bash
curl -X POST "https://api.mistral.ai/v1/files" \
  -H "Authorization: Bearer $MISTRAL_API_KEY" \
  -F "file=@data/mistral/dataset_train.jsonl" \
  -F "purpose=fine-tune"
```

### Via GitHub Action
Trigger the "Prepare Mistral Dataset" workflow with `upload_to_mistral: true`.

## Data Sources

The dataset is generated from:
1. Category README files (`docs/*/README.md`)
2. Individual contribution files (`docs/*/contributions/*.md`)
3. General Q&A about the Audierne2026 platform

## GitHub Secret Required

Add `MISTRAL_API_KEY` to your repository secrets for automated uploads.
