# Images — le plan, les formats, la génération

Une image sur une page SEO a trois coûts (poids, LCP, attention) et doit donc
avoir un rôle. Le plan d'images se décide avec le gabarit : pour chaque
emplacement, on sait **ce que l'image apporte**, d'où elle vient, son ratio,
son poids cible, son `alt` et sa légende. L'audit et la correction d'un site
existant : `seo-images`.

---

## 1. Quatre rôles, pas un de plus

| Rôle | Source | Exemple |
|---|---|---|
| **Prouver** | photo réelle | l'équipe, un chantier, l'atelier, le produit en situation |
| **Expliquer** | schéma tiré du contenu | étapes, comparaison, arbre de décision, chiffres clés |
| **Montrer** | capture, maquette d'écran | l'outil qui tourne, le livrable, un avant / après |
| **Situer** | photo de lieu, illustration | la ville d'une page locale, un sujet abstrait |

**La règle du schéma** : une figure porte de l'information tirée du contenu
qu'elle illustre. Si elle ne dit rien que le texte ne dise mieux, elle ne doit
pas exister. Sur un sujet technique ou B2B, un lecteur pressé ne lit pas
1 500 mots : il cherche le schéma qui résume l'arbitrage.

**Ce qu'on ne met pas** : photo de banque d'images générique (poignée de
main, skyline, personne souriante devant un ordinateur), illustration
décorative sans lien avec la section, visage généré qui passerait pour un
salarié ou un client, capture d'un outil tiers retouchée.

---

## 2. Le plan par type de page

| Type | Emplacements | Minimum |
|---|---|---|
| **Page service** | hero (photo réelle ou visuel qui montre la prestation) · figure de preuve (chantier, capture, schéma de la méthode) · photo de la bannière confiance | 3 |
| **Article** | image à la une (partages, Open Graph) · une figure de corps pour 600 à 800 mots, placée dans la section qu'elle explique | 1 dans le corps |
| **Page locale** | hero · photo réelle de la ville ou d'un chantier local dans la zone d'intervention · photo d'équipe | 2 |
| **Landing** | visuel du hero (produit, démonstration) · capture annotée · photos des témoignages si réelles | 2 |
| **Comparatif** | aucun hero décoratif ; captures des options comparées si vous les avez testées ; schéma de synthèse | 0 à 2 |
| **Outil** | aucune image avant l'outil ; un schéma de la méthode de calcul | 0 à 1 |
| **Lead magnet** | couverture ou aperçu de la ressource · photo de l'auteur | 2 |

Deux règles de lot :

- **Chaque page a ses propres visuels.** Deux articles d'un même cluster ou
  deux pages de villes voisines qui partagent un visuel se ressemblent dans
  les listes et les partages. Pour un nouveau sujet, un nouveau visuel.
- **Une image n'apparaît qu'une fois par page.** Répéter la photo du hero
  dans le corps double le poids pour rien.

**Piège du thème qui masque l'en-tête** : quand le gabarit de la page masque
l'en-tête du thème (pour poser son propre hero), l'image à la une ne
s'affiche nulle part sur la page. Il faut alors une figure dans le corps,
sinon l'article n'a aucun visuel.

---

## 3. Formats, dimensions, poids

| Emplacement | Ratio | Largeur source | Poids cible |
|---|---|---|---|
| Hero pleine largeur | 16:9 ou 21:9 | 1 920 px (jeu `srcset` 640 → 1 920) | < 200 Ko |
| Hero en demi-colonne | 4:3 ou 3:2 | 1 200 px | < 150 Ko |
| Figure de corps | 3:2 ou 16:9 | 1 200 px | < 120 Ko |
| Schéma | libre | SVG, ou 2 400 px en WebP pour la netteté sur écran haute densité | < 150 Ko |
| Capture d'écran | celui de l'écran | 1 600 px maximum | < 150 Ko |
| Portrait (confiance, auteur) | 1:1 ou 4:5 | 400 à 720 px | < 60 Ko |
| Open Graph / partage | 1,91:1 (1 200 × 630) | 1 200 px | < 300 Ko |
| Image à la une (blog) | celui du thème, fixe pour toute la série | selon le thème | < 150 Ko |

**Budget de page** : moins de 1 Mo d'images au total pour une page de
service, moins de 600 Ko pour un article.

