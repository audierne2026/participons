#!/usr/bin/env python3
"""
Consolidation script for Audierne2026 contributions.

This script:
1. Fetches all issues labeled 'conforme charte' from GitHub
2. Fetches discussions marked as contributions
3. Groups them by thematic category
4. Analyzes patterns and contradictions (TRIZ framework)
5. Generates a weekly consolidation report

Usage:
    python consolidate_contributions.py [--output report.md]
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter
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

CATEGORIES = [
    "economie",
    "logement",
    "culture",
    "ecologie",
    "associations",
    "jeunesse",
    "alimentation-bien-etre-soins"
]

# TRIZ contradiction matrix - simplified for our use case
TRIZ_PATTERNS = {
    "resource_constraint_vs_ambition": [
        "budget", "coût", "financement", "moyens", "ressources"
    ],
    "participation_vs_efficiency": [
        "consultation", "participation", "rapidité", "efficacité", "délai"
    ],
    "preservation_vs_development": [
        "patrimoine", "préservation", "développement", "modernisation", "changement"
    ],
    "individual_vs_collective": [
        "individuel", "collectif", "communauté", "personnel", "commun"
    ],
    "local_vs_external": [
        "local", "extérieur", "tourisme", "habitants", "résidents"
    ]
}

# =========================================================


def get_github_headers():
    """Return headers for GitHub API calls."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def fetch_issues(state="all"):
    """Fetch all issues from the repository."""
    print(f"🔍 Fetching issues from {GITHUB_REPO}...")

    issues = []
    page = 1
    headers = get_github_headers()

    while True:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
        params = {
            "state": state,
            "per_page": 100,
            "page": page
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"❌ Error fetching issues: {response.status_code}")
            print(response.text)
            break

        data = response.json()
        if not data:
            break

        # Filter out pull requests (they appear in issues endpoint)
        issues.extend([item for item in data if "pull_request" not in item])
        page += 1

        print(f"   Fetched page {page-1}: {len(data)} items")

        if len(data) < 100:
            break

    print(f"✅ Total issues fetched: {len(issues)}\n")
    return issues


def fetch_discussions():
    """Fetch discussions from the repository using GraphQL API."""
    print(f"🔍 Fetching discussions from {GITHUB_REPO}...")

    if not GITHUB_TOKEN:
        print("⚠️  GITHUB_TOKEN not set, cannot fetch discussions")
        return []

    # GraphQL query for discussions
    query = """
    query($owner: String!, $repo: String!, $cursor: String) {
      repository(owner: $owner, name: $repo) {
        discussions(first: 100, after: $cursor) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            number
            title
            body
            createdAt
            updatedAt
            author {
              login
            }
            category {
              name
            }
            labels(first: 10) {
              nodes {
                name
              }
            }
            comments(first: 100) {
              totalCount
              nodes {
                body
                author {
                  login
                }
                createdAt
              }
            }
          }
        }
      }
    }
    """

    owner, repo = GITHUB_REPO.split("/")
    discussions = []
    cursor = None

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    while True:
        variables = {
            "owner": owner,
            "repo": repo,
            "cursor": cursor
        }

        response = requests.post(
            "https://api.github.com/graphql",
            headers=headers,
            json={"query": query, "variables": variables}
        )

        if response.status_code != 200:
            print(f"❌ Error fetching discussions: {response.status_code}")
            print(response.text)
            break

        data = response.json()

        if "errors" in data:
            print(f"❌ GraphQL errors: {data['errors']}")
            break

        discussion_data = data["data"]["repository"]["discussions"]
        discussions.extend(discussion_data["nodes"])

        print(f"   Fetched {len(discussion_data['nodes'])} discussions")

        if not discussion_data["pageInfo"]["hasNextPage"]:
            break

        cursor = discussion_data["pageInfo"]["endCursor"]

    print(f"✅ Total discussions fetched: {len(discussions)}\n")
    return discussions


def categorize_item(item, item_type="issue"):
    """Extract categories from labels."""
    categories = []

    if item_type == "issue":
        labels = [label["name"].lower() for label in item.get("labels", [])]
    else:  # discussion
        label_nodes = item.get("labels", {}).get("nodes", [])
        labels = [label["name"].lower() for label in label_nodes]

    for cat in CATEGORIES:
        if cat in labels:
            categories.append(cat)

    # If no category found, try to infer from title
    if not categories:
        title_lower = item["title"].lower()
        for cat in CATEGORIES:
            if cat in title_lower:
                categories.append(cat)

    return categories if categories else ["autre"]


def is_contribution(item, item_type="issue"):
    """Check if an issue or discussion is a contribution (not a report/automation)."""
    if item_type == "issue":
        labels = [label["name"].lower() for label in item.get("labels", [])]
        # Exclude automated reports
        if "rapport" in labels or "automatisé" in labels:
            return False
        # Include items marked as conforming to charter
        return "conforme charte" in labels
    else:  # discussion
        # For discussions, we can check category or labels
        category = item.get("category", {})
        if category and category.get("name", "").lower() in ["contributions", "propositions", "idées"]:
            return True
        return False


