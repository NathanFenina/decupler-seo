---
name: seo-meta-serp
description: >
  Optimise les balises title et meta description pour le taux de clic et la
  citation par les moteurs IA : 3 variantes de title, 2 de meta, comptage
  pixel, aperçu SERP simulé, recommandation argumentée. Traite une page ou un
  lot. Déclencher sur "title", "balise title", "meta description", "améliorer
  le CTR", "réécris mes titles", "snippet", "aperçu SERP", "mes pages ont un
  mauvais taux de clic", "optimiser les métas".
---

# Title et meta description — le levier le moins cher du SEO

Une réécriture de title prend dix minutes et produit un effet mesurable en
deux semaines. Sur une page en position 6 avec 5 000 impressions, passer de
2 % à 4 % de CTR, c'est 100 clics par mois pour dix minutes de travail.

## Où chercher les pages à traiter

Search Console, 90 jours : les pages en position 3-10 dont le CTR est
**inférieur à la moitié du CTR attendu** pour leur position. Ce sont
celles-là, et pas les autres.

CTR attendu, ordre de grandeur : pos. 1 → 27 % · 2 → 15 % · 3 → 11 % ·
4 → 8 % · 5 → 6 % · 6-10 → 2-5 %.

Nuance 2026 : sur les requêtes déclenchant un AI Overview, tous les CTR
s'effondrent. Comparez vos pages entre elles plutôt qu'à cette table.

## Le title

**Contraintes techniques**
- 50-60 caractères. Google coupe autour de **580 px**, pas à un nombre fixe
  de caractères : les majuscules, les M et les W prennent plus de place que
  les i et les l. Un titre en capitales est tronqué bien plus tôt.
- Mot-clé principal dans les **3 premiers mots** — c'est là que l'œil se pose
- Marque en fin, séparée par un tiret, et seulement si elle apporte quelque
  chose. Sur un site inconnu, elle prend de la place pour rien.
- Unique sur tout le site

**Ce qui fait cliquer** — un bénéfice, une précision chiffrée, une contrainte
levée. « Devis en 24 h », « 12 modèles comparés », « sans engagement ».

**Trois variantes à produire systématiquement :**

| Angle | Principe | Exemple |
|-------|----------|---------|
| Mot-clé d'abord | Sûr, capte l'intention | `Logiciel de facturation : 12 solutions comparées (2026)` |
| Bénéfice d'abord | Meilleur CTR sur requêtes commerciales | `Facturez en 2 min : le comparatif de 12 logiciels` |
| Curiosité | Fort CTR, à manier avec prudence | `Le logiciel de facturation que 80 % des TPE choisissent à tort` |

L'angle curiosité ne doit jamais promettre ce que la page ne tient pas. Un
clic suivi d'un retour immédiat vers la SERP est pire que pas de clic.

Google réécrit environ 60 % des titles. Il le fait surtout quand le title
est trop long, bourré de mots-clés, ou déconnecté du H1. Un title honnête,
aligné sur le contenu, est repris tel quel.

## La meta description

Elle n'est pas un facteur de classement. Elle est un **argumentaire de
vente de 155 caractères**, et elle influence le CTR, qui compte.

Structure qui fonctionne :
- **~90 premiers caractères** : la promesse, avec le mot-clé (il est mis en
  gras dans la SERP quand il correspond à la requête)
- **~65 derniers** : la différenciation ou l'appel à l'action

Deux variantes à produire : une professionnelle et factuelle, une plus
conversationnelle. Selon le secteur et l'audience, l'écart de CTR entre les
deux est significatif.

Erreurs fréquentes : dupliquer la meta sur tout le site, y recopier le
title, dépasser 170 caractères, écrire une phrase creuse (« Découvrez nos
services de qualité »).

## L'aperçu SERP

Simulez le rendu, desktop et mobile — le mobile coupe plus tôt :

```
┌────────────────────────────────────────────────────┐
│ exemple.com › logiciels › facturation              │
│ Logiciel de facturation : 12 solutions comparées   │
│ Comparatif de 12 logiciels de facturation testés   │
│ sur 6 mois. Prix, fonctionnalités, conformité 2026 │
│ — et lequel choisir selon la taille de votre…      │
└────────────────────────────────────────────────────┘
   58 car. · 154 car. · ✓ ni l'un ni l'autre tronqué
```

## Le volet IA

Un snippet bien construit sert aussi à la citation par les moteurs IA. Notez
pour chaque proposition :

- Le title énonce-t-il clairement de quoi traite la page ? (un LLM s'en sert
  pour décider de la pertinence)
- La meta contient-elle une information factuelle extractible plutôt qu'une
  formule marketing ?
- Le couple title/meta est-il cohérent avec le H1 et la réponse directe ?

## Traitement en lot

Sur un lot de pages, produisez un CSV : URL, title actuel, title proposé,
longueur, meta actuelle, meta proposée, longueur, justification.

Si WordPress ou Webflow est branché et le mode autonomous actif,
l'application peut être directe — les titles et metas sont réversibles sans
risque, contrairement au contenu. Sauvegardez quand même l'état d'origine.

## Mesurer

Notez la date de modification et le CTR de départ. Reprenez à J+21 : c'est
le délai pour que Google recrawle et que les impressions s'accumulent
suffisamment. Avant, le bruit domine.

## Livrables

- `METAS.md` — variantes, aperçus, recommandations
- `metas.csv` — pour un traitement en lot
- `baseline-ctr.json` — pour mesurer dans trois semaines