| Format | Usage |
|---|---|
| **AVIF** | le plus léger, en première source d'un `<picture>` |
| **WebP** | le bon défaut, support universel |
| **JPEG** | repli, et maquettes à fond sombre (qualité 80-86) |
| **PNG** | uniquement la transparence ou une capture pleine de texte fin |
| **SVG** | logos, icônes, schémas simples ; texte réel, net à toute taille |

Redimensionnez **avant** de compresser : une photo de 3 000 px affichée dans
600 px, c'est 80 % du gaspillage.

---

## 4. Le balisage

**L'image LCP** (le hero, presque toujours) :

```html
<picture>
  <source type="image/avif" srcset="hero-1200.avif 1200w, hero-1920.avif 1920w" sizes="100vw">
  <source type="image/webp" srcset="hero-1200.webp 1200w, hero-1920.webp 1920w" sizes="100vw">
  <img src="hero-1200.jpg" alt="…" width="1920" height="1080" fetchpriority="high" decoding="async">
</picture>
```

- **jamais `loading="lazy"`** sur l'image LCP : c'est l'erreur la plus
  fréquente, souvent posée par un plugin qui l'applique à toutes les images ;
- `fetchpriority="high"`, et `<link rel="preload" as="image">` si l'image est
  en fond CSS ;
- **pas de carrousel** en hero : il charge plusieurs images pour en montrer
  une.

**Toutes les autres** :

```html
<img src="schema-800.webp" srcset="schema-800.webp 800w, schema-1600.webp 1600w"
     sizes="(max-width: 800px) 100vw, 760px" alt="…"
     width="1600" height="900" loading="lazy" decoding="async">
```

- `width` et `height` **toujours** (ou un `aspect-ratio` CSS) : sans eux, la
  page saute au chargement — première cause de CLS ;
- `loading="lazy"` sous la ligne de flottaison ;
- jamais une image en `data:` base64 dans le HTML : elle alourdit le document,
  n'est pas mise en cache, et gonfle chaque page qui la contient.

**Next.js** : `next/image` avec `sizes` renseigné (sinon le navigateur
télécharge la plus grande variante), `priority` sur l'image LCP seulement,
parent dimensionné (`aspect-ratio`) avec `fill`.

---

## 5. Texte alternatif, légende, crédit

**`alt`** — ce que l'image montre, pour quelqu'un qui ne la voit pas, et ce
qui compte dans ce contexte. 5 à 20 mots, 125 caractères au plus.

| ❌ | ✅ |
|---|---|
| `alt="image1"`, `alt="hero"` | `alt="Façade ravalée d'une maison en meulière, avant et après"` |
| `alt="expert comptable paris expert comptable pas cher"` | `alt="Expert-comptable relisant un bilan annuel avec une dirigeante"` |
| `alt="Image de …"`, `alt="Photo de …"` | commencez par le sujet |
| le titre de l'article recopié | ce que montre **cette** image |
| une description sur une image décorative | `alt=""` |

Le mot-clé y figure quand l'image le montre vraiment, pas par principe. Un
`alt` bourré de mots-clés sert mal les lecteurs d'écran et rien au SEO.
L'`alt` d'une image générée s'écrit **après** avoir regardé le résultat : le
modèle ne dessine pas toujours ce qu'on lui a demandé.

**Légende** (`<figcaption>`) — une phrase qui **interprète** l'image, pas qui
la décrit (« Le délai se joue à l'étape 2 : c'est là que les dossiers
incomplets reviennent »). Les légendes sont lues, bien plus que le texte
courant, et Google comprend l'image par ce qui l'entoure.

**Crédit** — obligatoire pour une photo tierce : « Photo : [auteur] /
[source] », dans la légende, avec lien vers la licence quand elle l'exige.

**Nom de fichier** — `[slug-de-la-page]-[role].webp` : minuscules, tirets,
sans accents, descriptif (`audit-energetique-lyon-hero.webp`, pas
`IMG_4837.JPG`). Unique par page, ce qui évite les collisions.

---

## 6. D'où viennent les images

Par ordre de préférence :

1. **Photos réelles** fournies par le client (équipe, chantiers, produits,
   locaux). Irremplaçables pour la confiance. Demandez-les dès le brief.
