#!/usr/bin/env python3
"""
Extract PDF content using Mistral Document AI (OCR).

This script:
1. Scans the 7 category folders in docs/ for PDF links
2. Uses Mistral OCR API to extract text from PDFs
3. Saves extracted content in docs/<category>/pdf_extracts/
4. Generates an index of all processed PDFs

Run locally (not in GitHub Actions - requires receiving API response):
    python extract_pdf_with_mistral.py [--list-only] [--limit N] [--category economie] [--delay 2]

Environment:
    MISTRAL_API_KEY: Required for Mistral OCR API
"""

import os
import re
import json
import time
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote
import requests

# Load .env for local development
try:
    from dotenv import load_dotenv

    load_dotenv()  # noqa: F841
except ImportError:
    pass

# ====================== CONFIGURATION ======================
MISTRAL_API_KEY = os.getenv("MISTRAL_OCR_API_KEY")
DOCS_DIR = Path("docs")

# Only scan these 7 category folders
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


def scan_categories_for_pdfs():
    """Scan only the 7 category folders for PDF links."""
    pdf_links = {}

    for category in CATEGORIES.keys():
        category_dir = DOCS_DIR / category

        if not category_dir.exists():
            continue

        # Scan all markdown files in this category
        for md_file in category_dir.rglob("*.md"):
            # Skip pdf_extracts folder
            if "pdf_extracts" in str(md_file):
                continue

            links = extract_pdf_links_from_file(md_file)

            for link in links:
                if link not in pdf_links:
                    pdf_links[link] = {
                        "url": link,
                        "category": category,
                        "source_files": [],
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
    filename = re.sub(r"[^\w\-.]", "_", filename)

    return filename.replace(".pdf", "")


def process_pdf_with_mistral(url):
    """Use Mistral OCR to extract text from PDF URL."""
    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "mistral-ocr-latest",
        "document": {"type": "document_url", "document_url": url},
        "include_image_base64": False,
    }

    print(f"      Calling Mistral OCR API...")
    response = requests.post(
        "https://api.mistral.ai/v1/ocr",
        headers=headers,
        json=payload,
        timeout=180,  # 3 minutes timeout for large PDFs
    )

    if response.status_code != 200:
        return {
            "success": False,
            "error": f"API error {response.status_code}: {response.text[:200]}",
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
        "usage": result.get("usage_info", {}),
    }


def save_pdf_extract(url, pdf_info, result):
    """Save extracted PDF content in the category's pdf_extracts folder."""
    filename = get_pdf_filename(url)
    category = pdf_info["category"]

    # Save in docs/<category>/pdf_extracts/
    output_dir = DOCS_DIR / category / "pdf_extracts"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{filename}.md"

    # Build markdown file
    lines = [
        f"# {filename}",
        "",
        f"**Source URL:** {url}",
        f"**Catégorie:** {CATEGORIES.get(category, category)}",
        f"**Extrait le:** {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}",
        f"**Pages:** {result.get('pages', 'N/A')}",
        "",
        "**Fichiers source (où ce PDF est référencé):**",
    ]

    for src in pdf_info["source_files"][:5]:
        lines.append(f"- `{src}`")

    if len(pdf_info["source_files"]) > 5:
        lines.append(f"- *...et {len(pdf_info['source_files']) - 5} autre(s)*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Contenu extrait",
            "",
            result.get("content", "*Pas de contenu extrait*"),
            "",
            "---",
            "",
            f"*Extrait via Mistral OCR API (`mistral-ocr-latest`)*",
        ]
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


def load_pdf_index():
    """Load existing PDF index from docs."""
    index_file = DOCS_DIR / ".pdf_extracts_index.json"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"pdfs": {}, "last_updated": None}


