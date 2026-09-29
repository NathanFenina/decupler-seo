# Écrire en triplets — réécritures et gabarits

## Avant / après

**Avant** — agréable à lire, impossible à extraire :

> Chez nous, chaque dossier est unique. C'est pourquoi notre accompagnement
> s'adapte à votre situation, avec un tarif qui reste raisonnable et des
> délais maîtrisés. Il comprend bien sûr tout ce dont vous avez besoin pour
> être serein face à l'administration.

Aucun sujet nommé, aucun objet vérifiable. Un moteur IA n'en tire rien, et
un concurrent qui écrit « Le bilan annuel coûte 1 200 € HT » prend la
citation.

**Après** — mêmes idées, faits extractibles :

> Le bilan annuel d'Atlas Conseil coûte 1 200 € HT pour une TPE et dure
> trois semaines. Il comprend la liasse fiscale, les comptes annuels et
> l'approbation des comptes. La liasse fiscale désigne l'ensemble des
> formulaires joints à la déclaration de résultat.

Triplets extraits : Atlas Conseil (bilan annuel) — coûte — 1 200 € HT ;
— dure — trois semaines ; La liasse fiscale — désigne — l'ensemble des
formulaires… La deuxième phrase a un pronom : acceptable **après** une
phrase qui nomme le sujet, jamais en ouverture de section, jamais dans une
réponse de FAQ.

## Les tournures qui cachent le triplet

| Tournure | Problème | Réécriture |
|----------|----------|------------|
| « Il coûte 1 200 € » en début de section | Sujet perdu à l'extraction | « Le bilan annuel coûte 1 200 € HT » |
| « Cette solution permet de… » | Démonstratif : renvoie à une phrase d'avant | « Le logiciel de paie permet de… » |
| « Comptez environ 1 200 € » | Pas de sujet, valeur floue | « Le bilan annuel coûte 1 200 € HT » |
| « Un tarif accessible » | Pas d'objet vérifiable | Le montant, avec HT/TTC |
| « Quelques semaines » | Idem | « trois semaines » |
| « Le barème fiscal, ce mécanisme qui… » (phrase sans verbe principal) | Aucun prédicat | « Le barème fiscal classe les entreprises selon leur chiffre d'affaires » |
| Trois chiffres dans une phrase | Le moteur en garde un, au hasard | Une phrase par chiffre |
| « joue un rôle clé dans », « est au cœur de » | Prédicat vide | Le vrai verbe : exige, permet de, s'applique à |
| Une valeur différente selon la page | Contradiction : les moteurs citent l'une ou aucune | La valeur du registre, partout |

## Les prédicats que le script reconnaît

Le script normalise les formes (singulier/pluriel, français/anglais) vers un
prédicat canonique ; c'est ce qui permet de comparer deux pages.

| Canonique | Formes reconnues |
|-----------|------------------|
| est | est, sont, c'est, était, is, are |
| désigne | désigne, signifie, se définit comme, refers to, means |
| correspond à / consiste à | correspond à, consiste à / en |
| coûte | coûte, s'élève à, revient à, est facturé, costs |
| dure | dure, prend (anglais : takes, lasts) |
| représente / compte | représente, atteint / compte, emploie |
| permet de | permet de, permet aux, allows, enables, helps |
| propose / comprend | propose, offre / comprend, inclut, couvre, regroupe |
| s'applique à / s'adresse à | s'applique à, concerne / s'adresse à, est destiné à |
| exige | exige, impose, oblige, nécessite, requiert |
| dépend de, classe, mesure, remplace, accompagne, intervient, devient, doit | formes usuelles |
| est situé à / fondé en | est basé, situé, installé à / a été fondé, créé en |

Un prédicat hors de cette liste reste valable dans le texte : le script ne
le relèvera simplement pas comme triplet. La négation est gardée
(« n'est pas », « n'exige pas »). Une question n'affirme rien et n'est pas
relevée ; sa réponse, oui.

## Gabarit — la section du brief

```markdown
### Triplets à affirmer

| # | Sujet | Prédicat | Objet | Source | Où |
|---|-------|----------|-------|--------|----|
| 1 | Le bilan annuel d'Atlas Conseil | coûte | 1 200 € HT | triplets.csv (grille 2026) | Réponse directe |
| 2 | Le bilan annuel d'Atlas Conseil | dure | trois semaines | triplets.csv | Réponse directe |
| 3 | La liasse fiscale | désigne | l'ensemble des formulaires joints à la déclaration de résultat | impots.gouv.fr | H2 « Ce que comprend le bilan » |
| 4 | Atlas Conseil | est situé à | Lyon | triplets.csv (mentions légales) | Intro + FAQ |

Entités : Expertise comptable (Q…, vérifié) · Lyon (Q…, vérifié) ·
Liasse fiscale (DefinedTerm, sans QID) · Bilan comptable → `about`.
Nouveaux faits à sourcer avant rédaction : aucun.
```

Règles : 3 à 8 triplets ; chaque valeur vient de `triplets.csv` ou d'une
source nommée à inscrire ; les triplets 1 et 2 sont ceux de la réponse
directe. Un triplet sans source n'entre pas dans le brief.

## Gabarit — FAQ

Chaque réponse s'ouvre par le triplet, sujet nommé, puis nuance :

> **Combien coûte un bilan annuel ?**
> Le bilan annuel d'Atlas Conseil coûte 1 200 € HT pour une TPE au régime
> réel simplifié. Le montant augmente avec le nombre d'écritures : au-delà
> de 1 500 pièces par an, le cabinet établit un devis.

La même phrase d'ouverture sert de `text` à la `Answer` du `FAQPage` : le
balisage dit exactement ce que dit la page.

## Gabarit — llms.txt

```markdown
## Faits clés
- Atlas Conseil est un cabinet d'expertise comptable situé à Lyon.
- Atlas Conseil accompagne les TPE et PME du Rhône.
- Le bilan annuel d'Atlas Conseil coûte 1 200 € HT et dure trois semaines.

## Pages de référence
- [Bilan annuel](https://www.atlas-conseil.example/offres/bilan-annuel/) : le bilan annuel d'Atlas Conseil coûte 1 200 € HT et dure trois semaines.
```

Les phrases sont celles du registre, mot pour mot. Elles se génèrent
depuis `triplets.csv` (lignes dont le sujet est la marque) plutôt que de se
réécrire à la main.

## Le contrôle rapide d'une page

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/triplets.py" extraire page.html
```

Lisez trois choses :

1. **La colonne Pos.** — les faits clés sont-ils sous 200 mots ?
2. **« Sujet non nommé en tête de page »** — chaque phrase listée est à
   réécrire avec son sujet.
3. **« Phrases à plusieurs faits »** — à couper.
