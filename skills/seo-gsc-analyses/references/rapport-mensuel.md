# GSC — Rapport mensuel

**Groupe :** Piloter · **Source :** Google Search Console

## La question à laquelle ce skill répond

À quoi ressemble le mois écoulé, et qu'est-ce que ça veut dire ?

## Données à récupérer

Mois courant vs M-1 vs même mois N-1. GA4 et PostHog si branchés.

Accès aux données : voir « Récupérer les données » dans `../SKILL.md`.

## Méthode

1. Donner d'abord les chiffres clés : clics, impressions, position moyenne, avec les deux comparaisons.
2. Nommer les 3 mouvements qui expliquent l'essentiel de la variation — pas une liste de 40 lignes.
3. Croiser avec les conversions si GA4 est disponible : « le trafic monte sur les pages qui ne convertissent pas » est une information, « le trafic monte » n'en est pas une.
4. Terminer par les actions du mois suivant, priorisées.
5. Ne jamais inventer un chiffre absent des données.

## Sortie attendue

Un rapport structuré : chiffres clés, ce qui a bougé et pourquoi, actions du mois suivant.

## Le prompt

```
Contexte : site {domaine}, rapport pour le client.
Objectif : un rapport qui DIT quelque chose, pas qui aligne des courbes.

1. Récupère : mois courant, mois précédent, et même mois l'an dernier.
2. Ouvre sur les chiffres clés — clics, impressions, position moyenne —
   avec les DEUX comparaisons. Sans la comparaison annuelle, on
   confond un cycle avec une tendance.
3. Nomme les 3 mouvements qui expliquent l'essentiel de la variation.
   Trois, pas quarante lignes de tableau.
4. Si GA4 est branché, croise avec les conversions par page d'entrée.
   « Le trafic monte sur les pages qui ne convertissent pas » est une
   information ; « le trafic monte » n'en est pas une.
5. Si PostHog est branché, ajoute où les visiteurs organiques décrochent.
6. Termine par les actions du mois suivant, priorisées par impact
   attendu, avec la page concernée pour chacune.

Rends : chiffres clés, les 3 mouvements expliqués, le croisement
conversion, puis les actions. Ton factuel, pas de superlatifs. Si un
chiffre est absent des données, écris-le au lieu de l'estimer.

Ne jamais inventer un chiffre : si la donnée manque ou si le volume
est trop faible pour conclure, dis-le explicitement.
Indique toujours la période et le volume qui portent tes conclusions.
```

Règles communes : voir `../SKILL.md`.
