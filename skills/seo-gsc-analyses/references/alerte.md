# GSC — Alerte

**Groupe :** Piloter · **Source :** Google Search Console

## La question à laquelle ce skill répond

Qu'est-ce qui vient de décrocher et que je n'ai pas vu ?

## Données à récupérer

7 derniers jours vs les 4 semaines précédentes.

Accès aux données : voir « Récupérer les données » dans `../SKILL.md`.

## Méthode

1. Définir les seuils avant de regarder les données, pour éviter de justifier après coup.
2. Surveiller : chute de clics d'une URL importante, perte de position sur une requête stratégique, effondrement de CTR, disparition d'une page de l'index.
3. Comparer à des jours équivalents — un lundi contre un dimanche ne veut rien dire.
4. Ne remonter que ce qui dépasse le seuil : une alerte qui crie tout le temps n'est plus lue.

## Sortie attendue

Une liste d'alertes ou, mieux, la confirmation explicite qu'il n'y a rien à signaler.

## Le prompt

```
Contexte : site {domaine}, surveillance hebdomadaire.
Objectif : ne remonter que ce qui mérite vraiment mon attention.

1. FIXE LES SEUILS AVANT de regarder les données. Sinon on justifie
   après coup ce qu'on a trouvé.
   Seuils proposés, à ajuster : −25 % de clics sur une URL qui pesait
   plus de 100 clics/mois ; −3 positions sur une requête stratégique ;
   −30 % de CTR à position stable ; disparition totale d'une page.
2. Compare les 7 derniers jours aux 4 semaines précédentes, sur des
   jours ÉQUIVALENTS. Un lundi contre un dimanche ne veut rien dire.
3. Écarte les variations explicables par la saisonnalité connue.
4. Ne remonte que ce qui dépasse un seuil. Une alerte qui se déclenche
   toutes les semaines n'est plus lue par personne.
5. Pour chaque alerte, donne la cause probable et l'action immédiate.

Rends soit la liste des alertes classées par gravité, soit — et c'est
une réponse parfaitement valable — la confirmation explicite qu'il n'y
a rien à signaler cette semaine, avec les seuils qui ont été testés.

Ne jamais inventer un chiffre : si la donnée manque ou si le volume
est trop faible pour conclure, dis-le explicitement.
Indique toujours la période et le volume qui portent tes conclusions.
```

Règles communes : voir `../SKILL.md`.
