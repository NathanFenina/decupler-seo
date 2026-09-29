---
name: seo-gsc-analyses
description: >
  Bibliothèque de 20 analyses Google Search Console, chacune répondant à une
  question précise : content decay, gagnants et perdants, requêtes émergentes
  sans page, saisonnalité, cannibalisation, CTR anormal, pages à créer,
  sections manquantes, FAQ et briefs tirés des vraies requêtes, consolidation,
  panier de requêtes cibles, Google face aux IA. Déclencher sur une question
  posée aux données Search Console : "qu'est-ce qui monte / qui baisse",
  "pages qui déclinent", "content decay", "nouvelles requêtes", "c'est
  saisonnier ?", "pages qui se cannibalisent", "quelle page créer", "quelles
  questions on me pose", "fusionner des pages", "mes requêtes cibles", ou un
  export Search Console à analyser.
---

# Analyses Search Console

Search Console est la seule source qui dit ce qui se passe réellement sur
**votre** site. Chaque analyse ci-dessous répond à une question, et une
seule. Choisissez celle qui correspond à la question posée, puis lisez sa
fiche dans `references/` : données à récupérer, méthode, format de sortie,
et un prompt prêt à l'emploi.

Quand une analyse a un skill de méthode complet, il est indiqué : l'analyse
trouve **quoi** faire, le skill dit **comment** le faire.

## Diagnostiquer — comprendre ce qui se passe

| Question | Fiche | Pour agir |
|---|---|---|
| Qu'est-ce qui monte et qu'est-ce qui tombe depuis le mois dernier ? | `gagnants-perdants.md` | |
| Quelles pages déclinent lentement, avant qu'elles ne disparaissent ? | `content-decay.md` | `seo-optimisation-onpage` |
| J'ai perdu du trafic : classement, CTR ou demande ? | `chute-trafic.md` | `seo-traffic-drop` |
| Cette baisse est-elle un problème, ou mon creux annuel habituel ? | `saisonnalite.md` | |
| Quelles pages sous-performent en clics pour leur position ? | `ctr-anormal.md` | `seo-meta-serp` |
| Quelles pages sont juste sous le seuil, et rapportent le plus vite ? | `quick-wins.md` | `seo-quick-wins` |
| Quelles pages se battent entre elles sur la même requête ? | `cannibalisation.md` | `consolidation.md` |
| Sur quelles requêtes Google me montre-t-il sans page dédiée ? | `requetes-neuves.md` | `page-a-creer.md` |

## Piloter — suivre dans le temps

| Question | Fiche | Pour agir |
|---|---|---|
| Qu'est-ce qui vient de décrocher et que je n'ai pas vu ? | `alerte.md` | `seo-veille` |
| Où en sont les requêtes sur lesquelles j'ai décidé de me battre ? | `panier-cibles.md` | |
| Qu'est-ce qui n'est pas indexé, et pourquoi ? | `indexation.md` | `seo-indexation` |
| Bien placé sur Google — les IA me citent-elles pour autant ? | `google-vs-llm.md` | `geo-share-of-model` |
| À quoi ressemble le mois écoulé, et qu'est-ce que ça veut dire ? | `rapport-mensuel.md` | `seo-reporting` |

## Produire — transformer les requêtes en contenu

| Question | Fiche | Pour agir |
|---|---|---|
| Quels sujets méritent une page que je n'ai pas encore ? | `page-a-creer.md` | `seo-brief` |
| Quelles questions cette page reçoit-elle sans y répondre ? | `sections-manquantes.md` | `seo-optimisation-onpage` |
| Quelles questions mettre en FAQ, d'après ce qu'on me demande vraiment ? | `faq-depuis-requetes.md` | `seo-faq-paa` |
| Comment écrire un brief à partir de ce que les gens tapent vraiment ? | `brief-depuis-requetes.md` | `seo-brief` |
| Comment réécrire titles et metas pour récupérer les clics perdus ? | `reecriture-title.md` | `seo-meta-serp` |
| Quels liens internes ajouter, et depuis quelles pages exactement ? | `maillage.md` | `seo-maillage-interne` |
| Comment fusionner des pages qui se cannibalisent sans perdre de trafic ? | `consolidation.md` | `seo-migration` (redirections) |

## Récupérer les données

Par ordre de préférence :

1. **`gsc.py`**, en direct, sans intermédiaire — dès que `GSC_SA_JSON` ou
   `GSC_CREDENTIALS_JSON` est défini :
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gsc.py" perf --par page --lignes 500 --compare --json
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gsc.py" perf --par query --jours 90 --json
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gsc.py" instantane     # page × requête → donnees/
   ```
2. **Le MCP `search-console`**, s'il est branché.
3. **Un connecteur** exposant Search Console (Windsor.ai ou équivalent) — en
   un clic, sans code, pratique pour un client qui ne veut pas de clé.
4. **Un export CSV** de l'interface, analysé par
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gsc_analyse.py" export.csv`.

Dans un projet, commencez par regarder `donnees/` : l'instantané de la
semaine y est peut-être déjà.

## Règles communes à toutes les analyses

- **Ne jamais inventer un chiffre.** Si la donnée manque, le dire — pas
  l'estimer en silence.
- Toujours indiquer la **période** et le **volume** sur lesquels repose une
  conclusion.
- Un pourcentage sans son volume absolu n'est pas une information : −80 %
  sur 5 clics ne pèse rien, −20 % sur 2 000 clics est une alerte.
- Écarter les **requêtes de marque** des analyses de performance, sauf
  demande contraire : elles mesurent la notoriété, pas le SEO.
- Search Console **échantillonne et plafonne** : au-delà de ~1 000 lignes
  dans l'interface, paginer ou segmenter par page ou par date (`gsc.py`
  pagine seul jusqu'à 25 000 lignes par appel).
- Les données ont **2 à 3 jours de retard** : ne jamais conclure sur hier.
- Comparer à **M-12**, pas seulement à M-1, avant de parler de tendance.

## Enchaîner

Une analyse qui ne débouche sur rien n'a servi à rien. Terminez toujours par
l'action suivante — le skill de la colonne « Pour agir » — et, dans un
projet, inscrivez les actions retenues dans `rapports/a-valider.md` ou dans
la roadmap.
