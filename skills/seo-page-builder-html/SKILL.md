---
name: seo-page-builder-html
description: >
  Génère des pages HTML complètes, esthétiques et responsive, prêtes à coller
  dans Elementor, Webflow, WordPress ou un site statique : sections
  alternées, tableaux, CTA, FAQ dépliable, schema intégré, sans dépendance
  externe. Déclencher sur "crée une page HTML", "génère la page", "code HTML",
  "page prête à coller", "Elementor", "landing page", "mets ça en HTML",
  "page de service", "composant HTML", "template de page", "hero",
  "bannière témoignages", "bloc auteur", "sommaire", "tableau comparatif".
---

# Génération de pages HTML

Le livrable est un fichier HTML qu'on copie, qu'on colle, et qui est beau
immédiatement. Pas un squelette à styliser.

**Le design se décide avant le HTML** : type de page, gabarit section par
section, plan de CTA, bannières, plan d'images. C'est le rôle de
`seo-design-pages` — lancez-le d'abord si `design-<slug>.md` n'existe pas.
Ce skill-ci le traduit en fragments, avec les composants de
`${CLAUDE_PLUGIN_ROOT}/templates/`.

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
6. **Le contenu réel du site.** Images et URL reprises de la page en ligne
   (ou fournies par le client), jamais inventées ni pointées vers une banque
   d'images : un lien vers `/devis` qui n'existe pas est une 404 livrée. Même
   règle pour les preuves : aucun témoignage, logo, note ou chiffre inventé.
7. **Les retours visuels validés se propagent.** Une correction acceptée sur
   la première page (couleur, espacement, ton du CTA) s'applique d'office aux
   pages suivantes. Le client ne doit jamais la redemander.

## Fragment pour Elementor ou un CMS

Le livrable est un **fragment**, pas un document :

- **Pas de `<!DOCTYPE>`, `<html>`, `<head>` ni `<body>`** — collés dans un
  widget, ils cassent la page hôte ou sont supprimés par l'éditeur
- **Tout le CSS scopé sous une classe racine** (`.dcp-page …`), dans le bloc
- **Bandes pleine largeur** quand la colonne du thème est plus étroite :

```css
.dcp-page{overflow-x:hidden}
.dcp-page .dcp-bande{position:relative;left:50%;right:50%;
  margin-left:-50vw;margin-right:-50vw;width:100vw}
```

  `overflow-x:hidden` sur le conteneur évite la barre de défilement
  horizontale que crée `100vw` avec une barre verticale. **Testez dans
  l'aperçu de l'éditeur** : certains thèmes posent un `overflow:hidden` sur
  la colonne qui coupe la bande.
- **Bandes alternées** : jamais deux fonds identiques d'affilée, sinon deux
  sections se lisent comme une seule
- **Aucune ligne vide**, ni dans le HTML ni dans `<style>`/`<script>`, et
  deux éléments en ligne voisins (deux boutons) sur la même ligne : le filtre
  wpautop de WordPress transforme les lignes vides en `<p>` et les retours à
  la ligne entre éléments en ligne en `<br>`. Détail :
  `seo-design-pages` → `references/integration-plateformes.md`

## La structure selon le type de page

L'ordre des sections dépend du type : page service, article, page locale,
landing, comparatif, outil ou calculateur, lead magnet. Les gabarits complets
(section, contenu, CTA, composant) sont dans `seo-design-pages` →
`references/gabarits-par-type-de-page.md`. Le plus courant, la page service :

```
1. Hero              — H1, réponse directe (40-60 mots), CTA principal     hero.html
2. Preuves           — 3-4 chiffres sourcés                                encadre-chiffres-cles.html
3. Le problème       — ce que vit le lecteur, en ses termes
4. La solution       — ce que vous faites, en 3-4 blocs                   CTA
5. Le visuel qui prouve — photo réelle, capture, schéma légendé            figure-legendee.html
6. Comment ça marche — les étapes, numérotées
7. Tableau           — inclus / exclu, tarifs, comparaison                tableau-comparatif.html
8. Confiance         — qui intervient, preuves vérifiables                banniere-eeat.html · CTA
9. Témoignages       — réels, attribués, sourcés                          banniere-temoignages.html
10. FAQ              — 6-8 questions dépliables                           composant-faq.html
11. CTA final        — la même action                                     banniere-contact.html
```

Alternez les fonds entre les sections. C'est ce qui donne le rythme visuel
et fait qu'une page ne ressemble pas à un document Word.

## Le squelette CSS

