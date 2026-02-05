#!/usr/bin/env python3
"""
Prepare JSONL dataset for Mistral fine-tuning from Audierne2026 documentation.

This script:
1. Reads all markdown files from docs/ directory
2. Extracts content and generates Q&A training pairs
3. Outputs JSONL format compatible with Mistral fine-tuning API

JSONL Format (per Mistral docs):
{
  "messages": [
    {"role": "system", "content": "System prompt"},
    {"role": "user", "content": "User question"},
    {"role": "assistant", "content": "Assistant response"}
  ]
}

Usage:
    python prepare_mistral_dataset.py [--output dataset.jsonl] [--split 0.9]

Environment:
    MISTRAL_API_KEY: For future API upload integration
"""

import os
import json
import argparse
import re
import random
from pathlib import Path
from datetime import datetime, timezone

# ====================== CONFIGURATION ======================
DOCS_DIR = Path("docs")

# System prompt for O Capistaine (the campaign AI assistant)
SYSTEM_PROMPT = """Tu es O Capistaine, l'assistant IA de la campagne municipale Audierne2026.

## Ton rôle
Tu aides les citoyens à comprendre le programme participatif d'Audierne-Esquibien 2026. Tu réponds aux questions sur les propositions, le contexte local, et les contributions citoyennes.

## Ton style
- Factuel et neutre : tu informes sans prendre parti politiquement
- Bienveillant : tu encourages la participation citoyenne
- Précis : tu cites les sources quand disponibles (numéros d'issues, liens)
- Concis : tu vas à l'essentiel tout en étant complet

## Les catégories du programme
1. Logement & Urbanisme
2. Associations & Vie locale
3. École & Jeunesse
4. Environnement
5. Économie locale
6. Culture & Patrimoine
7. Alimentation, bien-être et soins

## Règles
- Ne jamais inventer d'information
- Orienter vers le formulaire de contribution si pertinent
- Rester dans le cadre du programme Audierne2026"""

# Category titles for context
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


def extract_sections(content):
    """Extract sections from markdown content."""
    sections = {}
    current_section = "intro"
    current_content = []

    for line in content.split("\n"):
        # Match headers (## or ###)
        header_match = re.match(r'^(#{2,3})\s+(.+)$', line)
        if header_match:
            # Save previous section
            if current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = header_match.group(2).strip()
            current_content = []
        else:
            current_content.append(line)

    # Save last section
    if current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def extract_links(content):
    """Extract external links from content."""
    links = []
    # Match markdown links
    for match in re.finditer(r'\[([^\]]+)\]\((https?://[^)]+)\)', content):
        title, url = match.groups()
        if "github.com/audierne2026" not in url:
            links.append({"title": title, "url": url})
    return links


def extract_bullet_points(content):
    """Extract bullet points from content."""
    points = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("- ") or line.startswith("* "):
            points.append(line[2:].strip())
    return points


def generate_qa_pairs_from_readme(filepath, category_key):
    """Generate Q&A pairs from a category README file."""
    qa_pairs = []

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    sections = extract_sections(content)
    cat_title = CATEGORIES.get(category_key, category_key.capitalize())

    # Q&A about the category overview
    if "Catégorie" in content or cat_title in content:
        qa_pairs.append({
            "question": f"Quelles sont les propositions d'Audierne2026 pour {cat_title.lower()} ?",
            "answer": f"Voici les propositions d'Audierne2026 pour la catégorie **{cat_title}** :\n\n" +
                     content[:2000] if len(content) > 2000 else content,
            "category": category_key
        })

    # Q&A about constats (observations)
    for section_name, section_content in sections.items():
        if "constat" in section_name.lower():
            points = extract_bullet_points(section_content)
            if points:
                qa_pairs.append({
                    "question": f"Quels sont les constats d'Audierne2026 sur {cat_title.lower()} ?",
                    "answer": f"Les principaux constats pour **{cat_title}** sont :\n\n" +
                             "\n".join(f"- {p}" for p in points),
                    "category": category_key
                })

    # Q&A about propositions
    for section_name, section_content in sections.items():
        if "proposition" in section_name.lower():
            qa_pairs.append({
                "question": f"Quelles sont les propositions concrètes pour {cat_title.lower()} ?",
                "answer": f"Voici les propositions pour **{cat_title}** :\n\n{section_content[:1500]}",
                "category": category_key
            })

    # Q&A about external sources
    links = extract_links(content)
    if links:
        links_text = "\n".join(f"- [{l['title']}]({l['url']})" for l in links[:10])
        qa_pairs.append({
            "question": f"Où trouver plus d'informations sur {cat_title.lower()} à Audierne ?",
            "answer": f"Voici des sources d'information sur **{cat_title}** :\n\n{links_text}",
            "category": category_key
        })

    # Q&A about how to contribute
    qa_pairs.append({
        "question": f"Comment contribuer au programme {cat_title.lower()} ?",
        "answer": f"Pour contribuer au programme **{cat_title}**, vous pouvez utiliser le formulaire dédié : https://audierne2026.fr/formulaires/{category_key}/\n\nVos contributions sont anonymes et seront contextualisées par l'équipe avant d'être débattues publiquement.",
        "category": category_key
    })

    return qa_pairs


