---
name: seo-design-pages
description: >
  Conçoit le design d'une page SEO qui convertit : gabarit section par
  section selon le type de page (service, article, page locale, landing,
  comparatif, outil ou calculateur, lead magnet), placement et nombre des
  CTA, choix des bannières (contact, confiance E-E-A-T, témoignages, lead
  magnet), plan d'images (hero, corps, schémas, Open Graph, génération),
  tokens de design, règles mobile, accessibilité, performance, et checklist
  avant publication. Pour WordPress/Elementor, Webflow et Next.js/React.
  Déclencher sur "design de la page", "maquette", "structure de la page",
  "gabarit", "où mettre les CTA", "combien de CTA", "bannière", "hero",
  "images de la page", "plan d'images", "génère une image", "la page ne
  convertit pas", "mise en page", "composants", "design system", "UX de la
  page", "page de conversion".
---

# Design de pages SEO — la page qui se lit, se cite et convertit

Une page SEO bien écrite mais mal construite perd sur les trois tableaux :
le lecteur ne trouve pas la réponse, le moteur n'extrait rien de propre, et
personne ne clique. Le design n'est pas une couche de décoration posée après
la rédaction : c'est l'ordre des sections, la place des preuves, le nombre de
CTA et le rôle de chaque image. Tout cela se décide **avant** d'écrire le
HTML.

Ce skill donne la méthode. `seo-page-builder-html` fabrique ensuite le HTML
avec les composants de `${CLAUDE_PLUGIN_ROOT}/templates/`.

## Le déroulé

```
1. Typer        → quel type de page ? (tableau ci-dessous)
2. Gabarit      → la suite de sections du type          references/gabarits-par-type-de-page.md
3. Plan de CTA  → une action, ses emplacements, ses libellés   references/cta-et-bannieres.md
4. Bannières    → lesquelles, dans quel ordre, avec quelles preuves réelles
5. Plan d'images→ un rôle par image, formats, poids, alt      references/images.md
5 bis. Matière  → au moins 3 éléments réels : logos, captures, avant / après,
                  photos, schémas tirés des données          references/matiere-reelle.md
6. Tokens       → palette, typo, espacements du site          references/design-tokens.md
7. Construire   → composants + contraintes de la plateforme   references/integration-plateformes.md
8. Contrôler    → checklist bloquante, rendu réel 390 et 1440 px   references/checklist-design.md
```

Ne sautez pas l'étape 1. Une page de service construite comme un article
enterre le CTA sous 1 500 mots ; un article construit comme une landing page
se fait refuser l'extraction par les moteurs IA, parce que la réponse est
noyée dans l'argumentaire.

## 1. Typer la page

| La requête ou le besoin… | Type | Ce qui décide du gabarit |
|---|---|---|
| « [service] », « [service] prix », « agence [métier] » | **Page service** | problème → preuve → offre → action |
| « comment… », « qu'est-ce que… », « pourquoi… » | **Article / guide** | la réponse d'abord, le CTA ensuite |
| « [service] [ville] » | **Page locale** | contenu propre à la ville, zone d'intervention |
| trafic payant, campagne, lancement, produit | **Landing** | une promesse, une démonstration, une action |
| « X vs Y », « alternative à X », « meilleur [catégorie] » | **Comparatif** | le verdict et le tableau dans le premier écran |
| « calcul », « simulateur », « combien de… » | **Outil / calculateur** | l'outil dans le premier écran, la méthode sous l'outil |
| ressource contre un email | **Lead magnet** | la valeur visible avant le formulaire |

Une page qui hésite entre deux types (un guide qui vend, une landing qui
explique) choisit selon l'intention dominante de la SERP — voir
`seo-serp-analysis`. En cas de doute, regardez le format des trois premiers
résultats : c'est celui que Google a validé pour cette requête.

## 2. Les sept règles qui valent pour tous les types

