#!/usr/bin/env python3
"""
Sync GitHub contributions to RAG documentation files.

This script:
1. Fetches issues and discussions labeled 'conforme charte' from GitHub
2. Extracts content and links from contributions
3. Updates README.md files in docs/ categories with citizen contributions
4. Tracks versions linked to git commits
5. Complements existing content without duplication

Usage:
    python sync_contributions_to_rag.py [--dry-run] [--category economie]

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

# Section markers for README updates
CONTRIBUTIONS_SECTION_START = "### Contributions citoyennes (GitHub)"
CONTRIBUTIONS_SECTION_END = "<!-- FIN CONTRIBUTIONS CITOYENNES -->"

# =========================================================


def get_github_headers():
    """Return headers for GitHub API calls."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def get_git_commit_info():
    """Get current git commit hash and date."""
    try:
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()

        commit_date = subprocess.check_output(
            ["git", "log", "-1", "--format=%ci"],
            stderr=subprocess.DEVNULL
        ).decode().strip()

        return commit_hash, commit_date
    except subprocess.CalledProcessError:
        return None, None


def fetch_issues():
    """Fetch all contribution issues using gh CLI or API."""
    print(f"🔍 Récupération des issues depuis {GITHUB_REPO}...")

    issues = []

    # Try gh CLI first (handles authentication)
    try:
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
                labels_list = item.get("labels", [])
                labels = [l["name"].lower() for l in labels_list]
                if "rapport" not in labels and "automatisé" not in labels:
                    # Convert gh format to API format
                    item["html_url"] = item.pop("url", "")
                    item["created_at"] = item.pop("createdAt", "")
                    item["updated_at"] = item.pop("updatedAt", "")
                    # Handle comments (gh returns list)
                    comments_raw = item.get("comments", [])
                    if isinstance(comments_raw, list):
                        item["comments"] = len(comments_raw)
                    issues.append(item)

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

    print(f"✅ {len(issues)} issues trouvées")
    return issues


def fetch_discussions():
    """Fetch ALL discussions using gh CLI or GraphQL API."""
    print(f"🔍 Récupération des discussions depuis {GITHUB_REPO}...")

    owner, repo = GITHUB_REPO.split("/")

    # Try gh CLI first (handles authentication)
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
                          nodes {{ body author {{ login }} createdAt }}
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
                          nodes {{ body author {{ login }} createdAt }}
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
            number title body url createdAt updatedAt
            author { login }
            category { name }
            labels(first: 10) { nodes { name } }
            comments(first: 30) { totalCount nodes { body author { login } createdAt } }
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
        variables = {"owner": owner, "repo": repo, "cursor": cursor}

        response = requests.post(
            "https://api.github.com/graphql",
            headers=headers,
            json={"query": query, "variables": variables}
        )

        if response.status_code != 200:
            print(f"❌ Erreur GraphQL: {response.status_code}")
            break

        data = response.json()

        if "errors" in data:
            print(f"❌ Erreurs GraphQL: {data['errors']}")
            break

        discussion_data = data["data"]["repository"]["discussions"]
        discussions.extend(discussion_data["nodes"])

        if not discussion_data["pageInfo"]["hasNextPage"]:
            break

        cursor = discussion_data["pageInfo"]["endCursor"]

    print(f"✅ {len(discussions)} discussions trouvées")
    return discussions


def extract_links(text):
    """Extract URLs from text content."""
    if not text:
        return []

    # Match markdown links and raw URLs
    md_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    raw_url_pattern = r'https?://[^\s<>\)\]"\'`]+'

    links = []

    # Extract markdown links
    for match in re.finditer(md_link_pattern, text):
        title, url = match.groups()
        # Skip internal GitHub links
        if "github.com" not in url or "audierne2026" not in url:
            links.append({"title": title.strip(), "url": url.strip()})

    # Extract raw URLs not already captured
    existing_urls = {l["url"] for l in links}
    for match in re.finditer(raw_url_pattern, text):
        url = match.group()
        # Clean trailing punctuation
        url = url.rstrip(".,;:!?")
        if url not in existing_urls and "github.com/audierne2026" not in url:
            links.append({"title": "", "url": url})

    return links


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
                matched_categories.append(cat_key)
                break

    # Fallback: check title
    if not matched_categories:
        title_lower = item.get("title", "").lower()
        for cat_key, cat_info in CATEGORIES.items():
            for label in cat_info["labels"]:
                if label in title_lower:
                    matched_categories.append(cat_key)
                    break

    return matched_categories if matched_categories else []


def extract_contribution_data(item, item_type="issue"):
    """Extract structured data from an issue or discussion."""
    body = item.get("body", "") or ""

    # Extract links from body
    links = extract_links(body)

    # Extract links from comments
    if item_type == "issue":
        comment_bodies = []  # Would need separate API call
    else:
        comments = item.get("comments", {}).get("nodes", [])
        for comment in comments:
            comment_body = comment.get("body", "") or ""
            links.extend(extract_links(comment_body))

    # Build contribution object
    if item_type == "issue":
        return {
            "type": "issue",
            "number": item["number"],
            "title": item["title"],
            "url": item["html_url"],
            "created_at": item["created_at"][:10],
            "state": item["state"],
            "body_preview": body[:500] if body else "",
            "links": links,
            "comment_count": item.get("comments", 0)
        }
    else:
        return {
            "type": "discussion",
            "number": item["number"],
            "title": item["title"],
            "url": item["url"],
            "created_at": item["createdAt"][:10],
            "body_preview": body[:500] if body else "",
            "links": links,
            "comment_count": item.get("comments", {}).get("totalCount", 0)
        }


