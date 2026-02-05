#!/usr/bin/env python3
"""
Export GitHub contributions to individual Markdown files.

This script:
1. Fetches all issues labeled 'conforme charte' from GitHub
2. Fetches ALL discussions from the repository
3. Creates individual .md files for each issue and discussion
4. Organizes them in docs/<category>/contributions/
5. Generates a tree index of all contributions

Usage:
    python export_contributions_to_md.py [--clean] [--category economie]

Environment variables:
    GITHUB_TOKEN: GitHub token for API access
    GITHUB_REPO: Repository (default: audierne2026/participons)
"""

import os
import sys
import re
import json
import argparse
import subprocess
import shutil
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path
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

# Category mappings (GitHub label -> docs folder)
CATEGORIES = {
    "economie": {
        "folder": "economie",
        "title": "Économie locale",
        "labels": ["economie", "économie"]
    },
    "logement": {
        "folder": "logement",
        "title": "Logement & Urbanisme",
        "labels": ["logement", "urbanisme"]
    },
    "culture": {
        "folder": "culture",
        "title": "Culture & Patrimoine",
        "labels": ["culture", "patrimoine"]
    },
    "ecologie": {
        "folder": "environnement",
        "title": "Environnement",
        "labels": ["ecologie", "écologie", "environnement"]
    },
    "associations": {
        "folder": "associations",
        "title": "Associations & Vie locale",
        "labels": ["associations", "vie-locale"]
    },
    "jeunesse": {
        "folder": "jeunesse",
        "title": "École & Jeunesse",
        "labels": ["jeunesse", "école", "ecole"]
    },
    "alimentation-bien-etre-soins": {
        "folder": "alimentation-bien-etre-soins",
        "title": "Alimentation, bien-être et soins",
        "labels": ["alimentation", "bien-être", "soins", "alimentation-bien-etre-soins"]
    }
}

# =========================================================


def get_github_headers():
    """Return headers for GitHub API calls."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def get_git_commit_info():
    """Get current git commit hash."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except subprocess.CalledProcessError:
        return "unknown"


def fetch_issues():
    """Fetch all contribution issues with their comments using gh CLI."""
    print(f"🔍 Récupération des issues depuis {GITHUB_REPO}...")

    issues = []

    # Try gh CLI first
    try:
        # Fetch issues with label "conforme charte"
        cmd = [
            "gh", "issue", "list",
            "-R", GITHUB_REPO,
            "-l", "conforme charte",
            "-s", "all",
            "-L", "200",
            "--json", "number,title,body,state,createdAt,updatedAt,labels,comments,url"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            data = json.loads(result.stdout)

            for item in data:
                labels = [l["name"].lower() for l in item.get("labels", [])]
                if "rapport" not in labels and "automatisé" not in labels:
                    # Convert gh format to API format
                    item["html_url"] = item.pop("url", "")
                    item["created_at"] = item.pop("createdAt", "")
                    item["updated_at"] = item.pop("updatedAt", "")
                    issues.append(item)

            print(f"   {len(issues)} issues récupérées via gh CLI")

            # Process comments - gh CLI returns them directly
            print(f"   Traitement des commentaires...")
            for issue in issues:
                comments_raw = issue.get("comments", [])
                # Comments field from gh is already a list
                if isinstance(comments_raw, list) and comments_raw:
                    issue["comment_list"] = [
                        {
                            "body": c.get("body", ""),
                            "user": {"login": c.get("author", {}).get("login", "Anonyme") if c.get("author") else "Anonyme"},
                            "created_at": c.get("createdAt", "")
                        }
                        for c in comments_raw
                    ]
                    # Store count for display
                    issue["comments"] = len(comments_raw)
                else:
                    issue["comment_list"] = []
                    issue["comments"] = 0

            print(f"✅ {len(issues)} issues trouvées (via gh CLI)")
            return issues

    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"⚠️  gh CLI échoué: {e}")

    # Fallback to REST API
    page = 1
    headers = get_github_headers()

    while True:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
        params = {
            "state": "all",
            "labels": "conforme charte",
            "per_page": 100,
            "page": page
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"❌ Erreur GitHub API: {response.status_code}")
            break

        data = response.json()
        if not data:
            break

        for item in data:
            if "pull_request" in item:
                continue
            labels = [l["name"].lower() for l in item.get("labels", [])]
            if "rapport" not in labels and "automatisé" not in labels:
                issues.append(item)

        page += 1
        if len(data) < 100:
            break

    # Fetch comments for each issue
    print(f"   Récupération des commentaires...")
    for issue in issues:
        if issue.get("comments", 0) > 0:
            response = requests.get(issue["comments_url"], headers=headers)
            if response.status_code == 200:
                issue["comment_list"] = response.json()
            else:
                issue["comment_list"] = []
        else:
            issue["comment_list"] = []

    print(f"✅ {len(issues)} issues trouvées")
    return issues


