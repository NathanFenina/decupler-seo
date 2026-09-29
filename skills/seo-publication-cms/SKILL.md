---
name: seo-publication-cms
description: >
  Publie et met à jour du contenu sur WordPress, Webflow ou un CMS générique
  via API REST : création d'articles et de pages, mise à jour de balises,
  catégories, images, schema, avec sauvegarde préalable et publication en
  brouillon par défaut. Déclencher sur "publie", "mets en ligne", "envoie sur
  WordPress", "Webflow", "publier l'article", "mettre à jour la page",
  "pousser le contenu", "créer le brouillon", "carte de contenu WordPress".
  Sur WordPress, tout passe par scripts/wp.py : brouillon par défaut,
  révision pour une page en ligne, journal de mesure, maillage.
---

# Publication — mettre en ligne sans casser

C'est l'étape où une erreur coûte le plus cher, parce qu'elle est visible
publiquement et parfois irréversible.

## Étape 0 — Le garde-fou, systématiquement

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/guard.py" --action publier --cible <url>
```

| Verdict | Comportement |
|---------|--------------|
| `AUTORISE` | On publie, selon le statut par défaut de la config |
| `DEMANDE_VALIDATION` | On présente ce qui va être écrit, on attend le oui |
| `BLOQUE` | On produit le fichier en local et on explique comment le poser |

**Le statut par défaut est `draft`**, y compris en mode autonomous. Ce n'est
pas une limitation : Claude fait tout le travail, vous gardez le dernier
clic. Changez-le dans la config si vous voulez publier directement.

## Étape 1 — Sauvegarder avant d'écrire

Sur toute mise à jour d'un contenu existant :

```
.seo-decupler/backups/AAAA-MM-JJ-HHMMSS-<slug>.json
```

Contenu de la sauvegarde : titre, contenu, extrait, champs SEO bruts,
catégories, image à la une, statut, date. Tout ce qui permet de revenir en
arrière. Sur WordPress, `wp.py` la crée lui-même avant chaque écriture.

Le garde-fou `toujours_sauvegarder_avant_ecriture` est activé par défaut.
Ne le désactivez pas.

## WordPress — `wp.py`

Un seul script, bibliothèque standard uniquement : il tourne aussi dans les
routines cloud. Il appelle `guard.py`, sauvegarde, écrit, relit, journalise.

```bash
WP="${CLAUDE_PLUGIN_ROOT}/scripts/wp.py"
python3 "$WP" verifier            # compte, droits, extension SEO, champs exposés, garde-fou
```

**Authentification** : `WP_SITE_URL`, `WP_USER`, `WP_APP_PASSWORD` dans le
`.env` du projet ou l'environnement de la routine. Un **mot de passe
d'application** (Utilisateurs → Profil → Mots de passe d'application), jamais
le mot de passe de connexion. Rôle Éditeur au minimum pour les pages.
Aucune valeur n'est jamais affichée.

Lancez `verifier` une fois par site avant tout le reste : il dit si
l'extension SEO accepte l'écriture par l'API, ce qui décide de la suite.

### Les quatre règles que le script applique seul

| Règle | Comment |
|-------|---------|
| Brouillon par défaut | Un contenu neuf part en `publication.statut_par_defaut` (`draft`) |
| Rien en direct sans feu vert | Une page **déjà en ligne** n'est modifiée en direct qu'avec `--statut publish` (ou `--en-ligne`) **et** `AUTORISE` de `guard.py`. Sinon la modification part en **révision** (autosave) : la page publique ne bouge pas, la révision attend dans l'éditeur |
| Sauvegarde avant écriture | Restaurable par `cms_restore.py` |
| Journal | Toute modification mise en ligne passe par `journal.py ajouter`, avec sa valeur d'avant |

`DEMANDE_VALIDATION` (mode assisted) : lancez avec `--simuler`, montrez le
plan, attendez un **oui explicite**, puis relancez avec `--valide`. Jamais
`--valide` sans ce oui — en routine, jamais du tout. `BLOQUE` ne se lève pas.

### Publier

```bash
python3 "$WP" publier --html contenus/guide-audit-local.html \
  --titre "Audit SEO local : la méthode en 7 étapes" --slug audit-seo-local \
  --type post --categories "Guides" --extrait "…" \
  --image-une contenus/img/audit-local.webp --alt-image "Carte des fiches d'établissement d'une ville" \
  --meta-titre "Audit SEO local : méthode en 7 étapes" \
  --meta-description "…120 à 156 caractères…" --requete "audit seo local" --simuler
