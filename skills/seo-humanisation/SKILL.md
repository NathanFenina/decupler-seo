---
name: seo-humanisation
description: >
  Dernière passe d'écriture sur un texte français : repère et retire les tics
  d'écriture générée (vocabulaire de modèle, triades, « ce n'est pas X, c'est
  Y », tirets cadratins, puces en gras, rythme uniforme, sources vagues, ton
  promo, conclusions-résumés) sans toucher au fond ni inventer quoi que ce
  soit, en alignant le texte sur le style mesuré du client
  (memoire/style.md). Score des tics sur 100 par script, signaux ligne par
  ligne, comparatif avant / après qui bloque tout chiffre apparu. Appelée en
  fin de seo-redaction et sur tout texte existant. Déclencher sur
  "humanise", "humaniser", "ça sonne IA", "ça fait IA", "enlève les tics IA",
  "retire les tics d'écriture", "relis le style", "rends ce texte plus
  naturel", "détecteur IA", "détecteur d'IA", "texte trop robotique",
  "dé-IA-ise", "passe d'humanisation", "Pangram", "score Pangram",
  "passer les détecteurs".
---

# Humanisation : la dernière passe avant de rendre un texte

Un texte peut être juste, sourcé, bien construit, et sonner quand même comme
un modèle de langage : les mêmes mots, la même cadence, les mêmes
conclusions. Le lecteur décroche, le client ne s'y reconnaît pas. Cette passe
retire ces tics et rapproche le texte de la façon d'écrire du client.

Elle ne fait que ça. Elle ne rajoute pas de contenu, ne change pas le plan,
ne corrige pas le référencement.

## Le principe : la forme change, le fond reste

1. **Chaque information du texte d'origine survit.** On peut couper une
   phrase creuse, fusionner deux paragraphes, transformer une liste en
   phrases. On ne perd aucun fait, aucun chiffre, aucune nuance.
2. **Zéro fait inventé.** Pas de chiffre, de nom, de date, de client, de
   citation ni d'anecdote qui n'était pas dans le texte ou dans la mémoire
   du projet (`memoire/faits.md`, `memoire/marque.md`). Rendre un texte
   « vivant » avec une anecdote inventée, c'est mentir au lecteur.
3. **Un passage creux sans matière** ne se maquille pas : on le coupe, ou on
   pose un marqueur `[À COMPLÉTER : un exemple daté de chantier]` pour que
   le client fournisse la matière. `controle_contenu.py` bloque la
   publication tant que le marqueur reste.
4. **La voix du client prime sur ce catalogue.** Si ses propres pages
   emploient un tic de la liste (des tirets, des questions, un mot), on le
   garde au même dosage.

## Où elle se place

| Étape | Qui | Rôle |
|---|---|---|
| Écrire | `seo-redaction` (« Le style : ne pas écrire comme une IA ») | les règles d'écriture, appliquées pendant la rédaction |
| Mesurer la voix | `style_maison.py` → `memoire/style.md` | la cible : rythme, adresse, personne, expressions de la maison |
| **Relire et nettoyer** | **`seo-humanisation`** | mesure les tics restants, réécrit, vérifie que le fond est intact |
| Bloquer | `controle_contenu.py` | promesses, chiffres sans source, textes provisoires |

`seo-redaction` dit comment écrire ; cette passe vérifie ce qui a été écrit.
Elle s'applique aussi à tout texte existant : page client avant
optimisation, contenu livré par un rédacteur, texte collé dans la
conversation. Fiche pratique : SOP 4 (`docs/sop/04-redaction.md`).

## La cible : le style de la maison

Avant de réécrire, lire `memoire/style.md` (mesuré par `style_maison.py`) :

- **Rythme** : la phrase moyenne du texte à ±3 mots de celle de la maison,
  avec la même part de phrases courtes et longues. Le script affiche l'écart.
- **Adresse et personne** : vous ou tu, nous ou impersonnel, sans exception.
- **Expressions** : reprendre celles qui portent la marque, pas celles du
  catalogue ci-dessous.
- **Section « Lecture »** : registre, traits de voix, à faire, à éviter.

Sans `memoire/style.md` : `memoire/marque.md` et `projet.ton` de la config.
Un texte « humain » générique n'est pas l'objectif ; un texte que le client
reconnaît comme le sien, si.

## Procédure

