---
name: seo-images
description: >
  Audite et optimise les images : poids, formats modernes, dimensions, alt,
  lazy loading, nommage, impact sur le LCP et le CLS, sitemap images, schema
  ImageObject. Déclencher sur "images", "optimiser mes images", "alt", "poids
  des images", "WebP", "AVIF", "SEO images", "Google Images", "mes images sont
  trop lourdes", "lazy loading".
---

# Images — le poids mort le plus facile à corriger

Sur la plupart des sites, les images représentent 60 à 75 % du poids des
pages et sont responsables de l'essentiel du LCP dégradé. C'est aussi le
chantier le plus mécanique : les gains sont garantis.

## L'audit

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit_images.py" <url>
```

Par image : URL, format, poids, dimensions réelles, dimensions affichées,
présence de `alt`, `width`/`height`, `loading`, position dans la page.

## Les 8 points de contrôle

### 1. Le format
| Format | Usage |
|--------|-------|
| **AVIF** | Meilleure compression. ~50 % plus léger que JPEG à qualité égale |
| **WebP** | Le bon défaut. Support universel, 25-35 % plus léger que JPEG |
| **JPEG** | Repli photo |
| **PNG** | Uniquement si transparence nécessaire. Lourd |
| **SVG** | Logos, icônes, schémas. Vectoriel, léger, net à toute taille |

Servez plusieurs formats avec repli :
```html
<picture>
  <source srcset="photo.avif" type="image/avif">
  <source srcset="photo.webp" type="image/webp">
  <img src="photo.jpg" alt="…" width="1200" height="800">
</picture>
```

### 2. Le poids
Cible : **< 150 Ko** pour une image de contenu, < 250 Ko pour un hero.

Le gaspillage typique : une photo de 3 000 px de large affichée dans un
conteneur de 600 px. Redimensionnez **avant** de compresser — c'est là que
se trouvent 80 % des gains.

### 3. Le responsive
```html
<img src="photo-800.webp"
     srcset="photo-400.webp 400w, photo-800.webp 800w, photo-1600.webp 1600w"
     sizes="(max-width: 600px) 100vw, 800px"
     alt="…" width="800" height="533">
```
Un mobile ne doit jamais télécharger l'image desktop.

### 4. Dimensions explicites — pour le CLS
`width` et `height` **toujours** présents, même avec du CSS responsive. Ils
permettent au navigateur de réserver l'espace avant le chargement. Sans eux,
la page saute : c'est la première cause de CLS dégradé.

### 5. Lazy loading — attention au piège
```html
<img loading="lazy">   <!-- images sous la ligne de flottaison -->
<img fetchpriority="high">  <!-- image LCP : jamais lazy -->
```

Mettre `loading="lazy"` sur l'image du hero retarde le LCP de plusieurs
centaines de millisecondes. C'est l'erreur la plus fréquente depuis que le
lazy loading est passé en natif — beaucoup de plugins l'appliquent
aveuglément à toutes les images.

### 6. Le texte alternatif
Décrivez l'image, pour quelqu'un qui ne la voit pas.

| ❌ | ✅ |
|----|-----|
| `alt="image1"` | `alt="Plombier remplaçant un joint sous un évier"` |
| `alt="plombier lyon plombier pas cher plombier urgence"` | `alt="Intervention de dépannage sur une fuite de chauffe-eau"` |
| `alt=""` sur une image informative | Une description réelle |
| Une description sur une image décorative | `alt=""` (correct : le lecteur d'écran l'ignore) |

Le `alt` sert d'abord l'accessibilité. Le bénéfice SEO en découle. Un `alt`
bourré de mots-clés est à la fois inutile en SEO et hostile aux utilisateurs
de lecteurs d'écran.

### 7. Le nom de fichier
`plombier-remplacement-joint-evier.webp`, pas `IMG_4837.jpg`. Minuscules,
tirets, descriptif. Signal faible mais gratuit, et utile dans Google Images.

### 8. Le contexte
Google comprend une image par ce qui l'entoure : la légende, le paragraphe
qui la précède, le titre de la section. Une image placée dans un contexte
cohérent est mieux indexée qu'une image isolée.

## Le hero — traitement particulier

C'est presque toujours l'élément LCP. Checklist :

- [ ] Format moderne, compressé
- [ ] Dimensionné à la taille réellement affichée
- [ ] `fetchpriority="high"`
- [ ] **Pas** de `loading="lazy"`
- [ ] `<link rel="preload" as="image">` dans le `<head>` si chargée par CSS
- [ ] `width` et `height` explicites
- [ ] Pas de carrousel — un carrousel charge plusieurs images pour n'en
      montrer qu'une, et détruit le LCP

## Sitemap images et Google Images

Pour un site où l'image compte (immobilier, e-commerce, recettes, tourisme),
un sitemap images améliore la découverte :

```xml
<url>
  <loc>https://exemple.com/page</loc>
  <image:image>
    <image:loc>https://exemple.com/photo.webp</image:loc>
    <image:title>Titre descriptif</image:title>
  </image:image>
</url>
```

Et le schema `ImageObject` avec `license` et `creditText` si vous voulez
apparaître avec les informations de licence dans Google Images.

## Ce que l'automatisation peut faire

Si le repo est accessible :
- Conversion en WebP/AVIF avec repli
- Redimensionnement et génération des jeux `srcset`
- Ajout des `width`/`height` manquants depuis les dimensions réelles
- Correction du `loading` selon la position dans la page
- Correction des noms de fichiers, avec les redirections associées

Ce qui reste manuel : **rédiger les `alt`**. Ils demandent de savoir ce que
l'image montre et pourquoi elle est là. Proposez-les, faites-les valider.

## Livrables

- `IMAGES-AUDIT.md` — inventaire, poids total, gains estimés
- `images.csv` — par image : problèmes, correctif
- `images-optimisees/` — les fichiers convertis
- `alt-a-valider.csv` — les textes alternatifs proposés
