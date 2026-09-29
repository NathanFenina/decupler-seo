---
name: seo-traffic-drop
description: >
  Diagnostique une chute de trafic organique : datation précise, isolement du
  segment touché, arbre de causes (technique, mise à jour Google, saisonnalité,
  perte de positions, AI Overviews, concurrence), et plan de récupération.
  Déclencher sur "chute de trafic", "j'ai perdu du trafic", "baisse SEO",
  "mon trafic s'effondre", "pénalité", "core update", "je suis déclassé",
  "mes positions ont chuté", "moins de clics qu'avant".
---

# Chute de trafic — diagnostiquer avant de réagir

La pire réaction à une chute de trafic est de tout changer en même temps.
Vous perdez la capacité de savoir ce qui a marché, et vous ajoutez souvent
un deuxième problème au premier.

Ordre imposé : **dater → isoler → expliquer → corriger.** Ne sautez pas
d'étape.

## Étape 1 — Dater précisément

Dans Search Console, comparez jour par jour sur 16 mois. Vous cherchez la
**date exacte** de l'inflexion.

| Forme de la courbe | Famille de causes |
|--------------------|-------------------|
| Chute brutale sur 1-3 jours | Technique, ou mise à jour Google |
| Érosion lente sur 4-12 semaines | Concurrence, obsolescence, AI Overviews |
| Chute en escalier | Désindexation progressive par segment |
| Baisse cyclique | Saisonnalité — vérifiez l'an dernier avant de paniquer |

**Vérifiez la saisonnalité en premier.** Une part importante des « chutes »
signalées en août ou fin décembre sont des variations normales. Comparez à
la même période de l'année précédente, pas au mois précédent.

Puis confrontez la date à l'historique des mises à jour Google. Si elle
coïncide à 48 h près avec un core update, vous tenez probablement la cause.

## Étape 2 — Isoler ce qui a baissé

Ne regardez jamais le total. Segmentez :

- **Par page** — tout le site, ou 5 pages qui portaient tout ?
- **Par requête** — perte de positions, ou perte d'impressions à position
  stable ?
- **Par type d'appareil** — mobile seul ? Souvent un problème de rendu.
- **Par pays** — un seul marché ? Hreflang, ou concurrent local.
- **Par type de page** — les fiches produit, ou le blog ?

Cette étape élimine la moitié des hypothèses en dix minutes.

## Étape 3 — L'arbre de décision

### Les impressions ont chuté, la position est stable
→ **La demande a baissé** (saisonnalité, tendance, fin d'un pic d'actualité),
ou **la SERP a changé** (un AI Overview est apparu, une feature vous a
poussé plus bas dans la page).

Vérifiez : la requête déclenche-t-elle un AI Overview aujourd'hui ?
Si oui, votre position 3 vaut désormais ce que valait une position 8.

### La position a chuté
→ Perte de classement. Cherchez dans cet ordre :

1. **Technique** — la page est-elle toujours indexée ? Testez-la dans
   l'inspection d'URL. `noindex` ajouté par erreur, blocage robots.txt,
   canonical modifiée, 404, migration mal faite, certificat expiré.
2. **Contenu modifié** — quelqu'un a-t-il réécrit ou raccourci la page ?
   Comparez avec l'Internet Archive. Une refonte de design qui supprime du
   texte est une cause extrêmement fréquente et invisible.
3. **Perte de liens** — des backlinks ont-ils disparu ? (Ahrefs, liens
   perdus sur la période)
4. **Concurrence** — qui a pris votre place ? Qu'a-t-il de plus ?
5. **Mise à jour Google** — si la date colle et que rien d'autre n'explique.

### Les clics ont chuté, impressions et position stables
→ **Problème de CTR.** Causes : AI Overview qui capte le clic, un concurrent
a un snippet plus attractif, votre title/meta a été réécrit par Google, une
feature SERP s'est intercalée.

Correctif : réécrire title et meta. C'est peu coûteux et l'effet est rapide.

## Étape 4 — Si c'est un core update

Ce qu'il faut savoir, et dire clairement :

- Ce n'est **pas une pénalité**. C'est une réévaluation de ce que Google
  considère comme le meilleur résultat.
- Il n'y a **rien à « corriger »** au sens technique. Modifier des balises
  ne fera rien.
- La récupération passe par une amélioration réelle de la qualité, et se
  matérialise souvent lors du **core update suivant** (3 à 6 mois).
- Les réactions précipitées aggravent la situation.

Ce qui fonctionne : identifier les pages qui ont le plus chuté, les comparer
honnêtement à celles qui les ont remplacées, et combler l'écart réel —
profondeur, expérience de première main, preuves, auteur identifié,
fraîcheur, utilité concrète.

Ce qui ne fonctionne pas : supprimer massivement des pages, réécrire tout
le site avec de l'IA, changer de domaine, désavouer des liens au hasard.

## Étape 5 — Le cas des AI Overviews

Nouveau et sous-diagnostiqué. Symptôme typique : impressions stables ou en
hausse, clics en baisse continue, sur des requêtes informationnelles.

Vérification : vos 20 requêtes principales déclenchent-elles un AI Overview ?
Y êtes-vous cité ?

Si l'AI Overview est là et que vous n'y êtes pas, le sujet n'est plus le
ranking mais la **citabilité**. Voir `/seo geo`.

Si vous y êtes cité, une partie du trafic perdu est structurelle : le clic
ne reviendra pas. Il faut déplacer l'effort vers des requêtes à plus faible
risque zero-click (transactionnelles, locales, comparatives).

## Étape 6 — Le plan de récupération

1. **Corriger le technique immédiatement** — c'est la seule catégorie où
   l'effet est rapide et certain
2. **Restaurer ce qui a été perdu** — contenu supprimé, liens cassés,
   redirections manquantes
3. **Améliorer les pages les plus touchées** — celles qui portaient le plus
   de trafic, une par une
4. **Mesurer avant d'en faire plus** — attendez 3-4 semaines entre deux
   séries de modifications, sinon vous ne saurez jamais ce qui a agi

## Livrables

- `DIAGNOSTIC-CHUTE.md` — date, segment touché, cause identifiée, niveau de
  certitude (annoncez votre incertitude, elle fait partie du diagnostic)
- `pages-touchees.csv` — avant/après par page
- `PLAN-RECUPERATION.md` — par ordre, avec l'échéance de mesure de chacun
