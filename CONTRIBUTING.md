# audierne2026 : une archive ouverte

La campagne municipale de mars 2026 est terminée. Il n'y a plus de programme à co-construire : [audierne2026.fr](https://audierne2026.fr) est désormais **l'archive transparente de ce qui s'est passé pendant l'élection** — les réunions publiques, les programmes des quatre listes, les contributions citoyennes, et la façon dont tout cela a été rassemblé.

Tout y est **à la disposition de la mairie en place**, pour s'en servir ou pour demander que tout ou partie soit retiré. Une seule porte pour cela, ouverte à toutes et à tous : **les [issues](https://github.com/audierne2026/participons/issues) de ce dépôt GitHub**.

Une demande qui vous concerne personnellement (votre nom, une image de vous, une contribution que vous avez déposée) peut aussi se faire **par email, sans rien publier** : audierne2026@gmail.com (voir la [politique de confidentialité](https://audierne2026.fr/privacy/)).

## Ce que vous pouvez demander

| Vous voulez… | Ouvrez une issue et dites-nous |
|---|---|
| **corriger** une erreur, une citation, une date | ce qui est faux, et la source qui le montre |
| **compléter** une source manquante | le lien vers le document public |
| **retirer** une image, un passage ou une page qui vous concerne | ce qui doit être retiré, et en quoi vous êtes concerné·e |
| **fermer** le site, ou une partie (pour la mairie) | ce qui doit être fermé ; une demande de la mairie est appliquée |
| **utiliser** un contenu (pour la mairie, les associations, chacun) | ce que vous voulez reprendre : nous vous indiquons l'origine de chaque texte et de chaque image (voir *Licence*) |

Une **demande de retrait passe avant tout le reste**. Les caricatures générées par IA de personnalités publiques sont corrigées ou retirées sur demande de la personne représentée, comme l'annonce la page [À propos](https://audierne2026.fr/a-propos/).

## Ce que l'archive garantit

Ces règles ont tenu pendant la campagne ; elles tiennent pour chaque correction de l'archive, la nôtre comprise. Notre premier souci, depuis le début, est la façon dont l'IA et l'équipe traitent la matière démocratique d'une commune.

1. **Les quatre listes à égalité.** Une correction ne favorise ni ne dessert une liste ; l'ordre de présentation n'est pas un choix éditorial.
2. **Une source, ou rien.** Chaque affirmation de l'archive renvoie à un document public ou à une contribution citoyenne.
3. **Les images disent d'où elles viennent.** Une photo est créditée ; une source tierce est nommée ; une image générée par IA qui représente une personne réelle porte, sur l'image, le bandeau « Caricature générée par IA » et l'icône européenne, et la même mention dans le fichier. Nous gardons trace de la source de chaque image générée.
4. **Les personnes privées sont protégées.** Aucune donnée personnelle d'un particulier (adresse, téléphone, situation privée). Une personne qui n'est ni élue ni candidate n'est nommée que dans le récit d'un événement public auquel elle a pris part, n'est jamais représentée en image sans son accord, et peut demander à tout moment le retrait de son nom.
5. **Une personne décide.** Chaque demande est lue par un membre de l'équipe ; l'IA aide à préparer, elle ne décide pas. Un refus est toujours expliqué.

## Corriger vous-même (pull request)

Pour une correction précise, vous pouvez aussi proposer la modification directement :

1. *Forkez* le dépôt et créez une branche.
2. Corrigez la page concernée : un compte rendu dans `_posts/`, une page dans `_pages/`, une synthèse dans `docs/<catégorie>/`.
3. Si vous le pouvez, prévisualisez : `bundle install` puis `bundle exec jekyll serve`, et ouvrez http://127.0.0.1:4000/.
4. Ouvrez la pull request vers `main`, en recopiant cette liste dans sa description :

```markdown
- [ ] les quatre listes restent traitées à égalité
- [ ] la correction a sa source (lien)
- [ ] toute image ajoutée ou changée dit d'où elle vient (photo créditée, source tierce nommée, ou IA déclarée avec son outil et son image de départ)
- [ ] aucune donnée personnelle d'un particulier ; aucune personne privée sans son accord
- [ ] l'usage d'une IA pour le texte est indiqué, s'il y en a eu
```

Une pull request fusionnée dans `main` republie le site automatiquement.

## Licence

Le code et les textes écrits par l'équipe sont sous [licence MIT](LICENSE.md). Les documents de tiers gardent leurs auteurs : programmes des listes, documents et délibérations municipaux, articles de presse cités. Les images ont chacune leur origine : photo de l'équipe, source tierce, image générée. Demandez-nous l'origine d'un contenu avant de le reprendre.
