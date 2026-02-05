#!/usr/bin/env python3
"""
Extract PDF content using Mistral Document AI (OCR).

This script:
1. Scans docs/ for PDF links in markdown files
2. Uses Mistral OCR API to extract text from PDFs
3. Saves extracted content as markdown files in data/pdf_extracts/
4. Generates an index of all processed PDFs

Usage:
    python extract_pdf_with_mistral.py [--list-only] [--limit N]

Environment:
    MISTRAL_API_KEY: Required for Mistral OCR API
"""

import os
import re
import json
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote
import requests

# Load .env for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ====================== CONFIGURATION ======================
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
DOCS_DIR = Path("docs")
OUTPUT_DIR = Path("data/pdf_extracts")
PDF_INDEX_FILE = OUTPUT_DIR / "pdf_index.json"

# Category mapping for organizing PDFs
CATEGORIES = {
    "economie": "Économie locale",
    "logement": "Logement & Urbanisme",
    "culture": "Culture & Patrimoine",
    "environnement": "Environnement",
    "associations": "Associations & Vie locale",
    "jeunesse": "École & Jeunesse",
    "alimentation-bien-etre-soins": "Alimentation, bien-être et soins",
    "autre": "Autre"
}

# =========================================================


def extract_pdf_links_from_file(filepath):
    """Extract all PDF URLs from a markdown file."""
    links = []

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Match URLs ending in .pdf (with optional query params)
    pdf_pattern = r'https?://[^\s<>\)\]"\'`]+\.pdf[^\s<>\)\]"\'`]*'

    for match in re.finditer(pdf_pattern, content, re.IGNORECASE):
        url = match.group()
        # Clean URL
        url = url.rstrip(".,;:!?)")
        links.append(url)

    return list(set(links))  # Deduplicate


def scan_docs_for_pdfs():
    """Scan all docs for PDF links."""
    pdf_links = {}

    for md_file in DOCS_DIR.rglob("*.md"):
        links = extract_pdf_links_from_file(md_file)
        if links:
            # Determine category from path
            rel_path = md_file.relative_to(DOCS_DIR)
            parts = rel_path.parts
            category = parts[0] if parts[0] in CATEGORIES else "autre"

            for link in links:
                if link not in pdf_links:
                    pdf_links[link] = {
                        "url": link,
                        "category": category,
                        "source_files": []
                    }
                pdf_links[link]["source_files"].append(str(md_file))

    return pdf_links


def get_pdf_filename(url):
    """Generate a safe filename from PDF URL."""
    parsed = urlparse(url)
    path = unquote(parsed.path)

    # Get filename from URL path
    filename = Path(path).name
    if not filename or filename == "":
        # Use hash of URL as filename
        filename = hashlib.md5(url.encode()).hexdigest()[:12] + ".pdf"

    # Sanitize filename
    filename = re.sub(r'[^\w\-.]', '_', filename)

    return filename.replace(".pdf", "")


def process_pdf_with_mistral(url, output_path):
    """Use Mistral OCR to extract text from PDF URL."""
    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistral-ocr-latest",
        "document": {
            "type": "document_url",
            "document_url": url
        },
        "include_image_base64": False
    }

    response = requests.post(
        "https://api.mistral.ai/v1/ocr",
        headers=headers,
        json=payload,
        timeout=120
    )

    if response.status_code != 200:
        return {
            "success": False,
            "error": f"API error {response.status_code}: {response.text[:200]}"
        }

    result = response.json()

    # Extract markdown content from all pages
    pages = result.get("pages", [])
    markdown_content = []

    for page in pages:
        page_num = page.get("index", 0) + 1
        content = page.get("markdown", "")
        if content:
            markdown_content.append(f"<!-- Page {page_num} -->\n{content}")

    full_content = "\n\n---\n\n".join(markdown_content)

    return {
        "success": True,
        "content": full_content,
        "pages": len(pages),
        "usage": result.get("usage_info", {})
    }


