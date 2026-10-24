# Contribuer à audierne2026

Merci de vouloir améliorer [audierne2026.fr](https://audierne2026.fr). Tout se passe ici, sur ce dépôt GitHub : c'est la seule porte, ouverte à toutes et à tous.

| Vous voulez… | Ouvrez |
|---|---|
| signaler une erreur, une source manquante, une formulation injuste | une **[issue](https://github.com/audierne2026/participons/issues)** |
| discuter d'une idée avant d'en faire un changement | une **[discussion](https://github.com/audierne2026/participons/discussions)** |
| modifier une page vous-même | une **[pull request](https://github.com/audierne2026/participons/pulls)** (voir plus bas) |

Pas besoin de savoir coder : une issue bien sourcée vaut autant qu'une pull request.

## Ce que nous vous demandons

Depuis le début, notre premier souci est la façon dont l'IA et l'équipe traitent la matière démocratique d'une commune. Ces règles valent pour chaque proposition, la nôtre comprise.

### 1. Les quatre listes à égalité

- Aucune formulation ne favorise ni ne dessert une liste.
- Quand vous comparez les listes sur un point, citez-les toutes sur ce point, ou dites pourquoi l'une manque (par exemple : « pas de position publique trouvée »).
- L'ordre de présentation n'est pas un choix éditorial : gardez celui du site.

### 2. Une source, ou rien

- Chaque affirmation renvoie à un **document public** (délibération, programme, compte rendu, article) ou à une **contribution citoyenne** de ce dépôt, avec un lien.
- Pas de capture de message privé, pas de propos rapporté sans source.

### 3. Les images disent d'où elles viennent

| Votre image est… | Dites-nous |
|---|---|
| une **photo que vous avez prise** | que vous en êtes l'auteur, et le nom à créditer (« Photo : … ») |
| une **photo de quelqu'un d'autre** | sa source (lien) et son auteur s'il est connu : nous vérifions qu'elle peut être publiée |
| une **image générée par IA** | l'outil, et l'image ou la photo dont elle part, s'il y en a une |

Une image générée par IA qui représente une personne réelle est toujours signalée : sur la page, elle passe par `{% include ia.html src="…" alt="…" %}`, qui pose le bandeau « Caricature générée par IA » et l'icône européenne. N'incrustez pas de filigrane dans l'image : nous ne modifions jamais les pixels. Nous ajoutons nous-mêmes la mention « généré par IA » dans le fichier.

Une image générée qui pourrait passer pour une vraie photo d'une personne ou d'un lieu n'est jamais publiée sans cette déclaration.

### 4. Les personnes privées sont protégées

- Aucune donnée personnelle d'un particulier (adresse, téléphone, courriel, situation privée).
- Une personne qui n'est ni élue ni candidate n'apparaît pas, en image ou par son nom, sans son accord.

### 5. L'IA dans votre texte

Vous avez utilisé une IA pour rédiger ou traduire ? Dites-le dans la description. Ce n'est pas un défaut, c'est une information pour la relecture.

### 6. La charte de contribution

Les contributions citoyennes suivent la [charte de contribution](https://audierne2026.fr/contribuer/#charte-de-contribution).

## Ce que fait l'équipe ensuite

- **Une personne lit chaque proposition** avant qu'elle n'atteigne le site. L'IA aide à trier et à préparer, elle ne décide pas.
- Nous vérifions l'égalité des listes, les sources et l'origine des images ; nous ajoutons la mention dans le fichier des images générées et nous gardons trace de leur source.
- Nous répondons sous votre issue ou votre pull request. Un refus est toujours expliqué.
- Une pull request fusionnée dans `main` republie [audierne2026.fr](https://audierne2026.fr) automatiquement.

## Proposer une pull request

1. *Forkez* le dépôt et créez une branche.
2. Modifiez :
   - un article : `_posts/AAAA-MM-JJ-titre.md` (le format est celui des articles existants) ;
   - une page : `_pages/` ;
   - une synthèse thématique : `docs/<catégorie>/README.md`.
3. Si vous le pouvez, prévisualisez : `bundle install` puis `bundle exec jekyll serve`, et ouvrez http://127.0.0.1:4000/.
4. Ouvrez la pull request vers `main` et recopiez cette liste dans sa description :

```markdown
- [ ] les quatre listes sont traitées à égalité
- [ ] chaque affirmation a sa source (lien)
- [ ] chaque image : photo créditée, ou source et auteur donnés, ou IA déclarée (outil + image de départ)
- [ ] aucune donnée personnelle d'un particulier ; aucune personne privée sans son accord
- [ ] l'usage d'une IA pour le texte est indiqué, s'il y en a eu
- [ ] aperçu local vérifié (si possible)
```

## Licence

Ce dépôt est publié sous [licence MIT](LICENSE.md) : votre contribution l'est aussi.