def load_existing_tracked_items(readme_path):
    """Load already tracked issue/discussion numbers from README."""
    tracked = {"issues": set(), "discussions": set()}

    if not os.path.exists(readme_path):
        return tracked

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find tracked issues: #XX format
    issue_pattern = r'\[#(\d+)\]'
    for match in re.finditer(issue_pattern, content):
        tracked["issues"].add(int(match.group(1)))

    # Find tracked discussions: Discussion #XX format
    disc_pattern = r'Discussion #(\d+)'
    for match in re.finditer(disc_pattern, content):
        tracked["discussions"].add(int(match.group(1)))

    return tracked


def generate_contributions_section(contributions, category_key, commit_hash, commit_date):
    """Generate markdown section for contributions with links to individual files."""
    # Get the folder name for this category
    cat_folder = CATEGORIES.get(category_key, {}).get("folder", category_key)

    lines = [
        "",
        CONTRIBUTIONS_SECTION_START,
        "",
        f"**Dernière synchronisation :** {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}  ",
        f"**Commit de référence :** [`{commit_hash[:7]}`](https://github.com/{GITHUB_REPO.replace('participons', 'audierne2026.github.io')}/commit/{commit_hash})",
        "",
    ]

    if not contributions:
        lines.extend([
            "*Aucune contribution citoyenne pour cette catégorie.*",
            "",
            CONTRIBUTIONS_SECTION_END,
        ])
        return "\n".join(lines)

    # Group by type
    issues = [c for c in contributions if c["type"] == "issue"]
    discussions = [c for c in contributions if c["type"] == "discussion"]

    # Summary with link to contributions folder
    total = len(issues) + len(discussions)
    lines.extend([
        f"📁 **[{total} contribution(s)](contributions/INDEX.md)** dans cette catégorie",
        "",
    ])

    # Issues section - compact list with links to individual files
    if issues:
        lines.extend([
            f"#### Issues ({len(issues)})",
            "",
        ])
        for item in sorted(issues, key=lambda x: x["number"], reverse=True)[:10]:  # Limit to 10 in summary
            state_emoji = "🟢" if item["state"] == "open" else "✅"
            lines.append(f"- {state_emoji} [#{item['number']}](contributions/issue-{item['number']}.md): {item['title'][:60]}{'...' if len(item['title']) > 60 else ''}")

        if len(issues) > 10:
            lines.append(f"- *...et {len(issues) - 10} autre(s) → [Voir tout](contributions/INDEX.md)*")
        lines.append("")

    # Discussions section - compact list with links to individual files
    if discussions:
        lines.extend([
            f"#### Discussions ({len(discussions)})",
            "",
        ])
        for item in sorted(discussions, key=lambda x: x["number"], reverse=True)[:10]:
            state_emoji = "✅" if item.get("closed") else "💬"
            lines.append(f"- {state_emoji} [Discussion #{item['number']}](contributions/discussion-{item['number']}.md): {item['title'][:50]}{'...' if len(item['title']) > 50 else ''}")

        if len(discussions) > 10:
            lines.append(f"- *...et {len(discussions) - 10} autre(s) → [Voir tout](contributions/INDEX.md)*")
        lines.append("")

    # Collected links section (keep for quick reference)
    all_links = []
    for item in contributions:
        all_links.extend(item.get("links", []))

    # Deduplicate links by URL
    seen_urls = set()
    unique_links = []
    for link in all_links:
        if link["url"] not in seen_urls:
            seen_urls.add(link["url"])
            unique_links.append(link)

    if unique_links:
        lines.extend([
            f"#### Liens extraits des contributions ({len(unique_links)})",
            "",
        ])
        for i, link in enumerate(unique_links[:10], 1):  # Limit to 10 links in summary
            title = link["title"] or link["url"][:50]
            lines.append(f"{i}. [{title}]({link['url']})")

        if len(unique_links) > 10:
            lines.append(f"\n*...et {len(unique_links) - 10} autre(s) liens dans les fichiers individuels*")
        lines.append("")

    lines.append(CONTRIBUTIONS_SECTION_END)

    return "\n".join(lines)


