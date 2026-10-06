# Rapport — le 1er du mois

Lis `routines/_commun.md`, puis :

## Le rapport
1. Skill `seo-cycle` en mode rapport : `journal.py mesurer-tout --auto` puis `bilan`,
   `memoire/apprentissages.md`, demande et calendrier du mois.
2. `python3 .claude/decupler-seo/scripts/cartographie.py mensuel --prompts`
   (seulement si `memoire/decisions.md` autorise le relevé IA payant).
3. `rapport.py` : `rapports/<AAAA-MM>.md` et `.json`, section « Lecture et décisions » rédigée.
   Vérifie les runs du mois (`rapports/runs/` et branches `claude/*`) et signale toute absence en tête.

## Roadmap du mois — avant la livraison git
```bash
python3 .claude/decupler-seo/scripts/pilotage.py donnees --sortie donnees/pilotage.json
python3 .claude/decupler-seo/scripts/pilotage.py proposer --mois <AAAA-MM> --projet-id <id> --sortie donnees/actions-<AAAA-MM>.json
python3 .claude/decupler-seo/scripts/pilotage.py injecter --html donnees/tableau-de-bord.html --projet-id <id> \
  --donnees donnees/pilotage.json --actions donnees/actions-<AAAA-MM>.json
```
Republie la page, puis résume les actions proposées dans le rapport.

## Livrer
Commite, pousse, ouvre une PR (rapport, données, mémoire : rien du site). Ne la
fusionne pas : action `bloquee` « relire et fusionner » sur la page de suivi
(règle de `_commun.md`).
