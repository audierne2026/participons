#!/usr/bin/env python3
"""
Weekly Synthesis Script for Audierne2026

Generates a one-page French summary of how contributions
could enhance the program, organized by category.

Usage:
    python weekly_synthesis.py [--days 7] [--output synthese.md]
"""

import os
import argparse
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import requests

# Load .env for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ====================== CONFIGURATION ======================
GITHUB_REPO = os.getenv("GITHUB_REPO", os.getenv("GITHUB_REPOSITORY", "audierne2026/participons"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Program categories with French labels
PROGRAM_CATEGORIES = {
    "logement": {
        "label": "Logement & Urbanisme",
        "anchor": "logement",
        "keywords": ["logement", "urbanisme", "habitat", "rénovation", "construction", "immobilier", "loyer", "locataire"]
    },
    "associations": {
        "label": "Associations & Vie locale",
        "anchor": "associations",
        "keywords": ["association", "bénévole", "local", "communauté", "solidarité", "entraide"]
    },
    "jeunesse": {
        "label": "École & Jeunesse",
        "anchor": "jeunesse",
        "keywords": ["jeunesse", "école", "éducation", "enfant", "adolescent", "périscolaire", "jeune"]
    },
    "ecologie": {
        "label": "Environnement",
        "anchor": "environnement",
        "keywords": ["environnement", "écologie", "climat", "déchet", "énergie", "nature", "biodiversité"]
    },
    "economie": {
        "label": "Économie locale",
        "anchor": "economie",
        "keywords": ["économie", "commerce", "tourisme", "emploi", "entreprise", "artisan", "pêche"]
    },
    "culture": {
        "label": "Culture & Patrimoine",
        "anchor": "culture",
        "keywords": ["culture", "patrimoine", "musée", "chapelle", "église", "festival", "art", "histoire"]
    },
    "alimentation-bien-etre-soins": {
        "label": "Alimentation, bien-être et soins",
        "anchor": "alimentation-bien-etre-soins",
        "keywords": ["alimentation", "santé", "bien-être", "soins", "médecin", "bio", "local", "senior"]
    }
}

# =========================================================


def get_github_headers():
    """Return headers for GitHub API calls."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def fetch_issues_with_comments(since_date):
    """Fetch issues updated since a given date, with their comments."""
    print(f"🔍 Récupération des issues depuis {since_date.strftime('%d/%m/%Y')}...")

    issues = []
    page = 1
    headers = get_github_headers()

    while True:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
        params = {
            "state": "all",
            "since": since_date.isoformat(),
            "per_page": 100,
            "page": page
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"❌ Erreur: {response.status_code}")
            break

        data = response.json()
        if not data:
            break

        # Filter out pull requests
        issues.extend([item for item in data if "pull_request" not in item])
        page += 1

        if len(data) < 100:
            break

    # Fetch comments for each issue
    print(f"📝 Récupération des commentaires pour {len(issues)} issues...")

    for issue in issues:
        if issue.get("comments", 0) > 0:
            comments_url = issue["comments_url"]
            response = requests.get(comments_url, headers=headers)
            if response.status_code == 200:
                issue["comment_list"] = response.json()
            else:
                issue["comment_list"] = []
        else:
            issue["comment_list"] = []

    return issues


def is_contribution(issue):
    """Check if issue is a contribution (not automated report)."""
    labels = [label["name"].lower() for label in issue.get("labels", [])]
    if "rapport" in labels or "automatisé" in labels:
        return False
    return "conforme charte" in labels


def categorize_issue(issue):
    """Determine which program categories an issue relates to."""
    categories = []
    labels = [label["name"].lower() for label in issue.get("labels", [])]

    # Check labels first
    for cat_key, cat_info in PROGRAM_CATEGORIES.items():
        if cat_key in labels or any(kw in labels for kw in cat_info["keywords"]):
            categories.append(cat_key)

    # If no label match, check content
    if not categories:
        text = f"{issue['title']} {issue.get('body', '')}".lower()
        for cat_key, cat_info in PROGRAM_CATEGORIES.items():
            if any(kw in text for kw in cat_info["keywords"]):
                categories.append(cat_key)

    return categories if categories else ["autre"]


def extract_key_points(issue):
    """Extract key points from issue body and comments."""
    points = []

    # Skip patterns (metadata, form fields, etc.)
    skip_patterns = [
        "submitted", "soumis", "category:", "values:", "0.0.0.0",
        "formulaire", "framaforms", "anonyme", "utilisateur",
        "factuel:", "d'améliorations:", "constat factuel",
        "http://", "https://", "```", "---", "###"
    ]

    # Extract from body
    body = issue.get("body", "") or ""

    # Look for structured content after "Constat factuel" or "idées d'améliorations"
    sections = {
        "constat": "",
        "idees": ""
    }

    current_section = None
    for line in body.split("\n"):
        line_lower = line.lower().strip()

        if "constat factuel" in line_lower:
            current_section = "constat"
            continue
        elif "idées d'améliorations" in line_lower or "vos idées" in line_lower:
            current_section = "idees"
            continue

        if current_section and line.strip():
            # Skip metadata
            if any(skip in line_lower for skip in skip_patterns):
                continue
            sections[current_section] += line.strip() + " "

    # Extract meaningful points from sections
    for _, content in sections.items():
        if content and len(content) > 30:
            # Clean and truncate
            clean = content.strip()
            if len(clean) > 150:
                clean = clean[:147] + "..."
            points.append(clean)

    # Extract from comments (contextualizations by team)
    for comment in issue.get("comment_list", []):
        comment_body = comment.get("body", "") or ""
        # Skip bot comments
        if "bot" in comment.get("user", {}).get("login", "").lower():
            continue

        # Look for synthesis or context added by team
        for line in comment_body.split("\n"):
            line = line.strip()
            # Skip metadata and code blocks
            if any(skip in line.lower() for skip in skip_patterns):
                continue
            # Keep meaningful synthesis (starts with certain keywords)
            if len(line) > 40 and not line.startswith(("#", "-", "*", ">", "`")):
                clean = line[:150] + "..." if len(line) > 150 else line
                points.append(clean)
                break  # Only first meaningful line per comment

    # Deduplicate and limit
    seen = set()
    unique_points = []
    for point in points:
        key = point[:40].lower()
        if key not in seen:
            seen.add(key)
            unique_points.append(point)

    return unique_points[:3]  # Limit to 3 key points


def generate_synthesis(issues, days, output_file):
    """Generate a one-page French synthesis."""
    print(f"📄 Génération de la synthèse...")

    # Filter contributions
    contributions = [i for i in issues if is_contribution(i)]

    # Group by category
    by_category = defaultdict(list)
    for issue in contributions:
        cats = categorize_issue(issue)
        for cat in cats:
            by_category[cat].append(issue)

    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    # Generate report
    lines = [
        f"# Synthèse des contributions",
        f"",
        f"**Période :** {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')} ({days} jours)",
        f"",
        f"**Total contributions analysées :** {len(contributions)}",
        f"",
        f"---",
        f"",
    ]

    # Summary by category
    if not contributions:
        lines.append("*Aucune nouvelle contribution sur cette période.*")
    else:
        for cat_key, cat_info in PROGRAM_CATEGORIES.items():
            cat_issues = by_category.get(cat_key, [])

            if not cat_issues:
                continue

            lines.append(f"## {cat_info['label']}")
            lines.append(f"")
            lines.append(f"**{len(cat_issues)} contribution(s)** pouvant enrichir cette section du programme.")
            lines.append(f"")

            # Aggregate key points
            all_points = []
            issue_refs = []

            for issue in cat_issues[:5]:  # Limit to 5 issues per category
                points = extract_key_points(issue)
                all_points.extend(points)
                issue_refs.append(f"[#{issue['number']}]({issue['html_url']})")

            # Synthesize points (take unique, meaningful ones)
            seen = set()
            unique_points = []
            for point in all_points:
                # Simple deduplication
                key = point[:50].lower()
                if key not in seen and len(point) > 20:
                    seen.add(key)
                    unique_points.append(point)

            if unique_points:
                lines.append("**Points clés relevés :**")
                lines.append("")
                for point in unique_points[:3]:  # Max 3 points per category
                    # Truncate and clean
                    clean_point = point.replace("\n", " ").strip()
                    if len(clean_point) > 150:
                        clean_point = clean_point[:147] + "..."
                    lines.append(f"- {clean_point}")
                lines.append("")

            lines.append(f"*Issues : {', '.join(issue_refs)}*")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Handle "autre" category
        if by_category.get("autre"):
            lines.append("## Autres contributions")
            lines.append("")
            lines.append(f"**{len(by_category['autre'])} contribution(s)** à catégoriser.")
            lines.append("")
            for issue in by_category["autre"][:3]:
                lines.append(f"- [#{issue['number']}]({issue['html_url']}): {issue['title'][:60]}...")
            lines.append("")
            lines.append("---")
            lines.append("")

    # Footer with action items
    lines.extend([
        "## Actions suggérées",
        "",
        "1. **Contextualiser** les issues récentes avec des commentaires enrichissants",
        "2. **Migrer** vers discussions les contributions suffisamment contextualisées",
        "3. **Intégrer** les points validés dans le programme",
        "",
        "---",
        "",
        f"*Synthèse générée le {datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M UTC')}*",
        f"",
        f"*Script : `scripts/weekly_synthesis.py`*"
    ])

    # Write report
    report_content = "\n".join(lines)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"✅ Synthèse générée : {output_file}")
    return report_content


def main():
    parser = argparse.ArgumentParser(
        description="Génère une synthèse hebdomadaire des contributions"
    )
    parser.add_argument(
        "--days",
        "-d",
        type=int,
        default=7,
        help="Fenêtre temporelle en jours (défaut: 7)"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="synthese_hebdo.md",
        help="Fichier de sortie (défaut: synthese_hebdo.md)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("📋 Synthèse hebdomadaire Audierne2026")
    print("=" * 60)
    print()

    if not GITHUB_TOKEN:
        print("⚠️  GITHUB_TOKEN non défini. Limites d'API réduites.")
        print()

    # Calculate date range
    since_date = datetime.now(timezone.utc) - timedelta(days=args.days)

    # Fetch data
    issues = fetch_issues_with_comments(since_date)

    # Generate synthesis
    generate_synthesis(issues, args.days, args.output)

    print()
    print("=" * 60)
    print("✅ Synthèse terminée !")
    print(f"📄 Fichier : {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
