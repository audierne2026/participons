# Participons — Audierne-Esquibien 2026

[![Jekyll](https://img.shields.io/badge/Jekyll-3.10-red.svg)](https://jekyllrb.com/)
[![GitHub Pages](https://img.shields.io/badge/Hosted%20on-GitHub%20Pages-blue.svg)](https://pages.github.com/)
[![Licence du code](https://img.shields.io/badge/Code-MIT-green.svg)](LICENSE.md)

**L'archive ouverte de la campagne municipale d'Audierne-Esquibien 2026** : https://audierne2026.fr

## Ce qu'est ce site aujourd'hui

Pendant la campagne, ce site a servi de plateforme participative : les habitants y ont déposé 36 contributions, les réunions publiques des quatre listes y ont été rendues compte, et un outil permettait d'interroger les quatre programmes et d'obtenir des réponses sourcées.

Les élections ont eu lieu les 15 et 22 mars 2026. Depuis, le site est **l'archive ouverte de ce qui s'est passé**, à la disposition de la mairie, pour s'en servir ou pour demander que tout ou partie soit fermé. Rien n'est retiré de notre propre initiative. Le chapitre est raconté dans l'article [« Après le phare, la pleine mer ! »](https://audierne2026.fr/annonce/transparence/2026/10/24/apres-le-phare-la-pleine-mer.html).

## Ce que l'archive garantit

- **Les quatre listes à égalité** : le même traitement pour chacune ; les résultats sont présentés dans l'ordre des voix, rien d'autre n'en ordonne aucune.
- **Une source, ou rien** : chaque information renvoie à un document public ou à une contribution.
- **Une personne décide** : l'IA a préparé et classé, une personne a relu et publié.
- **L'IA le dit** : chaque image générée par IA qui représente une personne porte, sur la page de l'article, le bandeau « Caricature générée par IA » et l'icône européenne, et la même mention dans le fichier lui-même. Nous gardons trace de la source de chaque image.

## Corriger, compléter, demander un retrait

Une seule porte : les [issues de ce dépôt](https://github.com/audierne2026/participons/issues). On peut y demander de corriger une erreur, de compléter une source, de retirer une image ou un passage qui vous concerne (ces demandes passent avant tout le reste), de fermer tout ou partie du site (une demande de la mairie est appliquée), ou de réutiliser un contenu. Le détail est dans [CONTRIBUTING.md](CONTRIBUTING.md).

Une demande qui vous concerne personnellement (votre nom, une image de vous, une contribution que vous avez déposée) peut se faire **par email, sans rien publier** : audierne2026@gmail.com.

## Ce que contient le dépôt

```
.
├── _posts/                  # Les articles : comptes rendus, annonces, archive
├── _pages/                  # Pages fixes : programme, bilan participatif, à propos, mentions légales
├── _includes/               # Gabarits, dont le bandeau des images générées par IA (ia.html)
├── assets/images/           # Images, photographies créditées et caricatures déclarées
├── docs/<catégorie>/        # Les contributions par catégorie, leurs synthèses, les documents sources
├── docs/programmes/         # Les programmes des quatre listes
├── data/mistral/            # Jeux de questions-réponses
└── scripts/                 # Export des contributions, extraction des PDF
```

Les sept catégories : économie, logement, culture, environnement, associations, jeunesse, alimentation-bien-être-soins.

## Lancer le site en local

```bash
git clone https://github.com/audierne2026/participons.git
cd participons
bundle config set --local path vendor/bundle
bundle install
bundle exec jekyll serve --livereload
```

Le site est alors accessible sur http://127.0.0.1:4000/

## Stack technique

- **Générateur** : Jekyll 3.10 (`github-pages`), thème [Minimal Mistakes](https://mmistakes.github.io/minimal-mistakes/) en remote theme
- **Hébergement** : GitHub Pages ; chaque fusion dans `main` publie le site
- **Le moteur** : [Ò Capistaine](https://github.com/locki-io/ocapistaine), qui a rassemblé les documents et répondu aux questions pendant la campagne, poursuit sa route sur [ocapistaine.locki.io](https://ocapistaine.locki.io)

## Licence

Le **code** et les **textes de l'équipe** sont sous [licence MIT](LICENSE.md). Les documents de tiers (programmes des listes, documents municipaux, articles de presse cités, images d'autres auteurs) gardent leurs auteurs et leurs droits : l'origine de chacun est indiquée, et une réutilisation se demande dans les issues.

## Contact

- **Issues** : https://github.com/audierne2026/participons/issues
- **Email** : audierne2026@gmail.com