1. **La réponse avant l'argumentaire.** Le premier écran contient le H1, une
   réponse directe de 40 à 60 mots (ou la promesse chiffrée pour une page
   commerciale) et l'action principale. C'est ce paragraphe que les moteurs
   extraient.
2. **La preuve avant la demande.** Chiffres sourcés, auteur réel, méthode
   montrée : ils précèdent chaque CTA insistant. Une bannière de contact qui
   arrive avant toute preuve ne convertit pas.
3. **Une seule action principale**, répétée à l'identique (même libellé,
   même destination) à chaque emplacement prévu par le gabarit. Une action
   secondaire à plus faible engagement (téléphone, démo, WhatsApp) au plus.
4. **Chaque image a un rôle.** Elle prouve (photo réelle), elle explique
   (schéma tiré du contenu), elle montre (capture, maquette) — ou elle n'existe
   pas. Une illustration décorative alourdit la page et ne dit rien.
5. **Rien d'inventé.** Pas de faux témoignages, faux logos clients, compteurs
   gonflés, notes étoilées sans source, badges invérifiables. C'est une
   pratique commerciale trompeuse (Code de la consommation, art. L121-2 et
   suivants), c'est détectable, et une preuve fausse détruit la confiance que
   dix vraies ont construite. Voir `seo-eeat`.
6. **Le contenu reste visible sans JavaScript.** Texte, FAQ, tableaux et
   méthode d'un outil sont dans le HTML initial. Une animation d'apparition
   qui masque le contenu jusqu'à l'exécution d'un script finit toujours par
   laisser une page blanche quelque part.
7. **Au moins trois éléments de matière réelle**, de deux types au moins :
   logos des outils et plateformes cités, captures réelles (résultats,
   SERP, interface), exemple avant / après, photo réelle, schéma tiré des
   données sourcées. Chacun avec `alt` et légende. Sans eux, une page juste
   et bien construite reste plate : c'est le premier reproche d'un client
   à la relecture. Types, sources, interdits et pièges :
   `references/matiere-reelle.md` ; contrôle :
   `audit_images.py --matiere 3 --strict`.

## 3. Le plan de CTA en une minute

| Longueur de la page | CTA principaux | Où |
|---|---|---|
| Courte (< 800 mots) | 2 | hero · fin |
| Moyenne (800 à 2 000 mots) | 3 | hero · après la preuve ou la solution · fin |
| Longue page commerciale | 4 à 5 | chaque bande pleine largeur qui suit une preuve |
| Article | 2 + barre latérale | encart contextuel au milieu · fin · barre latérale collante sur ordinateur |

