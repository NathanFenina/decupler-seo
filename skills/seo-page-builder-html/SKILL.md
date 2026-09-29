---
name: seo-page-builder-html
description: >
  Génère des pages HTML complètes, esthétiques et responsive, prêtes à coller
  dans Elementor, Webflow, WordPress ou un site statique : sections
  alternées, tableaux, CTA, FAQ dépliable, schema intégré, sans dépendance
  externe. Déclencher sur "crée une page HTML", "génère la page", "code HTML",
  "page prête à coller", "Elementor", "landing page", "mets ça en HTML",
  "page de service", "composant HTML", "template de page".
---

# Génération de pages HTML

Le livrable est un fichier HTML qu'on copie, qu'on colle, et qui est beau
immédiatement. Pas un squelette à styliser.

## Contraintes non négociables

1. **Zéro dépendance externe.** Pas de CDN, pas de framework, pas de police
   Google. Tout est inline. La page doit s'afficher correctement dans un
   éditeur de bloc HTML qui n'a accès à rien.
2. **CSS scopé.** Toutes les classes préfixées (`dcp-`) et toutes les règles
   descendantes d'un conteneur racine, pour ne pas contaminer le thème du
   site hôte. Un `h2 { color: blue }` non scopé repeindra tout le site.
3. **Responsive sans media query complexe.** `clamp()`, `grid` avec
   `auto-fit` et `minmax`, `flex-wrap`. Ça tient sur tous les écrans sans
   points de rupture à maintenir.
4. **Accessible.** Contraste 4,5:1 minimum, `<details>` natif pour la FAQ,
   hiérarchie Hn respectée, `alt` sur chaque image, ordre de tabulation
   logique.
5. **Un seul H1 par page**, et il correspond au title.

## La structure type d'une page de service

```
1. Hero            — H1, réponse directe (40-60 mots), CTA principal
2. Preuves         — 3-4 chiffres clés, certifications, années d'expérience
3. Le problème     — ce que vit le lecteur, en ses termes
4. La solution     — ce que vous faites, en 3-4 blocs
5. Comment ça marche — les étapes, numérotées
6. Tableau         — comparaison, tarifs, ou caractéristiques
7. Preuve sociale  — témoignages, cas clients chiffrés
8. FAQ             — 5-8 questions dépliables
9. CTA final       — une action, une seule
```

Alternez les fonds entre les sections. C'est ce qui donne le rythme visuel
et fait qu'une page ne ressemble pas à un document Word.

## Le squelette CSS

```html
<div class="dcp-page">
<style>
.dcp-page{--dcp-primaire:#0B7285;--dcp-accent:#15AABF;--dcp-encre:#1A1A2E;
  --dcp-doux:#F1F6F8;--dcp-bord:#DCE7EB;--dcp-rayon:14px;
  --dcp-ombre:0 2px 16px rgba(11,114,133,.08);
  color:var(--dcp-encre);line-height:1.7;
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.dcp-page *{box-sizing:border-box}
.dcp-page section{padding:clamp(2rem,5vw,4rem) clamp(1rem,4vw,3rem)}
.dcp-page section:nth-of-type(even){background:var(--dcp-doux)}
.dcp-page h2{font-size:clamp(1.5rem,3.2vw,2.1rem);line-height:1.25;
  margin:0 0 1rem;color:var(--dcp-primaire)}
.dcp-page h3{font-size:clamp(1.1rem,2.2vw,1.35rem);margin:1.6rem 0 .5rem}
.dcp-grille{display:grid;gap:1.25rem;
  grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.dcp-carte{background:#fff;border:1px solid var(--dcp-bord);
  border-radius:var(--dcp-rayon);padding:1.5rem;box-shadow:var(--dcp-ombre)}
.dcp-cta{display:inline-block;background:var(--dcp-primaire);color:#fff;
  padding:.9rem 1.9rem;border-radius:var(--dcp-rayon);text-decoration:none;
  font-weight:600}
.dcp-cta:hover{background:var(--dcp-accent)}
.dcp-tableau{width:100%;border-collapse:collapse;font-size:.95rem}
.dcp-tableau th{background:var(--dcp-primaire);color:#fff;
  padding:.85rem;text-align:left}
.dcp-tableau td{padding:.85rem;border-bottom:1px solid var(--dcp-bord)}
.dcp-tableau tr:nth-child(even) td{background:var(--dcp-doux)}
.dcp-scroll{overflow-x:auto}
.dcp-faq details{border:1px solid var(--dcp-bord);border-radius:var(--dcp-rayon);
  margin-bottom:.75rem;background:#fff}
.dcp-faq summary{padding:1.05rem 1.25rem;cursor:pointer;font-weight:600;
  list-style:none}
.dcp-faq summary::-webkit-details-marker{display:none}
.dcp-faq summary::after{content:"+";float:right;font-size:1.4rem;line-height:1}
.dcp-faq details[open] summary::after{content:"−"}
.dcp-faq div{padding:0 1.25rem 1.15rem}
</style>
```

Adaptez la palette à la charte du client. Demandez ses couleurs si vous ne
les avez pas — une page aux mauvaises couleurs ne sera pas utilisée.

## Points de vigilance

**Les tableaux débordent en mobile.** Toujours envelopper dans
`<div class="dcp-scroll">`. C'est le défaut le plus fréquent des pages
générées.

**La FAQ en `<details>`** — pas de JavaScript. Le contenu reste dans le DOM,
donc lisible par Google et par les LLM. Une FAQ en accordéon JavaScript qui
charge à la demande est invisible pour les crawlers.

**Les images.** `width` et `height` explicites (sinon CLS), `loading="lazy"`
sauf pour le hero, `alt` descriptif. Ne référencez jamais une image depuis un
domaine externe : elle disparaîtra.

**Le CTA.** Un seul par écran, et la même action tout au long de la page.
Trois CTA différents dans une page divisent la conversion.

## Le schema

Générez le JSON-LD correspondant au type de page et intégrez-le dans un
`<script type="application/ld+json">` en fin de bloc. Sur WordPress avec un
plugin SEO, prévenez du risque de doublon : deux schemas `Article` sur la
même page créent une ambiguïté.

## Contraintes par plateforme

| Plateforme | À savoir |
|------------|----------|
| **Elementor** | Widget « HTML personnalisé ». Le CSS doit être dans le bloc. Un H1 existe souvent déjà dans le template — ne le doublez pas. |
| **WordPress (Gutenberg)** | Bloc « HTML personnalisé ». Attention aux filtres de contenu qui suppriment certaines balises. |
| **Webflow** | Embed HTML limité à 50 000 caractères. Découpez si nécessaire. |
| **Site statique** | Aucune contrainte. Vous pouvez sortir le CSS dans une feuille séparée. |

## Livrables

- `page-<slug>.html` — la page complète, autonome
- `page-<slug>.jsonld` — le schema, si séparé
- `INSTRUCTIONS.md` — où coller, quoi vérifier après collage

Vérifiez le rendu réel via le MCP Chrome DevTools avant de livrer. Une page
qui casse en mobile ne se voit pas dans le code.
