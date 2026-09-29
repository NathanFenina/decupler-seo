---
name: seo-cycle
description: >
  Le cycle SEO autonome d'un projet, en quatre modes : veille (quotidienne),
  optimisation (hebdo), contenu (hebdo), rapport (mensuel). Lit la mémoire du
  projet, décide sur les données Search Console, agit dans les limites des
  niveaux d'autonomie, journalise chaque modification et laisse une trace de
  chaque exécution. C'est le skill que lancent les routines. Déclencher sur
  "lance le cycle", "mode veille", "mode optimisation", "mode contenu",
  "mode rapport", "cycle hebdo", "routine SEO", ou quand une routine le demande.
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

## Étape 0 — Commune aux quatre modes

1. Lire `CLAUDE.md`, `decupler-seo.config.yml`, `memoire/decisions.md`,
   `memoire/apprentissages.md`. Une proposition déjà refusée dans
   `decisions.md` ne revient pas. Un type de modification noté comme
   nuisible dans `apprentissages.md` n'est plus appliqué automatiquement.
2. État du garde-fou :
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/guard.py" --statut`
   Si le mode est `safe`, vous ne publiez rien : vous produisez les fichiers
   et les propositions, point.
3. Identifier la source Search Console disponible, dans cet ordre : outils
   du MCP `search-console`, connecteur (Windsor.ai ou autre) exposant Search
   Console, export CSV déposé dans `donnees/`. **Si aucune n'est disponible,
   le dire dans le journal de run et s'arrêter** — on ne pilote pas à
   l'aveugle.

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

Anomalie → une entrée dans `rapports/a-valider.md` répondant à quatre
questions : **quoi, depuis quand, combien ça coûte, quoi faire**. Pas
d'anomalie → aucune entrée. Le silence est le bon comportement.

## Mode optimisation — hebdomadaire

1. **Instantané.** Search Console, 28 derniers jours, dimensions page +
   requête. Enregistrer dans `donnees/AAAA-SWW.json`.
2. **Mesures dues d'abord.** `seo-journal-mesure`, étape « mesurer » : on
   évalue ce qui a été fait avant d'en faire davantage.
3. **Candidats** : pages en position 4-20, au moins 100 impressions, non
   modifiées depuis 28 jours (vérifier dans `journal/modifications.csv` :
   modifier une page en cours de mesure fausse sa mesure).
4. **Diagnostic** selon `seo-quick-wins` : snippet, contenu, cannibalisation.
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
7. **Pour chaque action à valider** : brouillon dans le CMS, et une entrée
   dans `rapports/a-valider.md` avec le lien du brouillon et le gain attendu.

## Mode contenu — hebdomadaire

1. Lire la file éditoriale (`contenus/file.md` si elle existe, sinon
   proposer les sujets depuis `seo-keyword-research` et `seo-cocon-semantique`).
2. Au plus `cycle.pages_neuves_par_semaine_max` pages. **Jamais au-delà**,
   même si la file est longue : la mise à jour spam d'août 2026 a frappé des
   sites qui publiaient en masse, pas des sites qui publiaient lentement.
3. Pour chacune : `seo-brief` → `seo-redaction` (+ `projet-marque`) →
   `seo-optimisation-onpage` jusqu'à 85/100 minimum → brouillon CMS.
4. Chaque page : une entrée dans `rapports/a-valider.md`. Une fois publiée
   par un humain, elle sera journalisée comme `page-neuve`.

## Mode rapport — mensuel

1. `seo-journal-mesure` : mesurer tout ce qui est échu, puis `bilan`.
2. Reporter dans `memoire/apprentissages.md` uniquement ce que `bilan`
   signale (au moins 3 mesures du même type). Pas d'intuition.
3. Lister dans `rapports/a-valider.md` les retours arrière proposés
   (`journal.py a-annuler`).
4. Écrire `rapports/AAAA-MM.md` selon `seo-reporting`, et
   `rapports/AAAA-MM.json` avec ces clés, toujours les mêmes, pour que les
   rapports de tous les projets s'additionnent :
   ```json
   {"projet": "", "mois": "AAAA-MM", "clics": 0, "impressions": 0,
    "position_moyenne": 0, "clics_variation_pct": 0,
    "modifications": 0, "gains": 0, "neutres": 0, "pertes": 0,
    "a_valider": 0, "runs_attendus": 0, "runs_trouves": 0}
   ```
5. **Vérifier les routines** : compter les fichiers de `rapports/runs/` du
   mois. Environ 30 veilles, 4 optimisations, 4 contenus attendus. Toute
   absence est signalée en tête du rapport.

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