def fetch_all_discussions():
    """Fetch ALL discussions from the repository using gh CLI or API."""
    print(f"🔍 Récupération des discussions depuis {GITHUB_REPO}...")

    owner, repo = GITHUB_REPO.split("/")

    # Try using gh CLI first (it handles authentication)
    try:
        discussions = []
        cursor_param = ""

        while True:
            # Build query with cursor handling
            if cursor_param:
                query = f'''
                query {{
                  repository(owner: "{owner}", name: "{repo}") {{
                    discussions(first: 50, after: "{cursor_param}") {{
                      pageInfo {{ hasNextPage endCursor }}
                      nodes {{
                        number title body url createdAt updatedAt closed
                        author {{ login }}
                        category {{ name slug }}
                        labels(first: 10) {{ nodes {{ name }} }}
                        comments(first: 30) {{
                          totalCount
                          nodes {{
                            body
                            author {{ login }}
                            createdAt
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
                '''
            else:
                query = f'''
                query {{
                  repository(owner: "{owner}", name: "{repo}") {{
                    discussions(first: 50) {{
                      pageInfo {{ hasNextPage endCursor }}
                      nodes {{
                        number title body url createdAt updatedAt closed
                        author {{ login }}
                        category {{ name slug }}
                        labels(first: 10) {{ nodes {{ name }} }}
                        comments(first: 30) {{
                          totalCount
                          nodes {{
                            body
                            author {{ login }}
                            createdAt
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
                '''

            cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"⚠️  gh CLI échoué: {result.stderr[:100]}")
                break

            data = json.loads(result.stdout)

            if "errors" in data:
                print(f"❌ Erreurs GraphQL: {data['errors']}")
                break

            repo_data = data.get("data", {}).get("repository")
            if not repo_data:
                break

            discussion_data = repo_data["discussions"]
            discussions.extend(discussion_data["nodes"])

            print(f"   Récupéré {len(discussion_data['nodes'])} discussions...")

            if not discussion_data["pageInfo"]["hasNextPage"]:
                break

            cursor_param = discussion_data["pageInfo"]["endCursor"]

        if discussions:
            print(f"✅ {len(discussions)} discussions trouvées (via gh CLI)")
            return discussions

    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"⚠️  gh CLI non disponible: {e}")

    # Fallback to API with token
    if not GITHUB_TOKEN:
        print("⚠️  GITHUB_TOKEN non défini, impossible de récupérer les discussions")
        return []

    query = """
    query($owner: String!, $repo: String!, $cursor: String) {
      repository(owner: $owner, name: $repo) {
        discussions(first: 50, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            number title body url createdAt updatedAt closed
            author { login }
            category { name slug }
            labels(first: 10) { nodes { name } }
            comments(first: 30) {
              totalCount
              nodes {
                body
                author { login }
                createdAt
              }
            }
          }
        }
      }
    }
    """

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
            print(f"❌ Erreur GraphQL: {response.status_code}")
            print(f"   {response.text[:200]}")
            break

        data = response.json()

        if "errors" in data:
            print(f"❌ Erreurs GraphQL: {data['errors']}")
            break

        repo_data = data.get("data", {}).get("repository")
        if not repo_data:
            print("❌ Repository non trouvé")
            break

        discussion_data = repo_data["discussions"]
        discussions.extend(discussion_data["nodes"])

        print(f"   Récupéré {len(discussion_data['nodes'])} discussions...")

        if not discussion_data["pageInfo"]["hasNextPage"]:
            break

        cursor = discussion_data["pageInfo"]["endCursor"]

    print(f"✅ {len(discussions)} discussions trouvées")
    return discussions


