---
name: seo-cartographie
description: >
  Tient la cartographie d'un site : un tableau vivant où chaque page a son
  mot-clé principal (ce qu'elle doit gagner sur Google) et son prompt
  principal (la question qu'elle doit gagner dans ChatGPT, Gemini et Claude),
  suivis chaque mois — position de la page sur son mot-clé, citation par
  chaque moteur IA, action suggérée. Initialisation depuis Search Console, le
  sitemap et le calendrier éditorial, validation avec le client, relevé
  mensuel, alerte de cannibalisation, export Notion. Déclencher sur
  "cartographie", "carto", "mapping mots-clés", "un mot-clé par page",
  "mot-clé principal", "prompt principal", "keyword mapping", "plan de
  positionnement", "quelle page vise quoi", "suivi des positions par page".
---

# La cartographie — une page, un mot-clé, un prompt

La cartographie répond à une question qu'on pose à chaque décision : **cette
page, elle est là pour gagner quoi ?** Sur Google, un mot-clé principal. Dans
les assistants IA, un prompt principal. Tant que ce n'est pas écrit, deux
pages se disputent la même requête, un article vise « un peu tout », et le
rapport mensuel parle de trafic global sans dire quelle page tient sa promesse.

Le tableau vit dans le projet : `memoire/cartographie.csv`. Il appartient au
client autant qu'à vous : on le valide ensemble, on le relit chaque mois.

## Les trois règles

1. **Un mot-clé principal par page, une page par mot-clé principal.** Deux
   lignes qui partagent le même mot-clé, c'est une cannibalisation annoncée :
   `cartographie.py verifier` la signale et sort en erreur. On tranche —
   fusion, redirection proposée, ou changement de cible — avant de produire
   quoi que ce soit.
2. **Un prompt principal par page**, formulé comme un acheteur parle à un
   assistant, jamais en mots-clés, jamais avec le nom de la marque (sinon on
   mesure la notoriété de la question, pas la visibilité du site). Mêmes
   règles que la batterie de `geo-share-of-model`, contrôlées par le même code.
3. **Le plafond de KD s'applique aux pages à créer.** Une ligne `a-creer`
   (pilier comprise) ne prend pour mot-clé principal qu'une requête sous le
   plafond fixé par l'autorité du domaine (`seo-keyword-research` étape 4 ;
   KD ≤ 20 pour un site neuf). Une page existante qui vise plus haut est
   signalée à la validation : changer de cible ou la garder en connaissance
   de cause.
4. **Le script propose, le client valide.** Ce que le script a deviné est
   listé dans la colonne `a_valider`. Une ligne n'est validée que lorsque
   cette colonne est vide.

## Les colonnes

| Colonne | Valeurs | Qui la remplit |
|---|---|---|
| `url` | l'adresse de la page, vide pour une page à créer | script |
| `statut` | `existante` · `a-creer` · `en-cours` · `publiee` | script, puis vous |
| `type` | `pilier` · `cluster` · `offre` · `outil` · `lead-magnet` · `article` | proposé d'après l'URL ; pilier et cluster se décident à la main |
| `silo`, `cluster` | le thème (lexique du projet), le pilier de rattachement | silo proposé par le lexique ; cluster à la main |
| `mot_cle_principal` | la requête hors marque qui apporte le plus de clics à la page (à défaut, d'impressions) | proposé, **à valider** |
| `mots_cles_secondaires` | 3 requêtes suivantes, séparées par « \| » | script |
| `prompt_principal` | la question IA que la page doit gagner | proposé (gabarit FR/EN/AR), **à valider** |
| `langue`, `intention`, `funnel` | `fr`/`en`/`ar` · informationnel, commercial, transactionnel, navigationnel · TOFU/MOFU/BOFU | script |
| `priorite` | `P1` · `P2` · `P3` | proposée par la valeur du thème (lexique 3 → P1) ; c'est une décision business |
| `volume`, `kd` | demande mensuelle, difficulté | repris de `donnees/demande-*.csv`, ou `mensuel --volumes` |
| `a_valider` | les cellules proposées par le script | vider une fois validé |
| `derniere_maj`, `notes` | date du dernier changement, remarques | script / vous |

Ajoutez les colonnes dont le client a besoin (responsable, date de
publication…) : le script les conserve.

## Étape 1 — Initialiser

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cartographie.py" initialiser [--jours 90] [--categorie "cabinet d'expertise comptable"]
```

Le script assemble trois sources :

- **Search Console** (90 jours, requête × page) : une ligne par page qui a au
  moins 10 impressions, avec son mot-clé principal. Les requêtes de marque
  sont exclues avec la même détection que `opportunites.py`
  (`opportunites.marque` de la config, à défaut le nom et le domaine). Sans
  accès API : `--csv export.csv` (export Performances, requêtes × pages).
- **Le sitemap** (`https://<domaine>/sitemap.xml`, ou `--sitemap <url>`) : les
  pages publiées qui n'ont encore aucune impression. `--sans-sitemap` pour
  s'en passer.
- **Le dernier calendrier** (`rapports/calendrier-*.md`, écrit par
  `opportunites.py --calendrier`) : les créations prévues deviennent des
  lignes `a-creer`, sauf si leur mot-clé est déjà celui d'une page.

Le prompt principal est proposé à partir du mot-clé et de l'intention : un
mot-clé déjà formulé en question est gardé tel quel ; sinon un gabarit par
intention et par langue (français, anglais, arabe). Avec `--categorie`, les
pages commerciales et transactionnelles reprennent les gabarits de
`share_of_model.py`, ce qui rend les deux mesures comparables.

**Relancer `initialiser` ne casse rien.** Il complète les cellules vides et
ajoute les nouvelles pages ; il n'écrase jamais une cellule remplie. Seule
exception : une ligne `a-creer` dont la page existe désormais (journal des
modifications, ou Search Console sur le même mot-clé) reçoit son URL et passe
à `publiee`. `--dry-run` montre le bilan sans écrire.

## Étape 2 — Valider avec le client

C'est l'étape qui donne sa valeur au tableau. En séance, ligne par ligne,
en commençant par les P1 :

1. **Le mot-clé principal est-il celui qui rapporte ?** Le script a pris
   celui qui amène le plus de clics aujourd'hui ; le client sait lequel amène
   des clients. Une page « expert comptable Lyon » qui ranke surtout sur
   « salaire expert comptable » doit garder la cible business, et c'est le
   contenu qui suivra.
2. **Le prompt est-il une vraie question d'acheteur ?** Reformulez au ton
   parlé : « Quel cabinet choisir pour créer mon entreprise à Lyon ? » plutôt
   que « Que faut-il savoir sur création entreprise lyon ? ». Une question,
   20 mots au plus, sans la marque, sans formule de vendeur.
3. **Cannibalisation** : `cartographie.py verifier`. Chaque doublon se règle
   avant de continuer.
4. **Pages sans mot-clé** (souvent l'accueil, les pages légales, les pages
   qui ne rankent que sur la marque) : leur donner une cible, ou les laisser
   vides si elles n'ont pas vocation à ranker.
5. Vider `a_valider` sur chaque ligne validée, et consigner les arbitrages
   dans `memoire/decisions.md`.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cartographie.py" verifier
```

Ajoutez ensuite les prompts principaux validés à la batterie
`recherche/prompts-ia.csv` de `geo-share-of-model` (on ajoute, on ne retire
jamais) : ils seront mesurés chaque mois avec le reste.

## Étape 3 — Le relevé mensuel

À lancer **avant** `rapport.py`, qui en reprend la synthèse :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cartographie.py" mensuel --mois AAAA-MM
```

Pour chaque ligne, le mois et le mois précédent :

- les chiffres de la page (clics, impressions, CTR, position) ;
- **la position et les clics de la page sur son mot-clé principal**
  (croisement page × requête) — le chiffre qui dit si la page tient sa
  promesse, avec le Δ en places gagnées ;
- une autre page du site mieux placée sur ce mot-clé : c'est la
  cannibalisation vue dans les données, signalée dans l'action ;
- la visibilité IA du prompt principal : cité (avec son rang de source),
  nommé sans lien, ou absent, pour ChatGPT, Gemini et Claude (et Perplexity
  dans le JSON), et le concurrent cité à la place du site. Le script reprend
  les derniers relevés de `share_of_model.py` (`donnees/ia-*.csv`,
  `releves-ia-*.csv`) du mois ou d'avant ; les mesures sans web (notoriété)
  sont écartées ;
- une action suggérée, dans le vocabulaire de la colonne Action du schéma
  Notion (Optimiser → top 3, Mettre à jour (quick win), Garder / Maintenir,
  Vérifier indexation / Relancer…). Une page en cours de mesure dans le
  journal est marquée « ne pas toucher ».

Il écrit :

- `donnees/cartographie-historique.csv` — une ligne par page et par mois ;
  relancer le même mois remplace ses lignes, sans doublon ;
- `rapports/cartographie-AAAA-MM.md` — le tableau du mois, les plus fortes
  hausses et baisses sur les mots-clés principaux, les prompts gagnés et
  perdus, les concurrents cités à la place du site ;
- `rapports/cartographie-AAAA-MM.json` — les mêmes données. `--json` les
  affiche sans rien écrire.

Options payantes, désactivées par défaut — annoncez le coût avant :

| Option | Ce qu'elle fait | Coût |
|---|---|---|
| `--volumes` | rafraîchit `volume` par DataForSEO (`demande.py`) | affiché après l'appel |
| `--prompts` | interroge les moteurs IA sur les prompts principaux, écrit `donnees/cartographie-ia-AAAA-MM.csv` | un appel par prompt et par moteur, annoncé avant |
| `--moteurs openai,gemini` | limite les moteurs de `--prompts` | |

Sans accès API Search Console : `--csv export-du-mois.csv --csv-precedent
export-du-mois-precedent.csv` (exports requêtes × pages). Les chiffres par
page sont alors recalculés depuis les requêtes visibles, donc un peu sous-estimés.

### Lire le tableau

| Constat | Lecture | Suite |
|---|---|---|
| Position qui monte, prompt absent partout | Google suit, les IA non : la page répond mal à la question | réponse directe en tête, données chiffrées, FAQ (`seo-redaction`, « Article GEO ») |
| Prompt gagné, position qui baisse | la page est citée pour son contenu, pas pour son autorité | maillage interne et liens externes (`seo-maillage-interne`, `seo-netlinking`) |
| Perd 3 places ou plus | chute à expliquer avant d'agir | `seo-traffic-drop` |
| Autre page mieux placée | cannibalisation | consolider, ou changer le mot-clé de l'une des deux |
| Toujours le même concurrent cité | il a les sources que les moteurs lisent | `geo-citation-tracker` : d'où viennent ses citations |
| Absente sur son mot-clé | la page ne vise pas ce qu'on croit | revoir le mot-clé avec le client, ou réécrire l'angle |

Rédigez la section « Lecture et décisions » du fichier du mois : elle est
conservée quand on relance le script.

## Étape 4 — Synchroniser avec Notion (facultatif)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cartographie.py" exporter --notion-csv   # → rapports/cartographie-notion.csv
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cartographie.py" exporter --json         # mêmes lignes, pour le MCP
```

Les colonnes sont celles d'une base « Cartographie SEO — <client> » : Mot
clé (titre), Statut (Existant · À créer · En cours · Publié), Type, Format,
Silo, Cluster, Priorité, Potentiel business, Canal, Intention, Volume, KD, AI
Overview, Effort, Action, Position, CTR, Impressions, Clics, Évolution
position, Dernière MAJ, Slug, Dans inventaire — plus URL, Prompt principal,
Mots-clés secondaires, Funnel, ChatGPT, Gemini, Claude, Perplexity et À
valider. Position, CTR, Impressions et Clics sont ceux de la page **sur son
mot-clé principal**, au dernier mois de l'historique. Potentiel business,
Effort et AI Overview restent vides : ce sont des jugements, pas des mesures.

**Premier import** : Notion → Importer → CSV, puis régler les types
(sélection pour Statut, Priorité, Intention, Action ; nombre pour Position,
CTR, Volume, KD ; case à cocher pour Dans inventaire).

**Synchronisation mensuelle par le MCP Notion** (connecteur natif, voir
`seo-pilotage-notion`) :

1. `exporter --json` pour obtenir les lignes à jour.
2. `notion-search` pour retrouver la base, `notion-fetch` pour lire son
   schéma et ses lignes. La clé de rapprochement est **Slug** (ou URL) ;
   pour une page à créer, **Mot clé**.
3. Ligne existante : `notion-update-page` sur les seules colonnes mesurées
   (Position, CTR, Impressions, Clics, Évolution position, Action, ChatGPT,
   Gemini, Claude, Dernière MAJ). Ligne absente : `notion-create-pages`.
4. **Ne jamais écraser dans Notion** ce que le client y a décidé (Priorité,
   Potentiel business, Effort, Mot clé, Prompt principal) : si Notion et le
   CSV divergent, c'est Notion qui a raison, et on reporte la décision dans
   `memoire/cartographie.csv`.

Pour une base de plusieurs centaines de lignes, la lecture en masse par le MCP
peut être lente : procédez par lots, et ne mettez à jour que les lignes dont
les chiffres ont changé.

## Ce que la cartographie ne fait pas

- Elle ne choisit pas la priorité business : elle la propose, le client
  décide (valeur d'un lead, marge, saisonnalité).
- Elle ne remplace pas `opportunites.py` : le classement dit où agir d'abord
  sur tout le site ; la cartographie dit ce que chaque page doit gagner et si
  elle y arrive.
- Elle ne mesure pas les AI Overviews : Search Console ne les isole pas.
  Utilisez `demande.py serp` sur les mots-clés principaux P1 pour savoir s'il
  y en a un.