def analyze_triz_patterns(items_by_category):
    """Analyze contributions for TRIZ contradictions and patterns."""
    print("🔬 Analyzing TRIZ patterns...")

    analysis = {
        "contradictions": defaultdict(list),
        "common_themes": Counter(),
        "innovation_opportunities": []
    }

    for category, items in items_by_category.items():
        all_text = ""
        for item in items:
            all_text += f" {item['title']} {item['body'] or ''}"

        all_text_lower = all_text.lower()

        # Detect contradictions
        for contradiction_type, keywords in TRIZ_PATTERNS.items():
            matches = sum(1 for kw in keywords if kw in all_text_lower)
            if matches >= 2:  # At least 2 keywords found
                analysis["contradictions"][category].append({
                    "type": contradiction_type,
                    "strength": matches,
                    "keywords_found": [kw for kw in keywords if kw in all_text_lower]
                })

        # Extract common themes (simple word frequency)
        words = all_text_lower.split()
        # Filter out common words
        stopwords = {"le", "la", "les", "de", "du", "des", "un", "une", "et", "ou", "mais", "pour", "dans", "sur", "à"}
        meaningful_words = [w for w in words if len(w) > 4 and w not in stopwords]
        analysis["common_themes"].update(meaningful_words)

    print(f"✅ TRIZ analysis complete\n")
    return analysis