def categorize_item(item, item_type="issue"):
    """Determine which categories an item belongs to."""
    matched_categories = []

    # Get labels
    if item_type == "issue":
        labels = [l["name"].lower() for l in item.get("labels", [])]
    else:  # discussion
        label_nodes = item.get("labels", {}).get("nodes", [])
        labels = [l["name"].lower() for l in label_nodes]

    # Match against category labels
    for cat_key, cat_info in CATEGORIES.items():
        for label in cat_info["labels"]:
            if label in labels:
                if cat_key not in matched_categories:
                    matched_categories.append(cat_key)
                break

    # Fallback: check title
    if not matched_categories:
        title_lower = item.get("title", "").lower()
        for cat_key, cat_info in CATEGORIES.items():
            for label in cat_info["labels"]:
                if label in title_lower:
                    if cat_key not in matched_categories:
                        matched_categories.append(cat_key)
                    break

    return matched_categories if matched_categories else ["autre"]


def extract_links(text):
    """Extract URLs from text content."""
    if not text:
        return []

    links = []

    # Match markdown links
    md_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    for match in re.finditer(md_link_pattern, text):
        title, url = match.groups()
        if "github.com/audierne2026" not in url:
            links.append({"title": title.strip(), "url": url.strip()})

    # Match raw URLs
    raw_url_pattern = r'(?<!\()https?://[^\s<>\)\]"\'`]+'
    existing_urls = {l["url"] for l in links}
    for match in re.finditer(raw_url_pattern, text):
        url = match.group().rstrip(".,;:!?")
        if url not in existing_urls and "github.com/audierne2026" not in url:
            links.append({"title": "", "url": url})

    return links


def sanitize_filename(text):
    """Create a safe filename from text."""
    # Remove special characters, keep alphanumeric and hyphens
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text)
    return text[:50].strip('-')


def generate_issue_md(issue, commit_hash):
    """Generate markdown content for an issue."""
    labels = [l["name"] for l in issue.get("labels", [])]
    labels_str = ", ".join(f"`{l}`" for l in labels) if labels else "*Aucun*"

    state_emoji = "🟢 Ouverte" if issue["state"] == "open" else "✅ Fermée"

    lines = [
        f"# Issue #{issue['number']}: {issue['title']}",
        "",
        f"**État :** {state_emoji}  ",
        f"**Créée le :** {issue['created_at'][:10]}  ",
        f"**Mise à jour :** {issue['updated_at'][:10]}  ",
        f"**Labels :** {labels_str}  ",
        f"**Lien GitHub :** [{GITHUB_REPO}#{issue['number']}]({issue['html_url']})",
        "",
        "---",
        "",
        "## Contenu de la contribution",
        "",
    ]

    body = issue.get("body", "") or "*Pas de description*"
    lines.append(body)
    lines.append("")

    # Comments section
    comments = issue.get("comment_list", [])
    if comments:
        lines.extend([
            "---",
            "",
            f"## Commentaires ({len(comments)})",
            "",
        ])

        for i, comment in enumerate(comments, 1):
            author = comment.get("user", {}).get("login", "Anonyme")
            date = comment.get("created_at", "")[:10]
            lines.append(f"### Commentaire {i} - {author} ({date})")
            lines.append("")
            lines.append(comment.get("body", "") or "*Vide*")
            lines.append("")

    # Extract and list links
    all_text = body + " ".join(c.get("body", "") or "" for c in comments)
    links = extract_links(all_text)

    if links:
        lines.extend([
            "---",
            "",
            "## Liens extraits",
            "",
        ])
        for link in links:
            title = link["title"] or link["url"]
            lines.append(f"- [{title}]({link['url']})")
        lines.append("")

    # Footer
    lines.extend([
        "---",
        "",
        f"*Exporté le {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')} · Commit: `{commit_hash[:7]}`*"
    ])

    return "\n".join(lines)


