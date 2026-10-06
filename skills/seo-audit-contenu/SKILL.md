---
name: seo-audit-contenu
description: >
  Passe en revue toutes les pages publiées d'un site et donne à chacune un
  verdict et une action : vide, morte, périmée, mince, à pousser, saine ou
  technique — supprimer (410), rediriger (301), fusionner, mettre à jour,
  enrichir, pousser, garder. Croise Search Console sur 180 jours, la carte
  de contenu (nombre de mots, date de modification) et des signaux
  d'obsolescence (année passée dans un titre, versions retirées). Rien n'est
  modifié pendant l'audit. Déclencher sur "pages pourries", "audit de
  contenu", "nettoyage du site", "quelles pages supprimer", "pages
  obsolètes", "pages mortes", "contenu périmé", "élaguer le site", "content
  pruning", "quelles pages mettre à jour en priorité", "inventaire de
  contenu".
---

# Audit de contenu — un verdict et une action par page

Un site qui publie depuis des années accumule des pages que personne ne
regarde plus : brouillons publiés par erreur, articles d'actualité expirés,
guides datés, pages minces qui diluent le reste. Elles coûtent du budget de
crawl, cannibalisent les bonnes pages, et donnent aux moteurs IA des faits
périmés à citer.

Le livrable n'est pas une liste de 300 URL. C'est un tableau **trié par
urgence**, où chaque page a **un verdict et une action**, et un résumé des
cinq actions qui rapportent le plus. On ne touche à rien pendant l'audit : les
actions se font ensuite, page par page, avec sauvegarde.

## 1. Lancer l'audit

```bash
# la carte de contenu (WordPress) — une ligne par page publiée
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wp.py" carte

# l'audit : carte + Search Console sur 180 jours, en direct
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit_contenu.py"

# ou à partir d'un export Search Console (JSON de gsc.py, ou CSV de l'interface)
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gsc.py" perf --par page --jours 180 --lignes 25000 --json > donnees/gsc-pages.json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit_contenu.py" --gsc donnees/gsc-pages.json
```

Sortie : `donnees/audit-contenu.md` (lisible) et `donnees/audit-contenu.json`
(pour les scripts). Hors WordPress, toute carte CSV convient pourvu qu'elle
ait les colonnes `url` et `nb_mots` (`modifie`, `titre`, `h1`, `h2`,
`meta_description` affinent le verdict) — un export de crawl fait l'affaire.

**Pages construites avec un constructeur** (Elementor) : leur texte vit
dans une méta (`_elementor_data`), pas dans `content`. `wp.py carte` la lit
quand l'API l'expose et compte alors les mots de la page réelle ; sinon une
page riche sort à quelques mots et passe « vide ». Avant tout verdict
« vide » ou « mince » sur une page de ce type, ouvrez-la.

**Sans Search Console**, l'audit tourne en dégradé sur la longueur et l'âge
seulement, et le rapport le dit en tête : « morte » et « à pousser » ne
peuvent pas être établis sans impressions. Ne présentez jamais un audit
dégradé comme complet.

## 2. Les verdicts

| Verdict | Règle | Action par défaut |
|---|---|---|
| **technique** | Panier, compte, connexion, recherche, remerciement… | Vérifier `noindex` et absence du sitemap ; si c'est fait, ne rien faire |
| **vide** | < 80 mots et 0 impression | 410 si c'est un reste technique, sinon 301 vers la page la plus proche |
| **morte** | 0 impression sur 180 jours, page modifiée il y a plus de 6 mois | 301 vers la page qui couvre le sujet, ou fusion |
| **périmée** | Année passée dans le title, le H1, un H2 ou la meta ; ou motif daté propre au site | Mettre à jour si elle a du trafic, sinon fusionner |
| **mince** | < 400 mots mais montrée par Google | Enrichir : sections manquantes |
| **à pousser** | Position 8 à 20, ≥ 100 impressions | Quick win : title, sections, liens internes |
| **saine** | Le reste | Garder |

La première règle qui s'applique gagne, dans cet ordre. Les seuils sont
volontairement simples : un client doit pouvoir refaire le calcul et
contester un verdict.

