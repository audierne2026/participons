#!/usr/bin/env python3
"""
Prepare RAG (Retrieval-Augmented Generation) dataset with full document content.

This script exports COMPLETE documents (not truncated) for use in RAG systems.
The output can be uploaded to Mistral or other vector databases for semantic search.

Output format (JSONL):
{
  "id": "unique-document-id",
  "category": "economie",
  "source_type": "pdf_extract|contribution|readme",
  "title": "Document title",
  "url": "source URL if available",
  "content": "FULL document content",
  "metadata": { ... }
}

Usage:
    python prepare_rag_dataset.py [--output data/rag/documents.jsonl]
"""

import os
import json
import argparse
import re
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# ====================== CONFIGURATION ======================
DOCS_DIR = Path("docs")

CATEGORIES = {
    "economie": "Économie locale",
    "logement": "Logement & Urbanisme",
    "culture": "Culture & Patrimoine",
    "environnement": "Environnement",
    "associations": "Associations & Vie locale",
    "jeunesse": "École & Jeunesse",
    "alimentation-bien-etre-soins": "Alimentation, bien-être et soins",
}

# =========================================================


def generate_doc_id(source_type, category, filename):
    """Generate a unique document ID."""
    base = f"{source_type}-{category}-{filename}"
    return re.sub(r"[^a-z0-9-]", "-", base.lower())[:64]


def extract_readme_document(filepath, category_key):
    """Extract full content from a category README."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract title
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1) if title_match else f"README {category_key}"

    return {
        "id": generate_doc_id("readme", category_key, "main"),
        "category": category_key,
        "category_title": CATEGORIES.get(category_key, category_key),
        "source_type": "readme",
        "title": title,
        "url": f"https://github.com/audierne2026/audierne/blob/main/docs/{category_key}/README.md",
        "content": content,
        "metadata": {
            "filepath": str(filepath),
            "char_count": len(content),
            "word_count": len(content.split()),
        },
    }


def extract_contribution_document(filepath, category_key):
    """Extract full content from a contribution file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    filename = filepath.stem

    # Extract contribution number
    num_match = re.search(r"(issue|discussion)-(\d+)", filename)
    contrib_type = num_match.group(1) if num_match else "contribution"
    contrib_num = num_match.group(2) if num_match else filename

    # Extract title
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1) if title_match else f"Contribution {contrib_num}"

    # Extract GitHub link if present
    gh_match = re.search(
        r"\[.+?\]\((https://github\.com/audierne2026/participons/(?:issues|discussions)/\d+)\)",
        content,
    )
    url = gh_match.group(1) if gh_match else ""

    return {
        "id": generate_doc_id("contribution", category_key, filename),
        "category": category_key,
        "category_title": CATEGORIES.get(category_key, category_key),
        "source_type": "contribution",
        "contribution_type": contrib_type,
        "contribution_number": contrib_num,
        "title": title,
        "url": url,
        "content": content,
        "metadata": {
            "filepath": str(filepath),
            "char_count": len(content),
            "word_count": len(content.split()),
        },
    }