```

- Sans `--simuler`, le brouillon est créé ; le script affiche le lien
  d'aperçu et le lien d'édition.
- Le fichier passe d'abord `controle_contenu.py` : une erreur bloque la
  publication (en simulation, elle est seulement affichée).
- Le fichier HTML ne contient **pas de `<h1>`** : le thème affiche déjà le
  titre en H1.
- Les `<style>` et `<script>` inline sont protégés contre `wpautop` (qui
  coupe sur chaque ligne vide, même dans une feuille de style — la page sort
  cassée en ligne alors qu'elle était parfaite en local). `--brut` pour s'en
  passer.
- Un slug déjà pris est refusé, avec l'ID du contenu existant : on met à
  jour (`--id N`), on ne crée pas de doublon. Le dépôt est la source de
  vérité, WordPress le reflet — republier se fait toujours avec `--id`.
- Mise à jour (`--id N`) : seuls les champs fournis sont envoyés, le statut
  n'est jamais envoyé par défaut (il dépublierait la page).
- Catégories et étiquettes : noms ou IDs. Rien n'est créé : l'arborescence
  est une décision humaine.

### Images

```bash
python3 "$WP" media --fichier contenus/img/schema.webp --alt "Schéma : fiche, avis, pages locales"
```

Dernières lignes : `MEDIA_ID=…` et `SOURCE_URL=…`, à reprendre dans le HTML.
Alt obligatoire. Au-delà de 300 Ko le script prévient : WebP, 1600 px de
large au plus. Ne référencez jamais une image hébergée ailleurs.

### Title et meta description d'une page existante

```bash
python3 "$WP" meta --url https://exemple.com/audit-seo-local/ \
  --titre-seo "…" --description "…" --requete "audit seo local" [--auto]