```html
<div class="dcp-page">
<style>
:where(:root){--dcp-primaire:#1F4E79;--dcp-accent:#B4531A;--dcp-sur-accent:#FFFFFF;
  --dcp-encre:#1B1F24;--dcp-texte-2:#4B5563;--dcp-fond-doux:#F3F5F8;--dcp-bord:#D9DEE5;--dcp-rayon:12px}
.dcp-page{color:var(--dcp-encre);line-height:1.7;
  font-family:var(--dcp-police-texte,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif)}
.dcp-page *{box-sizing:border-box}
.dcp-page section{padding:clamp(2rem,5vw,4rem) clamp(1rem,4vw,3rem)}
.dcp-page section:nth-of-type(even){background:var(--dcp-fond-doux)}
.dcp-page h2{font-size:clamp(1.5rem,3.2vw,2.1rem);line-height:1.25;
  margin:0 0 1rem;color:var(--dcp-primaire)}
.dcp-page h3{font-size:clamp(1.1rem,2.2vw,1.35rem);margin:1.6rem 0 .5rem}
.dcp-page p{max-width:68ch}
.dcp-grille{display:grid;gap:1.25rem;
  grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.dcp-carte{background:#fff;border:1px solid var(--dcp-bord);
  border-radius:var(--dcp-rayon);padding:1.5rem}
.dcp-cta{display:inline-flex;align-items:center;min-height:48px;background:var(--dcp-accent);
  color:var(--dcp-sur-accent);padding:.9rem 1.9rem;border-radius:var(--dcp-rayon);
  text-decoration:none;font-weight:600}
.dcp-cta:hover{filter:brightness(.92)}
.dcp-page a:focus-visible,.dcp-page summary:focus-visible{outline:2px solid var(--dcp-primaire);outline-offset:3px}
.dcp-tableau{width:100%;border-collapse:collapse;font-size:.95rem}
.dcp-tableau th{background:var(--dcp-primaire);color:#fff;padding:.85rem;text-align:left}
.dcp-tableau td{padding:.85rem;border-bottom:1px solid var(--dcp-bord)}
.dcp-tableau tr:nth-child(even) td{background:var(--dcp-fond-doux)}
.dcp-scroll{overflow-x:auto}
@media (max-width:640px){.dcp-cta{width:100%;justify-content:center}}
@media (prefers-reduced-motion:reduce){.dcp-page *{transition:none!important;animation:none!important}}
</style>
```

Les variables `--dcp-*` sont le contrat commun de tous les composants :
déclarées une fois dans le `:root` du site, elles s'appliquent partout ;
`:where(:root)` donne des valeurs par défaut que la charte du site écrase
toujours. Voir `seo-design-pages` → `references/design-tokens.md`.

Adaptez la palette à la charte du client. Demandez ses couleurs si vous ne
les avez pas — une page aux mauvaises couleurs ne sera pas utilisée. Mesurez
les contrastes de sa charte avant de l'appliquer : un texte blanc sur une
couleur de marque moyenne passe souvent sous 4,5:1.

## Points de vigilance

**Les tableaux débordent en mobile.** Toujours envelopper dans
`<div class="dcp-scroll">`. C'est le défaut le plus fréquent des pages
générées.

**La FAQ en `<details>`** — pas de JavaScript. Le contenu reste dans le DOM,
donc lisible par Google et par les LLM. Une FAQ en accordéon JavaScript qui
charge à la demande est invisible pour les crawlers.

**Les images.** `width` et `height` explicites (sinon CLS), `loading="lazy"`
sauf pour le hero (`fetchpriority="high"`), `alt` descriptif, WebP ou AVIF.
Ne référencez jamais une image depuis un domaine externe : elle disparaîtra.
Chaque image a un rôle (prouver, expliquer, montrer) ; une même image
n'apparaît qu'une fois par page. Plan d'images et génération :
`seo-design-pages` → `references/images.md`.

**Le contenu visible sans JavaScript.** Pas de classe qui met le contenu à
`opacity: 0` en attendant un script d'apparition : un script cassé (une ligne
vide suffit sous WordPress) laisse la page entière invisible.

**Le CTA.** Un seul par écran, et la même action tout au long de la page.
Trois CTA différents dans une page divisent la conversion. Nombre et
emplacements selon la longueur et le type : `seo-design-pages` →
`references/cta-et-bannieres.md`.

## Les composants autonomes

Chaque composant est un **fichier à part**, collé dans son propre widget :
il se réutilise d'une page à l'autre sans toucher au reste.

| Composant | Modèle | Rôle |
|-----------|--------|------|
| Hero | `${CLAUDE_PLUGIN_ROOT}/templates/hero.html` | H1, réponse directe, action principale, image LCP |
| En bref | `${CLAUDE_PLUGIN_ROOT}/templates/encadre-en-bref.html` | 3-5 points autonomes, en tête ou en fin d'article |
| Sommaire | `${CLAUDE_PLUGIN_ROOT}/templates/sommaire.html` | ancres vers les H2, sans JavaScript |
| Chiffres clés | `${CLAUDE_PLUGIN_ROOT}/templates/encadre-chiffres-cles.html` | 3-4 chiffres, chacun sourcé |
| Encadré | `${CLAUDE_PLUGIN_ROOT}/templates/encadre.html` | conseil, attention, limites (YMYL) |
| Figure légendée | `${CLAUDE_PLUGIN_ROOT}/templates/figure-legendee.html` | image responsive, légende, crédit |
| Tableau comparatif | `${CLAUDE_PLUGIN_ROOT}/templates/tableau-comparatif.html` | lisible en mobile, option recommandée |
| CTA dans le texte | `${CLAUDE_PLUGIN_ROOT}/templates/bloc-cta-inline.html` | l'appel contextuel d'un article |
| FAQ | `${CLAUDE_PLUGIN_ROOT}/templates/composant-faq.html` | Répondre aux questions, alimenter le JSON-LD `FAQPage` |
| Bannière E-E-A-T | `${CLAUDE_PLUGIN_ROOT}/templates/banniere-eeat.html` | **Prouver** qui parle |
| Bannière témoignages | `${CLAUDE_PLUGIN_ROOT}/templates/banniere-temoignages.html` | Faire parler des clients **réels** |
| Bannière lead magnet | `${CLAUDE_PLUGIN_ROOT}/templates/banniere-lead-magnet.html` | Capturer un email contre une ressource |
| Bannière contact / devis | `${CLAUDE_PLUGIN_ROOT}/templates/banniere-contact.html` | **Déclencher** l'action |
| Bloc auteur | `${CLAUDE_PLUGIN_ROOT}/templates/bloc-auteur.html` | Signature, expertise, date de mise à jour |
| Page de service | `${CLAUDE_PLUGIN_ROOT}/templates/page-service.html` | Le gabarit service assemblé |

