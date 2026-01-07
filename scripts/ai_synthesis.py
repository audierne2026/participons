#!/usr/bin/env python3
"""
AI-Powered Synthesis Script for Audierne2026

Uses Claude API to generate a one-page French summary of contributions
organized by program category.

Usage:
    python ai_synthesis.py [--days 7] [--output synthese.md]

Environment variables:
    ANTHROPIC_API_KEY: Your Claude API key
    GITHUB_TOKEN: GitHub token for API access
"""

import os
import argparse
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import requests
import json

# Load .env for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ====================== CONFIGURATION ======================
GITHUB_REPO = os.getenv("GITHUB_REPO", os.getenv("GITHUB_REPOSITORY", "audierne2026/participons"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Program categories
PROGRAM_CATEGORIES = {
    "logement": "Logement & Urbanisme",
    "associations": "Associations & Vie locale",
    "jeunesse": "École & Jeunesse",
    "ecologie": "Environnement",
    "economie": "Économie locale",
    "culture": "Culture & Patrimoine",
    "alimentation-bien-etre-soins": "Alimentation, bien-être et soins"
}

# =========================================================


def get_github_headers():
    """Return headers for GitHub API calls."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def fetch_contributions(since_date):
    """Fetch contribution issues with their comments."""
    print(f"🔍 Récupération des contributions depuis {since_date.strftime('%d/%m/%Y')}...")

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
            print(f"❌ Erreur GitHub API: {response.status_code}")
            print(f"   {response.text[:200]}")
            break

        data = response.json()
        if not data:
            break

        # Filter: only contributions (not reports), exclude PRs
        for item in data:
            if "pull_request" in item:
                continue
            labels = [l["name"].lower() for l in item.get("labels", [])]
            # Include if has "conforme charte" and not automated report
            if "conforme charte" in labels and "rapport" not in labels:
                issues.append(item)

        page += 1
        if len(data) < 100:
            break

    print(f"✅ {len(issues)} contributions trouvées")

    # Fetch comments for each issue
    print(f"📝 Récupération des commentaires...")
    for issue in issues:
        if issue.get("comments", 0) > 0:
            response = requests.get(issue["comments_url"], headers=headers)
            if response.status_code == 200:
                issue["comment_list"] = response.json()
            else:
                issue["comment_list"] = []
        else:
            issue["comment_list"] = []

    return issues


def categorize_issue(issue):
    """Determine which program category an issue belongs to."""
    labels = [l["name"].lower() for l in issue.get("labels", [])]

    for cat_key in PROGRAM_CATEGORIES.keys():
        if cat_key in labels:
            return cat_key

    # Fallback: check title
    title_lower = issue["title"].lower()
    for cat_key in PROGRAM_CATEGORIES.keys():
        if cat_key in title_lower:
            return cat_key

    return "autre"


def prepare_contributions_for_ai(issues):
    """Prepare contribution data for AI summarization."""
    by_category = defaultdict(list)

    for issue in issues:
        category = categorize_issue(issue)
        cat_label = PROGRAM_CATEGORIES.get(category, "Autre")

        # Extract content
        body = issue.get("body", "") or ""
        comments = "\n".join([
            f"[Commentaire]: {c.get('body', '')}"
            for c in issue.get("comment_list", [])
            if c.get("body")
        ])

        contribution = {
            "numero": issue["number"],
            "titre": issue["title"],
            "contenu": body[:2000],  # Limit length
            "commentaires": comments[:1500],  # Limit length
            "url": issue["html_url"]
        }

        by_category[cat_label].append(contribution)

    return dict(by_category)


def call_claude_api(contributions_data, days):
    """Call Claude API to generate synthesis."""
    print("🤖 Appel à Claude API pour la synthèse...")

    if not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY non défini!")
        return None

    # Prepare the data
    contributions_json = json.dumps(contributions_data, ensure_ascii=False, indent=2)

    # =================================================================
    # SYSTEM PROMPT (O Capistaine persona)
    # This should match your Workbench prompt: ocapistaine-weekly-summary
    # =================================================================
    system_prompt = """Tu es O Capistaine, l'assistant IA de la campagne municipale Audierne2026.

## Ton rôle
Tu aides l'équipe de campagne à synthétiser les contributions citoyennes reçues via les formulaires anonymes Framaforms. Ces contributions sont ensuite contextualisées par l'équipe avant d'être débattues publiquement.

## Ton style
- Factuel et neutre : tu rapportes ce que disent les citoyens sans prendre parti
- Concis : tu vas à l'essentiel, maximum 400 mots
- Structuré : tu organises l'information par catégorie du programme
- Actionnable : tu proposes des pistes concrètes pour l'équipe

## Les catégories du programme
1. Logement & Urbanisme
2. Associations & Vie locale
3. École & Jeunesse
4. Environnement
5. Économie locale
6. Culture & Patrimoine
7. Alimentation, bien-être et soins

## Format de sortie attendu
Tu génères UNIQUEMENT du Markdown, sans préambule ni commentaire méta. Le format est :

# Synthèse des contributions citoyennes
**Période :** X jours

## [Catégorie]
**N contribution(s)**
[Points clés en 2-3 phrases, avec références #XX]

## Pistes d'action
1. [Action concrète]
2. [Action concrète]
3. [Action concrète]

## Règles strictes
- Ne jamais inventer de contenu
- Toujours citer les numéros d'issues (#XX)
- Rester dans la limite de 400 mots
- Ignorer les catégories sans contribution"""

    # =================================================================
    # USER PROMPT (données variables)
    # =================================================================
    user_prompt = f"""Génère la synthèse hebdomadaire pour les {days} derniers jours.

Voici les contributions organisées par catégorie :

{contributions_json}

Rappel : synthèse d'une page maximum, format Markdown, en français."""

    # Call Claude API
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    data = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt}
        ]
    }

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=data,
        timeout=60
    )

    if response.status_code != 200:
        print(f"❌ Erreur Claude API: {response.status_code}")
        print(f"   {response.text[:300]}")
        return None

    result = response.json()
    synthesis = result["content"][0]["text"]

    print("✅ Synthèse générée par Claude")
    return synthesis