2. **Schémas rendus à partir du contenu** : HTML/CSS aux couleurs du site,
   capturé en WebP 2 400 px, ou SVG. Les couleurs sont lues dans les tokens du
   site au moment du rendu, jamais recopiées — sinon la moindre évolution de
   la palette crée un décalage.
3. **Captures et maquettes** de l'outil ou du livrable.
4. **Photos libres de droits** de lieux (pages locales), créditées.
5. **Images générées** : sujets abstraits, illustrations de section, visuels
   de couverture. Jamais pour prouver.

**Hébergement** : toujours dans la médiathèque du site ou le dépôt, jamais en
lien vers un domaine externe (l'image disparaîtra). Sur WordPress, cherchez
le média par son nom avant de téléverser : un second envoi du même fichier
crée `-1`, `-2`, et le nom de l'original peut glisser.

**Marqueurs provisoires** : dans un fragment rédigé avant le téléversement,
utilisez des marqueurs explicites (`__IMG_HERO__`) remplacés par l'URL réelle
à la publication. `audit_images.py` refuse une page qui en contient encore.

---

## 7. Générer une image

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/images_generer.py" \
  --sujet "Plan de travail d'un cabinet de conseil, dossiers et graphiques imprimés" \
  --emplacement contenu --langue fr --slug audit-financier \
  --palette "#1F4E79,#B4531A,#F3F5F8"
```

| Emplacement | Ratio demandé | Usage |
|---|---|---|
| `hero` | 16:9 | haut de page, image LCP |
| `contenu` | 3:2 | figure dans une section |
| `og` | 16:9, à recadrer en 1 200 × 630 | partage social, image à la une |
| `carre` | 1:1 | vignette, carte |
| `portrait` | 4:5 | colonne étroite, mobile |

Le script :

- construit le prompt à partir du **sujet**, du **contexte** (`--titre`,
  `--section`), du **style du site** (`--style`, ou `design.style_images`
  dans `decupler-seo.config.yml`) et de la **palette** (`--palette`, ou
  `design.palette`) ;
- impose les interdits : **aucun texte dans l'image** (le texte va dans le
  HTML, où il est lisible, traduisible et indexé), aucun logo ni marque,
  aucun filigrane, **aucun visage reconnaissable** — des personnes de dos, à
  distance ou des mains au travail, jamais un portrait qui passerait pour un
  salarié ou un client ;
- appelle **Gemini** (`GEMINI_API_KEY`, modèle réglable par
  `IMAGES_MODELE_GEMINI`) ou, à défaut, **OpenAI** (`OPENAI_API_KEY`,
  `IMAGES_MODELE_OPENAI`) ;
- enregistre en **WebP** quand c'est possible (OpenAI le produit directement ;
  pour Gemini, si Pillow est installé), sinon en PNG avec la commande de
  conversion à lancer ;
- écrit à côté un **fichier `.json`** : prompt, modèle, dimensions cibles,
  nom de fichier, `alt` proposé dans la langue de la page, légende à
  rédiger — marqué « à valider ».

`--dry-run` affiche le prompt et le fichier `.json` sans appeler aucune API :
utile pour relire le prompt, ou pour le coller dans un autre outil. Sans clé
configurée, le script se comporte de la même façon.

**Avant d'utiliser une image générée** :

- regardez-la en taille réelle : mains, objets, perspective, texte parasite ;
- réécrivez l'`alt` d'après ce qu'elle montre réellement ;
- gardez le même style (prompt de style, palette) pour toute une série : la
  cohérence visuelle d'un blog prime sur l'originalité d'une image ;
- ne l'utilisez jamais comme preuve (équipe, client, chantier, résultat).

---

## 8. Contrôle

```bash
# page ou dossier produit, hors ligne
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit_images.py" build/ --strict
# page en ligne, poids réels
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit_images.py" https://exemple.com/page
```

Le contrôle local vérifie : `alt` absent, vide sur une image informative,
générique ou trop long ; `width`/`height` absents ; format ancien ;
`loading="lazy"` sur la première image ou `fetchpriority` absent ; `lazy`
manquant plus bas ; fichier trop lourd ou beaucoup plus large que son
affichage ; nom de fichier non descriptif ; image en base64 ; même image
répétée ; marqueur provisoire oublié ; image hébergée sur un autre domaine.
