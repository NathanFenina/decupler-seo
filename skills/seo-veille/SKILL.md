---
name: seo-veille
description: >
  Surveillance continue d'un site : positions, indexation, erreurs techniques,
  Core Web Vitals, liens perdus, mentions, mises à jour Google, mouvements
  concurrents. Détecte les anomalies et alerte avec un diagnostic, pas juste
  un chiffre. Déclencher sur "veille", "surveillance", "monitoring", "alerte",
  "surveiller mon site", "prévenir si", "détecter les problèmes", "suivi
  automatique", "check quotidien".
---

# Veille — détecter avant que ça coûte

Un `noindex` posé par erreur un vendredi soir coûte trois semaines de
trafic si personne ne le voit avant le lundi suivant. La veille sert à
raccourcir ce délai.

Principe : **alerter peu, et toujours avec un diagnostic.** Une alerte qui
dit « les positions ont baissé » sans dire lesquelles ni pourquoi sera
ignorée au bout de la troisième.

## Ce qu'on surveille, et à quelle fréquence

| Quoi | Fréquence | Seuil d'alerte |
|------|-----------|----------------|
| **Disponibilité** des pages clés | Quotidienne | Tout code ≠ 200 |
| **robots.txt** | Quotidienne | Toute modification |
| **Balises noindex** sur les pages clés | Quotidienne | Apparition |
| **Canonicals** des pages clés | Hebdomadaire | Changement |
| **Positions** sur les requêtes suivies | Hebdomadaire | Chute > 5 places, ou sortie du top 20 |
| **Clics organiques** | Hebdomadaire | Écart > 25 % vs la même semaine M-1 |
| **Couverture d'index** | Hebdomadaire | Hausse des erreurs > 10 % |
| **Core Web Vitals** | Mensuelle | Passage d'une métrique au rouge |
| **Backlinks perdus** | Mensuelle | Perte d'un lien à DR > 40 |
| **Mentions de marque** | Hebdomadaire | Nouvelle mention non liée |
| **Mises à jour Google** | En continu | Annonce officielle |
| **Concurrents** | Mensuelle | Nouvelle page dans le top 3 de vos requêtes |

Les trois premières lignes justifient à elles seules la mise en place. Ce
sont les incidents à la fois les plus fréquents et les plus coûteux.

## Le format d'une alerte utile

```
🔴 ALERTE — /services/plomberie est passée en noindex

Détecté      : 14/03 à 06:12
Depuis quand : entre le 13/03 22:00 et le 14/03 06:00
Impact       : 3 400 impressions/mois, 210 clics/mois, position moyenne 4,2
Origine      : balise meta robots dans le <head>. Probablement une
               modification de réglage dans le plugin SEO
Urgence      : critique — désindexation sous 3 à 7 jours

À faire : retirer le noindex, puis inspection d'URL dans Search Console
          pour demander une réindexation.
```

Chaque alerte répond à quatre questions : **quoi, depuis quand, combien ça
coûte, quoi faire.** Sans les quatre, ce n'est pas une alerte, c'est une
notification.

## Distinguer un incident d'une fluctuation

Le principal défaut d'une surveillance est le bruit. Filtres à appliquer :

- **Positions** : une variation de ±3 places est du bruit normal. N'alertez
  qu'au-delà de 5 places, ou sur une sortie du top 10.
- **Trafic** : comparez toujours à la même période de l'année précédente, pas
  à la semaine dernière. Une chute de 30 % la semaine du 15 août est normale.
- **Confirmez avant d'alerter** : une mesure isolée peut être un timeout.
  Reprenez la mesure avant de déclencher.
- **Regroupez** : dix pages qui passent en noindex en même temps = une seule
  alerte, pas dix.

## Les mises à jour Google

Surveillez les annonces officielles. Quand une mise à jour est confirmée :

1. Notez la date de début et de fin de déploiement
2. **N'analysez rien pendant le déploiement** — les positions bougent dans
   tous les sens, les conclusions tirées à ce moment sont fausses
3. Attendez la fin annoncée + 7 jours
4. Alors seulement, comparez avant/après par segment

Le pire réflexe est de modifier le site pendant un déploiement : vous ne
saurez jamais ce qui a causé quoi.

## Automatiser

Un contrôle quotidien léger :
```
/loop 24h /seo veille
```

Ou une Routine programmée pour tourner le matin, avec une notification
uniquement s'il y a quelque chose.

Contrôle complet hebdomadaire, rapport complet mensuel (`/seo rapport`).

**Le silence est le bon comportement.** Une veille qui envoie un message
chaque jour pour dire que tout va bien finit en filtre automatique. Ne
signalez que ce qui mérite une action.

## Le journal

Consignez chaque relevé dans `veille/historique.csv`, même sans alerte.
L'historique sert à répondre à la question « depuis quand ? » — qui est
toujours la première question posée quand un problème est découvert.

Format : date, indicateur, valeur, variation, alerte déclenchée (oui/non).

## Ce qu'on ne peut pas surveiller

Soyez honnête sur les limites :
- Les positions relevées ne sont pas celles de vos utilisateurs
  (personnalisation, géolocalisation)
- Les données Search Console ont 2-3 jours de retard
- Les Core Web Vitals de terrain reflètent 28 jours glissants — un correctif
  n'apparaît pas avant un mois
- La détection d'une pénalité manuelle passe uniquement par Search Console

## Livrables

- `veille/alertes.md` — les alertes de la période, avec leur diagnostic
- `veille/historique.csv` — le journal complet
- `veille/etat.json` — l'état courant, pour la comparaison au prochain passage