def generate_fallback_synthesis(contributions_data, days):
    """Generate a basic synthesis without AI (fallback)."""
    print("⚠️  Génération d'une synthèse basique (sans IA)...")

    lines = [
        "# Synthèse des contributions citoyennes",
        "",
        f"**Période :** {days} derniers jours",
        "",
        "---",
        "",
        "*Note : Cette synthèse a été générée automatiquement sans IA.*",
        "",
    ]

    for category, contributions in contributions_data.items():
        if not contributions:
            continue

        lines.append(f"## {category}")
        lines.append("")
        lines.append(f"**{len(contributions)} contribution(s)**")
        lines.append("")

        for contrib in contributions[:3]:
            lines.append(f"- [#{contrib['numero']}]({contrib['url']}): {contrib['titre'][:60]}...")

        lines.append("")

    lines.extend([
        "---",
        "",
        f"*Généré le {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}*"
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Génère une synthèse IA des contributions"
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=7,
        help="Fenêtre temporelle en jours (défaut: 7)"
    )
    parser.add_argument(
        "--output", "-o",
        default="synthese_ia.md",
        help="Fichier de sortie (défaut: synthese_ia.md)"
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Désactiver l'appel IA (extraction uniquement)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🤖 Synthèse IA Audierne2026")
    print("=" * 60)
    print()

    # Check configuration
    if not GITHUB_TOKEN:
        print("⚠️  GITHUB_TOKEN non défini - risque de rate limiting")

    if not ANTHROPIC_API_KEY and not args.no_ai:
        print("⚠️  ANTHROPIC_API_KEY non défini - mode fallback activé")

    # Calculate date range
    since_date = datetime.now(timezone.utc) - timedelta(days=args.days)

    # Fetch contributions
    issues = fetch_contributions(since_date)

    if not issues:
        print("❌ Aucune contribution trouvée sur cette période")
        # Create empty report
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(f"# Synthèse des contributions\n\n*Aucune contribution sur les {args.days} derniers jours.*\n")
        return

    # Prepare data
    contributions_data = prepare_contributions_for_ai(issues)

    # Generate synthesis
    if args.no_ai or not ANTHROPIC_API_KEY:
        synthesis = generate_fallback_synthesis(contributions_data, args.days)
    else:
        synthesis = call_claude_api(contributions_data, args.days)
        if not synthesis:
            synthesis = generate_fallback_synthesis(contributions_data, args.days)

    # Add metadata footer
    synthesis += f"\n\n---\n\n*Synthèse générée le {datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M UTC')}*\n"
    synthesis += f"*Script : `scripts/ai_synthesis.py`*\n"

    # Write output
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(synthesis)

    print()
    print("=" * 60)
    print(f"✅ Synthèse sauvegardée : {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
