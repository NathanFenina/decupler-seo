# Matière réelle — la page qui a de la vie

Une page bien écrite, bien structurée, aux bonnes couleurs, peut rester
**plate** : une colonne de texte, des cartes, un tableau, et rien qu'on ait
envie de regarder. Le client le dit en une phrase : « ça manque de vie ;
screenshots, logos, exemples, photos ». La correction n'est pas décorative.
C'est de la **matière réelle** : ce qui montre que le travail existe, que
les outils sont vrais, que l'exemple a été pensé pour ce lecteur.

## La règle

**Au moins trois éléments de matière réelle par page**, de deux types
différents au moins, chacun avec un `alt` (ou un `aria-label`) et une
légende qui dit ce qu'il prouve. Elle s'applique à toute page neuve
(service, locale, article, landing) et à toute refonte. Elle se décide au
brief, avec le plan d'images (`images.md`), pas après la rédaction.

Contrôle automatique, hors ligne :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit_images.py" page-<slug>.html --matiere 3 --strict
```

Est compté : chaque `<figure>` ; chaque élément marqué `data-matiere="…"`
(un bloc avant / après, une capture sans figure) ; chaque `<svg role="img">`
hors d'une figure. Une `<figure>` sans `<figcaption>` est signalée.

## Les six types

| Type | Ce que c'est | D'où ça vient |
|---|---|---|
| **Logos des outils et plateformes cités** | le moteur, la régie, le CMS, l'outil de mesure dont parle la page ; chacun avec une ligne qui dit à quoi il sert ici | site officiel de l'éditeur (kit presse) ou Wikimedia Commons, téléversé dans la médiathèque du site |
| **Captures réelles** | un résultat déjà publié (Search Console, régie, outil d'analyse), une SERP relevée, l'interface du produit ou de l'outil maison, un échange avec un moteur IA | captures des études de cas du client, rendu navigateur d'une page publique, relevé d'API mis en forme ; jamais retouchées |
| **Exemple avant / après** | un title et sa description, une fiche d'établissement, une annonce, un paragraphe d'ouverture, un extrait de code | écrit pour la page, **étiqueté comme exemple** (« cette entreprise n'existe pas ») ou tiré d'un cas réel nommé |
| **Photo réelle** | le lieu d'une page locale, l'auteur, l'équipe, un chantier | photos du client ; Wikimedia Commons avec auteur et licence affichés (`photos_libres.py`) |
| **Schéma tiré des données** | frise datée, déroulé d'une mission, barres ou répartition d'un chiffre sourcé, grille de points | SVG ou HTML rendu à partir des chiffres de la source des faits du projet, jamais d'un chiffre ajouté pour le schéma |
| **Logos clients réels** | une bande de clients qui ont accepté d'être nommés | médiathèque du client, accord écrit dans la mémoire du projet |

Une page de service type : une bande de logos d'outils, une capture de
résultat, un avant / après, plus la photo de l'auteur. Une page locale :
la photo de la ville, une capture, un exemple écrit pour le métier de la
ville. Un article : une capture ou un schéma par 600 à 800 mots.

## Les interdits

- **Une image générée ne représente jamais** une personne de l'équipe, un
  client, un lieu réel, ni une interface présentée comme une capture.
- **Aucun chiffre dans un visuel** qui ne soit pas dans la source des faits
  du projet. Une capture publiée peut montrer d'autres valeurs : la légende
  ne cite que celles qui sont consignées.
- **Un exemple inventé est dit inventé**, dans sa note : « exemple écrit pour
  illustrer, ce cabinet n'est pas un client ». Pas de nom de vraie marque
  dans un faux exemple (vérifier que le nom choisi n'existe pas, ou écrire
  « [Ton logiciel] »).
- **Un logo client exige l'accord du client** ; un logo d'outil ne dit pas
  « partenaire » ni « certifié » sans preuve.
- **Pas de capture d'un tiers dans une posture trompeuse** : une fiche, une
  SERP ou un résultat qui appartient à un autre se légende comme tel
  (« les fiches appartiennent à des entreprises tierces »).
- Pas de capture retouchée, pas de note ou de compteur recomposé.

## Les pièges payés en production

- **Logo blanc sur fond transparent** : sur une carte blanche, la case
  paraît vide. Repérer les logos clairs (canal alpha + pixels blancs) et
  leur donner un fond sombre.
- **Schéma étiré** : un SVG à `width:100%` sans largeur maximale transforme
  une grille de points en balles de 36 px sur ordinateur. Un schéma qui n'a
  pas de version large garde une `max-width` (450 à 560 px).
- **Texte de schéma illisible sur téléphone** : un SVG de 1 000 de large
  ramené à 340 px fait tomber un texte de 16 à 5 px. Soit une version
  portrait (affichée sous 700 px), soit un `viewBox` étroit (440 à 460) avec
  des textes à 17-20.
- **Code dans WordPress** : `wptexturize` change `"carte"` en `« carte »`
  hors des balises `<code>` et `<pre>`, et `wpautop` ajoute un `<br />`
  devant chaque saut de ligne (doublé par `white-space:pre-wrap`). Mettre le
  code dans `<code>`, les retours à la ligne en `<br>`, aucun `\n` brut.
- **Grille de logos en `auto-fill` trop étroite** : « OpenAI (ChatGP T) »
  coupé en trois lignes. Colonnes fixes (3 sur ordinateur, 2 sur téléphone)
  et `word-break:normal` sur le nom.
- **Une capture large dans une grille `1fr`** élargit la colonne : `minmax(0,1fr)`
  et `min-width:0` (voir `design-tokens.md`).
- **Même légende sur toutes les pages d'un lot** : le contrôle de
  duplication (`similarite_lot.py`) la compte. Une légende par page.

## Le registre

Comme les photos, les logos et les captures passent par un **registre du
projet** (clé → URL, dimensions, source, licence) et le gabarit n'accepte
qu'une clé du registre. Il vit dans le skill propre au projet
(`projet-…`) : c'est là qu'on retrouve, à la page suivante, le logo déjà
téléversé et la capture déjà allégée en WebP, au lieu de les refaire.

## Vérifier

1. `audit_images.py --matiere 3 --strict` sur le HTML produit.
2. Rendu navigateur à 390 et 1 440 px (`rendu.py`, ou Playwright sur un
   miroir de la vraie page) : capture de chaque bande qui contient de la
   matière, pas seulement la page entière réduite.
3. Le HTML servi par le CMS : `<figure>`, `<svg>` et `<code>` intacts,
   aucun `<p>` ni `<br />` ajouté dedans.