def generate_qa_pairs_from_contribution(filepath, category_key):
    """Generate Q&A pairs from an individual contribution file."""
    qa_pairs = []

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract issue/discussion number from filename
    filename = filepath.name
    if filename.startswith("issue-"):
        number = filename.replace("issue-", "").replace(".md", "")
        contrib_type = "issue"
    elif filename.startswith("discussion-"):
        number = filename.replace("discussion-", "").replace(".md", "")
        contrib_type = "discussion"
    else:
        return qa_pairs

    # Extract title
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else f"Contribution #{number}"

    # Extract main content (after "## Contenu")
    content_match = re.search(r'## Contenu[^\n]*\n\n(.+?)(?=\n---|\n## |$)', content, re.DOTALL)
    main_content = content_match.group(1).strip() if content_match else ""

    cat_title = CATEGORIES.get(category_key, category_key.capitalize())

    if main_content:
        # Q&A about this specific contribution
        qa_pairs.append({
            "question": f"Que propose la contribution #{number} sur {cat_title.lower()} ?",
            "answer": f"La contribution **#{number}** ({title}) propose :\n\n{main_content[:1200]}",
            "category": category_key
        })

    # Extract links from contribution
    links = extract_links(content)
    if links:
        links_text = "\n".join(f"- [{l['title']}]({l['url']})" for l in links[:5])
        qa_pairs.append({
            "question": f"Quelles sources sont mentionnées dans la contribution #{number} ?",
            "answer": f"Les sources mentionnées dans la contribution **#{number}** :\n\n{links_text}",
            "category": category_key
        })

    return qa_pairs


def generate_general_qa_pairs():
    """Generate general Q&A pairs about the campaign."""
    return [
        {
            "question": "Qu'est-ce qu'Audierne2026 ?",
            "answer": "**Audierne2026** est une plateforme citoyenne participative pour les élections municipales d'Audierne-Esquibien 2026. Elle permet aux habitants de contribuer anonymement aux propositions du programme via des formulaires dédiés. Les contributions sont ensuite contextualisées et débattues publiquement.",
            "category": "general"
        },
        {
            "question": "Comment fonctionne la participation citoyenne ?",
            "answer": "La participation fonctionne en plusieurs étapes :\n\n1. **Contribution** : Vous soumettez une idée via le formulaire anonyme\n2. **Contextualisation** : L'équipe enrichit votre contribution avec des données locales\n3. **Débat** : La contribution est discutée publiquement sur GitHub\n4. **Intégration** : Les meilleures propositions rejoignent le programme\n\nToutes les contributions sont traçables et transparentes.",
            "category": "general"
        },
        {
            "question": "Quelles sont les catégories du programme Audierne2026 ?",
            "answer": "Le programme Audierne2026 couvre 7 catégories thématiques :\n\n1. **Logement & Urbanisme** : Accès au logement, rénovation, PLU\n2. **Associations & Vie locale** : Soutien associatif, Maison des associations\n3. **École & Jeunesse** : Éducation, activités jeunesse\n4. **Environnement** : Écologie, protection de la nature\n5. **Économie locale** : Commerce, tourisme, pêche\n6. **Culture & Patrimoine** : Musée maritime, chapelles, événements\n7. **Alimentation, bien-être et soins** : Circuits courts, santé",
            "category": "general"
        },
        {
            "question": "Comment soumettre une contribution ?",
            "answer": "Pour soumettre une contribution :\n\n1. Rendez-vous sur https://audierne2026.fr/formulaires/\n2. Choisissez la catégorie correspondant à votre idée\n3. Remplissez le formulaire (constat factuel, proposition, améliorations)\n4. Soumettez - c'est anonyme !\n\nVotre contribution sera traitée dans les jours suivants par l'équipe.",
            "category": "general"
        },
        {
            "question": "Qui es-tu, O Capistaine ?",
            "answer": "Je suis **O Capistaine**, l'assistant IA de la campagne Audierne2026. Mon rôle est de vous aider à :\n\n- Comprendre les propositions du programme\n- Trouver des informations sur le contexte local\n- Vous orienter vers les bons formulaires de contribution\n- Répondre à vos questions sur la démarche participative\n\nJe suis factuel et neutre - je n'ai pas d'opinion politique !",
            "category": "general"
        },
        {
            "question": "Où se trouve Audierne ?",
            "answer": "**Audierne** est une commune du Finistère (29) en Bretagne, située dans le Cap Sizun à la pointe ouest de la France. C'est un port de pêche historique avec environ 3500 habitants. Depuis 2016, Audierne est fusionnée avec Esquibien pour former la commune nouvelle **Audierne**.",
            "category": "general"
        }
    ]


