---
name: seo-suivi-mensuel
description: >
  Suivi mensuel d'un projet sur deux mesures qui ne changent pas d'un mois à
  l'autre : la position réelle de chaque mot-clé principal de la cartographie
  dans Google (relevé direct, page qui ranke, concurrent devant, AI Overview),
  et la présence de la marque sur une batterie de prompts validée par le
  client dans ChatGPT, Gemini, Claude et Perplexity. Propose la batterie,
  la fait valider, relève, compare au mois précédent. Déclencher sur "suivi
  mensuel", "suivi des positions", "rank tracking", "est-ce qu'on remonte",
  "suivi des prompts", "prompts à suivre", "monitoring mensuel", "batterie de
  prompts", "faire valider les prompts", "positions du mois".
---

# Suivi mensuel — positions et prompts

Deux questions, chaque mois, avec la même liste : **remonte-t-on sur Google
sur les mots-clés qui comptent ?** et **les IA nous citent-elles sur les
questions qui comptent ?** Script : `scripts/suivi.py`.

## Ce qui le distingue de cartographie.py mensuel

| | `cartographie.py mensuel` | `suivi.py` |
|---|---|---|
| Source des positions | Search Console (position moyenne du mois) | Google en direct (DataForSEO) le jour du relevé |
| Fonctionne sans accès GSC | non | oui |
| Dit quelle page ranke et qui est devant | page du site seulement | oui, + concurrent devant + AI Overview |
| Prompts | le prompt principal de chaque page | une batterie validée par le client (noms, thèmes, agence, haut de funnel) |

Les deux se complètent : lancer les deux le premier du mois.

## 1. Proposer, puis faire valider la batterie

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/suivi.py" proposer
```
Ajoute à `recherche/prompts-suivi.csv` les prompts principaux de la
cartographie au statut `propose`. Compléter à la main pour couvrir **tout le
funnel**, par thème prioritaire :

- **BOFU nom** : « Comment faire venir [intervenant / produit phare] … ? » — ce
  qui marche déjà, à défendre ;
- **BOFU offre** : « Combien coûte… », « Comment réserver… », « Quelle agence… » ;
- **MOFU** : « Quel [catégorie] sur [thème] pour [contexte] ? », « Quels sont les meilleurs… » ;
- **TOFU** : le problème de l'acheteur, sans vocabulaire de vendeur.

20 à 40 prompts, jamais le nom de la marque. Le client valide ligne par
ligne (`statut` → `valide` / `refuse`) — dans la page de suivi ou l'artifact
du projet. **On ajoute, on ne retire jamais** : un prompt refusé garde sa
ligne pour ne pas revenir.

## 2. Relever

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/suivi.py" positions            # ~0,002 $ / mot-clé
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/suivi.py" prompts              # prompts « valide » seulement
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/suivi.py" prompts --tout       # relevé de référence avant validation
```
Annoncer le coût avant (nombre de mots-clés, prompts × moteurs). Relancer le
même mois remplace ses lignes ; l'historique est dans
`donnees/suivi-positions.csv` et `donnees/suivi-prompts.csv`.

## 3. Lire et décider

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/suivi.py" rapport --mois AAAA-MM
```
→ `rapports/suivi-AAAA-MM.md` (et `.json`), repris dans le rapport mensuel.

| Constat | Suite |
|---|---|
| « autre page » ranke sur le mot-clé | cannibalisation : `seo-cartographie`, consolider |
| Position stable hors top 10 depuis 2 mois | contenu insuffisant : `seo-brief` variante optimisation |
| Top 3 Google, prompt absent des IA | réponse directe, FAQ, données citables : `geo-citation-tracker` |
| Toujours le même concurrent devant | `seo-competitor-gap` ciblé sur ce domaine |
| AI Overview apparu | page à rendre citable en priorité, mesurer le CTR |
| Prompt perdu sur un moteur | lire les sources citées à la place : où publier |

## Garde-fous

- Un LLM est non déterministe : une case qui bascule une fois n'est pas une
  tendance. Conclure sur deux mois consécutifs ou plusieurs prompts du même thème.
- Ne jamais présenter une estimation comme une mesure : un prompt non relevé
  s'affiche « à mesurer ».