**Le verdict est une proposition, la décision est humaine.** Faux positifs
connus :
- une année citée à juste titre (« l'étude 2021 », « la loi de 2019 ») : le
  script ne lit l'année que dans les zones affichées (title, H1, H2, meta),
  pas dans le corps, mais un titre peut citer une date légitime ;
- une page récente sans impression : elle n'a pas eu le temps d'être
  indexée, d'où la condition des six mois ;
- une page « morte » qui reçoit des backlinks : la rediriger, jamais la
  supprimer (vérifiez les liens entrants externes avant tout 410).

### Les motifs d'obsolescence propres au site

Ce qui date un contenu dépend du métier : une version de logiciel, un
modèle d'IA retiré, une réglementation remplacée, un tarif d'une ancienne
grille. Déclarez-les, sous la forme `expression::libellé` :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit_contenu.py" \
  --obsolete "gpt-?3\.5|gpt-4o\b::anciens modèles d'IA" --obsolete "windows 7::OS en fin de vie"
```

Les motifs se cherchent dans le title, le H1, les H2, la meta et les
25 termes principaux du corps (colonne `termes` de la carte), pas dans le
corps entier : une mention isolée au fond d'un article ne sort pas. Pour un
contrôle plein texte (une version retirée citée dans un paragraphe),
`controle_contenu.py` ou une recherche dans l'export du site.

Pour un site qui parle d'outils d'IA, les modèles retirés sont le motif le
plus rentable : un guide qui recommande encore un modèle d'il y a deux
générations se fait déclasser par les lecteurs avant de l'être par Google.
Déclarez-les une fois pour toutes dans `decupler-seo.config.yml` :

```yaml
audit_contenu:
  obsolete:
    - 'gpt-?3\.5|gpt-4o\b::anciens modèles IA'
    - 'prime de 2023::barème expiré'
```

Dans la config, **une seule barre oblique inverse** (`\.`, `\b`) et des
guillemets simples : la valeur est lue telle quelle, sans échappement ; un
`\\.` y chercherait une barre oblique littérale et ne trouverait jamais rien.

## 3. Avant d'agir sur une page

1. **Reste technique déjà neutralisé ?** Une page technique hors index et
   hors sitemap ne se touche pas. C'est le cas typique des pages d'une
   extension e-commerce installée puis abandonnée (boutique, panier,
   commande, compte) : vides, mais sans effet si elles sont hors index.
   Notez où elles sont neutralisées (extension, réglage) dans
   `memoire/decisions.md`, pour que l'audit suivant ne les rouvre pas.
2. **Cannibalisation** avant toute redirection (`seo-gsc-analyses`, analyse
   cannibalisation) : la cible doit couvrir la même intention, sinon la 301
   perd le trafic.
3. **Contenu unique à transférer** avant une fusion (`seo-gsc-analyses`,
   analyse consolidation) : sections, exemples, données que la page absorbée
   est seule à avoir.
4. **Backlinks** : une page qui en reçoit se redirige, ne se supprime pas.
5. **Sauvegarde** du contenu avant toute écriture (`seo-publication-cms` le
   fait par script), redirections et 410 dans le gestionnaire du site, jamais
   en masse sans diff validé (`seo-technique-autofix`). **Un seul
   gestionnaire de redirections** par site (une extension versionnée, ou le
   serveur) : deux systèmes qui se recouvrent finissent en boucle. Chaque
   redirection ou 410 se vérifie après mise en ligne (code et cible, au
   `curl -I`), et entre dans les tests du gestionnaire s'il en a
   (`templates/wordpress/plugins/seo-crawl-fix/` centralise 410 et
   redirections sur WordPress).
6. **Journaliser** chaque action (`seo-journal-mesure`) : une suppression ou
   une fusion se mesure à J+28 comme le reste.

## 4. Mettre à jour une page périmée

- Remplacer versions, dates et chiffres par les valeurs actuelles,
  **vérifiées à la source** — jamais de mémoire ; refaire une capture qui
  montre une ancienne interface.
- Afficher la date de mise à jour, et la porter dans `dateModified` du
  JSON-LD (`seo-schema-jsonld`).
- Changer le title et l'URL ? Le title oui, si l'année y figurait ; l'URL
  non, sauf si elle contient l'année — et alors avec une 301.
- Si la page est un lead magnet, la refonte suit `seo-lead-magnet` (même
  URL, livrable, preuves à jour) plutôt qu'une simple correction de dates.
- Une page construite avec un constructeur : sauvegarder `content` **et** la
  méta du constructeur avant d'écrire (`seo-publication-cms`,
  `references/wordpress.md`).
- Mettre à jour la cartographie (`seo-cartographie`) : action et date.

## 5. Rendu

À partir de `audit-contenu.md`, livrez :
- le compte de pages par verdict ;
- **les 5 actions les plus rentables** — celles qui portent sur des pages
  qui ont déjà des impressions (le script les sort en tête) ;
- ce qui a été laissé volontairement tel quel, avec la raison ;
- la source et la période des chiffres, ou la mention « sans Search
  Console ».

## Liens

- `seo-gsc-analyses` — content decay (le déclin lent), cannibalisation,
  consolidation, sections manquantes
- `seo-quick-wins` — le traitement des pages « à pousser »
- `seo-indexation` — soft 404, pages exclues, budget de crawl
- `seo-migration` — quand le nettoyage touche des dizaines d'URL