Tous : CSS scopé sous leur classe racine, couleurs en variables `--dcp-*`,
aucune ligne vide, aucun JavaScript, aucune dépendance.

**FAQ.** Classes préfixées (`dcp-faq-…`). `<details>` sans JavaScript de
préférence. Si un accordéon JS est imposé, il se scope avec
`bouton.closest('.dcp-faq')`, **jamais par `id`** : deux FAQ sur la même
page (ou un widget dupliqué) partagent les mêmes `id` et le second
accordéon pilote le premier. Réponses de **3 phrases maximum**, la première
répond seule. Le JSON-LD `FAQPage` est inclus et reprend le texte visible
mot pour mot — sur un site qui a déjà un `@graph`, le nœud va dans ce graphe
(voir `seo-schema-jsonld`).

**Bannière E-E-A-T** — pleine largeur : photo réelle, sceau, titre
« [métier] depuis [année] », badges de preuve, CTA téléphone. **Uniquement
des preuves réelles et vérifiables** (certification avec numéro, année
tirée des mentions légales, avis avec leur source) : un badge invérifiable
retire de la confiance. Voir `seo-eeat`.

**Bannière contact / devis** — distincte de la précédente : l'une prouve,
l'autre demande. Fusionnées, elles font les deux à moitié, et le lecteur
voit la demande avant la preuve.

**Bannière témoignages** — avis réels, mot pour mot, attribués (prénom +
initiale, fonction ou ville, date, source avec lien). Sans avis réels, pas de
bannière. Pas de balisage `Review` sur votre propre entreprise : Google
n'affiche pas d'étoiles pour des avis auto-publiés.

**Composants collés inline** — corriger un modèle ne corrige pas les pages
déjà publiées. La classe racine du composant sert de signature pour
remplacer son seul bloc `<style>` partout, à l'identique, après un essai à
blanc.

## Le schema

Générez le JSON-LD correspondant au type de page selon `seo-schema-jsonld`.
Sur un site statique, il va dans un seul `<script type="application/ld+json">`
en fin de bloc. **Sur un CMS avec un plugin SEO, il ne va pas dans le
fragment** : le plugin pose déjà un graphe, et un second script crée deux
`Organization` que Google ignore toutes les deux. Livrez les nœuds à part,
pour injection dans le graphe du plugin côté serveur. Contrôle :
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/schema_validate.py" page-<slug>.html --strict`.

## Contraintes par plateforme

| Plateforme | À savoir |
|------------|----------|
| **Elementor** | Widget « HTML personnalisé », fragment sans `<html>`/`<body>`. Le CSS doit être dans le bloc. Section Elementor en pleine largeur, ou bandes en `100vw`. Un H1 existe souvent déjà dans le template — ne le doublez pas. |
| **WordPress (Gutenberg)** | Bloc « HTML personnalisé ». Attention aux filtres de contenu qui suppriment certaines balises. |
| **Webflow** | Embed HTML limité à 50 000 caractères. Découpez si nécessaire. Préférez les composants et variables natifs. |
| **Next.js / React** | Un composant par bloc, contenu en JSON, `next/image` (`priority` sur la seule image LCP), `next/font`. |
| **Site statique** | Aucune contrainte. Vous pouvez sortir le CSS dans une feuille séparée. |

## Livrables

- `design-<slug>.md` — le plan de `seo-design-pages` (gabarit, CTA, images)
- `page-<slug>.html` — la page complète, autonome (fragment)
- `faq-<slug>.html`, `banniere-eeat.html`, `banniere-contact.html` — les composants, un fichier chacun
- `page-<slug>.jsonld` — le schema, si séparé
- `INSTRUCTIONS.md` — où coller, quoi vérifier après collage

Avant de livrer :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit_images.py" page-<slug>.html --strict
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/controle_contenu.py" page-<slug>.html
```

puis la checklist de `seo-design-pages` (`references/checklist-design.md`)
et le rendu réel via le MCP Chrome DevTools, à 390 et 1 440 px, servi en
HTTP. Une page qui casse en mobile ne se voit pas dans le code.
