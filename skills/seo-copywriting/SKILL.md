---
name: seo-copywriting
description: >
  Écrit ou réécrit une page commerciale (offre, service, formation, landing)
  qui convainc et convertit sans perdre le SEO : top 5 lu, gap sémantique du
  brouillon, bénéfices et scènes métier, preuves réelles, objections, CTA,
  score copywriting.py. Déclencher sur « copywriting », « plus vendeur »,
  « ça ne donne pas envie », « page qui convertit ». Pas pour un article →
  seo-redaction ; pas pour la seule passe anti-tics → seo-humanisation.
---

# Copywriting — une page qui donne envie d'appeler

Une page commerciale bien référencée qui ne donne pas envie d'appeler est un
coût. Une page vendeuse que Google ne montre pas aussi. Ce skill tient les
deux : il part de ce que montre le top 5, garde intact ce que le client
impose, et réécrit tout le reste pour que le lecteur se reconnaisse, voie le
résultat, croie la promesse et sache quoi faire ensuite.

**Sans projet configuré, sans données ni accès** : ne vous arrêtez pas sur
une question. Réécrivez le texte fourni avec la méthode ci-dessous, marquez
`[à compléter : …]` chaque preuve ou donnée du client qui manque, et dites en
fin de réponse ce que la version mesurée demanderait (SERP, faits, style).

## L'essentiel — ce qui ne se négocie pas

1. **Le texte imposé ne bouge pas.** Programme, objectifs, mentions
   obligatoires (Qualiopi, légales, financement), textes fournis par le
   client : mot pour mot. Seules retouches permises : orthographe, tirets,
   listes d'exemples ouvertes. Le copywriting travaille **autour** : accroche,
   bénéfices, exemples, preuves, transitions, appels à l'action.
2. **Lire le top 5 avant d'écrire**, et mesurer le gap sur le brouillon
   (`serp_concurrents.py --brouillon`). Pas d'argument « de mémoire ».
3. **Chaque bloc répond à « et alors, pour moi ? »** : le bénéfice avant la
   fonctionnalité, une scène métier précise avant une généralité.
4. **Zéro preuve inventée** : ni chiffre, ni témoignage, ni logo, ni
   résultat. Les preuves viennent de `memoire/faits.md` ; une preuve absente
   devient `[à compléter : …]`.
5. **Vendre en positif.** Une limite s'écrit comme une condition (« le
   chiffrage suit l'audit »), jamais comme l'argument (« nous ne promettons
   rien »). Au-delà de 6 négations pour 1 000 mots, le texte se vend par ce
   qu'il ne fait pas.
6. **Trois appels à l'action au moins** : un dans le haut de page, un après
   la preuve la plus forte, un en fin de page. Libellé = l'action du
   lecteur (« Demander un devis », « Échanger sur votre projet »).
7. **Zéro tiret cadratin**, aucun tic d'écriture générée (`seo-humanisation`).
8. **Contrôlé avant de rendre** : `copywriting.py` ≥ 80, `humanisation.py`
   sous 25, `controle_contenu.py` publiable, puis une relecture à voix haute
   avec la grille `references/grille-relecture.md`.

## Étape 1 — Le top 5 et le gap sémantique (10 minutes)

```bash
python3 .claude/decupler-seo/scripts/serp_concurrents.py --mot "<mot-clé principal>" \
    --url <URL finale> --brouillon contenus/pages/<page>.md --repli-dataforseo
```

Le script lit les 5 premières pages lisibles (une page bloquée cède sa place
à la suivante), puis compare le brouillon au top : termes présents sur au
moins la moitié du top et absents de la page, sujets de H2 récurrents,
questions « Autres questions posées », longueur, ton. Sans DataForSEO, voir
les replis documentés dans le script (Firecrawl, relevé manuel).

Lisez réellement `recherche/serp-<slug>-<date>-contenus.md`, puis remplissez
`recherche/benchmarks/<page>-copy.md` :

| À relever chez chaque concurrent | Pourquoi |
|---|---|
| La promesse du hero, mot pour mot | voir ce que le lecteur a déjà lu ailleurs, et dire mieux |
| Les 3 bénéfices mis en avant | trouver l'angle que personne ne prend |
| Les preuves (chiffres, références, labels, garanties) | savoir ce qu'il faut égaler avec nos **vraies** preuves |
| Les objections traitées (prix, durée, niveau, financement) | ne laisser aucune question sans réponse |
| Les CTA : nombre, places, libellés | caler notre parcours |
| Les termes du gap qui décrivent **vraiment** l'offre | les intégrer là où ils sont vrais, jamais en liste |

