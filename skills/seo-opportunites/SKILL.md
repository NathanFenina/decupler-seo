---
name: seo-opportunites
description: >
  Classe toutes les opportunités SEO d'un client par ce qu'elles rapportent
  : clics gagnables × valeur du thème pour son chiffre d'affaires ×
  facilité, à partir de Search Console et du lexique de son métier. Donne
  pour chaque ligne la page, l'action (title, enrichissement, consolidation,
  page à créer, format spécial), l'étape du funnel, le schema conseillé et
  le gain estimé ; dit quels thèmes du métier ne sont pas encore couverts,
  compare le trafic au mix TOFU/MOFU/BOFU cible, produit un calendrier
  éditorial, et un mode budget réduit (3 actions par mois). Déclencher sur
  "opportunités", "par où commencer", "priorités SEO", "qu'est-ce qui
  rapporte le plus", "cartographie des opportunités", "plan d'action", "sur
  quoi travailler ce mois-ci", "calendrier éditorial", "budget réduit", et
  au début de chaque cycle d'optimisation.
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
expert-comptable,3,expert[- ]comptable|cabinet (d'|d )?expertise comptable
expert-comptable,3,accountant|accounting firm
creation-entreprise,3,cr[ée]+er? (une )?(soci[ée]t[ée]|entreprise)|statuts? (sas|sarl)
tva,2,\btva\b|\bvat\b|d[ée]claration de tva
fiscalite,2,imp[ôo]t|liasse fiscale|cfe
gestion,1,tr[ée]sorerie|note de frais|facturation
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
- Ce fichier de demande se produit sans connecteur, donc aussi dans une
  routine cloud :
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/demande.py" idees --lexique --langue fr --ecrire
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/opportunites.py" --demande donnees/demande-fr-<date>.csv --ecrire
  ```
  Les graines viennent des thèmes du lexique ; une passe par langue du
  projet. Renseignez ensuite la colonne `page` pour les requêtes déjà
  visées par une page publiée.
- `--jours 90` par défaut : assez pour lisser les semaines, assez court
  pour rester actuel.
- `--mix 60/25/15` : parts cibles TOFU / MOFU / BOFU (défaut :
  `opportunites.mix` de la config, sinon 60/25/15 — voir
  `seo-keyword-research`, étape 5).
- `--calendrier --semaines 8 --capacite 3` : écrit aussi
  `rapports/calendrier-AAAA-MM-JJ.md` (voir section 4).

## 3. Lire le résultat

| Action | Ce qu'elle veut dire | Skill qui l'exécute |
|---|---|---|
| Réécrire title et meta | page dans le top 3, CTR très sous la normale | `seo-meta-serp` |
| Enrichir, page 1 | position 4 à 10 | `seo-optimisation-onpage`, `seo-maillage-interne` |
| Renforcer, page 2 | position 11 à 20 | `seo-quick-wins` (sections manquantes) |
| Consolider | plusieurs pages du site se partagent la requête | `seo-gsc-analyses` → `cannibalisation.md` |
| Publiée mais invisible | la page existe, la requête ne lui donne aucune impression | `seo-optimisation-onpage`, `seo-maillage-interne`, `seo-netlinking` |
| Créer ou refondre | au-delà de la 20e place, ou absent | `seo-benchmark` → `seo-brief` → `seo-redaction` |
| Format spécial | la requête demande un outil ou une ressource (modèle, checklist, simulateur, calculateur, template, gratuit, pdf, glossaire…) | `seo-cocon-semantique` (formats spéciaux), `seo-page-builder-html` |

Chaque ligne porte aussi :

- **`funnel`** — TOFU / MOFU / BOFU, déduit de l'URL puis de la requête
  (motifs FR, EN, AR ; TOFU par défaut).
- **`intention`** — celle que renvoie `demande.py` pour la requête.
- **`schema`** — le balisage conseillé : transactionnelle → `Service` ou
  `Product` avec prix visible + `FAQPage` ; commerciale → `ItemList` +
  `FAQPage` ; informationnelle → `Article` + `FAQPage`, `HowTo` si
  pas-à-pas. À poser avec `seo-schema-jsonld`.

La section **« Répartition du trafic par étape du funnel »** compare les
impressions du site par étape au mix cible : un écart de plus de 10 points
dit quel type de contenu produire en priorité.

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
- **Calendrier** (`--calendrier`) : 80 % de créations, 20 %
  d'optimisations ; les créations réparties selon le mix, une seule
  optimisation par page ; semaines à partir du lundi suivant. Statuts :
  à planifier → en cours → publié → indexé. Mettez-les à jour dans le
  fichier ; la mesure commence à « indexé ».
- **Rapport mensuel** : les cinq premières actions, la couverture par thème,
  et ce qui a changé depuis le classement du mois précédent
  (`rapports/opportunites-*.md`).

## 5. Mode budget réduit — environ un jour par mois

Quand le temps disponible ne couvre pas le classement entier, on ne
saupoudre pas : on choisit.

- **Trois actions par mois, pas une de plus**, prises en tête du classement
  après exclusion des pages en cours de mesure.
- Chaque action porte **son levier** : **SEO** (title, contenu, maillage),
  **GEO** (réponse directe, FAQ, paragraphe citable, données structurées) ou
  **E-E-A-T** (auteur, preuves, sources, avis). Une action sans levier
  identifié n'est pas prête.
- Priorité aux actions qui touchent une page de valeur 3 déjà en page 1 ou 2 :
  c'est là qu'un jour de travail se voit à J+28.
- Le reste du classement est noté, daté, et repris le mois suivant — pas
  abandonné.

| # | Page | Action | Levier | Gain estimé | Skill |
|---|---|---|---|---|---|
| 1 | | | SEO / GEO / E-E-A-T | | |

## Garde-fous

- Pas de lexique = classement au trafic seul. Le rapport le signale ; dites
  au client que ses priorités business n'y sont pas encore.
- Une requête hors lexique qui revient souvent en tête est un thème oublié :
  ajoutez-le au lexique plutôt que de la traiter au cas par cas.
- Ne jamais présenter un gain estimé comme un engagement.