```

Le script lit la valeur **servie** avant d'écrire (celle de `yoast_head_json`
ou de la page publique), sauvegarde les champs bruts, écrit, **relit** pour
vérifier, puis journalise une ligne `title` et/ou `meta` avec avant et
après. `--auto` relève la situation de départ dans Search Console. Une
valeur déjà en place n'est pas réécrite. Description hors 120-156
caractères : refusée (`--hors-format` pour forcer).

| Extension | Champs | Écriture par l'API |
|-----------|--------|-------------------|
| Yoast | `_yoast_wpseo_title`, `_yoast_wpseo_metadesc` | Seulement si déclarés (mu-plugin) — sinon `--via-extrait` |
| Rank Math | `rank_math_title`, `rank_math_description` | Champs déclarés, ou sa route `rankmath/v1/updateMeta`, tentée automatiquement |
| SEOPress | `_seopress_titles_title`, `_seopress_titles_desc` | Seulement si déclarés |

WordPress ignore **sans erreur** un champ non exposé : un 200 ne prouve
rien, c'est pourquoi le script relit. Les deux solutions (mu-plugin de six
lignes, ou modèle Yoast réglé sur `%%excerpt%%` + `--via-extrait`) sont dans
`references/wordpress.md`.

### Carte de contenu, maillage, cannibalisation

```bash
python3 "$WP" carte                    # → donnees/carte-contenu.csv
python3 "$WP" maillage                 # pages peu liées : quelles pages devraient les lier
python3 "$WP" maillage --cible https://exemple.com/audit-seo-local/ --appliquer --simuler
python3 "$WP" maillage --html contenus/brouillon.html     # avant de publier un contenu neuf
```

La carte liste chaque article et page publiés : URL, titre, title et meta
servis, H2, termes principaux du corps, nombre de mots, liens internes **du
corps** (pas du menu), liens entrants. Elle signale orphelines, impasses et
paires au sujet presque identique (cannibalisation possible, à confirmer
dans Search Console). `--head` lit title et meta sur les pages publiques
quand l'API ne les donne pas.

`maillage --appliquer` pose le lien sur une ancre **déjà présente** dans le
texte de la page source — jamais dans un titre ni un lien existant, jamais
de phrase inventée. Sans ancre, le lien est listé « à placer à la main ».
Page source en ligne : révision à valider ; brouillon : modifié directement.
Avec `--html`, les liens sont posés dans le fichier local et le script
signale les pages existantes qui couvrent déjà le sujet.

### Remplacer un bloc partout

```bash
python3 "$WP" remplacer --motif "<!-- bandeau -->.*?<!-- /bandeau -->" --par-fichier bandeau.html --simuler
```

Un bloc copié dans chaque page ne change pas quand on corrige sa source.
Une page où le motif apparaît plusieurs fois est ignorée : on ne devine
pas. En révision par défaut, `--en-ligne` sous garde-fou.

### À savoir

- **Formatage** : WordPress applique `wpautop` et des filtres qui peuvent
  retirer des balises. Vérifiez le rendu, surtout tableaux et `<details>`.
- **API REST directe** (`POST /wp-json/wp/v2/posts`, champs `title`,
  `content`, `excerpt`, `status`, `slug`, `categories`, `tags`,
  `featured_media`, `meta`) : c'est ce que fait le script. Si vous passez
  par le MCP `wordpress` à la place, les quatre règles ci-dessus restent les
  vôtres à appliquer.
- Erreurs 401, 403, 404 : le script dit quoi faire. Détail dans
  `references/wordpress.md`.

## Webflow

**Authentification** : jeton d'API (Site settings → Apps & integrations).

Le modèle est différent : le contenu vit dans des **CMS Collections** dont
les champs sont définis à l'avance. Vous ne pouvez écrire que dans les
champs existants.

1. Lister les collections, récupérer le schéma des champs
2. Créer l'item avec les `slug` de champs exacts
3. Publier — la création ne publie pas, c'est une étape séparée

Contraintes à connaître : le champ Rich Text n'accepte pas n'importe quel
HTML ; les embeds sont limités à 50 000 caractères ; les champs de référence
attendent des IDs.

## CMS générique

Si ni l'un ni l'autre, l'adaptateur générique produit :

- Le HTML complet (`/seo page`)
- Le markdown
- Un JSON structuré avec tous les champs
- Des instructions de pose : où coller, dans quel ordre, quoi vérifier

C'est le mode de repli, et il fonctionne partout.

## Étape 2 — Vérifier après publication

Ne considérez jamais une publication comme réussie parce que l'API a
renvoyé 200.

- [ ] L'URL répond en 200
- [ ] Le contenu s'affiche entièrement (comparez le nombre de mots)
- [ ] Les balises title et meta sont bien celles envoyées
- [ ] Le schema JSON-LD est présent et valide
- [ ] Les images s'affichent
- [ ] Le rendu mobile tient (Chrome DevTools)
- [ ] Les liens internes fonctionnent
- [ ] Pas de doublon de schema (plugin + votre bloc)

Sur une mise à jour de page existante et positionnée, ajoutez : le contenu
d'origine n'a pas été perdu, l'URL n'a pas changé, la canonical est intacte.

## Étape 3 — Après la mise en ligne

0. Journaliser, si le script ne l'a pas fait (brouillon validé à la main
   dans WordPress) : `journal.py ajouter --type page-neuve --url … --apres "…"`.
   Sans situation de départ, pas de mesure à J+28.
1. Soumettre l'URL dans Search Console (inspection → demander l'indexation)
2. Poser les liens internes entrants prévus dans le brief — **c'est l'étape
   la plus souvent oubliée**, et c'est celle qui décide de la vitesse
   d'indexation. Sur WordPress : `wp.py carte` puis
   `wp.py maillage --cible <url> --appliquer`
3. Consigner la publication dans le suivi (Notion, base « Briefs & Contenus »)
4. Noter la date pour la mesure à J+30

## Revenir en arrière

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cms_restore.py" .seo-decupler/backups/<fichier>.json
```

Restaure l'état sauvegardé, champs SEO compris. Fonctionne pour WordPress
et Webflow. Une révision proposée (autosave) n'a rien changé en ligne :
il suffit de ne pas la restaurer dans l'éditeur.

## Livrables

- L'URL publiée
- `PUBLICATION-<slug>.md` — ce qui a été envoyé, où, quand, avec quel statut
- La sauvegarde de l'état antérieur
- La liste des vérifications, avec leur résultat