### 1. Mesurer

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/humanisation.py" contenus/<slug>.md
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/humanisation.py" page.html --json   # pour un traitement
```

Le script lit un `.md`, un `.html` (balises retirées) ou un `.txt`, ou
l'entrée standard (`-`). Il rend un **score de tics sur 100** (0 = aucun tic
relevé ; 15 ou moins faible, jusqu'à 35 modéré, au-delà élevé), le détail
par famille, et la liste des **signaux avec leur ligne et leur extrait** :
c'est la liste de travail.

### 2. Réécrire, paragraphe par paragraphe

Pour chaque paragraphe signalé :

1. Dire en une phrase ce que le paragraphe apporte. S'il n'apporte rien,
   le couper (ou marqueur `[À COMPLÉTER : …]` si l'idée est utile mais
   vide).
2. Le réécrire **en entier** autour de cette idée, dans le style de la
   maison. Remplacer un mot signalé par un synonyme ne suffit pas : la
   cadence et la structure restent celles d'un modèle.
3. Relire à voix haute. Se poser deux questions : qu'est-ce qui sonne
   encore généré ? Ai-je ajouté ou perdu une information ?

On ne touche pas : aux citations, aux noms propres, aux termes métier
validés (`memoire/marque.md`), aux mots-clés ciblés par le brief (leur
nombre d'occurrences est réglé par `seo-redaction`), aux blocs de code, au
front matter, aux liens.

### 3. Re-mesurer, avant / après

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/humanisation.py" --avant v1.md --apres contenus/<slug>.md --seuil 25
```

Le comparatif donne le score et chaque famille avant et après, la variation
du nombre de mots, et compare **les nombres** des deux versions : un nombre
présent après et absent avant fait échouer la commande (code 1), un nombre
disparu est signalé. Une baisse de plus de 30 % des mots est signalée aussi :
vérifier qu'aucune information n'est partie avec le remplissage.

`--seuil N` renvoie le code 1 si le score dépasse N : utilisable dans une
routine ou dans les commandes de contrôle. **25** est le seuil conseillé
pour un contenu à publier. Ne pas courir après 0 : un texte correct qui
garde deux « essentiel » et une énumération en trois est un texte normal.

### 3 bis. Contrôle par un détecteur externe : Pangram (facultatif)

