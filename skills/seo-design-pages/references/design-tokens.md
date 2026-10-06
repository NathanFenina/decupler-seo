# Tokens de design

Un token est une décision nommée : « la couleur des actions », « l'espace
entre deux sections ». Tant que ces décisions sont des valeurs recopiées dans
chaque page, la moindre correction se fait page par page et les pages
dérivent. Déclarées une fois, elles se corrigent une fois.

**Source unique** : les tokens vivent à un seul endroit (la feuille du thème,
les variables globales du constructeur, `tailwind.config` ou `globals.css`).
Composants, pages et schémas générés les **lisent**, ils ne les recopient pas.

---

## 1. Le contrat des composants

Tous les composants de `${CLAUDE_PLUGIN_ROOT}/templates/` lisent ces
variables, avec une valeur neutre par défaut :

```css
:root{
  /* Couleurs */
  --dcp-primaire:#1F4E79;        /* titres forts, liens, en-têtes de tableau */
  --dcp-primaire-fonce:#163A5C;  /* survol */
  --dcp-accent:#B4531A;          /* action principale — une seule couleur d'action */
  --dcp-sur-accent:#FFFFFF;      /* texte posé sur l'accent */
  --dcp-encre:#1B1F24;           /* texte principal */
  --dcp-texte-2:#4B5563;         /* texte secondaire, légendes */
  --dcp-fond:#FFFFFF;
  --dcp-fond-doux:#F3F5F8;       /* bandes alternées, encadrés */
  --dcp-bord:#D9DEE5;            /* filets, bordures */
  --dcp-sombre:#14212E;          /* bandes sombres */
  --dcp-sur-sombre:#C9D3DE;      /* texte secondaire sur fond sombre */
  /* Forme et typographie */
  --dcp-rayon:12px;
  --dcp-police-titres:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --dcp-police-texte:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
```

