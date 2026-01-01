# Instructions pour les relecteurs (TEMPLATE)

Copiez ce fichier localement en tant que `REVIEWER_INSTRUCTIONS.md` (ce fichier est dans `.gitignore` et ne doit **pas** être commité). Ce fichier est un template public ; vous pouvez y ajouter des notes privées locales.

## Objectif

Donner aux relecteurs un guide pas-à-pas pour :

- tester le site Jekyll localement
- vérifier la build GitHub Actions et la publication sur `gh-pages`
- la checklist de revue (contenu, liens, accessibilité, transparence)

---

## Installer l'environnement (macOS, zsh)

1. Installer Homebrew (si absent) :

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. Installer Ruby & Bundler :

```bash
brew install ruby
gem install bundler
```

3. Installer les dépendances Jekyll (depuis la racine du repo) :

```bash
bundle config set --local path vendor/bundle
bundle install --jobs 4 --retry 3
```

4. Servir le site localement :

```bash
bundle exec jekyll serve --livereload --host 127.0.0.1 --port 4000
# puis ouvrez http://127.0.0.1:4000/participons
```

Remarque : si vous modifiez `_config.yml`, arrêtez et relancez le serveur.

## Tester une branche ou une Pull Request localement

```bash
# récupérer la branche distante
git fetch origin
# basculer sur la branche à tester
git checkout feature/nom-de-branche
# installer les dépendances (si nécessaire)
bundle install
# lancer le server
bundle exec jekyll serve --livereload
```

## Vérifier la build CI / déploiement

1. Aller sur l'onglet **Actions** du dépôt et inspecter la dernière exécution du workflow **Build and deploy Jekyll to gh-pages** pour la branche `site/jekyll`.
2. Vérifier que le job `Deploy to GitHub Pages` a publié sur la branche `gh-pages` et qu'aucune erreur n'est apparue.
3. Ouvrir la page GitHub Pages (Settings → Pages) ou l'URL projet : `https://audierne2026.github.io/participons`.

## Checklist de relecture rapide

- [ ] Page d'accueil : titre, slogan et liens vers le dépôt
- [ ] Liens internes (Programme, Actualités, Contact) fonctionnent
- [ ] `TRANSPARENCY.md` présent et lien vers `wip-history` ok
- [ ] Pas d'informations personnelles ou sensibles exposées
- [ ] assets/images optimisées et accessible (alt tags)
- [ ] Test mobile rapide (responsive)
- [ ] Vérifier si `baseurl` est correct (/_config.yml_)

## Bonnes pratiques pour les PRs

- Ajouter une description claire et contextuelle
- Joindre capture d'écran si le changement est visuel
- Taguer au moins un relecteur (CODEOWNERS peut s'en charger)
- Documenter la raison des changements dans le commit/PR

---

Merci pour votre relecture — votre travail améliore la transparence et la qualité du site.