def generate_report(issues, discussions, output_file):
    """Generate a markdown consolidation report."""
    print(f"📝 Generating consolidation report...")

    # Filter contributions
    contribution_issues = [i for i in issues if is_contribution(i, "issue")]
    contribution_discussions = [d for d in discussions if is_contribution(d, "discussion")]

    # Group by category
    issues_by_category = defaultdict(list)
    discussions_by_category = defaultdict(list)

    for issue in contribution_issues:
        categories = categorize_item(issue, "issue")
        for cat in categories:
            issues_by_category[cat].append(issue)

    for discussion in contribution_discussions:
        categories = categorize_item(discussion, "discussion")
        for cat in categories:
            discussions_by_category[cat].append(discussion)

    # Combine all contributions for TRIZ analysis
    all_contributions_by_category = defaultdict(list)
    for cat in set(list(issues_by_category.keys()) + list(discussions_by_category.keys())):
        all_contributions_by_category[cat] = issues_by_category[cat] + discussions_by_category[cat]

    # TRIZ analysis
    triz_analysis = analyze_triz_patterns(all_contributions_by_category)

    # Generate report
    report_lines = [
        f"# Rapport de consolidation des contributions",
        f"",
        f"**Date :** {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}",
        f"**Période d'analyse :** Toutes les contributions à ce jour",
        f"",
        f"---",
        f"",
        f"## Vue d'ensemble",
        f"",
        f"- **Issues (contributions conformes) :** {len(contribution_issues)}",
        f"- **Discussions (contributions) :** {len(contribution_discussions)}",
        f"- **Total contributions :** {len(contribution_issues) + len(contribution_discussions)}",
        f"",
    ]

    # Breakdown by category
    report_lines.extend([
        f"### Répartition par catégorie",
        f"",
        f"| Catégorie | Issues | Discussions | Total |",
        f"|-----------|--------|-------------|-------|",
    ])

    all_categories = sorted(set(list(issues_by_category.keys()) + list(discussions_by_category.keys())))
    for cat in all_categories:
        issue_count = len(issues_by_category[cat])
        discussion_count = len(discussions_by_category[cat])
        total = issue_count + discussion_count
        report_lines.append(f"| {cat.capitalize()} | {issue_count} | {discussion_count} | {total} |")

    report_lines.extend([
        f"",
        f"---",
        f"",
        f"## Détail par catégorie",
        f"",
    ])

    # Detailed breakdown by category
    for cat in all_categories:
        report_lines.extend([
            f"### {cat.capitalize()}",
            f"",
        ])

        # Issues in this category
        if issues_by_category[cat]:
            report_lines.append(f"#### Issues en cours de contextualisation ({len(issues_by_category[cat])})")
            report_lines.append(f"")
            for issue in issues_by_category[cat]:
                labels = ", ".join([l["name"] for l in issue["labels"] if l["name"] not in ["conforme charte", cat]])
                report_lines.append(f"- [#{issue['number']}]({issue['html_url']}): {issue['title']}")
                if labels:
                    report_lines.append(f"  - Labels: `{labels}`")
                report_lines.append(f"  - Créé: {issue['created_at'][:10]}")
                report_lines.append(f"  - Commentaires: {issue.get('comments', 0)}")
            report_lines.append(f"")

        # Discussions in this category
        if discussions_by_category[cat]:
            report_lines.append(f"#### Discussions actives ({len(discussions_by_category[cat])})")
            report_lines.append(f"")
            for discussion in discussions_by_category[cat]:
                comment_count = discussion.get("comments", {}).get("totalCount", 0)
                report_lines.append(f"- [Discussion #{discussion['number']}](https://github.com/{GITHUB_REPO}/discussions/{discussion['number']}): {discussion['title']}")
                report_lines.append(f"  - Créé: {discussion['createdAt'][:10]}")
                report_lines.append(f"  - Commentaires: {comment_count}")
            report_lines.append(f"")

        # TRIZ analysis for this category
        if cat in triz_analysis["contradictions"] and triz_analysis["contradictions"][cat]:
            report_lines.extend([
                f"#### 🔬 Analyse TRIZ - Contradictions identifiées",
                f"",
            ])
            for contradiction in triz_analysis["contradictions"][cat]:
                report_lines.append(f"- **{contradiction['type'].replace('_', ' ').title()}**")
                report_lines.append(f"  - Force: {contradiction['strength']} occurrences")
                report_lines.append(f"  - Mots-clés: {', '.join(contradiction['keywords_found'])}")
            report_lines.append(f"")

        report_lines.append(f"---")
        report_lines.append(f"")

    # TRIZ common themes
    if triz_analysis["common_themes"]:
        report_lines.extend([
            f"## 🧩 Thèmes transversaux (TRIZ)",
            f"",
            f"Mots-clés les plus fréquents dans toutes les contributions :",
            f"",
        ])
        top_themes = triz_analysis["common_themes"].most_common(20)
        for word, count in top_themes:
            if count >= 3:  # Only show words appearing at least 3 times
                report_lines.append(f"- **{word}** : {count} occurrences")
        report_lines.append(f"")

    # Recommendations
    report_lines.extend([
        f"---",
        f"",
        f"## 💡 Recommandations pour la consolidation",
        f"",
        f"### Issues prêtes pour migration vers Discussions",
        f"",
    ])

    ready_for_discussion = []
    for issue in contribution_issues:
        # Consider ready if: has comments, older than 7 days, marked as documented
        age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))).days
        labels = [l["name"].lower() for l in issue["labels"]]

        if age_days >= 7 or "documentation" in labels or issue.get("comments", 0) >= 3:
            ready_for_discussion.append(issue)

    if ready_for_discussion:
        for issue in ready_for_discussion:
            cats = categorize_item(issue, "issue")
            report_lines.append(f"- [#{issue['number']}]({issue['html_url']}) ({', '.join(cats)}): {issue['title']}")
        report_lines.append(f"")
    else:
        report_lines.append(f"*Aucune issue prête pour le moment (critères: 7+ jours, 3+ commentaires, ou label 'documentation')*")
        report_lines.append(f"")

    report_lines.extend([
        f"### Contradictions à résoudre (approche TRIZ)",
        f"",
    ])

    if triz_analysis["contradictions"]:
        for cat, contradictions in triz_analysis["contradictions"].items():
            if contradictions:
                report_lines.append(f"**{cat.capitalize()}:**")
                for c in contradictions[:2]:  # Top 2 per category
                    report_lines.append(f"- {c['type'].replace('_', ' ').title()}: Nécessite une résolution créative")
                report_lines.append(f"")
    else:
        report_lines.append(f"*Aucune contradiction majeure détectée*")
        report_lines.append(f"")

    report_lines.extend([
        f"### Actions suggérées",
        f"",
        f"1. **Contextualisation active** : Commenter les issues récentes pour enrichir le contexte",
        f"2. **Migration** : Transférer les issues prêtes vers Discussions",
        f"3. **Synthèse thématique** : Créer des discussions de synthèse pour les thèmes transversaux",
        f"4. **Résolution TRIZ** : Organiser des ateliers pour résoudre les contradictions identifiées",
        f"",
        f"---",
        f"",
        f"*Rapport généré automatiquement par `scripts/consolidate_contributions.py`*",
        f"",
        f"**Prochaine étape :** Consolidation finale début février 2026",
    ])

    # Write report
    report_content = "\n".join(report_lines)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"✅ Report generated: {output_file}\n")
    return report_content


def main():
    parser = argparse.ArgumentParser(
        description="Consolidate contributions from GitHub issues and discussions"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="consolidation_report.md",
        help="Output markdown file (default: consolidation_report.md)"
    )
    parser.add_argument(
        "--skip-discussions",
        action="store_true",
        help="Skip fetching discussions (requires GitHub token)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🔧 Consolidation des contributions Audierne2026")
    print("=" * 60)
    print()

    if not GITHUB_TOKEN:
        print("⚠️  Warning: GITHUB_TOKEN not set. API rate limits will be restricted.")
        print("   Set GITHUB_TOKEN in .env or environment for full functionality.\n")

    # Fetch data
    issues = fetch_issues()

    if args.skip_discussions or not GITHUB_TOKEN:
        print("⏭️  Skipping discussions fetch")
        discussions = []
    else:
        discussions = fetch_discussions()

    # Generate report
    report = generate_report(issues, discussions, args.output)

    print("=" * 60)
    print("✅ Consolidation complete!")
    print(f"📄 Report saved to: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
