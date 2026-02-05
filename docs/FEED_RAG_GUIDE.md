# Guide : Feed Mistral RAG

Ce guide explique comment alimenter le système RAG (Retrieval-Augmented Generation) pour l'assistant O Capistaine.

## Architecture

```
docs/
├── <category>/
│   ├── README.md              # Contenu principal
│   ├── contributions/         # Issues/discussions GitHub
│   │   ├── INDEX.md
│   │   ├── issue-1.md
│   │   └── discussion-2.md
│   └── pdf_extracts/          # PDFs extraits (OCR Mistral)
│       ├── INDEX.md
│       └── document.md
└── FEED_RAG_GUIDE.md

data/mistral/
├── dataset_train.jsonl        # 90% pour fine-tuning
├── dataset_val.jsonl          # 10% pour validation
└── dataset_metadata.json      # Statistiques
```

---

## Étape 1 : Extraction des PDFs (local uniquement)

L'extraction OCR nécessite une réponse API, donc **exécution locale uniquement**.

```bash
# Configurer la clé API
export MISTRAL_OCR_API_KEY='votre-clé'

# Lister les PDFs disponibles
python scripts/extract_pdf_with_mistral.py --list-only

# Extraire tous les PDFs (délai 2s entre requêtes par défaut)
python scripts/extract_pdf_with_mistral.py

# Options utiles
python scripts/extract_pdf_with_mistral.py -c economie      # Une catégorie
python scripts/extract_pdf_with_mistral.py -n 5             # Limiter à 5
python scripts/extract_pdf_with_mistral.py --delay 5        # 5s entre requêtes
python scripts/extract_pdf_with_mistral.py --force          # Retraiter tout
```

**Sortie :** `docs/<category>/pdf_extracts/*.md`

Les PDFs déjà traités sont ignorés (index : `docs/.pdf_extracts_index.json`).

---

## Étape 2 : Générer le dataset (GitHub Actions)

1. Aller sur **Actions** > **Feed Mistral RAG** > **Run workflow**
2. Optionnel : cocher `Upload dataset to Mistral API` pour envoi direct
3. Le workflow exécute :
   - `export_contributions_to_md.py` : Exporte issues/discussions GitHub
   - `prepare_mistral_dataset.py` : Génère le JSONL depuis :
     - README des catégories
     - Contributions individuelles
     - **PDF extraits** (nouveau)

**Artifact téléchargeable :** `mistral-rag-data`

---

## Étape 3 : Tester localement (optionnel)

```bash
# Exporter les contributions (nécessite gh CLI connecté)
python scripts/export_contributions_to_md.py

# Générer le dataset
python scripts/prepare_mistral_dataset.py --output data/mistral/dataset.jsonl

# Vérifier le résultat
head -1 data/mistral/dataset_train.jsonl | python -m json.tool
```

---

## Sources incluses dans le dataset

| Source | Script | Contenu |
|--------|--------|---------|
| README catégories | `prepare_mistral_dataset.py` | Propositions du programme |
| Contributions | `export_contributions_to_md.py` | Issues & discussions GitHub |
| PDF extraits | `extract_pdf_with_mistral.py` | Documents officiels (OCR) |

---

## Format JSONL Mistral

```json
{
  "messages": [
    {"role": "system", "content": "Tu es O Capistaine..."},
    {"role": "user", "content": "Que contient le document X ?"},
    {"role": "assistant", "content": "Le document X contient..."}
  ]
}
```

---

## Flux complet

```
[LOCAL]                              [GITHUB ACTIONS]
   │                                       │
   ▼                                       ▼
extract_pdf_with_mistral.py         export_contributions_to_md.py
   │                                       │
   └──► docs/<cat>/pdf_extracts/    docs/<cat>/contributions/ ◄──┘
                    │                       │
                    └───────────┬───────────┘
                                ▼
                    prepare_mistral_dataset.py
                                │
                                ▼
                    data/mistral/dataset_*.jsonl
                                │
                                ▼
                    [Upload to Mistral API]
```

---

## Commandes rapides

```bash
# Voir les PDFs disponibles
python scripts/extract_pdf_with_mistral.py --list-only

# Extraire nouveaux PDFs
python scripts/extract_pdf_with_mistral.py

# Vérifier le nombre de paires générées
python scripts/prepare_mistral_dataset.py 2>&1 | grep paires
```

---

*Dernière mise à jour : Février 2026*