Libellé : **verbe + objet + bénéfice** (« Recevoir mon devis sous 48 h »),
jamais « En savoir plus » ni « Envoyer ». Sous le bouton, une ligne de
réassurance vraie (délai de réponse, gratuité, absence d'engagement). Tout
le détail, les bannières et les cas particuliers :
`references/cta-et-bannieres.md`.

## 4. Les composants disponibles

Fragments autonomes, CSS scopé, couleurs en variables, sans dépendance, sans
JavaScript. Un composant = un fichier = un widget.

| Composant | Fichier | Rôle |
|---|---|---|
| Hero | `hero.html` | H1, réponse directe, action principale, visuel LCP |
| En bref | `encadre-en-bref.html` | 3 à 5 points à retenir, en tête ou en fin d'article |
| Sommaire | `sommaire.html` | ancres vers les H2, articles longs |
| Chiffres clés | `encadre-chiffres-cles.html` | 3-4 chiffres sourcés et datés |
| Encadré | `encadre.html` | conseil, point d'attention, limites (YMYL) |
| Figure légendée | `figure-legendee.html` | image responsive, légende, crédit |
| Tableau comparatif | `tableau-comparatif.html` | comparaison lisible en mobile, option recommandée |
| CTA dans le texte | `bloc-cta-inline.html` | l'appel contextuel au milieu d'un article |
| Bannière confiance | `banniere-eeat.html` | qui parle, preuves vérifiables |
| Bannière témoignages | `banniere-temoignages.html` | avis réels, attribués et sourcés |
| Bannière lead magnet | `banniere-lead-magnet.html` | ressource, aperçu, formulaire court |
| Bannière contact | `banniere-contact.html` | déclencher l'action |
| Bloc auteur | `bloc-auteur.html` | signature, expertise, date de mise à jour |
| FAQ | `composant-faq.html` | `<details>` natif + JSON-LD `FAQPage` |
| Page de service complète | `page-service.html` | le gabarit service assemblé |

Tous lisent les mêmes variables (`--dcp-primaire`, `--dcp-accent`,
`--dcp-encre`…) avec une valeur neutre par défaut : déclarez la palette du
site **une fois** et tous les composants la prennent. Voir
`references/design-tokens.md`.

## 5. Les images

Le plan d'images se décide avec le gabarit, pas après la rédaction. Pour
chaque emplacement : rôle, source (photo réelle, schéma, capture, image
générée), ratio, poids cible, `alt`, légende. Détail par type de page,
formats, poids et génération : `references/images.md`.

Générer une image (Gemini, ou OpenAI en repli) avec un prompt construit à
partir du style du site, du ratio de l'emplacement et du sujet — sans texte
dans l'image, sans logo, sans faux visage — plus une proposition d'`alt` :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/images_generer.py" \
  --sujet "Bureau de cabinet de conseil, dossiers ouverts et ordinateur portable" \
  --emplacement hero --langue fr --dry-run
```

`--dry-run` affiche le prompt sans rien appeler ni facturer. Contrôle des
images d'une page produite, hors ligne, avec le minimum de matière réelle :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit_images.py" page-<slug>.html --matiere 3 --strict
```

## 6. La plateforme

| Cible | Ce qui change | Détail |
|---|---|---|
| **WordPress / Elementor** | fragment HTML collé dans un bloc HTML ; aucune ligne vide ; CSS minifié ; H1 du thème | `references/integration-plateformes.md` |
| **Webflow** | composants et variables natifs ; embed limité à 50 000 caractères | idem |
| **Next.js / React** | un composant par bloc, contenu en JSON, `next/image`, `next/font` | idem |
| **Site statique** | aucune contrainte ; CSS commun dans une feuille | idem |

## 7. Avant de livrer

`references/checklist-design.md` est bloquante. Les quatre points qui
échouent le plus souvent :

- le **rendu mobile réel** n'a pas été regardé (390 px) : tableau qui
  déborde, titre coupé, bouton hors écran ;
- l'**image LCP** est en `loading="lazy"`, ou sans `width`/`height` ;
- un **CTA pointe vers une URL qui n'existe pas**, ou un bouton
  « Télécharger » ne télécharge rien ;
- une **preuve affichée n'a pas de source** (note, chiffre, logo, avis) ;
- la page n'a **aucune matière réelle** (ni logo, ni capture, ni exemple,
  ni schéma) : juste, mais plate.

Vérifiez le rendu dans le vrai thème, avec les vraies polices, servi en HTTP
(jamais en `file://`, où le chargement différé et les animations ne se
déclenchent pas et simulent de fausses régressions). La capture ne fait pas
foi, le DOM si : `scripts/rendu.py` (ou le MCP Chrome DevTools) compte les
éléments qui débordent ; et un fragment WordPress se relit **tel que servi**,
après wpautop. Pour une photo de lieu réelle et créditée :
`scripts/photos_libres.py` (`references/images.md`).

## Livrables

- `design-<slug>.md` — type, gabarit retenu section par section, plan de
  CTA, bannières, plan d'images (emplacement, source, ratio, `alt`) et les
  trois éléments de matière réelle au moins (type, source, légende)
- les fragments HTML (via `seo-page-builder-html`) ou les composants du site
- `images/` + un fichier `.json` par image générée (prompt, `alt` proposé à
  valider)
- la checklist remplie, avec les captures 390 px et 1440 px
