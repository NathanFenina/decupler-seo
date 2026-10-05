---
name: seo-lead-magnet
description: >
  Crée ou refond une page « lead magnet » (guide, kit, modèles, checklist
  offerts contre un email) qui ranke ET capture : ciblée sur un mot-clé
  principal et un prompt IA principal, authentique (logos et visuels réels
  des outils cités, exemples réels, parti pris signé, limites assumées),
  avec un livrable téléchargeable, un formulaire qui ne cache jamais le
  contenu à Google, et un parcours de capture vérifié avant publication.
  Déclencher sur "lead magnet", "aimant à prospects", "guide gratuit contre
  email", "ressource téléchargeable", "kit à télécharger", "page de
  capture", "commente X et reçois le guide", "pop-up d'inscription",
  "contenu verrouillé", "gated content", "refais ce lead magnet".
---

# Lead magnet — une page qui donne tout, ranke, et capture l'email

Un lead magnet échoue de deux façons. Soit il cache tout derrière un
formulaire : Google ne lit rien, la page ne ranke pas, et le visiteur part.
Soit il ne donne rien de concret : on promet un « guide complet » et on livre
trois paragraphes génériques. Ce skill fait l'inverse : **la page donne la
méthode en entier, en clair**, et l'email s'échange contre ce qui se garde —
le fichier, le kit, les modèles.

## 0. Cibler avant d'écrire

1. **Le mot-clé principal** : sur une niche, les requêtes réelles de la page
   ou du site (Search Console, 180 jours, page × requête) valent mieux que
   les volumes d'un outil, souvent vides. Préférez une requête qui a déjà
   des impressions en position 5-25, et une difficulté faible.
2. **Le prompt principal** : la question qu'un acheteur poserait à ChatGPT
   ou Perplexity, et dont la page doit être la réponse citée. Même règles
   que la cartographie (`seo-cartographie`) : formulé comme on parle, sans
   le nom de la marque.
3. **Anti-cannibalisation** : vérifier qu'aucune page du site ne vise déjà
   la même intention (`seo-gsc-analyses`, analyse cannibalisation).
4. **Inscrire** le mot-clé et le prompt dans la cartographie.

Le mot-clé va dans le title, le H1, la meta, le premier paragraphe et un ou
deux H2. Le prompt principal devient une question de la FAQ et la
phrase-réponse du premier écran.

## 1. Les blocs qui rendent la page crédible

Ce qui distingue un lead magnet qu'on garde d'un lead magnet qu'on oublie,
dans l'ordre d'impact constaté :

| Bloc | Pourquoi | Comment |
|---|---|---|
| **Livrable téléchargeable** | La promesse tenue, tout de suite | Un ZIP ou un PDF réel (kit, modèles, prompts, checklist), sources versionnées dans le dépôt. Un lead magnet sans rien à emporter ne tient pas sa promesse |
| **Bande de logos** des outils cités | On voit d'emblée de quoi on parle | Logos officiels (favicon ou `apple-touch-icon` du site de l'outil), hébergés sur le site |
| **Visuel officiel par outil** | Preuve que l'outil existe | `og:image` du site de l'outil, légendée « Visuel officiel, <domaine> » |
| **Exemple d'échange** ou de mise en œuvre | Montre comment on s'en sert, pas seulement quoi | Titré « Exemple » quand c'est une illustration ; « Échange réel » seulement si c'en est un, avec date et chiffres du jour |
| **Commandes repliées** (`<details>`) | La valeur technique sans effrayer | Commandes vérifiées dans la documentation officielle de chaque outil, version relevée, jamais de mémoire |
| **Exemples réels** | La preuve par le résultat | Captures fournies par le client, légendées honnêtement ; noms de sites masqués si le client le demande, avec la mention « nom masqué » |
| **Méthode pas à pas** | Donne la méthode, pas seulement l'outil | Liste numérotée tirée des exemples ; un parcours cliquable (ancres `#etape-N`) si les étapes sont longues |
| **Parti pris signé** | Une voix, une position | 2-3 paragraphes à la première personne, signés d'une personne réelle. Aucune anecdote inventée |
| **Ce que ça ne fait pas** | Le bloc le moins imitable | 4 limites concrètes |
| **CTA** | Conversion | Un encart d'inscription après le premier bloc de valeur, l'action principale (RDV, essai) en bas |

