import os
import re
import sys
from datetime import datetime, timedelta, timezone
from collections import Counter
from imap_tools import MailBox, AND
import requests

# Load .env file for local development (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed

# ====================== CONFIGURATION ======================
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

GITHUB_REPO = os.getenv(
    "GITHUB_REPO", os.getenv("GITHUB_REPOSITORY")
)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

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


def parse_date_input(date_str: str) -> datetime:
    """Parse date in DD/MM/YYYY format"""
    try:
        day, month, year = date_str.split("/")
        return datetime(int(year), int(month), int(day), tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        print(f"❌ Format de date invalide. Utilisez DD/MM/YYYY (ex: 06/01/2025)")
        sys.exit(1)


# ====================== MAIN ======================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rerun_poll_email.py <date>")
        print("Format de date: DD/MM/YYYY (ex: 06/01/2025)")
        sys.exit(1)

    target_date_input = sys.argv[1]
    target_date = parse_date_input(target_date_input)

    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Create log file with timestamp
    log_filename = f"poll_email_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_for_{target_date.strftime('%Y%m%d')}.log"
    log_path = os.path.join(logs_dir, log_filename)

    # Redirect output to both console and log file
    class Logger:
        def __init__(self, filename):
            self.terminal = sys.stdout
            self.log = open(filename, "w", encoding="utf-8")

        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)

        def flush(self):
            self.terminal.flush()
            self.log.flush()

    sys.stdout = Logger(log_path)

    print(f"📅 Analyse manuelle pour la date: {target_date.strftime('%d/%m/%Y')}")
    print(f"📝 Log sauvegardé dans: {log_path}")
    print(f"{'='*60}\n")

    if not EMAIL_USER or not EMAIL_PASS:
        print("ERREUR : EMAIL_USER ou EMAIL_PASS manquants dans les secrets.")
        sys.exit(1)

    counts = Counter()
    processed_uids = set()

    print("Connexion à la boîte mail...")
    with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASS, "INBOX") as mailbox:
        # Récupère tous les emails (pas seulement les non lus pour permettre le retraitement)
        print("\n🔍 Recherche des emails Framaforms...")
        messages = list(mailbox.fetch(
            mark_seen=False,
        ))

        print(f"📬 Total d'emails récupérés: {len(messages)}")

        # Define the target period (00:00 to 23:59 UTC)
        target_start = datetime.combine(
            target_date.date(), datetime.min.time(), tzinfo=timezone.utc
        )
        target_end = target_start + timedelta(days=1)

        print(f"Période recherchée: {target_start.strftime('%Y-%m-%d %H:%M')} à {target_end.strftime('%Y-%m-%d %H:%M')}\n")

        framaforms_count = 0
        for msg in messages:
            # Filtre: ne traiter que les emails Framaforms
            subject_lower = (msg.subject or "").lower()
            if not any(keyword in subject_lower for keyword in ["framaforms", "submitted on", "soumission"]):
                continue

            framaforms_count += 1
            print(f"\n[{framaforms_count}] Email Framaforms détecté: {msg.subject[:60]}...")

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
                print(f"    Date extraite du corps: None → Utilisation date réception: {submission_date.strftime('%Y-%m-%d %H:%M')}")
            else:
                print(f"    Date extraite du corps: {submission_date.strftime('%Y-%m-%d %H:%M')}")

            # Only process emails from the target date
            if target_start <= submission_date < target_end:
                print(f"\n{'='*60}")
                print(f"📧 Email trouvé:")
                print(f"  Sujet: {msg.subject}")
                print(f"  Date réception: {msg.date}")
                print(f"  Date soumission: {submission_date}")
                print(f"  Catégorie: {category}")

                counts[category] += 1
                print(f"  ✅ Compté dans la catégorie '{category}'")
                processed_uids.add(msg.uid)
            else:
                print(f"    ❌ Hors période cible")

        print(f"\n{'='*60}")
        print(f"📊 Résumé:")
        print(f"  - Total emails dans INBOX: {len(messages)}")
        print(f"  - Emails Framaforms détectés: {framaforms_count}")
        print(f"  - Emails correspondant à la date {target_date.strftime('%d/%m/%Y')}: {len(processed_uids)}")

    # Création du rapport
    if sum(counts.values()) > 0:
        target_str = target_date.strftime("%d %B %Y")
        report_lines = [
            f"# Rapport contributions Framaforms – {target_str}",
            "",
            "Nombre de contributions reçues via les formulaires anonymes :",
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
        report_lines.append("\nLabel : `rapport` `framaforms` `automatisé` `rerun`")

        body_issue = "\n".join(report_lines)

        print(f"\n{'='*60}")
        print("📊 RAPPORT GÉNÉRÉ:")
        print(body_issue)
        print(f"{'='*60}\n")

        # Création de l'issue GitHub
        if GITHUB_TOKEN and GITHUB_REPO:
            headers = {
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
            }
            data = {
                "title": f"Rapport Framaforms – {target_str} ({total} contributions) [RERUN]",
                "body": body_issue,
                "labels": ["rapport", "framaforms", "automatisé", "rerun"],
            }

            url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
            response = requests.post(url, json=data, headers=headers)

            if response.status_code == 201:
                print("✅ Issue de rapport créée avec succès !")
                print(f"   URL: {response.json().get('html_url', '')}")
            else:
                print(f"❌ Erreur lors de la création de l'issue : {response.status_code}")
                print(response.text)
        else:
            print("⚠️  Mode test local: GITHUB_TOKEN ou GITHUB_REPO non défini, issue non créée.")
    else:
        print(f"Aucune contribution trouvée pour {target_date.strftime('%d/%m/%Y')} – pas d'issue créée.")

    print(f"\n✅ Analyse terminée. Log sauvegardé: {log_path}")
