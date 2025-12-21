import os
import re
from datetime import datetime, timedelta, timezone
from collections import Counter
from imap_tools import MailBox, AND
import requests

# ====================== CONFIGURATION ======================
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")  # Par défaut Gmail
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

GITHUB_REPO = os.getenv(
    "GITHUB_REPO", os.getenv("GITHUB_REPOSITORY")
)  # Automatique dans Actions
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Token automatique fourni par GitHub Actions

# Mapping des catégories
CATEGORY_MAPPING = {
    "economie": "economie",
    "économies": "economie",
    "culture": "culture",
    "ecologie": "ecologie",
    "environnement": "ecologie",
    "jeunesse": "jeunesse",
    "ecole": "jeunesse",
    "école-jeunesse": "jeunesse",
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


def extract_category(body: str) -> str:
    body_lower = body.lower()
    # Priorité au titre du formulaire dans le sujet ou corps
    for keyword, cat in TITLE_TO_CATEGORY.items():
        if keyword in body_lower:
            return cat
    # Sinon recherche du champ category/categorie
    match = re.search(r"category:\s*(\w+)|categorie:\s*(\w+)", body, re.IGNORECASE)
    if match:
        value = (match.group(1) or match.group(2)).lower()
        return CATEGORY_MAPPING.get(value, value)
    return "autre"


def extract_submission_date(body: str) -> datetime | None:
    # Format Framaforms français : "Vendredi, décembre 19, 2025 - 19:14"
    match1 = re.search(
        r"Submitted on\s+[A-Za-zçéû]+,\s*([A-Za-zçéû]+)\s*(\d{1,2}),\s*(\d{4})\s*-\s*(\d{2}:\d{2})",
        body,
    )
    if match1:
        month_name, day, year, time_str = match1.groups()
        month = FRENCH_MONTHS.get(month_name.lower())
        if month:
            hour, minute = map(int, time_str.split(":"))
            return datetime(
                int(year), month, int(day), hour, minute, tzinfo=timezone.utc
            )

    # Format alternatif possible (ex. notification Framaforms)
    match2 = re.search(
        r"(\d{1,2})\s+([A-Za-zçéû]+)\s+(\d{4})\s+à\s+(\d{2}:\d{2})", body
    )
    if match2:
        day, month_name, year, time_str = match2.groups()
        month = FRENCH_MONTHS.get(month_name.lower())
        if month:
            hour, minute = map(int, time_str.split(":"))
            return datetime(
                int(year), month, int(day), hour, minute, tzinfo=timezone.utc
            )

    return None


# ====================== MAIN ======================
if not EMAIL_USER or not EMAIL_PASS:
    print("ERREUR : EMAIL_USER ou EMAIL_PASS manquants dans les secrets.")
    exit(1)

counts = Counter()
processed_uids = set()

print("Connexion à la boîte mail...")
with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASS, "INBOX") as mailbox:
    # Récupère tous les emails non lus contenant Framaforms ou "Submitted on"
    messages = mailbox.fetch(
        AND(seen=False, subject=["Framaforms", "Submitted on", "Soumission"]),
        mark_seen=False,
    )

    for msg in messages:
        body = msg.text or msg.html or ""
        category = extract_category(body or msg.subject or "")
        submission_date = extract_submission_date(body)

        # Si pas de date dans le corps, utiliser la date de réception de l'email
        if submission_date is None:
            submission_date = (
                msg.date.replace(tzinfo=timezone.utc)
                if msg.date
                else datetime.now(timezone.utc)
            )

        # Définit la période "hier" (du 00:00 au 23:59 UTC)
        yesterday_start = datetime.now(timezone.utc).date() - timedelta(days=1)
        yesterday_start = datetime.combine(
            yesterday_start, datetime.min.time(), tzinfo=timezone.utc
        )
        yesterday_end = yesterday_start + timedelta(days=1)

        if yesterday_start <= submission_date < yesterday_end:
            counts[category] += 1

        processed_uids.add(msg.uid)

    # Marque tous les emails analysés comme lus
    if processed_uids:
        mailbox.flag(list(processed_uids), "\\Seen", True)
        print(f"{len(processed_uids)} email(s) marqué(s) comme lu(s).")

# Création de l'issue si au moins une contribution hier
if sum(counts.values()) > 0:
    yesterday_str = yesterday_start.strftime("%d %B %Y")
    report_lines = [
        f"# Rapport quotidien contributions Framaforms – {yesterday_str}",
        "",
        "Nombre de contributions reçues **hier** via les formulaires anonymes :",
        "",
    ]
    for cat, nb in counts.most_common():
        cat_name = cat.capitalize()
        report_lines.append(f"- **{cat_name}** : {nb}")

    total = sum(counts.values())
    report_lines.append(f"\n**Total** : {total}")
    report_lines.append(
        "\nCes contributions seront prochainement transcrites anonymement sur GitHub pour débat public."
    )
    report_lines.append("\nLabel : `rapport` `framaforms` `automatisé`")

    body_issue = "\n".join(report_lines)

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
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
        print("Issue de rapport créée avec succès !")
    else:
        print(f"Erreur lors de la création de l'issue : {response.status_code}")
        print(response.text)
else:
    print("Aucune nouvelle contribution hier – pas d'issue créée.")