Règles de fond : aucun chiffre client, avis ou note inventé ; un chiffre
d'outil vient de sa documentation, avec la version relevée ; un exemple
fictif se dit fictif et met des crochets à la place des chiffres.

**À retirer lors d'une refonte** : affirmations invérifiables (« n°1 en
France »), gains de temps chiffrés non mesurés, sections bâties sur une
version datée d'un outil (`seo-audit-contenu` les repère).

## 2. La capture — ne jamais cacher le contenu à Google

| Visiteur | Comportement |
|---|---|
| **Moteur de recherche et visiteur organique** | Tout le contenu est dans le HTML initial, lisible. Fenêtre d'inscription **fermable**, jamais à l'arrivée sur mobile (après ~25 s ou en fin de lecture), une fois par session |
| **Visiteur d'une campagne** (lien avec paramètre, ex. `?acces=campagne`) | Fenêtre obligatoire possible : il est venu chercher la ressource promise dans le post |
| **Déjà inscrit** | Plus rien : téléchargement direct |

- **Le livrable est verrouillé, pas la page.** Le lien de téléchargement
  porte un attribut (`data-verrou`, par exemple) : le clic ouvre la fenêtre,
  et le téléchargement part tout seul après l'inscription. Sans ce verrou, un
  visiteur de campagne prend le fichier pendant les secondes qui précèdent la
  fenêtre.
- Masquer le contenu en `opacity: 0` ou derrière un flou en attente du
  formulaire, c'est le cacher aux moteurs IA et à Google — voir
  `seo-design-pages`.
- Fenêtre en `role="dialog"`, focus piégé, fermeture au clavier.
- Un service d'emailing qui n'offre pas d'API officielle d'inscription :
  vérifier, à chaque installation, qu'un email de test arrive vraiment.
- Si une autre fenêtre d'inscription existe sur le site, exclure la page
  lead magnet de celle-ci : deux fenêtres qui s'empilent font fuir.

## 3. Assembler

La page se construit avec `seo-page-builder-html` (gabarit lead magnet,
composants, bannière `banniere-lead-magnet.html`), le plan de design avec
`seo-design-pages`, le texte avec `seo-redaction`. Rythme : jamais plus de
deux bandes claires d'affilée — une bande sombre pour le kit ou le parti
pris, un ruban chiffré, une vraie photo.

**Animations au défilement** (IntersectionObserver), jamais au chargement :
sinon elles sont finies avant que le lecteur arrive. Et jamais d'opacité de
départ à zéro.

## 4. Vérifier avant de publier — non négociable

1. **Rendu réel** à 390 et 1 440 px, images servies en local : aucun
   débordement, grilles alignées, captures recadrées sur la zone utile (une
   page A4 réduite à 860 px est illisible).
2. **Les trois parcours de capture** : visiteur organique (fenêtre
   fermable), visiteur de campagne (fenêtre obligatoire, téléchargement
   après inscription), déjà inscrit (rien). Avec de vraies minuteries : une
   horloge simulée rate les `setTimeout` posés après coup.
3. **Le HTML servi par le CMS**, pas le fichier local : sur WordPress, zéro
   `<p>` vide, `<br>` parasite ou `<p><a>` ajouté par wpautop
   (`seo-publication-cms`).
4. **Un seul H1** : le thème n'ajoute pas le sien.
5. **Le livrable se télécharge** et s'ouvre.
6. Contrôles automatiques :
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/controle_contenu.py" page-<slug>.html
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit_images.py" page-<slug>.html --strict
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/schema_validate.py" page-<slug>.html --strict
   ```

## 5. Publier et tracer

- Brouillon, relecture, publication (`seo-publication-cms`). Une refonte
  se fait **à la même URL**, contenu d'origine sauvegardé.
- Cartographie à jour (mot-clé et prompt principal), journal de la
  modification (`seo-journal-mesure`), sitemap resoumis.
- Mesure à J+28 : positions sur le mot-clé, citation sur le prompt
  (`geo-share-of-model`), inscriptions — **par source** (organique contre
  campagne), sinon on ne sait pas ce que la page rapporte seule.

## Livrables

- `page-<slug>.html` — la page, prête à coller
- `<slug>-kit.zip` (ou PDF) — le livrable, sources versionnées
- `faq-<slug>.json` — la FAQ, reprise mot pour mot dans le `FAQPage`
- `VERIFICATION-<slug>.md` — captures aux deux largeurs, parcours de capture testés
