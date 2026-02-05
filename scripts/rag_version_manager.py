#!/usr/bin/env python3
"""
RAG Version Manager for Audierne2026 documentation.

This script provides utilities to:
1. Track versions of RAG documentation linked to git commits
2. Compare versions and detect changes
3. Generate version history
4. Validate RAG content consistency

Usage:
    python rag_version_manager.py status              # Show current sync status
    python rag_version_manager.py history [--limit N] # Show version history
    python rag_version_manager.py validate            # Validate RAG files
    python rag_version_manager.py diff <commit1> <commit2> # Compare versions
    python rag_version_manager.py export [--format json|md] # Export RAG index

Environment variables:
    GITHUB_REPO: Repository (default: audierne2026/audierne2026.github.io)
"""

import os
import sys
import json
import argparse
import subprocess
import re
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

# ====================== CONFIGURATION ======================
GITHUB_REPO = os.getenv("GITHUB_REPO", "audierne2026/audierne2026.github.io")
DOCS_DIR = Path("docs")

CATEGORIES = {
    "economie": "Économie locale",
    "logement": "Logement & Urbanisme",
    "culture": "Culture & Patrimoine",
    "environnement": "Environnement",
    "associations": "Associations & Vie locale",
    "jeunesse": "École & Jeunesse",
    "alimentation-bien-etre-soins": "Alimentation, bien-être et soins"
}

# =========================================================


def run_git_command(args, capture_output=True):
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=capture_output,
            text=True,
            check=True
        )
        return result.stdout.strip() if capture_output else None
    except subprocess.CalledProcessError as e:
        return None


def get_current_commit():
    """Get current HEAD commit info."""
    commit_hash = run_git_command(["rev-parse", "HEAD"])
    commit_date = run_git_command(["log", "-1", "--format=%ci"])
    commit_msg = run_git_command(["log", "-1", "--format=%s"])

    return {
        "hash": commit_hash,
        "short_hash": commit_hash[:7] if commit_hash else None,
        "date": commit_date,
        "message": commit_msg
    }


def get_file_version(file_path):
    """Extract version info from a RAG README file."""
    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract version line
    version_match = re.search(r'Version\s+(\d+\.\d+)\s+[–-]\s+(\d{1,2}\s+\w+\s+\d{4})', content)

    # Extract sync info
    sync_match = re.search(r'\*\*Dernière synchronisation\s*:\*\*\s*([^\n]+)', content)

    # Extract commit reference
    commit_match = re.search(r'Commit de référence.*?`([a-f0-9]{7,})`', content)

    # Count contributions
    issue_count = len(re.findall(r'\[#\d+\]', content))
    discussion_count = len(re.findall(r'Discussion #\d+', content))

    # Count external links
    link_count = len(re.findall(r'https?://(?!github\.com/audierne2026)[^\s<>\)\]"\'`]+', content))

    return {
        "version": version_match.group(1) if version_match else "unknown",
        "version_date": version_match.group(2) if version_match else None,
        "last_sync": sync_match.group(1).strip() if sync_match else None,
        "commit_ref": commit_match.group(1) if commit_match else None,
        "issue_count": issue_count,
        "discussion_count": discussion_count,
        "link_count": link_count
    }


