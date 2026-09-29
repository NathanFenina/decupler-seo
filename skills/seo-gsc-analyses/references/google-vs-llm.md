# GSC — Google vs llm

**Groupe :** Piloter · **Source :** Google Search Console

## La question à laquelle ce skill répond

Je suis bien placé sur Google — est-ce que les IA me citent pour autant ?

## Données à récupérer

Requêtes cibles GSC + interrogation des moteurs génératifs (Perplexity, ChatGPT).

Accès aux données : voir « Récupérer les données » dans `../SKILL.md`.

## Méthode

1. Prendre les requêtes où le site est déjà bien positionné sur Google.
2. Poser ces mêmes questions aux moteurs génératifs et relever qui est cité, et à quel rang.
3. Mettre les deux colonnes face à face : l'écart est la feuille de route GEO.
4. Identifier les sources que les moteurs citent à la place — c'est là qu'il faut aller se faire mentionner.
5. Journaliser chaque relevé pour mesurer l'évolution d'un mois sur l'autre.

## Sortie attendue

Le tableau position Google / citation LLM par requête, l'écart chiffré, et les sources concurrentes à travailler.

## Le prompt

```
Contexte : site {domaine}, marché France.
Objectif : mesurer l'écart entre ma visibilité Google et ma visibilité
dans les moteurs génératifs.

1. Prends mes requêtes cibles où je suis déjà bien placé sur Google
   (position 1 à 10 selon Search Console).
2. Pose ces mêmes questions aux moteurs génératifs
   (`scripts/share_of_model.py` : ChatGPT, Gemini, et Claude ou Perplexity
   si leur clé existe), en langage naturel — pas en mots-clés. Un utilisateur d'IA écrit des phrases.
3. Pour chaque réponse, relève : mon domaine est-il cité ? à quel rang
   parmi les sources ? et QUI est cité à ma place ?
4. Mets les deux colonnes face à face : position Google contre présence
   LLM. L'écart est la feuille de route GEO — les requêtes où je suis
   1er sur Google et absent des IA sont les plus urgentes.
5. Analyse les sources citées à ma place : sont-elles des concurrents,
   des annuaires, des forums, des médias ? C'est là qu'il faut aller
   se faire mentionner.
6. Journalise le relevé avec sa date pour comparer d'un mois sur l'autre.

Rends le tableau requête | position Google | cité par les moteurs IA |
rang de citation | sources citées à ma place. Puis les 5 requêtes au
plus gros écart, avec pour chacune l'action concrète pour y entrer.

Ne jamais inventer un chiffre : si la donnée manque ou si le volume
est trop faible pour conclure, dis-le explicitement.
Indique toujours la période et le volume qui portent tes conclusions.
```

Règles communes : voir `../SKILL.md`.