def generate_discussion_md(discussion, commit_hash):
    """Generate markdown content for a discussion."""
    label_nodes = discussion.get("labels", {}).get("nodes", [])
    labels = [l["name"] for l in label_nodes]
    labels_str = ", ".join(f"`{l}`" for l in labels) if labels else "*Aucun*"

    category = discussion.get("category", {})
    cat_name = category.get("name", "N/A") if category else "N/A"

    state_emoji = "✅ Fermée" if discussion.get("closed") else "🟢 Ouverte"

    author = discussion.get("author", {})
    author_name = author.get("login", "Anonyme") if author else "Anonyme"

    lines = [
        f"# Discussion #{discussion['number']}: {discussion['title']}",
        "",
        f"**État :** {state_emoji}  ",
        f"**Catégorie GitHub :** {cat_name}  ",
        f"**Auteur :** {author_name}  ",
        f"**Créée le :** {discussion['createdAt'][:10]}  ",
        f"**Mise à jour :** {discussion['updatedAt'][:10]}  ",
        f"**Labels :** {labels_str}  ",
        f"**Lien GitHub :** [{GITHUB_REPO} Discussion #{discussion['number']}]({discussion['url']})",
        "",
        "---",
        "",
        "## Contenu de la discussion",
        "",
    ]

    body = discussion.get("body", "") or "*Pas de description*"
    lines.append(body)
    lines.append("")

    # Comments section
    comments_data = discussion.get("comments", {})
    comments = comments_data.get("nodes", [])

    if comments:
        lines.extend([
            "---",
            "",
            f"## Commentaires ({comments_data.get('totalCount', len(comments))})",
            "",
        ])

        for i, comment in enumerate(comments, 1):
            author = comment.get("author", {})
            author_name = author.get("login", "Anonyme") if author else "Anonyme"
            date = comment.get("createdAt", "")[:10]

            lines.append(f"### Commentaire {i} - {author_name} ({date})")
            lines.append("")
            lines.append(comment.get("body", "") or "*Vide*")
            lines.append("")

            # Include replies
            replies = comment.get("replies", {}).get("nodes", [])
            for j, reply in enumerate(replies, 1):
                reply_author = reply.get("author", {})
                reply_author_name = reply_author.get("login", "Anonyme") if reply_author else "Anonyme"
                reply_date = reply.get("createdAt", "")[:10]

                lines.append(f"#### ↳ Réponse {j} - {reply_author_name} ({reply_date})")
                lines.append("")
                lines.append(reply.get("body", "") or "*Vide*")
                lines.append("")

    # Extract and list links
    all_text = body
    for comment in comments:
        all_text += " " + (comment.get("body", "") or "")
        for reply in comment.get("replies", {}).get("nodes", []):
            all_text += " " + (reply.get("body", "") or "")

    links = extract_links(all_text)

    if links:
        lines.extend([
            "---",
            "",
            "## Liens extraits",
            "",
        ])
        for link in links:
            title = link["title"] or link["url"]
            lines.append(f"- [{title}]({link['url']})")
        lines.append("")

    # Footer
    lines.extend([
        "---",
        "",
        f"*Exporté le {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')} · Commit: `{commit_hash[:7]}`*"
    ])

    return "\n".join(lines)