def format_as_mistral_jsonl(qa_pair, system_prompt=SYSTEM_PROMPT):
    """Format a Q&A pair as Mistral JSONL format."""
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": qa_pair["question"]},
            {"role": "assistant", "content": qa_pair["answer"]}
        ]
    }


def main():
    parser = argparse.ArgumentParser(
        description="Prépare un dataset JSONL pour fine-tuning Mistral"
    )
    parser.add_argument(
        "--output", "-o",
        default="data/mistral/dataset.jsonl",
        help="Fichier de sortie (défaut: data/mistral/dataset.jsonl)"
    )
    parser.add_argument(
        "--split",
        type=float,
        default=0.9,
        help="Ratio train/validation (défaut: 0.9 = 90%% train)"
    )
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Répertoire de documentation (défaut: docs)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed pour reproductibilité (défaut: 42)"
    )

    args = parser.parse_args()
    random.seed(args.seed)

    print("=" * 60)
    print("📚 Préparation du dataset Mistral")
    print("=" * 60)
    print()

    docs_dir = Path(args.docs_dir)
    all_qa_pairs = []

    # Generate general Q&A pairs
    print("📝 Génération des Q&A générales...")
    general_pairs = generate_general_qa_pairs()
    all_qa_pairs.extend(general_pairs)
    print(f"   {len(general_pairs)} paires générées")

    # Process category READMEs
    print("\n📁 Traitement des catégories...")
    for cat_key in CATEGORIES.keys():
        readme_path = docs_dir / cat_key / "README.md"
        if readme_path.exists():
            pairs = generate_qa_pairs_from_readme(readme_path, cat_key)
            all_qa_pairs.extend(pairs)
            print(f"   {cat_key}: {len(pairs)} paires")

    # Process individual contributions
    print("\n📄 Traitement des contributions individuelles...")
    contrib_count = 0
    for cat_key in CATEGORIES.keys():
        contrib_dir = docs_dir / cat_key / "contributions"
        if contrib_dir.exists():
            for filepath in contrib_dir.glob("*.md"):
                if filepath.name != "INDEX.md":
                    pairs = generate_qa_pairs_from_contribution(filepath, cat_key)
                    all_qa_pairs.extend(pairs)
                    contrib_count += len(pairs)

    print(f"   {contrib_count} paires depuis contributions")

    # Shuffle and split
    random.shuffle(all_qa_pairs)

    split_idx = int(len(all_qa_pairs) * args.split)
    train_pairs = all_qa_pairs[:split_idx]
    val_pairs = all_qa_pairs[split_idx:]

    print(f"\n📊 Dataset total: {len(all_qa_pairs)} paires")
    print(f"   Train: {len(train_pairs)} ({args.split*100:.0f}%)")
    print(f"   Validation: {len(val_pairs)} ({(1-args.split)*100:.0f}%)")

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write train JSONL
    train_file = args.output.replace(".jsonl", "_train.jsonl")
    with open(train_file, "w", encoding="utf-8") as f:
        for pair in train_pairs:
            jsonl_obj = format_as_mistral_jsonl(pair)
            f.write(json.dumps(jsonl_obj, ensure_ascii=False) + "\n")

    print(f"\n✅ Train dataset: {train_file}")

    # Write validation JSONL
    val_file = args.output.replace(".jsonl", "_val.jsonl")
    with open(val_file, "w", encoding="utf-8") as f:
        for pair in val_pairs:
            jsonl_obj = format_as_mistral_jsonl(pair)
            f.write(json.dumps(jsonl_obj, ensure_ascii=False) + "\n")

    print(f"✅ Validation dataset: {val_file}")

    # Write metadata
    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_pairs": len(all_qa_pairs),
        "train_pairs": len(train_pairs),
        "val_pairs": len(val_pairs),
        "split_ratio": args.split,
        "categories": {cat: 0 for cat in list(CATEGORIES.keys()) + ["general"]},
        "system_prompt_length": len(SYSTEM_PROMPT)
    }

    for pair in all_qa_pairs:
        cat = pair.get("category", "general")
        if cat in metadata["categories"]:
            metadata["categories"][cat] += 1

    metadata_file = args.output.replace(".jsonl", "_metadata.json")
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"✅ Metadata: {metadata_file}")

    print("\n" + "=" * 60)
    print("🎉 Dataset prêt pour Mistral fine-tuning!")
    print("=" * 60)
    print("\nPour uploader vers Mistral:")
    print(f"  mistral files upload {train_file}")
    print(f"  mistral files upload {val_file}")


if __name__ == "__main__":
    main()