`humanisation.py` mesure des tics ; il ne dit pas comment un détecteur d'IA
lira le texte. Quand le client le demande (éditeur, école, plateforme qui
filtre), on ajoute une mesure Pangram après la réécriture :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pangram.py" contenus/<slug>.md --cout        # mots et coût, sans appel
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pangram.py" contenus/<slug>.md --seuil 0.2
```

Le script rend la part du texte jugée IA, assistée par IA et humaine, puis
les **passages à reprendre avec leur ligne**, dont ceux que Pangram
reconnaît comme passés dans un outil de reformulation (« humanisés »).
`--seuil 0.2` renvoie le code 1 si IA + assisté dépasse 20 %.

- Un passage signalé se reprend comme à l'étape 2 : l'idée, puis la phrase
  réécrite en entier dans la voix de la maison. Jamais un « humaniseur »
  automatique : Pangram les détecte, et ils abîment le sens.
- Pangram ne fait que mesurer. Pas plus de deux allers-retours : si un
  passage reste signalé, c'est souvent qu'il manque de matière propre au
  client (exemple, chiffre de `memoire/faits.md`) ; on pose un marqueur
  `[À COMPLÉTER : …]` plutôt que de tourner la phrase dans tous les sens.
- Le texte part chez un tiers : pas sur un contenu confidentiel sans
  l'accord du client. Clé `PANGRAM_API_KEY`, environ 0,05 $ les 100 mots
  (tarif public, à vérifier).
- Un score Pangram bas n'est ni une garantie de qualité ni un critère
  Google : c'est une contrainte du client, pas un objectif SEO.

### 4. Rapport

À rendre avec le texte :

- score avant → après, et les familles qui ont le plus baissé ;
- si mesuré, la part IA + assisté selon Pangram, avant → après ;
- ce qui a été coupé (et pourquoi : redite, phrase creuse) ;
- les marqueurs `[À COMPLÉTER : …]` posés, avec la question à poser au
  client ;
- les signaux laissés volontairement (voix de la maison, terme métier) ;
- la confirmation « mêmes chiffres avant et après ».

## Catalogue des marqueurs, en français

Le script les cherche dans `config/marqueurs-ia-fr.json`. Aucun n'est une
preuve à lui seul : c'est l'accumulation qui signe un texte non relu.

### 1. Vocabulaire de modèle

« crucial », « essentiel », « incontournable », « véritable », « en somme »,
« en définitive », « il est important de noter », « dans un monde où »,
« à l'ère du », « plongeons », « levier », « booster », « optimiser » à
toutes les sauces, « écosystème », « synergie », « jouer un rôle clé »,
« tirer parti », « exploiter tout le potentiel », « s'inscrit dans »,
« en outre », « force est de constater ».

> **Avant** : Il est crucial de comprendre que l'isolation joue un rôle clé
> dans l'optimisation de votre confort. C'est un véritable levier
> incontournable.
>
> **Après** : Une maison mal isolée reste froide, même avec une chaudière
> neuve. Commencez par les combles.

(Le « après » ne dit rien de plus que l'« avant » : il le dit avec des mots
ordinaires. « Commencez par les combles » ne s'écrit que si la source le
dit ; sinon, `[À COMPLÉTER : par quoi commencer]`.)

### 2. Structures répétitives

- **Triades systématiques** : trois adjectifs, trois bénéfices, trois
  verbes, paragraphe après paragraphe (« rapide, fiable et efficace »).
- **« Ce n'est pas X, c'est Y »**, « non seulement… mais aussi », « il ne
  s'agit pas de… mais de… ».
- **Questions rhétoriques en série** : « Vous voulez plus de clients ? Vous
  cherchez à vous démarquer ? »
- **Conclusions-résumés** : un dernier paragraphe qui répète le texte.
- **Puces en gras partout** : « **Terme** : explication » à chaque ligne.
- **Titres en Majuscule Initiale À L'Anglaise** : « Comment Choisir Son
  Expert-Comptable ». En français, seule la première lettre et les noms
  propres prennent une majuscule.

> **Avant** : Le diagnostic n'est pas une simple formalité, c'est un
> véritable outil de décision. Rapide, précis et fiable, il vous aide à
> choisir, anticiper et économiser.
>
> **Après** : Le diagnostic sert à décider. Il dit quels travaux font
> baisser la facture et lesquels ne changent rien.

### 3. Ponctuation

- **Tirets cadratins (—)** pour relier deux idées, plusieurs fois par
  paragraphe. En français courant : virgule, deux-points, parenthèses ou
  point.
- **Deux-points en cascade** : « Résultat : un constat : il faut agir. »
- **Emojis** dans un contenu éditorial (🚀, ✅, 💡).

> **Avant** : Le devis — souvent négligé — est pourtant la clé : sans lui,
> rien n'est possible 🚀
>
> **Après** : On néglige souvent le devis. Sans lui, impossible de comparer
> deux artisans.

### 4. Rythme

Phrases de longueur identique (15 à 20 mots, sujet-verbe-complément),
paragraphes de taille identique (trois phrases, partout). Le script mesure
l'écart-type de la longueur des phrases : plus il est faible, plus la
lecture devient mécanique.

> **Avant** : Le chauffage représente une part importante de la facture.
> L'isolation permet de réduire cette part de façon durable. Les aides
> publiques permettent de financer une partie des travaux.
>
> **Après** : Le chauffage pèse lourd sur la facture. L'isolation la fait
> baisser durablement, et une partie des travaux peut être financée par
> les aides publiques, sous conditions de revenus et de matériaux.

(La précision « sous conditions » ne s'ajoute que si elle figure dans la
source ou dans `memoire/faits.md`.)

### 5. Flou

- **Sources vagues** : « selon les experts », « des études montrent »,
  « il est largement admis ».
- **Chiffres ronds sans source** : « 90 % des entreprises… ».
- **Superlatifs** : « le meilleur », « sans précédent », « inégalé »,
  « ultime ».

> **Avant** : Selon les experts, 80 % des sites perdent des clients à cause
> de leur lenteur. C'est la meilleure optimisation possible.
>
> **Après** : Un site lent perd des visiteurs avant même l'affichage.
> [À COMPLÉTER : chiffre sourcé et daté, ou retirer]

Un chiffre vague ne se « corrige » pas par un chiffre précis inventé : on
le source (`memoire/faits.md`) ou on le retire.

### 6. Ton

- **Promo** : « n'hésitez pas », « idéal pour », « à couper le souffle »,
  « un véritable atout », « expérience unique », points d'exclamation.
- **Enthousiasme forcé** sur un sujet qui ne s'y prête pas.
- **Précautions réflexes** : « il peut être intéressant de », « cela
  pourrait permettre de », « dans une certaine mesure », « potentiellement ».

> **Avant** : N'hésitez pas à nous contacter ! Il peut être intéressant de
> réaliser un audit, qui pourrait potentiellement permettre d'identifier des
> pistes d'amélioration.
>
> **Après** : Un audit montre ce qui freine le site. Écrivez-nous pour le
> programmer.

Une précaution utile (une limite réelle, une condition légale) se garde.

### 7. Ouvertures et fermetures génériques

« Dans un monde où… », « À l'ère du numérique… », « De nos jours… »,
« Vous êtes-vous déjà demandé… ? » en ouverture ; « En conclusion »,
« En résumé », « Vous l'aurez compris » et un H2 « Conclusion » en fin.

> **Avant** : Dans un monde où le numérique est en constante évolution, la
> visibilité en ligne est devenue essentielle pour les entreprises.
>
> **Après** : Vos clients cherchent un artisan sur leur téléphone, souvent
> le soir. Si votre fiche n'apparaît pas, ils appellent le suivant.

(Ouvrir sur la situation du lecteur décrite dans le brief ou dans
`memoire/marque.md`, pas sur une scène imaginée.)

## Ce qu'on ne corrige pas

- Un mot du catalogue employé une fois, à sa place.
- Une énumération qui énumère vraiment trois choses.
- Le style du client quand il diffère du catalogue : ses pages font foi.
- Une expression citée entre guillemets, un titre d'ouvrage, un nom propre
  (le script ignore déjà ce qui est entre guillemets).
- Une précision juridique, une limite, une mise en garde utile.
- Un texte simplement sobre : la sobriété n'est pas un tic.

### Adapter les marqueurs à un projet

`config/marqueurs-ia-fr.json` appartient à la méthode (remplacé à chaque
synchronisation). Un projet ajoute ses propres marqueurs, ou ignore ceux qui
font partie de sa voix, dans `memoire/marqueurs-ia.json` :

```json
{
  "ignorer": ["levier", "écosystème"],
  "ajouter": {"vocabulaire": ["\\bsolution clé en main\\b"]},
  "familles_ignorees": ["ponctuation"]
}
```

Chaque exception se justifie dans `memoire/decisions.md` (ex. « le client
emploie des tirets cadratins dans toutes ses pages »).

## Honnêteté : ce que cette passe promet, et ce qu'elle ne promet pas

- **Les détecteurs d'IA sont peu fiables.** Ils produisent des faux
  positifs (des textes humains notés « IA », en particulier ceux de
  personnes qui écrivent dans une langue qui n'est pas la leur) et des faux
  négatifs. OpenAI a retiré son propre classifieur en 2023 pour manque de
  précision. Un score de détecteur n'est ni une preuve ni un objectif.
- **On ne promet jamais un texte « indétectable ».** Ni au client, ni dans
  un rapport. Le score du script mesure des tics d'écriture, pas l'origine
  d'un texte ; un score bas ne garantit rien face à un détecteur.
- **Google ne pénalise pas l'IA en soi.** Ses consignes publiques (Google
  Search Central, février 2023) visent le contenu sans valeur, produit en
  masse pour manipuler le classement, quelle que soit la façon dont il a été
  écrit. Un texte humanisé mais vide reste vide.
- **Le but est un texte meilleur**, reconnaissable comme celui du client.
  Retirer les tics améliore la lecture ; ça ne crée pas de valeur.
- **Le vrai levier, c'est l'information propre** : le gain d'information
  par rapport au top, l'expérience du client (cas, erreurs vues sur le
  terrain, chiffres de ses propres dossiers), ses données. C'est ce que ni
  un concurrent ni un modèle ne peuvent recopier. Quand la passe révèle un
  paragraphe sans rien de tout ça, le bon réflexe est le marqueur
  `[À COMPLÉTER : …]` et une question au client, pas une reformulation.

## Livrables

- Le texte réécrit, au même endroit que l'original (fichier ou bloc).
- Le comparatif `humanisation.py --avant … --apres …` (score, familles,
  chiffres identiques).
- Le rapport court décrit à l'étape 4, avec les questions au client.

## Source d'inspiration

Le catalogue s'inspire du skill [humanizer](https://github.com/blader/humanizer)
(licence MIT, Siqi Chen), lui-même tiré de la page Wikipédia « Signs of AI
writing » du WikiProject AI Cleanup. Les marqueurs, les exemples et le
script ont été réécrits pour le français et pour la méthode decupler-seo.