def extract_pdf_document(filepath, category_key):
    """Extract full content from a PDF extract file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    filename = filepath.stem

    # Extract title
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1) if title_match else filename

    # Extract source URL
    url_match = re.search(r"\*\*Source URL:\*\*\s*(.+?)$", content, re.MULTILINE)
    source_url = url_match.group(1).strip() if url_match else ""

    # Extract page count
    pages_match = re.search(r"\*\*Pages:\*\*\s*(\d+)", content)
    pages = int(pages_match.group(1)) if pages_match else 0

    # Extract the actual content (after "## Contenu extrait")
    content_match = re.search(r"## Contenu extrait\n\n(.+?)(?=\n---\n|\Z)", content, re.DOTALL)
    extracted_content = content_match.group(1).strip() if content_match else content

    return {
        "id": generate_doc_id("pdf", category_key, filename),
        "category": category_key,
        "category_title": CATEGORIES.get(category_key, category_key),
        "source_type": "pdf_extract",
        "title": title,
        "url": source_url,
        "content": extracted_content,
        "metadata": {
            "filepath": str(filepath),
            "original_filename": filename,
            "pages": pages,
            "char_count": len(extracted_content),
            "word_count": len(extracted_content.split()),
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Prepare RAG dataset with full document content"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="data/rag/documents.jsonl",
        help="Output file (default: data/rag/documents.jsonl)",
    )
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Documentation directory (default: docs)",
    )
    parser.add_argument(
        "--format",
        choices=["jsonl", "json"],
        default="jsonl",
        help="Output format (default: jsonl)",
    )

    args = parser.parse_args()
    docs_dir = Path(args.docs_dir)

    print("=" * 60)
    print("📚 RAG Dataset Preparation (Full Documents)")
    print("=" * 60)
    print()

    all_documents = []

    # Process category READMEs
    print("📁 Processing category READMEs...")
    readme_count = 0
    for cat_key in CATEGORIES.keys():
        readme_path = docs_dir / cat_key / "README.md"
        if readme_path.exists():
            doc = extract_readme_document(readme_path, cat_key)
            all_documents.append(doc)
            readme_count += 1
            print(f"   ✓ {cat_key}/README.md ({doc['metadata']['word_count']} words)")

    print(f"   Total: {readme_count} READMEs")

    # Process contributions
    print("\n📄 Processing contributions...")
    contrib_count = 0
    for cat_key in CATEGORIES.keys():
        contrib_dir = docs_dir / cat_key / "contributions"
        if contrib_dir.exists():
            for filepath in contrib_dir.glob("*.md"):
                if filepath.name != "INDEX.md":
                    doc = extract_contribution_document(filepath, cat_key)
                    all_documents.append(doc)
                    contrib_count += 1

    print(f"   Total: {contrib_count} contributions")

    # Process PDF extracts
    print("\n📑 Processing PDF extracts...")
    pdf_count = 0
    for cat_key in CATEGORIES.keys():
        pdf_dir = docs_dir / cat_key / "pdf_extracts"
        if pdf_dir.exists():
            for filepath in pdf_dir.glob("*.md"):
                if filepath.name != "INDEX.md":
                    doc = extract_pdf_document(filepath, cat_key)
                    all_documents.append(doc)
                    pdf_count += 1

    print(f"   Total: {pdf_count} PDF extracts")

    # Calculate totals
    total_chars = sum(d["metadata"]["char_count"] for d in all_documents)
    total_words = sum(d["metadata"]["word_count"] for d in all_documents)

    print()
    print("=" * 60)
    print(f"📊 Total: {len(all_documents)} documents")
    print(f"   - READMEs: {readme_count}")
    print(f"   - Contributions: {contrib_count}")
    print(f"   - PDF extracts: {pdf_count}")
    print(f"   - Total characters: {total_chars:,}")
    print(f"   - Total words: {total_words:,}")
    print(f"   - Estimated size: ~{total_chars // 1024:,} KB")
    print("=" * 60)

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    if args.format == "jsonl":
        with open(output_path, "w", encoding="utf-8") as f:
            for doc in all_documents:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_documents, f, indent=2, ensure_ascii=False)

    print(f"\n✅ RAG dataset saved: {output_path}")

    # Write metadata
    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_documents": len(all_documents),
        "by_type": {
            "readme": readme_count,
            "contribution": contrib_count,
            "pdf_extract": pdf_count,
        },
        "by_category": {},
        "total_characters": total_chars,
        "total_words": total_words,
    }

    for cat_key in CATEGORIES.keys():
        metadata["by_category"][cat_key] = len(
            [d for d in all_documents if d["category"] == cat_key]
        )

    metadata_path = str(output_path).rsplit(".", 1)[0] + "_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"✅ Metadata saved: {metadata_path}")


if __name__ == "__main__":
    main()
