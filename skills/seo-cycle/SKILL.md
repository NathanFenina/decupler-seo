---
name: seo-cycle
description: >
  Le cycle SEO autonome d'un projet : le mode hebdo (le mercredi, par défaut,
  qui enchaîne contrôle, actions validées, mesure et bilan de la semaine dans
  la page de suivi), ou quatre modes séparés pour un gros site : veille
  (quotidienne), optimisation (hebdo), contenu (hebdo), rapport (mensuel). Lit la mémoire du
  projet, décide sur les données Search Console, agit dans les limites des
  niveaux d'autonomie, journalise chaque modification et laisse une trace de
  chaque exécution. C'est le skill que lancent les routines. Déclencher sur
  "lance le cycle", "mode veille", "mode optimisation", "mode contenu",
  "mode rapport", "mode hebdo", "cycle hebdo", "routine du mercredi",
  "routine SEO", ou quand une routine le demande.
---

# Le cycle SEO autonome

Vous travaillez seul, sans personne pour valider en direct. Trois règles en
découlent, avant tout le reste :

1. **Le périmètre est écrit, pas deviné.** Ce que vous avez le droit de faire
   est dans `CLAUDE.md` (niveaux d'autonomie) et `decupler-seo.config.yml`
   (`cycle`, `seuils`). Dans le doute, une action passe au niveau supérieur :
   automatique → validation → proposition.
2. **Rien n'est fait tant que ce n'est pas journalisé.** Chaque publication
   passe par `seo-journal-mesure` avant la suivante.
3. **Chaque exécution laisse une trace**, y compris quand il n'y avait rien
   à faire. C'est le seul moyen de savoir qu'une routine a réellement tourné.

## Étape 0 — Commune à tous les modes

1. Lire `CLAUDE.md`, `decupler-seo.config.yml`, `memoire/decisions.md`,
   `memoire/apprentissages.md`. Une proposition déjà refusée dans
   `decisions.md` ne revient pas. Un type de modification noté comme
   nuisible dans `apprentissages.md` n'est plus appliqué automatiquement.
2. État du garde-fou :
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/guard.py" --statut`
   Si le mode est `safe`, vous ne publiez rien : vous produisez les fichiers
   et les propositions, point.
3. Identifier la source Search Console disponible, dans cet ordre :
   `gsc.py` (identifiants `GSC_SA_JSON` dans l'environnement), outils du MCP
   `search-console`, connecteur (Windsor.ai ou autre) exposant Search
   Console, export CSV déposé dans `donnees/`. **Si aucune n'est disponible,
   le dire dans le journal de run et s'arrêter** — on ne pilote pas à
   l'aveugle.

## Mode hebdo — le mercredi, la routine par défaut

Un seul passage par semaine fait le travail des quatre modes ci-dessous, dans
cet ordre, et le consigne dans la page de suivi (skill `seo-pilotage`) :

1. **Contrôle** : le mode veille ci-dessous (lecture seule).
2. **Mesure** : instantané Search Console, puis les mesures dues
   (`seo-journal-mesure`) avant toute nouvelle modification.
3. **Actions validées** sur la page de suivi, tous chantiers confondus, selon
   les règles des modes optimisation et contenu (plafonds, niveaux
   d'autonomie, journal). Une action qui attend quelqu'un passe en `bloquee`
   avec `--attend` : elle remonte dans « À décider ».
4. **Sans action validée** : le travail automatique du mode optimisation.
   Aucune page neuve sans action validée.
5. **Premier mercredi du mois** : le mode rapport, puis les propositions du
   mois (`pilotage.py proposer` et `injecter`).
6. **Bilan de la semaine** dans l'onglet du mois : `pilotage.py mois` (résumé,
   wins mesurés, contenus avec leur lien Notion, reporting), republication, puis
   `pilotage.py sauvegarder` (copie `journal/pilotage.json` dans git).

Le détail de chaque étape est dans `routines/hebdo.md` du projet.

## Mode veille — quotidien, lecture seule

Rien n'est écrit sur le site. Contrôlez les pages prioritaires
(`projet.pages_prioritaires`, à défaut les 10 pages à plus d'impressions du
dernier instantané) :

- code HTTP 200
- absence de `noindex` (meta et en-tête `X-Robots-Tag`) :
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fetch_page.py" <url> --json`
- canonical inchangée depuis le dernier passage
- robots.txt inchangé (comparer à `donnees/robots-reference.txt`, le créer
  au premier passage)
- sitemap accessible

Puis le contrôle complet de production, qui fait tout cela sur **chaque URL
du sitemap** (200 sans redirection, https, pas de noindex, canonical
auto-référente, robots.txt sain) :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/seo_live.py" --json
```

Il retente deux fois avant de déclarer une page injoignable : une alerte
fausse coûte plus cher qu'elle n'en a l'air, parce qu'elle apprend à ignorer
les vraies.

Anomalie → une entrée dans `rapports/a-valider.md` répondant à quatre
questions : **quoi, depuis quand, combien ça coûte, quoi faire**. Pas
d'anomalie → aucune entrée. Le silence est le bon comportement.

## Publier : deux mécaniques selon le site

`decupler-seo.config.yml` → `publication.mode` :

**`cms`** — WordPress, Webflow, Contentful… Publication par l'API, via
`seo-publication-cms` : sauvegarde, écriture, vérification. Les pages neuves
partent en brouillon.

**`depot`** — site en code (Next.js, Astro, générateur statique) : le
contenu vit dans le dépôt, et **publier, c'est fusionner**.
1. Travailler sur une branche `claude/<mode>-AAAA-MM-JJ` partie de la
   branche principale à jour.
2. Contrôles, tous bloquants :
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/controle_contenu.py" <fichiers modifiés>`,
   puis chaque commande de `controle.commandes` (typiquement le build, le
   typage, le contrôle de contenu du site).
3. Ouvrir une pull request qui liste les pages, les requêtes visées, le
   résumé du benchmark et tout chiffre « à confirmer ».
4. **Fusionner seulement si** tous les contrôles sont verts, qu'aucun chiffre
   n'est resté douteux, et que le mode est `autonomous`. Sinon, laisser la
   PR ouverte et écrire dans sa description ce qui bloque. Le déploiement
   suit la fusion : sur ce type de site, une fusion est une mise en ligne.
   Si la session refuse la fusion (permissions), même chose : PR ouverte,
   « à fusionner par un humain » dans la description et le journal de run,
   puis terminer — une routine n'attend jamais de réponse.
5. Après déploiement : `seo_live.py --ping` (IndexNow si `INDEXNOW_KEY`
   est défini).

## Mode optimisation — hebdomadaire

1. **Instantané.** `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gsc.py" instantane` — page ×
   requête, 28 derniers jours, écrit dans `donnees/AAAA-SWW.json`.
2. **Mesures dues d'abord.** `seo-journal-mesure`, étape « mesurer » : on
   évalue ce qui a été fait avant d'en faire davantage.
3. **Candidats, dans l'ordre** : `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/opportunites.py" --ecrire`
   (skill `seo-opportunites`). Le classement pondère par la valeur des
   thèmes du client (`memoire/lexique.csv`) et exclut déjà les pages en
   cours de mesure : modifier une page en cours de mesure fausse sa mesure.
   On prend les actions de haut en bas.
4. **Diagnostic** de chaque candidat selon `seo-quick-wins` : snippet,
   contenu, cannibalisation.
5. **Agir, dans le plafond** `cycle.pages_optimisees_par_semaine_max` :

| Diagnostic | Action | Niveau |
|---|---|---|
| CTR sous la moitié de l'attendu | nouveau title et meta (`seo-meta-serp`) | automatique |
| Questions PAA non couvertes | FAQ ajoutée (`seo-faq-paa`) | automatique |
| Schema absent ou invalide | JSON-LD (`seo-schema-jsonld`) | automatique |
| Page sous-liée | 3 liens internes contextuels (`seo-maillage-interne`) | automatique |
| Sections manquantes face au top 3 | réécriture de section | **validation** |

   Chaque texte produit applique `projet-marque` si le projet en a un.
6. **Pour chaque action automatique**, dans cet ordre, sans en sauter :
   garde-fou → sauvegarde → publication → vérification que la page affiche
   bien la modification → `seo-journal-mesure` (ajout avec la situation de
   départ). Une étape qui échoue arrête l'action, et on passe à la suivante.
7. **Pour chaque action à valider** : brouillon dans le CMS (ou pull
   request laissée ouverte en mode `depot`), et une entrée dans
   `rapports/a-valider.md` avec le lien et le gain attendu.

## Mode contenu — hebdomadaire

0. Si `memoire/decisions.md` confie le contenu à un skill propre au projet
   (une routine de contenu existait avant l'adoption), ce mode ne fait rien :
   deux routines qui écrivent les mêmes pages se contredisent.
1. **Les idées viennent de la demande, pas de l'intuition.** Une fois par
   mois (première semaine), rafraîchir la demande puis le calendrier :
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/demande.py" idees --lexique --langue <langue> --ecrire   # par langue du projet
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/opportunites.py" --demande donnees/demande-<langue>-<date>.csv \
     --calendrier --semaines 4 --capacite <cycle.pages_neuves_par_semaine_max> --ecrire
   ```
   Le calendrier (`rapports/calendrier-*.md`) respecte le mix TOFU/MOFU/BOFU
   de `opportunites.mix`, 80 % de créations et 20 % d'optimisations, et
   propose un outil ou une ressource quand la requête en demande un. Chaque
   semaine, prendre les lignes de la semaine ; à défaut, la file éditoriale
   (`contenus/file.md` ou celle que désigne `memoire/decisions.md`).
2. Au plus `cycle.pages_neuves_par_semaine_max` pages. **Jamais au-delà**,
   même si la file est longue : la mise à jour spam d'août 2026 a frappé des
   sites qui publiaient en masse, pas des sites qui publiaient lentement.
3. Pour chacune — en parallèle, un agent par page quand elles sont
   indépendantes :
   - `serp_concurrents.py --mot "<requête>"` : top 5 lu page par page
     (plan Hn, longueur, FAQ, schémas), questions « Autres questions
     posées », AI Overview et ses sources, termes du top absents chez nous ;
   - `seo-benchmark` (au moins 5 axes gagnés, sinon la page n'est pas prête) ;
   - `seo-brief` (18 sections + triplets à affirmer, écrit dans
     `recherche/briefs/`), dans le style mesuré de `memoire/style.md` ;
   - `seo-redaction` (+ `projet-marque`, et la passe anti-cannibalisation) ;
   - `seo-design-pages` : gabarit du type de page, CTA, bannières, plan
     d'images (`images_generer.py` si aucune photo réelle ne convient) ;
   - contrôles bloquants : `seo-optimisation-onpage` jusqu'à 85/100,
     `controle_contenu.py`, `triplets.py verifier --strict`,
     `audit_images.py --strict`, `schema_validate.py --strict`.
4. **Chaque chiffre** est vérifié à sa source officielle et reporté dans
   `memoire/faits.md` et `memoire/triplets.csv`, la seule source des chiffres
   du site : un même fait ne doit jamais avoir deux valeurs sur deux pages.
   Une fois par semaine : `triplets.py coherence contenus/ --triplets
   memoire/triplets.csv` (ou le dossier des contenus du site).
5. Publication selon `publication.mode` (voir plus haut) : brouillon CMS
   (`wp.py publier` sur WordPress) et entrée dans `rapports/a-valider.md`, ou
   pull request. Chaque page publiée entre au journal avec les requêtes
   qu'elle vise : `journal.py ajouter --auto --type page-neuve --url <url>
   --requete "<requête 1> | <requête 2>"`, et sa ligne de
   `memoire/cartographie.csv` passe en « publiee ».

### La boucle de fraîcheur — une page par semaine

En plus des pages neuves, reprendre **la page publiée revérifiée depuis le
plus longtemps** (date de dernière vérification, ou à défaut de dernière
modification ; pages légales exclues). Revérifier chacun de ses chiffres à
la source, corriger ce qui a changé — en le signalant dans la page si une
règle a bougé — puis mettre à jour sa date de vérification.

**Ne jamais changer une date de mise à jour sans avoir réellement
revérifié.** Une fraîcheur affichée mais fausse est exactement ce que les
évaluateurs de Google et les moteurs IA apprennent à repérer.

## Mode rapport — mensuel

1. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/journal.py" mesurer-tout --auto`, puis `bilan`
   (voir `seo-journal-mesure`).
2. Reporter dans `memoire/apprentissages.md` uniquement ce que `bilan`
   signale (au moins 3 mesures du même type). Pas d'intuition.
3. Lister dans `rapports/a-valider.md` les retours arrière proposés
   (`journal.py a-annuler`).
4. **Visibilité IA**, même liste chaque mois : `share_of_model.py --prompts
   recherche/prompts-ia.csv --concurrents "<concurrents de la config>"
   --exporter donnees/ia-<AAAA-MM>.csv` (le mois du rapport), puis
   une fois par trimestre `--sans-web --exporter donnees/ia-<AAAA-MM>-sans-web.csv`
   (notoriété). Dans le rapport : la
   visibilité par moteur, son évolution, et les prompts MOFU/BOFU où la
   marque manque partout — ce sont les briefs du mois suivant (`seo-redaction`,
   « Article GEO : gagner un prompt IA »).
5. **La cartographie, avant le rapport** (si `memoire/cartographie.csv`
   existe, skill `seo-cartographie`) :
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cartographie.py" mensuel --mois <AAAA-MM>`.
   Elle écrit `rapports/cartographie-AAAA-MM.md` et une ligne par page dans
   `donnees/cartographie-historique.csv` : la position de chaque page sur son
   mot-clé principal et la citation de son prompt principal par ChatGPT,
   Gemini et Claude, reprise des relevés de l'étape 4. Pas d'option payante
   (`--volumes`, `--prompts`) en routine sans accord écrit dans
   `memoire/decisions.md`. Une cannibalisation signalée va dans
   `rapports/a-valider.md`.
6. **Les chiffres par script** : `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/rapport.py"`
   écrit la partie factuelle de `rapports/AAAA-MM.md` et `rapports/AAAA-MM.json`
   (mois, mois précédent, an passé ; marque et hors marque ; pages et requêtes
   en hausse et en baisse ; requêtes nouvelles ; verdicts ; routines ; la
   synthèse de la cartographie quand elle existe). Vous
   rédigez seulement la section « Lecture et décisions » selon `seo-reporting` :
   les causes, pas les courbes. Ne recalculez jamais un chiffre à la main.
   Le JSON garde ces clés, toujours les mêmes, pour que les rapports de tous
   les projets s'additionnent :
   ```json
   {"projet": "", "mois": "AAAA-MM", "clics": 0, "impressions": 0,
    "position_moyenne": 0, "clics_variation_pct": 0,
    "modifications": 0, "gains": 0, "neutres": 0, "pertes": 0,
    "a_valider": 0, "runs_attendus": 0, "runs_trouves": 0}
   ```
   Une clé `cartographie` s'y ajoute (null sans cartographie) : pages suivies,
   hausses et baisses sur les mots-clés principaux, prompts gagnés et perdus.
7. **Opportunités** : `opportunites.py --ecrire`, et dans le rapport les
   cinq premières actions, les thèmes de valeur 3 non couverts, et ce qui a
   changé depuis le classement du mois précédent.
8. **Vérifier les routines** : `rapport.py` compte les journaux de
   `rapports/runs/` **et** les branches poussées par les routines
   (`claude/hebdo-AAAA-MM-JJ`, `claude/veille-…`, `claude/optimisation-…`, `contenu/…`) : une
   routine travaille sur sa branche, son journal n'atteint la branche
   principale qu'à la fusion. Au rythme hebdo : un passage par semaine du
   mois ; avec les quatre routines : environ 30 veilles, 4 optimisations,
   4 contenus. Toute absence est signalée en tête du rapport. Recopier ensuite
   dans la branche du rapport les journaux de veille du mois (`git show
   origin/claude/veille-<date>:rapports/runs/<date>-veille.md`), pour qu'ils
   arrivent sur la branche principale avec lui.

## Le journal de run — obligatoire, dans tous les modes

À la fin de chaque exécution, même sans rien à faire :
`rapports/runs/AAAA-MM-JJ-<mode>.md`

```markdown
# <mode> — AAAA-MM-JJ
- Source Search Console : <MCP / connecteur / CSV / aucune>
- Mode du garde-fou : <safe / assisted / autonomous>
- Publié automatiquement : N (ids du journal : …)
- Soumis à validation : N
- Mesuré : N (gains / neutres / pertes)
- Anomalies : N
- Problèmes rencontrés : <outil absent, erreur, refus du garde-fou…>
```

Puis commit sur une branche `claude/<mode>-AAAA-MM-JJ` et push.

## Ce que le cycle ne fait jamais seul

Supprimer un contenu. Toucher robots.txt, les redirections ou les canonicals
en production. Contacter quelqu'un. Publier sur un forum ou un réseau.
Modifier une fiche Google Business. Dépasser un plafond. Il le propose dans
`rapports/a-valider.md`, et un humain décide.
