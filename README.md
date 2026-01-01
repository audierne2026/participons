# Participons — Audierne-Esquibien 2026

[![Jekyll](https://img.shields.io/badge/Jekyll-4.x-red.svg)](https://jekyllrb.com/)
[![GitHub Pages](https://img.shields.io/badge/Hosted%20on-GitHub%20Pages-blue.svg)](https://pages.github.com/)
[![License](https://img.shields.io/badge/License-Open-green.svg)](LICENSE)

Bienvenue sur la plateforme participative pour la campagne municipale Audierne-Esquibien 2026.

**Site web** : https://audierne2026.github.io/participons

## À propos

Ce projet ouvert vise à co-construire ensemble un programme municipal pour les élections de mars 2026, dans une démarche de transparence radicale et de démocratie participative.

### Principes

- **Transparence totale** : Code source public, modifications traçables
- **Participation citoyenne** : Tous les habitants peuvent contribuer
- **Open source** : Utilisation d'outils libres et gratuits
- **Co-construction** : Le programme évolue avec vos contributions

## Comment contribuer

**Guide complet** : Consultez la page [Contribuer](https://audierne2026.github.io/participons/contribuer/) sur le site
Plusieurs façons de participer :

### 1. Formulaires participatifs (pour tous)

Partagez vos idées via les formulaires thématiques (en cours de mise en place)

### 2. Discussions GitHub

Participez aux [discussions](https://github.com/audierne2026/participons/discussions) sur les différents sujets

### 3. Issues

Les issues sont le premier receptacle des contributions et des améliorations du site .

#### 3a. Les contributions

Quand elles sont dans les issues elles sont à l'étude, c'est à dire que l'on y vérifie :

- la conformité à la charte
- le contexte du domaine (catégorie)
- le recoupement de la problematique ailleurs
- on regle des imprecisions sur la problématique

#### 3b. Les améliorations du site

Signalez des problèmes ou proposez des améliorations via les [issues](https://github.com/audierne2026/participons/issues)

### 4. Pull Requests (changement d'origine tierce)

Proposer directement des améliorations au site cad. nouveau theme, nouvelle fonctionnalité (pour contributeurs techniques)
Proposez directement des modifications au programme (pour contributeurs techniques)

---

## Structure du projet

```
.
├── _config.yml              # Configuration Jekyll
├── _data/
│   └── navigation.yml       # Menus de navigation
├── _pages/                  # Pages principales
│   ├── programme.md         # Programme participatif
│   ├── contribuer.md        # Guide de contribution
│   ├── discussions.md       # Les discussions actuelles
│   ├── a-propos.md          # À propos de la démarche
│   ├── contact.md           # Contact
│   └── actualites.md        # Page des actualités
├── _actualites/             # Articles d'actualités
├── assets/images/           # assets/images et assets
├── docs/                    # Documentation consolidation et technique
└── scripts/                 # Scripts utilitaires
```

## Installation locale

Pour tester le site en local :

```bash
# Cloner le dépôt
git clone https://github.com/audierne2026/participons.git
cd participons

# Installer les dépendances
bundle config set --local path vendor/bundle
bundle install

# Lancer le serveur local
bundle exec jekyll serve --livereload

# Ou utiliser le script fourni
./scripts/serve.sh
```

En local, le site sera accessible sur http://127.0.0.1:4000/participons

## Stack technique

- **Générateur** : Jekyll 3.x (compatible GitHub Pages)
- **Thème** : [Minimal Mistakes](https://mmistakes.github.io/minimal-mistakes/) (remote theme)
- **Hébergement** : GitHub Pages (gratuit)
- **Formulaires** : Framaforms
- **Coût** : 0€ (hébergement) + ~10€/an (domaine custom optionnel)

## Documentation

- [Plan technique de déploiement](DEPLOYMENT_READY.md)
- [Transparence et processus](./docs/TRANSPARENCY.md)
- [Instructions pour reviewers](./docs/help/REVIEWER_INSTRUCTIONS_TEMPLATE.md)

## Licence

Ce projet est sous licence libre. Le contenu est destiné au bien commun et à la participation citoyenne.

## Contact

- **Email** : audierne2026@gmail.com
- **Issues** : [Signaler un problème](https://github.com/audierne2026/participons/issues)
- **Discussions** : [Participer aux échanges](https://github.com/audierne2026/participons/discussions)

---

**Rejoignez-nous pour construire ensemble l'avenir d'Audierne-Esquibien.**
