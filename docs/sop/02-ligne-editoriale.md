<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 2 · Ligne éditoriale

**Skills** : `seo-opportunites`, `seo-keyword-research` · **Commande** : `/seo opportunites`

**Objectif** : Décider quoi écrire, dans quel ordre et sur quel ton, à partir de ce qui rapporte.

**Quand** : Une fois par mois, avant de lancer la production.

**Dis à Claude** : « Classe mes opportunités par ce qu'elles rapportent et propose un calendrier de 8 semaines, 3 contenus par semaine. »

## Étapes

1. Remplis le lexique de ton métier : tes services et ce qu'ils valent pour toi. C'est lui qui dit qu'un sujet compte plus qu'un autre.
2. Claude classe chaque opportunité : clics gagnables × valeur du thème × facilité, avec l'action à mener (title, enrichissement, consolidation, page à créer).
3. Il ajoute la demande où tu n'apparais pas encore (`demande.py idees --lexique`, avec DataForSEO). Indispensable sur un site jeune.
4. Il équilibre le funnel (par défaut 60 % découverte, 25 % comparaison, 15 % décision) et sort un calendrier (`opportunites.py --calendrier --semaines 8 --capacite 3`).
5. Il mesure ton style sur 5 à 10 de tes pages (`style_maison.py`) et l'écrit dans `memoire/style.md` : longueur des phrases, tutoiement ou vouvoiement, expressions qui reviennent.

**MCP nécessaires** : Search Console. DataForSEO ou Ubersuggest pour la demande.

**Livrable** : `rapports/opportunites-<date>.md`, `rapports/calendrier-<date>.md`, `memoire/style.md` et `memoire/marque.md`.

## Pièges

- Prioriser au volume brut. On vise la valeur pour ton chiffre d'affaires.
- Écrire du neuf avant de rattraper les pages en position 4 à 20.
- Sans `locId`, les volumes Ubersuggest sont mondiaux : il faut le dire.

> Chez nous : En tête du classement de decupler.com le 01/10/2026 : « agence geo bordeaux », position 8,5, 78 impressions par mois, action « enrichir la page et son maillage ».
