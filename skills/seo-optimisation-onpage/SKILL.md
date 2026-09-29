---
name: seo-optimisation-onpage
description: >
  Audite un contenu existant face à un mot-clé cible, le note sur 100 avec un
  feu rouge/orange/vert par critère, PUIS réécrit la version optimisée prête à
  publier. Remplace Yoast et Rank Math : il note et il corrige. Déclencher sur
  "optimise cette page", "score SEO", "note sur 100", "audit on-page",
  "est-ce que c'est bien optimisé", "passe au vert", "réécris cette page",
  "améliore ce contenu", "optimisation on-page", ou un texte/URL collé avec
  un mot-clé cible.
---

# Optimisation on-page — noter puis corriger

Les plugins SEO vous disent que c'est orange. Ils ne le passent pas au vert.
Ce skill fait les deux.

## Entrées

- Le contenu : URL (à récupérer) ou texte collé
- Le mot-clé cible principal — **s'il n'est pas donné, demandez-le.** Sans
  cible, il n'y a pas d'optimisation possible.
- Les secondaires, si connues

## Le barème — 100 points

### Bloc A · Balises et structure (25 pts)

| Critère | Points | Vert | Orange | Rouge |
|---------|--------|------|--------|-------|
| Title | 6 | Mot-clé dans les 3 premiers mots, 50-60 car. | Mot-clé présent mais tardif, ou 45-70 car. | Absent, dupliqué, ou sans mot-clé |
| Meta description | 4 | 150-160 car., mot-clé, promesse claire | Longueur limite ou fade | Absente ou > 170 car. |
| H1 | 5 | Un seul, contient le mot-clé | Un seul, mot-clé approximatif | Absent ou multiple |
| Hiérarchie Hn | 5 | Séquentielle, titres explicites | Un saut de niveau | Anarchique ou inexistante |
| URL | 5 | Courte, mot-clé, sans paramètre | Longue mais lisible | Illisible ou sans rapport |

### Bloc B · Contenu et sémantique (30 pts)

| Critère | Points | Vert | Rouge |
|---------|--------|------|-------|
| Présence du mot-clé | 6 | H1 + 100 premiers mots + un H2 + conclusion | Absent des zones clés, ou bourrage évident |
| Champ sémantique | 8 | Entités et cooccurrences attendues couvertes | Vocabulaire pauvre, hors sujet |
| Profondeur | 6 | Couvre le sujet au niveau du top 3 | Contenu mince, < 300 mots utiles |
| Lisibilité | 5 | Phrases courtes, paragraphes aérés | Blocs compacts, jargon non expliqué |
| Originalité | 5 | Donnée, exemple ou méthode propre | Paraphrase de ce qui existe déjà |

### Bloc C · GEO et citabilité (20 pts)

| Critère | Points | Vert | Rouge |
|---------|--------|------|-------|
| Réponse directe | 6 | 40-60 mots en haut, autonome | Aucune réponse avant le 3e écran |
| Structure extractible | 4 | Listes, tableaux, titres explicites | Bloc de texte continu |
| Définitions | 3 | Termes clés définis en une phrase autonome | Rien de définissable |
| FAQ | 4 | 4+ questions, réponses de 40-60 mots | Absente |
| Données sourcées | 3 | Chiffres avec source vérifiable | Chiffres non sourcés, ou aucun |

### Bloc D · E-E-A-T (15 pts)

| Critère | Points |
|---------|--------|
| Auteur identifié avec credentials | 4 |
| Expérience de première main démontrée | 4 |
| Sources externes d'autorité citées | 3 |
| Date de publication et de mise à jour | 2 |
| Transparence (contact, mentions, affiliation déclarée) | 2 |

### Bloc E · Maillage et technique (10 pts)

| Critère | Points |
|---------|--------|
| 3+ liens internes contextuels, ancres descriptives | 4 |
| Liens externes pertinents | 2 |
| Images avec alt descriptif | 2 |
| Schema JSON-LD adapté et valide | 2 |

## Le rapport

```
SCORE : 61/100  🟠

  A · Balises et structure    18/25  🟠
  B · Contenu et sémantique   19/30  🟠
  C · GEO et citabilité        6/20  🔴
  D · E-E-A-T                  9/15  🟠
  E · Maillage et technique    9/10  🟢
```

Puis, pour chaque critère non vert, dans cet ordre :

1. **Ce qui est en place** — la valeur actuelle, citée
2. **Pourquoi c'est un problème** — l'effet concret, pas la règle
3. **Le correctif** — la version corrigée, écrite

Exemple :

> **Title — 3/6 🟠**
> Actuel : « Nos prestations » (17 car.)
> Aucun mot-clé, aucune promesse, aucun repère géographique. Sur une SERP,
> ce titre ne donne au lecteur aucune raison de cliquer plutôt que sur les
> neuf autres.
> **Corrigé** : « Plombier à Lyon : dépannage en 2 h, devis gratuit » (52 car.)

Barème global : 85-100 🟢 publiable · 70-84 🟢 bon, corrections mineures ·
50-69 🟠 à retravailler · 30-49 🔴 réécriture partielle · <30 🔴 repartir de zéro.

## La réécriture — la partie qui compte

Après le rapport, produisez **le contenu optimisé complet**, pas des
extraits. L'utilisateur doit pouvoir copier-coller et publier.

Contraintes :
- **Garder ce qui marche.** Ne réécrivez pas une page qui ranke déjà : vous
  remettriez le compteur à zéro. Ajoutez, précisez, restructurez.
- Ne jamais supprimer une information juste pour raccourcir
- Aucun chiffre inventé — si le texte d'origine cite un chiffre sans
  source, signalez-le plutôt que de le reprendre à votre compte
- Respecter le ton du site (`config` → `projet.ton`)
- Le style humain : voir `seo-redaction`, section « ne pas écrire comme une IA »

Livrez dans l'ordre : title, meta description, H1, contenu complet balisé,
FAQ, schema JSON-LD, liens internes à poser.

## Le nouveau score

Terminez en re-notant la version réécrite, avec le même barème. L'utilisateur
voit 61 → 92 et sait exactement ce qui a bougé.

## Livrables

- `ONPAGE-<slug>.md` — rapport + contenu optimisé
- `optimise-<slug>.html` — version HTML si destinée à un CMS
- Le tableau avant/après par critère