Contrastes des valeurs par défaut sur blanc : encre 16,6:1, texte secondaire
7,6:1, primaire 8,7:1, accent 5,0:1 (texte blanc sur l'accent : 5,0:1).

Pour appliquer la charte d'un site, **déclarez ces variables une fois**
(`:root` dans le CSS additionnel du thème, variables globales Elementor,
variables Webflow, `globals.css`) : tous les composants collés les prennent.
Chaque composant garde sa valeur de repli (`var(--dcp-accent, #B4531A)`) pour
rester beau s'il est collé seul. Une page complète déclare ses valeurs par
défaut dans `:where(:root){…}` : spécificité nulle, la charte du site
l'emporte toujours, quel que soit l'ordre des feuilles (c'est ce que fait
`page-service.html`).

Avant de remplacer les valeurs par défaut, **mesurez les contrastes de la
charte** : texte courant ≥ 4,5:1, gros texte (≥ 24 px, ou ≥ 18,7 px gras)
≥ 3:1, texte d'un bouton ≥ 4,5:1. Une couleur de marque qui échoue sur blanc
reste la couleur des aplats et des filets ; les textes et boutons prennent sa
variante foncée.

---

## 2. La couleur

- **Une seule couleur d'action.** L'accent est réservé à l'action principale.
  Si tout est coloré, rien n'appelle le clic.
- **Pas de second accent**, pas de dégradé décoratif, pas de texte en
  dégradé transparent (`background-clip: text`) : sa couleur réelle est
  `transparent`, les outils de contraste se trompent, et c'est devenu une
  signature de page générée.
- **Un état se lit par une marque, pas seulement par une teinte.** « Oui » =
  une coche **et** le mot ; option recommandée = un libellé **et** une
  bordure. Environ un homme sur douze distingue mal le rouge du vert.
- **Rouge = erreur**, et seulement erreur. Un rouge décoratif fait chercher
  l'erreur.
- **Fonds sombres** : le texte secondaire y tombe vite sous 4,5:1 (un gris
  moyen sur bleu nuit mesure souvent 3,5:1). Vérifiez chaque niveau de gris.
- **Fonds semi-transparents** : le contraste se mesure sur la couleur
  composée avec ce qu'il y a derrière, pas sur la couleur déclarée.

## 3. La typographie

| Rôle | Taille | Interligne | Remarque |
|---|---|---|---|
| H1 | `clamp(1.9rem, 4.5vw, 2.8rem)` | 1,1 à 1,2 | 20 caractères de large au plus par ligne (`max-width: 20ch`), `text-wrap: balance` |
| H2 | `clamp(1.5rem, 3.2vw, 2.1rem)` | 1,2 à 1,3 | |
| H3 | `clamp(1.1rem, 2.2vw, 1.35rem)` | 1,3 | |
| Chapô | 1,1 à 1,2 rem | 1,6 | 55 à 60 caractères de large |
| Corps | 1 à 1,0625 rem (16-17 px) | 1,65 à 1,75 | **60 à 70 caractères par ligne** (`max-width: 68ch`, ou en `em` : voir plus bas) |
| Légende, note | 0,8 à 0,875 rem | 1,5 | jamais sous 12 px |
| Chiffres | `font-variant-numeric: tabular-nums` | | tout chiffre comparable s'aligne |

- **`ch` ment avec certaines polices.** L'unité vaut la largeur du « 0 » :
  large dans les polices à chiffres larges (Inter : environ 0,75 em), elle
  laisse passer 85 à 90 caractères de français sous un `max-width: 66ch`.
  Mesurez la ligne réelle au rendu ; si elle dépasse, exprimez les mesures
  de lecture en `em` (environ 36 em pour 72 caractères).
- **Plancher de 12 px** (`.75rem`) pour tout texte qui porte une information
  (pastille, étiquette, légende) ; en dessous, c'est de la décoration.
- **Deux familles au plus**, trois ou quatre graisses en tout. Chaque graisse
  est un fichier à charger.
- **Pile système par défaut** (zéro requête, zéro décalage). Police de marque :
  auto-hébergée, en WOFF2, `font-display: swap`, préchargée pour la graisse du
  H1 seulement. Pas de police chargée depuis un domaine tiers dans un
  fragment collé : elle bloque le rendu et dépend d'un service externe.
- **Pas de capitales espacées** en surtitre de chaque section : une ou deux
  étiquettes dans la page, pas une par bloc.
- **Langues** : les tailles secondaires montent d'un cran en arabe ou en
  écritures denses ; pas d'interlettrage ni d'italique en arabe ; propriétés
  logiques (`margin-inline-start`, `text-align: start`) pour que la mise en
  page se retourne en RTL ; valeurs mixtes (pourcentages, montants) dans des
  `<bdi>`.

## 4. L'espace

Échelle sur une base de 8 px : `0.5 · 1 · 1.5 · 2 · 3 · 4 · 6 rem`.

| Usage | Valeur |
|---|---|
| Entre deux sections | `clamp(2.5rem, 6vw, 5rem)` de marge verticale |
| Gouttière latérale | `clamp(1rem, 4vw, 3rem)` — 16 px minimum en mobile |
| Largeur de lecture | 720 px (articles) |
| Largeur de page | 1 140 à 1 240 px (landing, service) |
| Espace titre → texte | 0,75 à 1 rem |
| Entre cartes | 1 à 1,5 rem |

Des respirations généreuses entre sections et serrées à l'intérieur : c'est
ce contraste qui fait lire les sections comme des blocs.

## 5. Formes, ombres, mouvement

- **Rayon** : une valeur pour toute la page (0 à 14 px). Mélanger des coins
  vifs et des coins très arrondis fait bricolage.
- **Ombres** : légères et rares. Une page où tout flotte n'a plus de relief.
  Les filets de 1 px et les fonds alternés structurent mieux qu'une ombre.
- **Mouvement** : transitions de 150 à 300 ms sur les survols ; rien qui
  bouge en permanence à côté d'un texte ; tout est neutralisé sous
  `@media (prefers-reduced-motion: reduce)`.
- **Apparition au défilement** : le contenu est **visible par défaut**.
  L'animation n'est qu'un plus, ajoutée par le script qui la gère. Une classe
  qui met le contenu à `opacity: 0` en CSS et compte sur un script pour le
  révéler a déjà laissé des pages entières invisibles (un script cassé par une
  ligne vide suffit). Si vous le faites malgré tout : filet `<noscript>` et
  forçage de l'affichage au bout de 2 à 3 secondes.
- **Animer la translation, jamais l'opacité.** Un `from { opacity: 0 }`
  rend le texte invisible partout où l'animation ne tourne pas : crawler
  IA, JavaScript coupé, capture sans interface. `from { transform:
  translateY(18px) }` donne le même effet sans rien cacher.
- **Déclencher au défilement** (`IntersectionObserver`), pas au chargement :
  jouée au chargement, l'animation d'un bloc situé 9 000 px plus bas est
  finie avant que le lecteur n'y arrive, et on croit qu'elle manque.
- **Une animation de fond (canvas, SVG animé)** : le texte reste dans le
  HTML, jamais peint dans le canvas ; ordre de peinture explicite (canvas
  en `z-index:0` et `pointer-events:none`, contenu en `position:relative;
  z-index:1`) plutôt qu'un `z-index:-1` qui dépend du thème ; une seule
  image fixe sous `prefers-reduced-motion` ; boucle arrêtée quand l'onglet
  passe en arrière-plan ; aucune dépendance externe si quelques dizaines de
  lignes suffisent.
- **Focus clavier** : un anneau visible de 2 px, décalé de 2 à 3 px, sur tout
  élément interactif (`:focus-visible`). Ne le supprimez jamais sans le
  remplacer.

## 5 bis. Les signatures d'une interface générée

Une page se fait repérer comme produite en série sur des motifs visuels,
avant qu'on lise une phrase. Ceux qui reviennent le plus :

| Motif | Ce qu'on voit | À la place |
|---|---|---|
| Barre latérale colorée | 3-4 px de couleur ou de dégradé sur le bord gauche de chaque carte | Rien, ou un filet complet |
| Halo coloré | Ombres teintées de la couleur de marque | Élévation neutre (ombre grise ou encre très diluée) |
| Bord fin + ombre large | 1 px de bordure et 40 px de flou sur la même carte | Choisir : bord net **ou** élévation |
| Numérotation décorative | « 01, 02, 03 » sur des éléments qui ne sont pas une séquence | Numéroter seulement une vraie suite ; l'étiquette porte une information utile |
| Surtitre partout | Petite étiquette en capitales au-dessus de chaque H2 | Une ou deux dans la page |
| Capitales longues | Une pastille de 35 caractères en capitales | Capitales sur 2-3 mots au plus |
| Texte en dégradé | `background-clip:text` sur les titres | Couleur pleine (voir § 2) |
| Grilles orphelines, bandes monotones | voir la checklist | voir la checklist |

Un détecteur déterministe de ces motifs (par exemple Impeccable,
impeccable.style) transforme l'impression « ça fait généré » en liste
vérifiable. **Lancez-le en mode navigateur, sur la page servie en HTTP**,
jamais sur le fichier : l'analyse statique ne résout pas `clamp()` ni les
variables, et signale des défauts qui n'existent pas. Un signal qui relève
de la charte assumée du client se garde et se note ; un faux positif se
vérifie au DOM (une longueur de ligne se mesure, elle ne s'estime pas).

Deux règles de correction :
- **Corriger la règle à sa source.** Surcharger en fin de fichier laisse du
  code mort que le détecteur (et le prochain qui lira la feuille) voit
  encore.
- **Ne jamais supposer les couleurs d'un composant.** Relire la règle avant
  de changer un fond : une pastille qu'on croyait porter un chiffre blanc en
  portait un violet foncé, et le passage en aplat foncé l'a rendue
  illisible (1,5:1).

## 5 ter. Le rythme vertical

- Deux bandes **de même fond** qui se suivent additionnent leurs marges :
  150 à 180 px de vide, le « bas de page vide ». Fusionnez-les ou changez
  le fond de l'une.
- Une bande de respiration (ruban sombre, fine) a peu de marge : elle doit
  trancher, pas respirer.
- Un titre posé sur une photo pleine largeur tient en une ou deux lignes
  (22 caractères environ) : sur trois lignes, il mange la photo.

## 6. Mobile

La moitié du trafic, et la moitié des défauts. À vérifier à 375-390 px :

- aucun défilement horizontal (tableaux dans un conteneur
  `overflow-x: auto`, bandes pleine largeur sous `overflow-x: hidden`) ;
- grilles en une colonne sous 640 px (`repeat(auto-fit, minmax(260px, 1fr))`
  le fait tout seul) ;
- H1 réduit, sous-titre en pleine largeur (un `max-width` en `ch` pensé pour
  l'ordinateur coupe le texte) ;
- boutons en pleine largeur, empilés, cibles de 44 px ;
- éléments décoratifs flottants masqués ;
- champs de formulaire à 16 px minimum (sinon iOS zoome à la saisie) ;
- rien de collant qui masque le texte (bouton flottant, barre de CTA,
  bannière cookies : vérifiez-les ensemble).

## 7. Correspondance par plateforme

| Token | CSS pur / fragment | Elementor | Webflow | Tailwind / Next.js |
|---|---|---|---|---|
| Couleurs | `:root{--dcp-…}` | Couleurs globales + CSS personnalisé du site déclarant les `--dcp-*` | Variables (collection Couleurs) | `theme.extend.colors` ou `@theme` en v4, reliés aux mêmes variables |
| Typographie | `--dcp-police-*` | Polices globales | Variables de typographie | `next/font` + `fontFamily` |
| Espacements | valeurs `clamp()` | Espacements du kit | Variables de taille | échelle `spacing` |
| Rayon | `--dcp-rayon` | Kit de site | Variable | `borderRadius` |