def generate_tree_index(contributions_by_category, docs_dir, commit_hash):
    """Generate a tree index of all contributions."""
    lines = [
        "# 🌳 Arbre des contributions citoyennes",
        "",
        f"**Généré le :** {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}  ",
        f"**Commit de référence :** `{commit_hash[:7]}`",
        "",
        "---",
        "",
        "## Vue d'ensemble",
        "",
    ]

    # Summary table
    lines.extend([
        "| Catégorie | Issues | Discussions | Total |",
        "|-----------|--------|-------------|-------|",
    ])

    total_issues = 0
    total_discussions = 0

    for cat_key in sorted(CATEGORIES.keys()):
        cat_info = CATEGORIES[cat_key]
        cat_data = contributions_by_category.get(cat_key, {"issues": [], "discussions": []})

        issue_count = len(cat_data["issues"])
        disc_count = len(cat_data["discussions"])
        total = issue_count + disc_count

        total_issues += issue_count
        total_discussions += disc_count

        lines.append(f"| [{cat_info['title']}](#{cat_key}) | {issue_count} | {disc_count} | {total} |")

    # Handle "autre" category
    if "autre" in contributions_by_category:
        autre_data = contributions_by_category["autre"]
        issue_count = len(autre_data["issues"])
        disc_count = len(autre_data["discussions"])
        total_issues += issue_count
        total_discussions += disc_count
        lines.append(f"| [Autre](#autre) | {issue_count} | {disc_count} | {issue_count + disc_count} |")

    lines.append(f"| **TOTAL** | **{total_issues}** | **{total_discussions}** | **{total_issues + total_discussions}** |")
    lines.append("")

    # Detailed tree by category
    lines.extend([
        "---",
        "",
        "## Arbre détaillé",
        "",
    ])

    all_categories = list(CATEGORIES.keys()) + (["autre"] if "autre" in contributions_by_category else [])

    for cat_key in all_categories:
        if cat_key == "autre":
            cat_title = "Autre (non catégorisé)"
            cat_folder = "autre"
        else:
            cat_info = CATEGORIES[cat_key]
            cat_title = cat_info["title"]
            cat_folder = cat_info["folder"]

        cat_data = contributions_by_category.get(cat_key, {"issues": [], "discussions": []})

        if not cat_data["issues"] and not cat_data["discussions"]:
            continue

        lines.extend([
            f"### {cat_title} {{#{cat_key}}}",
            "",
            f"📁 `docs/{cat_folder}/contributions/`",
            "",
        ])

        # Issues
        if cat_data["issues"]:
            lines.append("**Issues :**")
            for issue in sorted(cat_data["issues"], key=lambda x: x["number"], reverse=True):
                state = "🟢" if issue["state"] == "open" else "✅"
                filename = f"issue-{issue['number']}.md"
                lines.append(f"- {state} [`{filename}`]({cat_folder}/contributions/{filename}) - {issue['title'][:60]}")
            lines.append("")

        # Discussions
        if cat_data["discussions"]:
            lines.append("**Discussions :**")
            for disc in sorted(cat_data["discussions"], key=lambda x: x["number"], reverse=True):
                state = "✅" if disc.get("closed") else "💬"
                filename = f"discussion-{disc['number']}.md"
                lines.append(f"- {state} [`{filename}`]({cat_folder}/contributions/{filename}) - {disc['title'][:60]}")
            lines.append("")

        lines.append("")

    # Footer
    lines.extend([
        "---",
        "",
        "*Généré par `scripts/export_contributions_to_md.py`*"
    ])

    return "\n".join(lines)


