# Intégration par plateforme

Le même gabarit se construit différemment selon la cible. Ce fichier liste ce
qui casse, plateforme par plateforme — presque tout a été constaté en
production, et presque rien ne se voit dans le code.

---

## 1. WordPress et Elementor (HTML à coller)

**Le livrable est un fragment** : pas de `<!DOCTYPE>`, `<html>`, `<head>` ni
`<body>`. Un composant par bloc « HTML personnalisé » (Gutenberg) ou widget
HTML (Elementor). Jamais dans un bloc Paragraphe : WordPress y ajoute des
`<p>` et des `<br>`.

### wpautop réécrit votre HTML

WordPress transforme chaque ligne vide en `</p><p>` et enveloppe dans un `<p>`
ce qui traîne entre deux blocs. Le filtre s'applique au contenu sans blocs :
éditeur classique, contenu envoyé brut par l'API REST, certains thèmes. Un
bloc HTML personnalisé de Gutenberg ou un widget Elementor y échappent — mais
un fragment écrit pour y résister ne perd rien ailleurs : écrivez-les tous
ainsi. Quatre conséquences :

1. **Aucune ligne vide dans le contenu.** Une ligne vide au milieu d'une
   grille crée un `<p></p>` parasite qui la casse.
2. **Aucune ligne vide dans un `<style>` ni dans un `<script>`.** wpautop
   coupe aussi à l'intérieur : le navigateur abandonne toutes les règles CSS
   après la première balise injectée, et un script coupé ne s'exécute plus.
   Minifiez le CSS sur une ligne à la génération ; retirez les lignes vides
   du JavaScript. Un `<noscript>` multiligne se coupe en deux et sa feuille de
   secours s'applique alors tout le temps : sur une ligne, lui aussi.
3. **Pas d'élément en ligne orphelin entre deux blocs.** Un `<span>`, `<a>`,
   `<svg>`, `<b>` voisin direct d'un `<div>` se fait envelopper dans un `<p>`
   dont l'ouverture avale la fermeture du bloc suivant. Dans un conteneur qui
   contient des `<div>`, n'utilisez que des `<div>` ; un `<svg>` isolé va dans
   un `<div>`. Un lien bouton reste sur la même ligne que le `</p>` qui le
   précède.
4. **Deux éléments en ligne voisins sur la même ligne.** Un retour à la ligne
   entre deux `<a>` d'un même conteneur devient un `<br>` : les deux boutons
   côte à côte se retrouvent l'un sous l'autre.

### Le thème

- **Le H1 en double** : le thème affiche le titre de la page ; votre hero
  aussi. Soit le fragment n'a pas de H1 (le titre du thème en tient lieu),
  soit le titre du thème est masqué — en CSS, plus un court script qui le
  retire du DOM, car la règle CSS seule ne suffit pas sur tous les gabarits.
- **La marge au-dessus du hero** : beaucoup de thèmes réservent 40 à 60 px
  au-dessus du contenu. Neutralisez-la sur les pages pleine largeur.
- **Les bandes pleine largeur** dans une colonne de thème contrainte :

  ```css
  .dcp-bande{width:100vw;margin-left:calc(50% - 50vw);margin-right:calc(50% - 50vw)}
  ```

  avec `overflow-x: hidden` sur le conteneur pour éviter la barre de
  défilement horizontale que crée `100vw`. Aucun ancêtre ne doit avoir
  `overflow: hidden`, sinon la bande est rognée — vérifiez au pixel, pas à la
  géométrie : un élément rogné garde les bonnes dimensions.
- **Colonne flex qui se réduit** : dans certains thèmes, le conteneur
  principal est un élément flex sans largeur explicite ; il se réduit à la
  largeur de son contenu et se colle à gauche. `width: 100%` et
  `flex: 1 1 100%` sur la colonne principale.
- **CSS scopé** sous une classe racine préfixée : un `h2 { color: … }` non
  scopé repeint tout le site.

### Droits et cache

- `<style>` et `<script>` ne survivent que pour un compte qui a le droit
  `unfiltered_html` (administrateur) : un éditeur les voit supprimés à
  l'enregistrement.
- **Cache Elementor** : une modification écrite en base (par l'API) n'apparaît
  pas tant que les fichiers CSS ne sont pas régénérés (Elementor → Outils →
  Régénérer les fichiers et les données).
- **Composants collés inline** : corriger le modèle ne corrige pas les pages
  déjà publiées. Prévoyez le remplacement du seul bloc `<style>` du
  composant, repéré par sa classe racine, page par page, avec essai à blanc.

### Médias

Téléversez dans la médiathèque, avec l'`alt` renseigné dans le média (il
servira aux prochaines insertions). Cherchez le média par son nom avant
l'envoi : WordPress ne dédoublonne pas.

---

## 2. Webflow