def save_pdf_index(index):
    """Save PDF index to docs."""
    index["last_updated"] = datetime.now(timezone.utc).isoformat()
    index_file = DOCS_DIR / ".pdf_extracts_index.json"

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def generate_category_pdf_index(category, pdfs):
    """Generate an INDEX.md for a category's pdf_extracts folder."""
    output_dir = DOCS_DIR / category / "pdf_extracts"

    if not output_dir.exists():
        return

    lines = [
        f"# PDF Extracts - {CATEGORIES.get(category, category)}",
        "",
        f"**Dernière mise à jour:** {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}",
        "",
        "Ces fichiers contiennent le texte extrait des PDFs référencés dans cette catégorie.",
        "",
        "---",
        "",
        f"## Documents ({len(pdfs)})",
        "",
    ]

    for pdf in sorted(pdfs, key=lambda x: x.get("filename", "")):
        filename = pdf.get("filename", "unknown")
        pages = pdf.get("pages", "?")
        lines.append(f"- [{filename}]({filename}.md) ({pages} pages)")

    lines.extend(["", "---", "", "[← Retour au README principal](../README.md)"])

    index_path = output_dir / "INDEX.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(
        description="Extrait le contenu des PDFs avec Mistral Document AI (exécution locale)"
    )
    parser.add_argument(
        "--list-only", action="store_true", help="Lister les PDFs sans les traiter"
    )
    parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=0,
        help="Limiter le nombre de PDFs à traiter (0 = tous)",
    )
    parser.add_argument(
        "--category",
        "-c",
        choices=list(CATEGORIES.keys()),
        help="Traiter uniquement une catégorie",
    )
    parser.add_argument(
        "--force", action="store_true", help="Retraiter les PDFs déjà extraits"
    )
    parser.add_argument(
        "--delay",
        "-d",
        type=float,
        default=2.0,
        help="Délai en secondes entre chaque requête API (défaut: 2.0)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("📄 Extraction de PDFs avec Mistral Document AI")
    print("   (Exécution locale uniquement)")
    print("=" * 60)
    print()

    # Scan for PDFs in category folders only
    print("🔍 Scan des 7 catégories...")
    pdf_links = scan_categories_for_pdfs()

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
    for cat in sorted(CATEGORIES.keys()):
        count = len(by_category.get(cat, []))
        if count > 0:
            cat_title = CATEGORIES[cat]
            print(f"   - {cat_title}: {count} PDF(s)")

    print()

    # List-only mode
    if args.list_only:
        print("📋 Liste des PDFs:")
        print("-" * 60)
        for cat in sorted(CATEGORIES.keys()):
            if args.category and cat != args.category:
                continue
            if cat not in by_category:
                continue

            print(f"\n### {CATEGORIES[cat]}")
            print(f"    → docs/{cat}/pdf_extracts/")
            for url, info in by_category[cat]:
                filename = get_pdf_filename(url)
                print(f"  - {filename}")
                print(f"    {url[:70]}{'...' if len(url) > 70 else ''}")
        return

    # Check API key
    if not MISTRAL_API_KEY:
        print("❌ MISTRAL_API_KEY non défini!")
        print()
        print("Pour extraire les PDFs:")
        print("  export MISTRAL_API_KEY='votre-clé-api'")
        print("  python scripts/extract_pdf_with_mistral.py")
        print()
        print("Ou utilisez --list-only pour voir la liste sans extraction.")
        return

    # Load existing index
    index = load_pdf_index()

    # Process PDFs
    processed = 0
    skipped = 0
    errors = 0

    pdfs_to_process = []
    for cat in sorted(CATEGORIES.keys()):
        if args.category and cat != args.category:
            continue
        for url, info in by_category.get(cat, []):
            pdfs_to_process.append((url, info))

    if args.limit > 0:
        pdfs_to_process = pdfs_to_process[: args.limit]

    print(f"🚀 Traitement de {len(pdfs_to_process)} PDF(s)...")
    if args.delay > 0:
        print(f"   (délai de {args.delay}s entre les requêtes)")
    print()

    for idx, (url, info) in enumerate(pdfs_to_process):
        filename = get_pdf_filename(url)
        category = info["category"]

        # Check if already processed
        url_hash = hashlib.md5(url.encode()).hexdigest()
        if url_hash in index["pdfs"] and not args.force:
            print(f"⏭️  {filename} (déjà traité)")
            skipped += 1
            continue

        print(f"📄 [{category}] {filename}...")

        try:
            result = process_pdf_with_mistral(url)

            if result["success"]:
                output_path = save_pdf_extract(url, info, result)

                # Update index
                index["pdfs"][url_hash] = {
                    "url": url,
                    "filename": filename,
                    "category": category,
                    "output_path": str(output_path),
                    "pages": result.get("pages", 0),
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                }

                print(f"   ✅ {result.get('pages', '?')} pages → {output_path}")
                processed += 1
            else:
                print(f"   ❌ {result.get('error', 'Unknown error')}")
                errors += 1

        except Exception as e:
            print(f"   ❌ Exception: {str(e)[:100]}")
            errors += 1

        # Sleep between API calls (except after the last one)
        if args.delay > 0 and idx < len(pdfs_to_process) - 1:
            time.sleep(args.delay)

    # Save index
    save_pdf_index(index)

    # Generate category indexes
    print()
    print("📝 Génération des index par catégorie...")
    for cat in CATEGORIES.keys():
        cat_pdfs = [p for p in index["pdfs"].values() if p.get("category") == cat]
        if cat_pdfs:
            generate_category_pdf_index(cat, cat_pdfs)
            print(f"   ✅ docs/{cat}/pdf_extracts/INDEX.md")

    print()
    print("=" * 60)
    print(f"✅ Traitement terminé!")
    print(f"   - Traités: {processed}")
    print(f"   - Ignorés (déjà faits): {skipped}")
    print(f"   - Erreurs: {errors}")
    print(f"   - Index: docs/.pdf_extracts_index.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
