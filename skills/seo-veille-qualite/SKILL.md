---
name: seo-veille-qualite
description: >
  Chaque mois, relit les pages déjà publiées face à la SERP du moment : note
  sur 100 (intention, valeur et gap sémantique, concurrence, GEO, on-page),
  historique des scores, pages les plus faibles d'abord, corrélation avec les
  mesures J+28. Déclencher sur « veille qualité », « relire mes pages », « quelles
  pages améliorer », et le premier mercredi du mois. Pas pour une page neuve →
  seo-benchmark ; pas pour élaguer → seo-audit-contenu.
---

# Veille qualité : relire les pages publiées, chaque mois

Une page optimisée il y a trois mois n'est plus forcément la meilleure : la SERP
bouge, les concurrents réécrivent, les IA citent d'autres sources. Ce skill
repasse sur les pages qui comptent, les note avec une grille fixe, garde
l'historique, et vérifie que la grille prédit vraiment les gains mesurés.

## Règles critiques

- **Une note sans preuve vaut 0.** Chaque critère jugé porte une preuve d'une
  ligne (citation, chiffre, URL du concurrent, réponse d'IA).
- **Ne jamais modifier une page en cours de mesure** (`journal/modifications.csv`,
  `date_mesure` > aujourd'hui), sauf correction factuelle. On prépare la
  correction, on l'applique à la sortie de mesure.
- **Lire `memoire/apprentissages.md` avant de proposer** : un type de
  modification qui « nuit souvent » sur ce site ne se propose plus sans raison.
- Niveaux d'autonomie du projet : titles, metas, FAQ, maillage et
  enrichissements = automatique ; réécriture d'une section qui ranke =
  validation.

## Grille (100 points)

Détail des critères, barème 0/1/2 et preuves attendues :
`references/grille-veille.md`. Cinq blocs de 20 points :

| Bloc | Ce qu'on compare | Source |
|---|---|---|
| A. Intention et SERP actuelle | format attendu, intention, cannibalisation | SERP relue ce mois-ci (`serp_concurrents.py`) |
| B. Valeur et gap sémantique | entités et questions couvertes, information gain | top 5 + PAA + réponses IA |
| C. Concurrence | axes de la grille « faire mieux » encore battus | `seo-benchmark`, relu |
| D. GEO | réponse directe citable, triplets, citée ou non par les IA | `geo-citation-tracker`, relevé IA |
| E. On-page et confiance | `onpage_score.py` ramené sur 20, faits sourcés | script + `memoire/faits.md` |

## Déroulé mensuel

1. **Choisir les pages** : les pages prioritaires de la config
   (`projet.pages_prioritaires`) et celles de la cartographie qui ont des
   impressions ; au plus 10 par mois, en commençant par
   `veille_qualite.py classement` (les plus faibles et les plus anciennes notes).
2. **Pour chaque page** : relire la SERP et le top 5 du moment, lancer
   `onpage_score.py <url> "<mot-clé>" --entites "<entités du top 5>" --json`,
   relever le prompt principal sur les moteurs IA, noter les 5 blocs avec
   preuves, puis enregistrer :
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/veille_qualite.py" ajouter \
     --url <url> --motcle "<mot-clé>" --a 16 --b 12 --c 10 --d 8 --e 17 \
     --position 11.4 --impressions 820 --note "top 5 : X a ajouté un comparatif"
   ```
3. **Classer** : `veille_qualite.py classement` (score, évolution sur le mois
   précédent, bloc le plus faible). Priorité aux pages faibles en position 8 à
   30 avec des impressions : l'effort y paie le plus vite.
4. **Corriger** : pour les 3 premières, liste de corrections précises (texte
   proposé pour une phrase, un H2, une FAQ), effort S/M/L, niveau d'autonomie ;
   appliquer ce qui est automatique et hors mesure, journaliser
   (`seo-journal-mesure`), mettre le reste « à valider ».
5. **Vérifier la grille** : `veille_qualite.py correler`. Si les pages à 80 et
   plus ne gagnent pas plus souvent à J+28 que les autres, un bloc est mal
   pondéré : le signaler dans le rapport, ne pas changer la grille seul.
6. **Rapport** : `rapports/qualite/AAAA-MM.md` (moyenne, évolution, critères
   les plus souvent ratés, actions). Un critère raté sur 3 pages ou plus devient
   une règle dans `memoire/decisions.md` ou un skill `projet-*` ; s'il vaut pour
   tous les sites, une remontée (`projet.py remonter`).

## Mode dégradé

Sans SERP en direct ni relevé IA : noter A, B, C et D sur la dernière SERP
enregistrée (`recherche/serp-*.md`) en le signalant (« SERP du JJ/MM »), et
noter E normalement. Une page sans aucune SERP enregistrée n'est pas notée sur
A à D : on la liste « à relever ».