def load_sync_metadata():
    """Load synchronization metadata."""
    metadata_path = DOCS_DIR / ".rag_sync_metadata.json"

    if not metadata_path.exists():
        return None

    with open(metadata_path, "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_status(args):
    """Show current sync status of RAG documentation."""
    print("=" * 60)
    print("📊 Statut de la documentation RAG")
    print("=" * 60)
    print()

    # Current git status
    commit = get_current_commit()
    if commit["hash"]:
        print(f"📌 Commit actuel: {commit['short_hash']}")
        print(f"   Date: {commit['date']}")
        print(f"   Message: {commit['message'][:60]}...")
    print()

    # Sync metadata
    metadata = load_sync_metadata()
    if metadata:
        print(f"🔄 Dernière synchronisation: {metadata.get('last_sync', 'N/A')}")
        print(f"   Commit de sync: {metadata.get('commit_hash', 'N/A')[:7]}")
        print(f"   Issues: {metadata.get('issues_count', 0)}")
        print(f"   Discussions: {metadata.get('discussions_count', 0)}")
    else:
        print("⚠️  Aucune métadonnée de synchronisation trouvée")
        print("   Exécutez: python scripts/sync_contributions_to_rag.py")
    print()

    # Per-category status
    print("📁 Statut par catégorie:")
    print("-" * 60)
    print(f"{'Catégorie':<30} {'Version':<10} {'Issues':<8} {'Liens':<8}")
    print("-" * 60)

    for cat_key, cat_title in CATEGORIES.items():
        readme_path = DOCS_DIR / cat_key / "README.md"
        version_info = get_file_version(readme_path)

        if version_info:
            print(f"{cat_key:<30} {version_info['version']:<10} {version_info['issue_count']:<8} {version_info['link_count']:<8}")
        else:
            print(f"{cat_key:<30} {'N/A':<10} {'-':<8} {'-':<8}")

    print("-" * 60)


def cmd_history(args):
    """Show version history from git commits."""
    print("=" * 60)
    print("📜 Historique des versions RAG")
    print("=" * 60)
    print()

    limit = args.limit or 10

    # Get commits that modified docs/
    commits = run_git_command([
        "log",
        f"--max-count={limit}",
        "--format=%H|%ci|%s",
        "--", "docs/"
    ])

    if not commits:
        print("Aucun historique trouvé pour docs/")
        return

    for line in commits.split("\n"):
        if not line:
            continue

        parts = line.split("|", 2)
        if len(parts) != 3:
            continue

        commit_hash, date, message = parts

        # Check which categories were modified
        files_changed = run_git_command([
            "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash,
            "--", "docs/"
        ])

        categories_changed = set()
        if files_changed:
            for f in files_changed.split("\n"):
                for cat in CATEGORIES.keys():
                    if cat in f:
                        categories_changed.add(cat)

        print(f"📌 {commit_hash[:7]} ({date[:10]})")
        print(f"   {message[:70]}")
        if categories_changed:
            print(f"   Catégories: {', '.join(sorted(categories_changed))}")
        print()


def cmd_validate(args):
    """Validate RAG documentation files."""
    print("=" * 60)
    print("✅ Validation de la documentation RAG")
    print("=" * 60)
    print()

    errors = []
    warnings = []

    for cat_key, cat_title in CATEGORIES.items():
        readme_path = DOCS_DIR / cat_key / "README.md"

        if not readme_path.exists():
            errors.append(f"❌ {cat_key}: README.md manquant")
            continue

        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check required sections
        required_sections = [
            "# Contexte RAG",
            "## Catégorie",
            "### Invitation à contribution"
        ]

        for section in required_sections:
            if section not in content:
                warnings.append(f"⚠️  {cat_key}: Section '{section}' manquante")

        # Check for broken internal links
        internal_links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', content)
        for title, link in internal_links:
            if link.startswith("http"):
                continue
            link_path = readme_path.parent / link
            if not link_path.exists():
                errors.append(f"❌ {cat_key}: Lien cassé vers {link}")

        # Check version format
        version_info = get_file_version(readme_path)
        if version_info and version_info["version"] == "unknown":
            warnings.append(f"⚠️  {cat_key}: Format de version non reconnu")

        # Check for duplicate links
        links = re.findall(r'https?://[^\s<>\)\]"\'`]+', content)
        link_counts = defaultdict(int)
        for link in links:
            link_counts[link.rstrip(".,;:!?")] += 1

        duplicates = [l for l, c in link_counts.items() if c > 1]
        if duplicates:
            warnings.append(f"⚠️  {cat_key}: {len(duplicates)} lien(s) en double")

    # Report results
    if errors:
        print("Erreurs:")
        for e in errors:
            print(f"  {e}")
        print()

    if warnings:
        print("Avertissements:")
        for w in warnings:
            print(f"  {w}")
        print()

    if not errors and not warnings:
        print("✅ Toutes les validations ont réussi!")

    print()
    print(f"Résumé: {len(errors)} erreur(s), {len(warnings)} avertissement(s)")


def cmd_diff(args):
    """Compare RAG versions between two commits."""
    commit1 = args.commit1
    commit2 = args.commit2

    print("=" * 60)
    print(f"📊 Comparaison {commit1[:7]}...{commit2[:7]}")
    print("=" * 60)
    print()

    for cat_key in CATEGORIES.keys():
        readme_path = f"docs/{cat_key}/README.md"

        # Get diff
        diff_output = run_git_command([
            "diff",
            commit1, commit2,
            "--", readme_path
        ])

        if diff_output:
            lines_added = diff_output.count("\n+") - 1  # Exclude header
            lines_removed = diff_output.count("\n-") - 1

            print(f"📁 {cat_key}:")
            print(f"   +{lines_added} / -{lines_removed} lignes")
        else:
            print(f"📁 {cat_key}: Aucun changement")


def cmd_export(args):
    """Export RAG index in specified format."""
    export_format = args.format or "json"

    print("=" * 60)
    print(f"📤 Export de l'index RAG ({export_format})")
    print("=" * 60)
    print()

    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "commit": get_current_commit(),
        "categories": {}
    }

    for cat_key, cat_title in CATEGORIES.items():
        readme_path = DOCS_DIR / cat_key / "README.md"
        version_info = get_file_version(readme_path)

        index["categories"][cat_key] = {
            "title": cat_title,
            "path": str(readme_path),
            "version": version_info["version"] if version_info else "N/A",
            "last_sync": version_info["last_sync"] if version_info else None,
            "stats": {
                "issues": version_info["issue_count"] if version_info else 0,
                "discussions": version_info["discussion_count"] if version_info else 0,
                "links": version_info["link_count"] if version_info else 0
            }
        }

    if export_format == "json":
        output_path = DOCS_DIR / "rag_index.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        print(f"✅ Index exporté: {output_path}")

    elif export_format == "md":
        output_path = DOCS_DIR / "RAG_INDEX.md"

        lines = [
            "# Index RAG - Audierne 2026",
            "",
            f"**Généré le:** {index['generated_at']}",
            f"**Commit:** `{index['commit']['short_hash']}`",
            "",
            "## Catégories",
            "",
            "| Catégorie | Version | Issues | Discussions | Liens |",
            "|-----------|---------|--------|-------------|-------|"
        ]

        for cat_key, cat_data in index["categories"].items():
            stats = cat_data["stats"]
            lines.append(
                f"| [{cat_data['title']}]({cat_key}/README.md) | "
                f"{cat_data['version']} | "
                f"{stats['issues']} | "
                f"{stats['discussions']} | "
                f"{stats['links']} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "*Généré par `scripts/rag_version_manager.py`*"
        ])

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"✅ Index exporté: {output_path}")

    # Also save metadata
    metadata = load_sync_metadata()
    if metadata:
        index["sync_metadata"] = metadata

    return index