- Construisez les gabarits en **composants natifs** (Components) et les
  tokens en **variables** : un embed HTML n'est pas éditable par le client.
- **Embed HTML limité à 50 000 caractères** : découpez une page générée en
  plusieurs embeds, un par section.
- Le **champ texte riche** d'une Collection n'accepte pas de HTML libre ;
  un composant (FAQ, tableau) y passe par un embed ou par un champ dédié.
- Les images téléversées reçoivent leurs variantes responsives
  automatiquement ; l'`alt` se règle dans le panneau de l'asset ou de
  l'élément. Le chargement différé est souvent actif par défaut : passez
  l'image du hero en **eager**.
- La publication est une étape séparée de l'écriture d'un élément de
  Collection.

---

## 3. Next.js / React

Un composant par bloc du gabarit, le contenu dans des fichiers de données
(un JSON par page et par langue) : **aucun texte en dur dans les
composants**.

| Bloc | Composant | Notes |
|---|---|---|
| Hero | `Hero` | H1 + chapô + CTA ; image avec `priority` |
| En bref | `Summary` | liste, visible sans JS |
| Sommaire | `Toc` | construit depuis la liste des sections ; ancres avec `scroll-margin-top` pour passer sous l'en-tête collant |
| Chiffres clés | `KeyFigures` | `<dl>`, appels de note vers les sources |
| Tableau | `ComparisonTable` | `<th scope>`, conteneur défilant |
| Bannières | `TrustBanner`, `Testimonials`, `CtaBand`, `LeadMagnet` | données réelles uniquement |
| FAQ | `Faq` | `<details>` natif, rendu serveur |
| Outil | `…Calculator` | seul composant client (`"use client"`) ; méthode et sources rendues côté serveur à côté |

- **Composants serveur par défaut** ; `"use client"` uniquement pour ce qui
  réagit à l'utilisateur (outil, menu mobile). La FAQ n'a pas besoin de
  JavaScript.
- **Le JSON-LD est généré depuis les mêmes données** que le rendu (la FAQ
  affichée et le `FAQPage` viennent du même tableau) : ils ne peuvent pas
  diverger.
- **`next/image`** : `sizes` toujours renseigné ; `priority` sur l'image LCP et
  nulle part ailleurs ; avec `fill`, un parent dimensionné par `aspect-ratio`.
  Activez AVIF (`images.formats: ['image/avif', 'image/webp']`). Un registre
  unique des photos (source, dimensions, `alt` par langue, crédit) évite
  qu'une même photo reçoive trois `alt` différents.
- **`next/font`** : polices auto-hébergées, `display: 'swap'`, sous-ensembles
  limités aux langues du site.
- **Outils** : champs avec `<label>`, `<fieldset>`/`<legend>`, résultat en
  `aria-live="polite"`, erreurs en `role="alert"` ; le CTA du résultat
  transporte le calcul (message ou formulaire pré-rempli).
- **Multilingue** : propriétés logiques Tailwind (`ps-`, `pe-`,
  `text-start`), `dir="rtl"` sur la langue concernée, `<bdi>` autour des
  valeurs mixtes.
- `npm run build` doit passer avant tout déploiement.

---

## 4. Site statique (générateur maison)

- Structure figée dans un gabarit partagé, **tous les textes dans les
  fichiers de contenu** : changer un texte ne touche jamais le gabarit.
- Une variante de page se pilote par des clés de contenu (visuel du hero,
  second CTA, section propre à la page), pas par une copie du gabarit.
- Build **déterministe** (deux builds successifs donnent des fichiers
  identiques) et contrôle bloquant avant chaque déploiement : langue du
  document, canonical, hreflang réciproques, liens internes, parité des
  langues.
- Déploiement par **delta** : seuls les fichiers modifiés partent, comparés
  au build ; jamais de suppression en masse côté serveur.

---

## 5. Vérifier le rendu réel

- **Servez en HTTP**, jamais en `file://` : le chargement différé et les
  animations ne s'y déclenchent pas, et on croit à une régression qui n'existe
  pas (`python3 -m http.server`).
- **Deux largeurs** : 390 px et 1 440 px. Contrôlez le défilement horizontal
  (`document.documentElement.scrollWidth` égal à la largeur de la fenêtre),
  les débordements hors d'un conteneur défilant, les contrastes réels.
- **Dans le vrai thème, avec les vraies polices.** Une coquille locale sans
  les polices web du site rend avec des polices système plus étroites : le
  texte tient là où il débordera en production. Pour juger un brouillon sans
  le publier : injectez le fragment dans une copie locale d'une page réelle
  du site (thème, polices et images rapatriés).
- Le MCP Chrome DevTools fait tout cela : `resize_page`, `take_screenshot`,
  `evaluate_script`, `lighthouse_audit`.