def generate_category_index(cat_key, cat_data, commit_hash):
    """Generate an index for a category's contributions folder."""
    if cat_key == "autre":
        cat_title = "Autre (non catégorisé)"
    else:
        cat_title = CATEGORIES[cat_key]["title"]

    lines = [
        f"# Contributions - {cat_title}",
        "",
        f"**Dernière mise à jour :** {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}  ",
        f"**Commit :** `{commit_hash[:7]}`",
        "",
        "---",
        "",
    ]

    # Issues
    if cat_data["issues"]:
        lines.extend([
            f"## Issues ({len(cat_data['issues'])})",
            "",
        ])
        for issue in sorted(cat_data["issues"], key=lambda x: x["number"], reverse=True):
            state = "🟢" if issue["state"] == "open" else "✅"
            date = issue["created_at"][:10]
            lines.append(f"- {state} [Issue #{issue['number']}](issue-{issue['number']}.md) - {issue['title']}")
            lines.append(f"  - *{date} · {issue.get('comments', 0)} commentaire(s)*")
        lines.append("")

    # Discussions
    if cat_data["discussions"]:
        lines.extend([
            f"## Discussions ({len(cat_data['discussions'])})",
            "",
        ])
        for disc in sorted(cat_data["discussions"], key=lambda x: x["number"], reverse=True):
            state = "✅" if disc.get("closed") else "💬"
            date = disc["createdAt"][:10]
            comment_count = disc.get("comments", {}).get("totalCount", 0)
            lines.append(f"- {state} [Discussion #{disc['number']}](discussion-{disc['number']}.md) - {disc['title']}")
            lines.append(f"  - *{date} · {comment_count} commentaire(s)*")
        lines.append("")

    lines.extend([
        "---",
        "",
        f"[← Retour au README principal](../README.md)"
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Exporte les contributions GitHub vers des fichiers Markdown individuels"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Supprimer les fichiers contributions existants avant export"
    )
    parser.add_argument(
        "--category", "-c",
        help="Exporter une catégorie spécifique uniquement"
    )
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Répertoire de documentation (défaut: docs)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Afficher ce qui serait créé sans écrire les fichiers"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("📄 Export des contributions vers Markdown")
    print("=" * 60)
    print()

    # Get git info
    commit_hash = get_git_commit_info()
    print(f"📌 Commit actuel: {commit_hash[:7]}")
    print()

    # Fetch data
    issues = fetch_issues()
    discussions = fetch_all_discussions()

    print()

    # Group by category
    contributions_by_category = defaultdict(lambda: {"issues": [], "discussions": []})

    for issue in issues:
        categories = categorize_item(issue, "issue")
        for cat in categories:
            contributions_by_category[cat]["issues"].append(issue)

    for discussion in discussions:
        categories = categorize_item(discussion, "discussion")
        for cat in categories:
            contributions_by_category[cat]["discussions"].append(discussion)

    # Summary
    print("📊 Répartition:")
    for cat_key in sorted(contributions_by_category.keys()):
        cat_data = contributions_by_category[cat_key]
        print(f"   - {cat_key}: {len(cat_data['issues'])} issues, {len(cat_data['discussions'])} discussions")

    print()

    if args.dry_run:
        print("[DRY RUN] Fichiers qui seraient créés:")
        print()

    docs_dir = Path(args.docs_dir)
    files_created = 0

    # Process each category
    for cat_key, cat_data in contributions_by_category.items():
        if args.category and cat_key != args.category:
            continue

        if cat_key == "autre":
            cat_folder = "autre"
        else:
            cat_info = CATEGORIES.get(cat_key)
            if not cat_info:
                continue
            cat_folder = cat_info["folder"]

        contrib_dir = docs_dir / cat_folder / "contributions"

        # Clean if requested
        if args.clean and contrib_dir.exists() and not args.dry_run:
            shutil.rmtree(contrib_dir)
            print(f"🗑️  Nettoyé: {contrib_dir}")

        # Create directory
        if not args.dry_run:
            contrib_dir.mkdir(parents=True, exist_ok=True)

        # Export issues
        for issue in cat_data["issues"]:
            filename = f"issue-{issue['number']}.md"
            filepath = contrib_dir / filename

            if args.dry_run:
                print(f"   📄 {filepath}")
            else:
                content = generate_issue_md(issue, commit_hash)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

            files_created += 1

        # Export discussions
        for discussion in cat_data["discussions"]:
            filename = f"discussion-{discussion['number']}.md"
            filepath = contrib_dir / filename

            if args.dry_run:
                print(f"   📄 {filepath}")
            else:
                content = generate_discussion_md(discussion, commit_hash)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

            files_created += 1

        # Create category index
        index_path = contrib_dir / "INDEX.md"
        if args.dry_run:
            print(f"   📄 {index_path}")
        else:
            index_content = generate_category_index(cat_key, cat_data, commit_hash)
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index_content)

        files_created += 1

        if not args.dry_run:
            print(f"✅ {cat_folder}/contributions/: {len(cat_data['issues'])} issues, {len(cat_data['discussions'])} discussions")

    # Generate main tree index
    tree_path = docs_dir / "CONTRIBUTIONS_TREE.md"
    if args.dry_run:
        print(f"   📄 {tree_path}")
    else:
        tree_content = generate_tree_index(contributions_by_category, docs_dir, commit_hash)
        with open(tree_path, "w", encoding="utf-8") as f:
            f.write(tree_content)
        print(f"✅ Arbre généré: {tree_path}")

    files_created += 1

    # Save metadata
    if not args.dry_run:
        metadata = {
            "last_export": datetime.now(timezone.utc).isoformat(),
            "commit_hash": commit_hash,
            "issues_exported": len(issues),
            "discussions_exported": len(discussions),
            "files_created": files_created,
            "categories": {
                cat: {
                    "issues": len(data["issues"]),
                    "discussions": len(data["discussions"])
                }
                for cat, data in contributions_by_category.items()
            }
        }

        metadata_path = docs_dir / ".contributions_export_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 60)
    if args.dry_run:
        print(f"[DRY RUN] {files_created} fichier(s) seraient créés")
    else:
        print(f"✅ {files_created} fichier(s) créés")
    print("=" * 60)


if __name__ == "__main__":
    main()
