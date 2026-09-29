---
name: seo-cocon-semantique
description: >
  Conçoit l'architecture éditoriale d'un site : silos thématiques, pages
  piliers et satellites, cocon sémantique, plan de maillage entre les niveaux,
  et calendrier de production. Déclencher sur "cocon sémantique", "silo",
  "architecture éditoriale", "topic cluster", "page pilier", "structurer mon
  contenu", "plan de contenu", "arborescence éditoriale", "comment organiser
  mes articles", "stratégie de contenu".
---

# Cocon sémantique — construire une autorité de sujet

Google ne classe plus des pages isolées, il évalue la **couverture d'un
sujet par un site**. Trente articles éparpillés valent moins que quinze
articles qui se répondent.

## Le modèle

```
        PAGE PILIER  ── le sujet dans son ensemble
         (transactionnelle ou guide de référence)
              │
    ┌─────────┼─────────┐
    │         │         │
  SATELLITE SATELLITE SATELLITE   ── une question précise chacune
    │         │         │
   sous-     sous-     sous-      ── longue traîne
   pages     pages     pages
```

Trois règles, et elles ne se négocient pas :

1. **Chaque satellite lie vers son pilier.** C'est ainsi que l'autorité
   remonte vers la page qui vend.
2. **Le pilier lie vers tous ses satellites.** C'est ainsi qu'ils sont
   découverts et crawlés.
3. **Les satellites d'un même silo se lient entre eux** quand c'est
   pertinent. Pas de lien entre silos différents sans raison éditoriale
   réelle — ça dilue le signal thématique.

## Étape 1 — Définir les silos

Un silo = un sujet sur lequel vous voulez être une référence, et qui a un
lien direct avec ce que vous vendez.

Partez de la proposition de valeur (`config` → `projet.proposition_valeur`)
et des clusters issus de `/seo motscles`.

Combien de silos ? **3 à 5 maximum au départ.** Un site qui ouvre 12 silos
avec 2 articles chacun n'est une référence sur rien. Mieux vaut dominer un
sujet et en ouvrir un second ensuite.

## Étape 2 — La page pilier

Elle vise la requête principale du silo — la plus large, la plus
concurrentielle. Caractéristiques :

- Couvre le sujet dans son ensemble, mais **sans épuiser** les satellites :
  chaque sous-partie donne l'essentiel puis renvoie vers l'article dédié
- 2 000 à 4 000 mots selon le sujet
- Structure claire, sommaire, réponse directe en haut
- URL courte et proche de la racine : `/plomberie/`, pas `/blog/2024/03/…`
- C'est la page qui doit recevoir le plus de liens internes du silo

Si le silo est commercial, le pilier est votre **page de service ou de
catégorie**, pas un article de blog. C'est un choix structurant : c'est elle
qui doit capter l'autorité, parce que c'est elle qui convertit.

## Étape 3 — Les satellites

Un satellite = une question précise, une intention unique, une réponse
complète.

Sources : People Also Ask, Reddit, questions posées par vos clients,
suggestions Google, gaps concurrents.

Par satellite : la requête cible, l'intention, l'angle, le format
(guide / comparatif / tutoriel / étude de cas / FAQ), 800-1 800 mots, et le
lien remontant vers le pilier avec une ancre descriptive.

**8 à 15 satellites par silo.** En dessous de 5, le silo n'existe pas aux
yeux de Google.

## Étape 4 — Le plan de maillage

Le plan doit être exécutable ligne par ligne :

| Depuis | Vers | Ancre | Emplacement |
|--------|------|-------|-------------|
| /plomberie/fuite-eau | /plomberie/ | dépannage plomberie à Lyon | intro, 2e paragraphe |
| /plomberie/ | /plomberie/fuite-eau | que faire en cas de fuite d'eau | section « Nos interventions » |
| /plomberie/fuite-eau | /plomberie/prix-depannage | tarifs d'un dépannage | conclusion |

Règles d'ancres :
- Descriptives, jamais « cliquez ici » ni l'URL nue
- Variées : ne répétez pas la même ancre exacte 30 fois vers la même page
- Dans le corps du texte, pas seulement dans un bloc « articles liés » en
  pied de page — les liens contextuels pèsent nettement plus lourd

## Étape 5 — L'ordre de production

Contre-intuitif mais efficace : **les satellites d'abord, le pilier ensuite.**

Le pilier vise la requête la plus difficile. Il a besoin de l'autorité que
lui envoient les satellites pour ranker. Publier le pilier seul, c'est le
condamner à stagner en page 3 pendant des mois.

Séquence : 4-5 satellites → pilier → maillage complet → satellites restants
au fil de l'eau.

## Étape 6 — Le calendrier

| Semaine | Publication | Silo | Maillage à poser |
|---------|-------------|------|------------------|
| S1 | Satellite : que faire en cas de fuite | Plomberie | → pilier (à venir) |
| S2 | Satellite : prix d'un dépannage | Plomberie | → S1 |
| S3 | Satellite : choisir son plombier | Plomberie | → S1, S2 |
| S4 | **Pilier : plombier à Lyon** | Plomberie | → S1, S2, S3 |
| S5 | Reprise du maillage : S1-S3 → pilier | Plomberie | — |

Un rythme tenable battra toujours un plan ambitieux abandonné au bout de
trois semaines. Une publication par semaine, tenue six mois, construit un
silo. Cinq par semaine pendant un mois puis rien ne construit rien.

## Attention aux dérives

- **Cannibalisation** : deux satellites qui visent la même intention se
  concurrencent. Si le top 10 de leurs requêtes est identique à plus de
  60 %, ce sont deux versions de la même page. Fusionnez.
- **Pilier fantôme** : un pilier qui n'est qu'un sommaire de liens ne
  ranke pas. Il doit avoir sa valeur propre.
- **Silo décoratif** : un silo qui ne mène à aucune conversion est un centre
  de coût. Chaque silo doit avoir un chemin vers ce que vous vendez.

## Livrables

- `COCON.md` — les silos, piliers, satellites, avec les requêtes cibles
- `maillage.csv` — le plan de liens, exécutable ligne par ligne
- `CALENDRIER.md` — l'ordre de production, daté

Enchaînez : `/seo brief <requête>` pour chaque page du plan.
