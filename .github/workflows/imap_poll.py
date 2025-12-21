import os
import re
import json
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from collections import Counter
from imap_tools import MailBox, AND
import requests  # Pour GitHub API

# ====================== CONFIGURATION ======================
IMAP_SERVER = os.getenv("IMAP_SERVER")  # ex: imap.gmail.com
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")  # App password recommandé

GITHUB_REPO = os.getenv("GITHUB_REPO")  # ex: "audierne2026/participons"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

STATE_FILE = "processed_emails.json"  # Stocké dans le repo (commité automatiquement si checkout avec write)

# Mapping catégories (normalisé)
CATEGORY_MAPPING = {
    "economie": "economie",
    "économies": "economie",
    "culture": "culture",
    "ecologie": "ecologie",
    "environnement": "ecologie",
    "jeunesse": "jeunesse",
    "ecole": "jeunesse",
    "associations": "associations",
    "logement": "logement",
}

TITLE_TO_CATEGORY = {
    "économies": "economie",
    "culture": "culture",
    "environnement": "ecologie",
    "école-jeunesse": "jeunesse",
    "associations": "associations",
    "logement": "logement",
}

FRENCH_MONTHS = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}
# =========================================================


def load_processed_uids():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_processed_uids(uids):
    with open(STATE_FILE, "w") as f:
        json.dump(list(uids), f)
    # Commit et push si dans GitHub Actions (optionnel, mais utile pour persistance)
    os.system('git config user.name "GitHub Action"')
    os.system('git config user.email "action@github.com"')
    os.system("git add " + STATE_FILE)
    os.system('git commit -m "Update processed emails state" || echo "No changes"')
    os.system('git push || echo "Push failed or no changes"')


def extract_category(body: str) -> str:
    body_lower = body.lower()
    # Priorité au titre du formulaire
    for keyword, cat in TITLE_TO_CATEGORY.items():
        if keyword in body_lower:
            return cat
    # Sinon champ category/categorie
    match = re.search(r"category:\s*(\w+)|categorie:\s*(\w+)", body, re.IGNORECASE)
    if match:
        value = (match.group(1) or match.group(2)).lower()
        return CATEGORY_MAPPING.get(value, value)
    return "autre"


def extract_submission_date(body: str) -> datetime | None:
    # Format 1 : "Vendredi, décembre 19, 2025 - 19:14"
    match1 = re.search(
        r"Submitted on\s+[A-Za-zçéû]+,\s*([A-Za-zçéû]+)\s*(\d{1,2}),\s*(\d{4})\s*-\s*(\d{2}:\d{2})",
        body,
    )
    if match1:
        month_name, day, year, time = match1.groups()
        month = FRENCH_MONTHS.get(month_name.lower())
        if month:
            return datetime(
                int(year),
                month,
                int(day),
                int(time[:2]),
                int(time[3:]),
                tzinfo=timezone.utc,
            )

    # Format 2 : "20 décembre 2025 à 15:30"
    match2 = re.search(
        r"Soumise le\s*:\s*(\d{1,2})\s*([A-Za-zçéû]+)\s*(\d{4})\s*à\s*(\d{2}:\d{2})",
        body,
    )
    if match2:
        day, month_name, year, time = match2.groups()
        month = FRENCH_MONTHS.get(month_name.lower())
        if month:
            return datetime(
                int(year),
                month,
                int(day),
                int(time[:2]),
                int(time[3:]),
                tzinfo=timezone.utc,
            )

    return None


# ====================== MAIN ======================
processed_uids = load_processed_uids()
new_processed = set()
counts = Counter()

with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASS, "INBOX") as mailbox:
    # Récupérer tous les emails non lus avec sujet Framaforms ou Submitted
    messages = mailbox.fetch(
        AND(seen=False, subject=["Framaforms", "Submitted on"]), mark_seen=False
    )

    for msg in messages:
        if msg.uid in processed_uids:
            continue

        body = msg.text or msg.html or ""
        category = extract_category(body)
        submission_date = extract_submission_date(body)

        # Si pas de date précise, utiliser date de réception
        if submission_date is None:
            submission_date = msg.date.replace(tzinfo=timezone.utc)

        # Rapport pour la veille (hier, du 00:00 au 23:59 UTC)
        yesterday_start = (
            datetime.now(timezone.utc).date() - timedelta(days=1)
        ).replace(tzinfo=timezone.utc)
        yesterday_end = yesterday_start + timedelta(days=1)

        if yesterday_start <= submission_date < yesterday_end:
            counts[category] += 1

        new_processed.add(msg.uid)

    # Marquer comme lus les emails traités (même si pas dans la veille)
    if new_processed:
        mailbox.flag(list(new_processed), "\\Seen", True)

processed_uids.update(new_processed)
save_processed_uids(processed_uids)

# Créer l'issue si au moins une contribution hier
if sum(counts.values()) > 0:
    yesterday_str = yesterday_start.strftime("%d %B %Y")
    report_lines = [
        f"# Rapport quotidien contributions Framaforms – {yesterday_str}",
        "",
        "Nombre de contributions reçues hier via les formulaires anonymes :",
        "",
    ]
    for cat, nb in counts.most_common():
        report_lines.append(f"- **{cat.capitalize()}** : {nb}")

    total = sum(counts.values())
    report_lines.append(f"\n**Total** : {total}")
    report_lines.append(
        "\nCes contributions seront prochainement transcrites anonymement sur GitHub pour débat public."
    )

    body_issue = "\n".join(report_lines)

    headers = {
        "Authorization": f'Bearer {os.getenv("GITHUB_TOKEN")}',  # Ou directement github.token si context
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "title": f"Rapport quotidien Framaforms – {yesterday_str} ({total} contributions)",
        "body": body_issue,
        "labels": ["rapport", "framaforms", "automatisé"],
    }

    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 201:
        print("Issue créée avec succès !")
    else:
        print("Erreur création issue :", response.text)
else:
    print("Aucune nouvelle contribution hier – pas d'issue créée.")
