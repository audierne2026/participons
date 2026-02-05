# Beta Preview Deployment

Ce guide explique comment publier une version beta du site pour validation avant publication sur main.

## Configuration initiale (une seule fois)

### Environnement GitHub

Aller sur GitHub → **Settings** → **Environments** → **beta** → **Deployment branches and tags**

Ajouter ces patterns pour autoriser les branches de preview :
- `article/*`
- `feature/*`

Cela permet à toutes les branches de preview de se déployer sans blocage.

## Architecture

```
main (production)     →  https://audierne2026.fr/
feature-branch (beta) →  https://audierne2026.fr/beta/
```

Le site utilise GitHub Actions pour le déploiement. Deux workflows existent :
- `jekyll.yml` : déploiement automatique de `main` (production)
- `jekyll-beta.yml` : déploiement manuel d'une branche beta

## Publier une Beta

### 1. Préparer la branche

```bash
# Créer et basculer sur la branche article
git checkout -b article/mon-nouvel-article

# Faire les modifications...
# Ajouter les fichiers
git add .
git commit -m "Ajout article: mon-nouvel-article"

# Pousser la branche sur GitHub
git push -u origin article/mon-nouvel-article
```

### 2. Déclencher le déploiement beta

1. Aller sur GitHub → **Actions** → **Deploy Beta to GitHub Pages**
2. Cliquer sur **Run workflow**
3. Sélectionner votre branche (ex: `article/mon-nouvel-article`)
4. Choisir le mode de déploiement :
   - **subdirectory** (recommandé) : la beta est accessible à `/beta/`, production reste intacte
   - **replace** : remplace temporairement la production (pour review finale)
5. Cliquer sur **Run workflow**

### 3. Partager le lien beta

Mode subdirectory :
```
https://audierne2026.fr/beta/
```

Mode replace :
```
https://audierne2026.fr/
```

### 4. Après validation

Si la beta est approuvée :
```bash
# Fusionner dans main
git checkout main
git merge article/mon-nouvel-article
git push origin main
# → Le workflow jekyll.yml se déclenche automatiquement
```

Si mode "replace" était utilisé, la production est automatiquement mise à jour avec le contenu final.

## Modes de déploiement

| Mode | URL Beta | Production | Usage |
|------|----------|------------|-------|
| `subdirectory` | `/beta/` | Intacte | Review sans risque |
| `replace` | `/` | Remplacée | Review finale avant merge |

### Mode subdirectory (recommandé)

- La production reste accessible à la racine
- La beta est accessible sous `/beta/`
- Idéal pour montrer un article à quelqu'un sans impacter les visiteurs
- Après merge dans main, la production est mise à jour et `/beta/` disparait au prochain build

### Mode replace

- Remplace entièrement la production
- Utile pour une dernière vérification avant merge
- Pour restaurer : relancer le workflow `jekyll.yml` depuis main

## Exemple concret : article Van Praët

```bash
# Situation actuelle
git checkout article/meeting-van-praet

# Pousser si pas déjà fait
git push -u origin article/meeting-van-praet

# Sur GitHub :
# Actions → Deploy Beta to GitHub Pages → Run workflow
# Branch: article/meeting-van-praet
# Mode: subdirectory

# Partager le lien :
# https://audierne2026.fr/beta/campaign/2026/01/11/meeting-liste-mvp.html

# Après validation :
git checkout main
git merge article/meeting-van-praet
git push origin main
```

## Bonnes pratiques

### Chemins des images

**Toujours utiliser des chemins absolus** dans les posts et pages :

```markdown
<!-- ✓ Correct -->
![description](/assets/images/mon-image.jpg)

<!-- ✗ Incorrect - ne fonctionne pas -->
![description](../assets/images/mon-image.jpg)
```

En mode subdirectory, les images à `/assets/...` restent accessibles car la production est aussi déployée.

## Troubleshooting

### La beta ne se déploie pas
- Vérifier que la branche est bien poussée sur GitHub
- Vérifier les logs dans Actions → Deploy Beta to GitHub Pages
- Vérifier que l'environnement `beta` autorise votre branche (Settings → Environments → beta)

### Les images ne s'affichent pas
- Utiliser des chemins absolus : `/assets/images/...`
- Ne PAS utiliser de chemins relatifs : `../assets/images/...`
- Les chemins absolus fonctionnent car la production (avec ses assets) est aussi déployée

### Les liens sont cassés en beta
- En mode subdirectory, les liens absolus pointent vers la production
- Utiliser `{{ site.baseurl }}` dans les templates pour des liens relatifs

### Revenir à la production après un "replace"
```bash
# Option 1: Relancer le workflow production
# Actions → Deploy Jekyll site to Pages → Run workflow (depuis main)

# Option 2: Faire un commit vide pour déclencher le build
git checkout main
git commit --allow-empty -m "Trigger rebuild"
git push origin main
```

## Notes techniques

- Le workflow beta utilise l'environnement `beta` (sans protection stricte)
- Le workflow production utilise l'environnement `github-pages` (protégé, main uniquement)
- Le workflow beta clone `main` pour la production et la branche courante pour la beta
- Les deux builds sont fusionnés : production à `/` et beta à `/beta/`
- Le baseurl est automatiquement configuré (`/beta` en mode subdirectory)