def cmd_complement(args):
    """Add complementary information to a category without duplicating."""
    category = args.category
    content = args.content

    if category not in CATEGORIES:
        print(f"❌ Catégorie invalide: {category}")
        print(f"   Catégories disponibles: {', '.join(CATEGORIES.keys())}")
        return

    readme_path = DOCS_DIR / category / "README.md"

    if not readme_path.exists():
        print(f"❌ Fichier non trouvé: {readme_path}")
        return

    with open(readme_path, "r", encoding="utf-8") as f:
        current_content = f.read()

    # Check for duplication
    content_lower = content.lower()
    if content_lower in current_content.lower():
        print("⚠️  Ce contenu existe déjà dans le fichier (pas de duplication)")
        return

    # Find insertion point (before "### Invitation à contribution" if exists)
    insertion_marker = "### Invitation à contribution"

    if insertion_marker in current_content:
        new_content = current_content.replace(
            insertion_marker,
            f"\n{content}\n\n{insertion_marker}"
        )
    else:
        new_content = current_content.rstrip() + f"\n\n{content}\n"

    if args.dry_run:
        print(f"[DRY RUN] Ajouterait à {readme_path}:")
        print(content[:200] + "..." if len(content) > 200 else content)
        return

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ Contenu ajouté à {readme_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Gestionnaire de versions RAG pour Audierne2026"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")

    # status command
    subparsers.add_parser("status", help="Afficher le statut actuel")

    # history command
    history_parser = subparsers.add_parser("history", help="Afficher l'historique")
    history_parser.add_argument("--limit", "-n", type=int, default=10,
                                help="Nombre de commits à afficher")

    # validate command
    subparsers.add_parser("validate", help="Valider les fichiers RAG")

    # diff command
    diff_parser = subparsers.add_parser("diff", help="Comparer deux versions")
    diff_parser.add_argument("commit1", help="Premier commit")
    diff_parser.add_argument("commit2", help="Second commit")

    # export command
    export_parser = subparsers.add_parser("export", help="Exporter l'index RAG")
    export_parser.add_argument("--format", "-f", choices=["json", "md"],
                               default="json", help="Format d'export")

    # complement command
    complement_parser = subparsers.add_parser("complement",
                                              help="Ajouter du contenu complémentaire")
    complement_parser.add_argument("category", help="Catégorie à compléter")
    complement_parser.add_argument("content", help="Contenu à ajouter")
    complement_parser.add_argument("--dry-run", action="store_true",
                                   help="Ne pas appliquer les modifications")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    commands = {
        "status": cmd_status,
        "history": cmd_history,
        "validate": cmd_validate,
        "diff": cmd_diff,
        "export": cmd_export,
        "complement": cmd_complement
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