def update_readme(readme_path, contributions_section, dry_run=False):
    """Update README.md with the new contributions section."""
    if not os.path.exists(readme_path):
        print(f"⚠️  Fichier non trouvé: {readme_path}")
        return False

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if section already exists
    if CONTRIBUTIONS_SECTION_START in content:
        # Replace existing section
        pattern = re.compile(
            re.escape(CONTRIBUTIONS_SECTION_START) + r".*?" + re.escape(CONTRIBUTIONS_SECTION_END),
            re.DOTALL
        )
        new_content = pattern.sub(contributions_section.strip(), content)
    else:
        # Add section before "### Invitation à contribution" or at the end
        insertion_markers = [
            "### Invitation à contribution",
            "### Liens sources externes",
            "### Etude topographique"
        ]

        inserted = False
        for marker in insertion_markers:
            if marker in content:
                new_content = content.replace(marker, contributions_section + "\n\n" + marker)
                inserted = True
                break

        if not inserted:
            # Append at the end
            new_content = content.rstrip() + "\n" + contributions_section

    if dry_run:
        print(f"   [DRY RUN] Modifications pour {readme_path}")
        return True

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True


def update_version_header(readme_path, commit_hash, dry_run=False):
    """Update the version line in README header."""
    if not os.path.exists(readme_path):
        return False

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Update version line pattern: "Version X.X – DD MMMM YYYY"
    today = datetime.now(timezone.utc)
    months_fr = {
        1: "janvier", 2: "février", 3: "mars", 4: "avril",
        5: "mai", 6: "juin", 7: "juillet", 8: "août",
        9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"
    }
    date_str = f"{today.day:02d} {months_fr[today.month]} {today.year}"

    # Find and update version line
    version_pattern = r'(Version\s+)(\d+\.\d+)(\s+[–-]\s+)\d{1,2}\s+\w+\s+\d{4}'

    def increment_version(match):
        prefix = match.group(1)
        version = match.group(2)
        separator = match.group(3)
        major, minor = version.split(".")
        new_version = f"{major}.{int(minor) + 1}"
        return f"{prefix}{new_version}{separator}{date_str}"

    new_content = re.sub(version_pattern, increment_version, content)

    if new_content == content:
        return False

    if dry_run:
        return True

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Synchronise les contributions GitHub vers les fichiers RAG"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Afficher les modifications sans les appliquer"
    )
    parser.add_argument(
        "--category", "-c",
        help="Synchroniser une catégorie spécifique uniquement"
    )
    parser.add_argument(
        "--skip-discussions",
        action="store_true",
        help="Ignorer les discussions (nécessite GitHub token)"
    )
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Répertoire de documentation (défaut: docs)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("📚 Synchronisation Contributions → RAG")
    print("=" * 60)
    print()

    # Get git info
    commit_hash, commit_date = get_git_commit_info()
    if commit_hash:
        print(f"📌 Commit actuel: {commit_hash[:7]} ({commit_date})")
    else:
        print("⚠️  Impossible de récupérer les infos git")
        commit_hash = "unknown"
        commit_date = ""

    # Fetch data
    issues = fetch_issues()

    if args.skip_discussions or not GITHUB_TOKEN:
        discussions = []
    else:
        discussions = fetch_discussions()

    # Group by category
    contributions_by_category = defaultdict(list)

    for issue in issues:
        categories = categorize_item(issue, "issue")
        contrib_data = extract_contribution_data(issue, "issue")
        for cat in categories:
            contributions_by_category[cat].append(contrib_data)

    for discussion in discussions:
        categories = categorize_item(discussion, "discussion")
        contrib_data = extract_contribution_data(discussion, "discussion")
        for cat in categories:
            contributions_by_category[cat].append(contrib_data)

    print()
    print("📊 Répartition par catégorie:")
    for cat in sorted(CATEGORIES.keys()):
        count = len(contributions_by_category[cat])
        print(f"   - {cat}: {count} contribution(s)")

    print()

    # Update READMEs
    docs_dir = Path(args.docs_dir)
    updated_count = 0

    for cat_key, cat_info in CATEGORIES.items():
        if args.category and cat_key != args.category:
            continue

        readme_path = docs_dir / cat_info["folder"] / "README.md"

        if not readme_path.exists():
            print(f"⚠️  {readme_path} n'existe pas, ignoré")
            continue

        contributions = contributions_by_category[cat_key]

        # Generate section
        section = generate_contributions_section(
            contributions,
            cat_key,
            commit_hash,
            commit_date
        )

        # Update README
        print(f"📝 Mise à jour de {readme_path}...")

        if update_readme(str(readme_path), section, dry_run=args.dry_run):
            update_version_header(str(readme_path), commit_hash, dry_run=args.dry_run)
            updated_count += 1
            if args.dry_run:
                print(f"   [DRY RUN] {len(contributions)} contribution(s)")
            else:
                print(f"   ✅ {len(contributions)} contribution(s) synchronisées")
        else:
            print(f"   ❌ Échec de la mise à jour")

    print()
    print("=" * 60)
    if args.dry_run:
        print(f"✅ [DRY RUN] {updated_count} fichier(s) seraient mis à jour")
    else:
        print(f"✅ {updated_count} fichier(s) mis à jour")
    print("=" * 60)

    # Save sync metadata
    if not args.dry_run:
        metadata = {
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "commit_hash": commit_hash,
            "issues_count": len(issues),
            "discussions_count": len(discussions),
            "categories_updated": list(contributions_by_category.keys())
        }

        metadata_path = docs_dir / ".rag_sync_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"📄 Métadonnées sauvegardées: {metadata_path}")


if __name__ == "__main__":
    main()
