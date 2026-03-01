---
layout: single
title: "Notre méthode participative"
permalink: /contribuer-aller-plus-loin/

toc: true
toc_label: "Notre méthode"
toc_icon: "hands-helping"
---

<div class="notice--warning" markdown="1">
**Phase de consultation terminée.** Les formulaires et discussions ont été clôturés fin février 2026. Cette page est conservée comme archive de notre méthode participative. Les contributions ont été intégrées dans [notre programme](/programme/).
</div>

## Pull Requests (pour les contributeurs techniques)

Vous maîtrisez Git et Markdown ? Proposez directement des modifications au programme :

```bash
# Cloner le dépôt
git clone https://github.com/audierne2026/participons.git
cd participons

# Créer une branche pour votre contribution
git checkout -b amelioration-programme-logement

# Modifier les fichiers (ex: _pages/programme.md)
# Puis commiter et pousser
git add _pages/programme.md
git commit -m "Ajout: Proposition habitat participatif"
git push origin amelioration-programme-logement

# Créer une Pull Request sur GitHub
```

**Toutes les PR sont bienvenues** :

- Corrections de fautes
- Ajout de propositions argumentées
- Amélioration de la clarté
- Ajout de ressources et références

---

## Processus de validation

### Comment vos contributions sont traitées

**Vous avez rempli un formulaire ? Vous vous demandez ce qu'il advient de votre contribution ?**

Voici le parcours complet, de votre soumission anonyme jusqu'à l'intégration potentielle dans notre programme électoral.

## Le principe : anonymat + transparence

Notre défi : **préserver votre anonymat total** tout en garantissant une **transparence complète** sur le traitement de chaque contribution. Comment y parvenir ? Par un processus en 6 étapes soigneusement conçu.

## Étape 1 : Votre contribution anonyme

**📝 Vous remplissez un formulaire thématique**

Via [Framaforms](https://framaforms.org), service respectueux de vos données :

- Économie locale
- Logement & urbanisme
- Culture & patrimoine
- Associations & vie locale
- École & jeunesse
- Environnement
- Alimentation, bien-être & soins

**✨ Garantie d'anonymat complet :** aucune donnée personnelle n'est collectée, ni nom, ni adresse IP, ni email.

## Étape 2 : Agrégation automatique quotidienne

**🤖 Chaque jour à 9h (heure française)**

Un script automatique ([GitHub Actions](https://github.com/audierne2026/participons/actions)) :

1. Se connecte à notre boîte mail
2. Compte les contributions de la veille par catégorie
3. Crée un [rapport public sur GitHub](https://github.com/audierne2026/participons/issues?q=label%3Arapport)

**Exemple de rapport :**

```
Rapport quotidien – 5 janvier 2026

- Culture : 2 contributions
- Économie : 1 contribution
- Environnement : 2 contributions

Total : 5 contributions
```

**🔒 Votre anonymat préservé :** seules les statistiques sont publiées, jamais le contenu de vos soumissions à ce stade.

## Étape 3 : Vérification de conformité

**👥 L'équipe de campagne (sous 7 jours)**

Nous lisons chaque contribution individuellement et vérifions sa conformité avec notre [charte de contribution](/contribuer/#charte-de-contribution).

**✅ Contributions acceptées :**

- Propositions concrètes et argumentées
- Critiques constructives
- Questions et demandes de clarification
- Partage d'expériences et d'expertise

**❌ Contributions rejetées :**

- Attaques personnelles ou propos discriminatoires
- Spam ou publicité
- Propositions sans rapport avec Audierne-Esquibien
- Informations mensongères

**🏷️ Label appliqué :** `conforme charte` ou clôture avec explication.

## Étape 4 : Contextualisation publique

**📋 Création d'une issue GitHub avec contexte**

Pour chaque contribution conforme, nous créons une [issue publique sur GitHub](https://github.com/audierne2026/participons/issues) contenant :

- Le sujet de la proposition (sans identifier l'auteur)
- Une analyse initiale de l'équipe
- Des liens vers propositions similaires
- Une invitation à commenter et enrichir

**Labels thématiques appliqués :** `economie`, `logement`, `culture`, `ecologie`, `associations`, `jeunesse`, etc.

**⏱️ Durée variable :** L'issue reste ouverte aussi longtemps que nécessaire pour permettre :

- Aux habitants d'apporter leur éclairage
- De croiser les perspectives
- De documenter le sujet en profondeur

**Exemples actuels :**

- [Issue #39 : Contribution culture](https://github.com/audierne2026/participons/issues/39)
- [Issue #37 : Contribution économie](https://github.com/audierne2026/participons/issues/37)
- [Issue #33 : Contribution associations/jeunesse](https://github.com/audierne2026/participons/issues/33)

## Étape 5 : Migration vers les Discussions

**💬 Quand le contexte est suffisant**

L'équipe transfère le sujet vers [GitHub Discussions](https://github.com/audierne2026/participons/discussions) pour :

- Un débat plus approfondi et structuré
- Une participation communautaire élargie
- Une réflexion collective sur la meilleure mise en œuvre

**⏰ Durée :** À déterminer selon la complexité du sujet et le rythme de participation.

## Étape 6 : Intégration au programme

**🎯 Début février 2026 : processus de consolidation**

1. **Synthèse** : L'équipe consolide les résultats des discussions
2. **Rédaction** : Les propositions retenues sont rédigées en texte de programme
3. **Revue publique** : Le brouillon est soumis à relecture communautaire
4. **Publication** : Le programme finalisé est publié avec traçabilité complète

**📊 Transparence totale :** Chaque décision (intégration, adaptation ou report) est documentée publiquement avec justification.

## Pourquoi ce processus ?

### Anonymat vs. responsabilité

- Les formulaires permettent une vraie participation anonyme
- La curation par l'équipe évite les abus tout en préservant l'anonymat
- La discussion publique assure la transparence sans exposer les contributeurs

### Signal vs. bruit

- L'agrégation automatique montre les tendances de participation
- La revue manuelle filtre les contributions non-constructives
- La contextualisation ajoute profondeur et nuance

### Délibération vs. efficacité

- Les issues permettent une revue rapide et une contextualisation initiale
- Les discussions favorisent une délibération plus longue et approfondie
- Un calendrier clair (début février) assure l'achèvement avant la campagne

### Transparence vs. charge de travail

- L'automatisation gère l'agrégation routinière
- L'équipe se concentre sur la curation à haute valeur ajoutée
- GitHub fournit une infrastructure gratuite et auditable

## En résumé

```
Votre formulaire anonyme
    ↓
Rapport automatique quotidien (stats uniquement)
    ↓
Vérification conformité charte (équipe)
    ↓
Issue GitHub avec contexte (public)
    ↓
Discussion communautaire (public)
    ↓
Intégration programme (février 2026)
```

## Vous voulez suivre le processus ?

- **Voir les rapports quotidiens :** [Issues avec label "rapport"](https://github.com/audierne2026/participons/issues?q=label%3Arapport)
- **Suivre les contributions en cours :** [Issues avec label "conforme charte"](https://github.com/audierne2026/participons/issues?q=label%3A%22conforme+charte%22)
- **Participer aux discussions :** [GitHub Discussions](https://github.com/audierne2026/participons/discussions)

## Documentation complète

Le processus complet est documenté en détail (en anglais) dans notre dépôt :
→ [contribution process](https://audierne2026.fr/contribution-process/)

---