Un terme du gap n'entre que s'il est vrai pour le client : « débutant »
entre si la formation accueille des débutants, « CPF » n'entre pas si l'offre
n'y est pas éligible. Le gap est une liste de questions, pas de mots à caser.

## Étape 2 — La carte de persuasion (avant la première phrase)

Une demi-page, écrite dans le benchmark, qui sert de brief au texte :

- **Qui lit**, et ce qui l'inquiète avant d'acheter (les mots qu'il emploie :
  `memoire/marque.md`, avis, Reddit, questions des commerciaux).
- **La promesse en une phrase** : le résultat pour le lecteur, pas l'activité
  du prestataire. « Vos commerciaux préparent un rendez-vous en dix minutes »
  plutôt que « nous formons vos équipes à l'IA ».
- **Trois bénéfices**, chacun prouvé par un fait, un livrable ou une méthode.
- **Les preuves disponibles** (faits.md) et leur place : près des CTA.
- **Les objections**, avec la réponse du client : elles nourrissent la FAQ et
  les blocs de réassurance.
- **Ce qui distingue le client** du top 5, dit avec ses mots.
- **Le CTA principal et le CTA secondaire** (devis, échange, audit, appel).

## Étape 3 — Écrire bloc par bloc

Les formules, les banques de libellés et des exemples avant / après sont
dans `references/formules.md` : lisez-les avant d'écrire le hero.

- **Hero** : résultat pour le lecteur + pour qui + comment (format, durée,
  lieu) + une preuve courte + le CTA. Moins de 60 mots, adressé au lecteur,
  le mot-clé dans la première phrase.
- **Bénéfices** : caractéristique → avantage → bénéfice. Une scène métier par
  bénéfice (qui, quelle tâche, ce qui change). Les outils sont des exemples
  (« notamment », « entre autres »), la compétence est le sujet.
- **Contenu imposé** (programme, mentions) : intact, introduit par une phrase
  qui dit au lecteur ce qu'il y gagne.
- **Preuves** : labels, notes, volumes **sourcés**, méthode, équipe nommée.
  Toujours à côté d'un CTA, jamais regroupées en bas.
- **Objections** : en FAQ et dans le texte, réponses directes de 40 à 80 mots,
  la réponse dans la première phrase.
- **Rythme** : phrases de 14 à 18 mots en moyenne, une idée par phrase, des
  paragraphes de 2 à 4 phrases. Verbes d'action ; pas de « permet de », « afin
  de », « il est important de » : dire directement ce que le lecteur fait ou
  obtient.
- **SEO sans dommage** : mot-clé dans le title, le H1 et la première phrase ;
  entités et termes du gap là où ils sont vrais ; aucune répétition forcée.

## Étape 4 — Contrôler

```bash
python3 .claude/decupler-seo/scripts/copywriting.py <page> --section "Contenu" --marque "<marque>"
python3 .claude/decupler-seo/scripts/humanisation.py <page>
python3 .claude/decupler-seo/scripts/controle_contenu.py <page>
```

`copywriting.py` mesure les tirets, l'orientation lecteur (vous / nous), les
négations, le rythme, le ton explicatif, les promesses creuses, les CTA et
l'accroche, et liste les lignes à reprendre. Il ne juge pas la justesse d'un
argument : la grille de relecture (`references/grille-relecture.md`) le fait,
à voix haute, phrase par phrase.

Rendre : la page, le score avant / après, et les 3 arguments du top 5 que la
page bat désormais.

## Garde-fous

- **Ne jamais copier** un concurrent : on relève un angle, on écrit le sien.
- **Pas de fausse urgence ni de fausse rareté** (« plus que 2 places »), pas
  de superlatif invérifiable (« le meilleur », « n° 1 »).
- **Promesse réaliste** : un bénéfice recherché (« gagner du temps sur les
  comptes rendus ») plutôt qu'un résultat chiffré non prouvé.
- **Le style du client prime** (`memoire/style.md`, skill `projet-…`) : le
  copywriting ne remplace pas sa voix, il la rend plus nette.
