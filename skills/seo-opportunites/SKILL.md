---
name: seo-opportunites
description: >
  Classe toutes les opportunités SEO d'un client par ce qu'elles rapportent :
  clics gagnables × valeur du thème pour son chiffre d'affaires × facilité,
  à partir de Search Console et du lexique de son métier. Donne pour chaque
  ligne la page, l'action (title, enrichissement, consolidation, page à
  créer) et le gain estimé, et dit quels thèmes du métier ne sont pas encore
  couverts. Déclencher sur "opportunités", "par où commencer", "priorités
  SEO", "qu'est-ce qui rapporte le plus", "cartographie des opportunités",
  "plan d'action", "sur quoi travailler ce mois-ci", et au début de chaque
  cycle d'optimisation.
---

# Opportunités — agir d'abord là où ça rapporte

`seo-quick-wins` corrige des pages. Ce skill décide **lesquelles, et dans
quel ordre**, pour ce client-là. Deux sites qui ont le même trafic n'ont pas
les mêmes priorités : une requête « prix » vaut plus qu'une requête
« définition » pour un cabinet, l'inverse pour un média.

## 1. Le lexique du client — une fois, puis à chaque nouveau service

`memoire/lexique.csv`, une ligne par motif :

```csv
theme,valeur,motif
creation-societe,3,cr[ée]+er? (une )?(soci[ée]t[ée]|entreprise)
creation-societe,3,company (formation|setup|registration)
creation-societe,3,تأسيس شركة
tva,2,\btva\b|\bvat\b|zatca|ضريبة القيمة المضافة
guide-pays,1,vivre|expatri|culture
```

- **Thèmes** : les services et les sujets du métier, pas des mots-clés.
  Entre 5 et 15 : au-delà, la couverture ne se lit plus.
- **Valeur** : 3 = ce qui se vend (intention d'achat, service facturé),
  2 = ce qui y mène (coûts, étapes, comparaisons), 1 = ce qui fait
  connaître (information, culture). À valider avec le client — c'est lui qui
  sait ce qui rapporte.
- **Motifs** : expressions régulières, insensibles à la casse, dans **toutes
  les langues du projet**. Partir des requêtes réelles de Search Console et
  de `seo-keyword-research`, pas de l'intuition.
- Le premier motif qui correspond l'emporte : mettez les thèmes les plus
  précis en haut.

La marque est exclue du classement (nom du projet et nom de domaine par
défaut, ou `opportunites.marque` dans la config) : ce trafic est déjà acquis.

## 2. Lancer

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/opportunites.py" --ecrire
```

- Sans API Search Console : exporter Performances en requêtes × pages et
  passer `--csv export.csv`.
- Pour voir aussi la demande où le site **n'apparaît pas** : un CSV
  `requete,volume,page` issu de DataForSEO, Ubersuggest ou Semrush, en
  `--demande mots-cles.csv`. La colonne `page` (facultative) indique la page
  publiée qui vise la requête : elle distingue « page à créer » de « page
  publiée mais invisible ». C'est indispensable sur un site jeune, qui a
  encore peu d'impressions — et le script fonctionne alors même sans accès
  Search Console.
- `--jours 90` par défaut : assez pour lisser les semaines, assez court
  pour rester actuel.

## 3. Lire le résultat

| Action | Ce qu'elle veut dire | Skill qui l'exécute |
|---|---|---|
| Réécrire title et meta | page dans le top 3, CTR très sous la normale | `seo-meta-serp` |
| Enrichir, page 1 | position 4 à 10 | `seo-optimisation-onpage`, `seo-maillage-interne` |
| Renforcer, page 2 | position 11 à 20 | `seo-quick-wins` (sections manquantes) |
| Consolider | plusieurs pages du site se partagent la requête | `seo-gsc-analyses` → `cannibalisation.md` |
| Publiée mais invisible | la page existe, la requête ne lui donne aucune impression | `seo-optimisation-onpage`, `seo-maillage-interne`, `seo-netlinking` |
| Créer ou refondre | au-delà de la 20e place, ou absent | `seo-benchmark` → `seo-brief` → `seo-redaction` |

Le gain estimé sert à **comparer** les actions entre elles, pas à promettre
un trafic : le CTR réel dépend de la SERP (AI Overview, annonces, vidéos).
Le vrai gain se lit à J+28 dans le journal.

La **couverture par thème** est souvent la partie la plus utile : un thème
de valeur 3 marqué « aucune page » est une page ou une section qui manque au
site, et qui passe avant toute optimisation ; « invisible » veut dire que la
page existe mais que Google ne la montre pas. Sans Search Console, la
position est « ? » : le rapport ne prétend pas savoir ce qu'il ne mesure pas.

## 4. Ce qu'on en fait

- **Cycle d'optimisation** : prendre les actions dans l'ordre, dans la
  limite de `cycle.pages_optimisees_par_semaine_max`, en sautant celles qui
  ne sont pas au niveau automatique. Chaque action publiée est journalisée
  avec son `type_journal`.
- **Pages en cours de mesure** : le script les exclut. Ne pas les forcer : les
  modifier maintenant rendrait illisible la mesure de la modification
  précédente.
- **Rapport mensuel** : les cinq premières actions, la couverture par thème,
  et ce qui a changé depuis le classement du mois précédent
  (`rapports/opportunites-*.md`).

## Garde-fous

- Pas de lexique = classement au trafic seul. Le rapport le signale ; dites
  au client que ses priorités business n'y sont pas encore.
- Une requête hors lexique qui revient souvent en tête est un thème oublié :
  ajoutez-le au lexique plutôt que de la traiter au cas par cas.
- Ne jamais présenter un gain estimé comme un engagement.
