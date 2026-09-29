# GSC — Reecriture title

**Groupe :** Produire · **Source :** Google Search Console

## La question à laquelle ce skill répond

Comment réécrire mes titles et metas pour récupérer les clics que je laisse sur la table ?

## Données à récupérer

Sortie de `gsc-ctr-anormal` + title/meta actuels des pages ciblées.

Accès aux données : voir « Récupérer les données » dans `../SKILL.md`.

## Méthode

1. Reprendre les pages identifiées en déficit de CTR.
2. Réécrire en intégrant **la formulation exacte** de la requête la plus porteuse de la page.
3. Respecter les limites d'affichage (environ 60 caractères pour le title, 120 à 156 pour la meta).
4. Proposer deux variantes par page pour permettre un test.
5. Estimer le gain de clics si le CTR rejoint la médiane de sa position.

## Sortie attendue

Un tableau : URL, title actuel → 2 propositions, meta actuelle → 2 propositions, gain de clics estimé.

## Le prompt

```
Contexte : site {domaine}.
Objectif : réécrire les titles et metas des pages qui sous-performent
en clics à position égale.

1. Pars de la sortie de gsc-ctr-anormal. Si tu ne l'as pas, lance
   d'abord l'analyse : courbe CTR/position du site, puis écart.
2. Pour chaque page ciblée, récupère le title et la meta actuels ainsi
   que sa requête la plus porteuse en impressions.
3. Réécris en intégrant la FORMULATION EXACTE de cette requête, pas une
   variante élégante. Google met en gras ce qui correspond.
4. Respecte les limites d'affichage : environ 60 caractères pour le
   title, 120 à 156 pour la meta. Compte-les et affiche le compte.
5. Produis DEUX variantes par page, avec des angles différents — une
   factuelle, une orientée bénéfice — pour permettre un test.
6. Estime le gain si le CTR rejoint la médiane de sa position.

Rends un tableau : URL | title actuel (nb caractères) | variante A |
variante B | meta actuelle | variante A | variante B | gain estimé.
Ajoute une phrase par page expliquant ton angle.

Ne jamais inventer un chiffre : si la donnée manque ou si le volume
est trop faible pour conclure, dis-le explicitement.
Indique toujours la période et le volume qui portent tes conclusions.
```

Règles communes : voir `../SKILL.md`.