def save_pdf_extract(url, pdf_info, result, output_dir):
    """Save extracted PDF content as markdown."""
    filename = get_pdf_filename(url)
    category = pdf_info["category"]

    # Create category subdirectory
    cat_dir = output_dir / category
    cat_dir.mkdir(parents=True, exist_ok=True)

    output_path = cat_dir / f"{filename}.md"

    # Build markdown file
    lines = [
        f"# {filename}",
        "",
        f"**Source URL:** {url}",
        f"**Catégorie:** {CATEGORIES.get(category, category)}",
        f"**Extrait le:** {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}",
        f"**Pages:** {result.get('pages', 'N/A')}",
        "",
        "**Fichiers source:**",
    ]

    for src in pdf_info["source_files"][:5]:
        lines.append(f"- `{src}`")

    lines.extend([
        "",
        "---",
        "",
        "## Contenu extrait",
        "",
        result.get("content", "*Pas de contenu extrait*"),
        "",
        "---",
        "",
        f"*Extrait via Mistral OCR API (`mistral-ocr-latest`)*"
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


def load_pdf_index():
    """Load existing PDF index."""
    if PDF_INDEX_FILE.exists():
        with open(PDF_INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"pdfs": {}, "last_updated": None}


def save_pdf_index(index):
    """Save PDF index."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    index["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(PDF_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Extrait le contenu des PDFs avec Mistral Document AI"
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Lister les PDFs sans les traiter"
    )
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=0,
        help="Limiter le nombre de PDFs à traiter (0 = tous)"
    )
    parser.add_argument(
        "--category", "-c",
        help="Traiter uniquement une catégorie"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Retraiter les PDFs déjà extraits"
    )
    parser.add_argument(
        "--output-dir",
        default="data/pdf_extracts",
        help="Répertoire de sortie (défaut: data/pdf_extracts)"
    )

    args = parser.parse_args()

    global OUTPUT_DIR, PDF_INDEX_FILE
    OUTPUT_DIR = Path(args.output_dir)
    PDF_INDEX_FILE = OUTPUT_DIR / "pdf_index.json"

    print("=" * 60)
    print("📄 Extraction de PDFs avec Mistral Document AI")
    print("=" * 60)
    print()

    # Scan for PDFs
    print("🔍 Scan des documents...")
    pdf_links = scan_docs_for_pdfs()

    print(f"✅ {len(pdf_links)} PDFs uniques trouvés")
    print()

    # Group by category
    by_category = {}
    for url, info in pdf_links.items():
        cat = info["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append((url, info))

    print("📊 Par catégorie:")
    for cat in sorted(by_category.keys()):
        count = len(by_category[cat])
        cat_title = CATEGORIES.get(cat, cat)
        print(f"   - {cat_title}: {count} PDF(s)")

    print()

    # List-only mode
    if args.list_only:
        print("📋 Liste des PDFs:")
        print("-" * 60)
        for cat in sorted(by_category.keys()):
            if args.category and cat != args.category:
                continue
            print(f"\n### {CATEGORIES.get(cat, cat)}")
            for url, info in by_category[cat]:
                filename = get_pdf_filename(url)
                print(f"  - {filename}")
                print(f"    {url[:80]}{'...' if len(url) > 80 else ''}")
        return

    # Check API key
    if not MISTRAL_API_KEY:
        print("❌ MISTRAL_API_KEY non défini!")
        print("   Définissez la variable d'environnement ou utilisez --list-only")
        return

    # Load existing index
    index = load_pdf_index()

    # Process PDFs
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    processed = 0
    skipped = 0
    errors = 0

    pdfs_to_process = []
    for cat in sorted(by_category.keys()):
        if args.category and cat != args.category:
            continue
        for url, info in by_category[cat]:
            pdfs_to_process.append((url, info))

    if args.limit > 0:
        pdfs_to_process = pdfs_to_process[:args.limit]

    print(f"🚀 Traitement de {len(pdfs_to_process)} PDF(s)...")
    print()

    for url, info in pdfs_to_process:
        filename = get_pdf_filename(url)
        category = info["category"]

        # Check if already processed
        url_hash = hashlib.md5(url.encode()).hexdigest()
        if url_hash in index["pdfs"] and not args.force:
            print(f"⏭️  {filename} (déjà traité)")
            skipped += 1
            continue

        print(f"📄 {filename}...")

        try:
            result = process_pdf_with_mistral(url, OUTPUT_DIR)

            if result["success"]:
                output_path = save_pdf_extract(url, info, result, OUTPUT_DIR)

                # Update index
                index["pdfs"][url_hash] = {
                    "url": url,
                    "filename": filename,
                    "category": category,
                    "output_path": str(output_path),
                    "pages": result.get("pages", 0),
                    "extracted_at": datetime.now(timezone.utc).isoformat()
                }

                print(f"   ✅ {result.get('pages', '?')} pages → {output_path}")
                processed += 1
            else:
                print(f"   ❌ {result.get('error', 'Unknown error')}")
                errors += 1

        except Exception as e:
            print(f"   ❌ Exception: {str(e)[:100]}")
            errors += 1

    # Save index
    save_pdf_index(index)

    print()
    print("=" * 60)
    print(f"✅ Traitement terminé!")
    print(f"   - Traités: {processed}")
    print(f"   - Ignorés (déjà faits): {skipped}")
    print(f"   - Erreurs: {errors}")
    print(f"   - Index: {PDF_INDEX_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
