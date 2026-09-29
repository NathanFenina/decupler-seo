---
name: seo-programmatique
description: >
  Conçoit, génère et audite des pages SEO à l'échelle depuis une source de
  données : motifs d'URL, gabarits, variables, garde-fous anti-contenu mince,
  maillage automatique, stratégie de canonical. Bloque au-delà des seuils sans
  audit qualité. Déclencher sur "SEO programmatique", "pages à l'échelle",
  "générer des centaines de pages", "pages ville", "pages par catégorie",
  "template de page", "pSEO", "pages automatiques", "landing pages en masse".
---

# SEO programmatique — l'échelle sans le contenu mince

Le SEO programmatique fonctionne quand chaque page apporte une information
que le visiteur ne trouve pas ailleurs. Il échoue — et il fait couler le
site entier — quand les pages ne sont que des permutations de variables.

Google n'évalue pas ces pages une par une. Il évalue le **lot**. Si 60 % du
lot est vide, les 40 % utiles tombent avec.

## Garde-fous

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/guard.py" --action generer-pages --volume <N>
```

| Volume | Comportement |
|--------|--------------|
| < 100 | Autorisé |
| 100-499 | ⚠️ Validation demandée + audit d'un échantillon de 20 pages |
| ≥ 500 | 🛑 **Bloqué** tant que l'audit qualité n'est pas passé |
| Pages locales ≥ 30 | ⚠️ Risque de doorway pages |
| Pages locales ≥ 50 | 🛑 Bloqué |

Ces seuils ne sont pas désactivables. Ils existent parce que le mode d'échec
est catastrophique et différé : tout va bien pendant trois mois, puis le
site entier décroche.

## Le test de valeur unique

Avant de générer quoi que ce soit, répondez :

> **Qu'est-ce que la page « [variable A] » contient que la page
> « [variable B] » ne contient pas — au-delà du nom de la variable ?**

Si la réponse est « rien », il ne faut pas générer ces pages. Faites une
seule page avec un filtre.

| ✅ Ça marche | ❌ Ça ne marche pas |
|--------------|---------------------|
| « Vol Paris-Lisbonne » : prix réels, horaires, compagnies, durée — données propres à cette paire | « Plombier à [ville] » : le même texte avec le nom de la ville changé |
| « Salaire d'un développeur à Lyon » : données salariales locales issues d'un jeu de données | « Meilleur [produit] pour [métier] » : trois adjectifs permutés |
| « [Logiciel A] vs [Logiciel B] » : comparaison de caractéristiques réelles | « Acheter [produit] pas cher [ville] » : rien de local |

## La source de données

Elle doit être **riche**. Une bonne source de données programmatique a au
moins 8-10 champs exploitables par entrée, et de préférence des données que
personne d'autre n'a — les vôtres.

Sources possibles : votre base métier, un jeu de données public, des données
agrégées de vos clients (anonymisées), une API tierce, vos propres mesures.

Qualité : pas de champ vide sur les pages générées. Une page avec « prix :
N/A, disponibilité : N/A » est pire que pas de page. **Filtrez les entrées
incomplètes avant génération** — c'est la règle la plus importante de ce
skill.

## L'architecture

**Motif d'URL** — court, lisible, sans paramètre :
`/vols/paris-lisbonne/` et non `/search?from=CDG&to=LIS`

**Le gabarit**, avec la part de contenu unique :

| Zone | Part | Contenu |
|------|------|---------|
| H1 | unique | Variables |
| Réponse directe | unique | Générée à partir des données réelles |
| Bloc de données | **unique** | Le cœur : tableau, chiffres, graphique |
| Analyse | unique | 150-300 mots générés depuis les données, pas un texte à trous |
| Contexte | partagé | Explication générale du domaine |
| FAQ | mixte | 2 questions dynamiques, 3 statiques |
| Maillage | unique | Pages liées calculées par proximité |

**Visez au moins 60 % de contenu unique par page.** En dessous, c'est de la
duplication à l'échelle.

Le « texte à trous » (`Vous cherchez un {métier} à {ville} ? Nos {métier}s
à {ville} sont…`) est la signature du contenu mince. Générez la prose **à
partir des données** : « Sur cette liaison, le prix médian est de 89 €,
soit 23 % sous la moyenne des vols depuis Paris. »

## Le maillage automatique

Sans maillage, les pages générées sont orphelines et ne seront jamais
indexées. Prévoyez :

- Une **page index** listant toutes les pages générées, paginée par 50
- Des **liens de proximité** entre pages : mêmes catégories, valeurs
  voisines, alternatives (5-8 liens par page)
- Un lien **remontant** vers la catégorie parente
- L'inclusion dans un sitemap dédié

## Canonicals et prévention du gonflement d'index

- Chaque page générée : canonical **auto-référente**
- Les variantes de tri, de filtre ou de pagination : canonical vers la page
  principale
- Les combinaisons à faible valeur (moins de X entrées de données) :
  `noindex, follow` — la page reste accessible, elle ne pollue pas l'index
- Sitemap séparé pour les pages programmatiques : le rapport de couverture
  GSC devient exploitable par segment

## Le déploiement progressif — la seule méthode sûre

1. **Générer 20 pages.** Choisir les 20 entrées les plus riches en données.
2. **Auditer manuellement** : chaque page apporte-t-elle une valeur propre ?
   Un humain la trouverait-elle utile ?
3. **Publier** ces 20, attendre **4 à 6 semaines**.
4. **Mesurer** : combien sont indexées ? Combien reçoivent des impressions ?
   Quel est le taux d'indexation ?

| Taux d'indexation à 6 semaines | Décision |
|-------------------------------|----------|
| > 80 % avec impressions | ✅ Déployer le reste, par lots de 100 |
| 50-80 % | ⚠️ Enrichir le gabarit avant d'aller plus loin |
| < 50 % | 🛑 Arrêter. Le gabarit ne tient pas. |

Ne générez **jamais** 2 000 pages d'un coup. Si le gabarit est mauvais, vous
l'apprendrez trois mois plus tard, sur un site abîmé.

## Auditer un déploiement existant

Si des pages programmatiques existent déjà :

1. Taux d'indexation par segment (GSC)
2. Pages sans aucune impression depuis 6 mois → candidates au `noindex` ou
   à la suppression du sitemap
3. Cannibalisation : plusieurs pages sur la même requête
4. Contenu mince : comptage de mots uniques hors gabarit
5. Orphelines : pages générées sans lien entrant

Le correctif le plus fréquent : passer 70 % des pages en `noindex` et
enrichir les 30 % qui ont du potentiel. Un index plus petit et plus dense
performe mieux qu'un index gonflé.

## Livrables

- `PROGRAMMATIQUE-PLAN.md` — motif d'URL, gabarit, source de données, seuils
- `gabarit.html` — le template
- `echantillon/` — les 20 premières pages, à auditer
- `AUDIT-QUALITE.md` — le verdict sur l'échantillon
- `maillage-programmatique.csv` — le plan de liens
