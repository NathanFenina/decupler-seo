# Extensions WordPress — modèles decupler-seo

Trois petites extensions écrites pour un vrai site WordPress, après des
incidents réels, puis rendues génériques : aucune donnée d'un client n'y
figure, tout se règle dans un fichier de configuration.

| Extension | Où elle va | Ce qu'elle règle | Niveau d'autonomie |
|---|---|---|---|
| `mu-plugins/seo-meta-rest.php` | `wp-content/mu-plugins/` | Title, meta description, requête cible, canonique et noindex écrivables par l'API REST (Yoast, Rank Math, SEOPress) | **Validation** |
| `plugins/seo-crawl-fix/` | `wp-content/plugins/` | 410 sur les URL de spam ou supprimées, sitemap pour les faire repasser, page d'erreur légère, pagination hors limites en 404, pages hors index et hors sitemap, redirections, robots.txt | **Interdit** (proposition) |
| `plugins/seo-entite/` | `wp-content/plugins/` | Organisation, personne et site dans le JSON-LD, avec `sameAs` et un seul identifiant par entité | **Validation** |

## La règle avant tout

**Rien n'est installé en production sans sauvegarde et sans validation
humaine.** Une extension touche le serveur : c'est le site entier qui
répond, pas une page.

- **Validation** (`seo-meta-rest`, `seo-entite`) : l'agent prépare le fichier
  et sa configuration, l'inscrit dans `rapports/a-valider.md` ; une personne
  relit, sauvegarde, installe, puis teste.
- **Interdit** (`seo-crawl-fix`) : il agit sur des **410, des redirections, le
  noindex et le robots.txt** — exactement ce que la table des niveaux
  d'autonomie (`CLAUDE.md` du projet) réserve à l'humain. L'agent **propose**
  la configuration (liste des URL, motifs, pages à sortir), chiffres de
  Search Console à l'appui ; il ne l'installe jamais lui-même et ne modifie
  jamais sa configuration en ligne.
- Avant toute installation : sauvegarde complète (fichiers + base) chez
  l'hébergeur ou par l'extension de sauvegarde du site, et note de l'état
  de départ (les commandes de test ci-dessous, lancées **avant**).
- Après : la modification entre au journal (`journal.py ajouter`, via
  `seo-journal-mesure`), pour être mesurée à J+28 et pouvoir être annulée.
- Testez d'abord sur un site de préproduction quand il en existe un.

## 1. `seo-meta-rest.php` — les métas SEO par l'API

**L'incident.** Un script met à jour la meta description de vingt pages par
l'API REST. WordPress répond 200 à chaque fois. Rien n'a changé en ligne :
Yoast n'ouvre ses champs qu'aux articles (et pas aux pages), et jamais la
canonique ni le noindex. WordPress **jette sans erreur** un champ `meta`
non déclaré. `wp.py` relit chaque écriture et le signale, mais ne peut pas
l'ouvrir lui-même.

**Ce qu'il fait.** Détecte l'extension active (Yoast, Rank Math ou
SEOPress) et déclare ses champs dans l'API REST, pour tous les types de
contenu publics, avec un contrôle de droits par contenu (`edit_post`) et un
nettoyage par type (texte, URL, drapeau noindex). Aucune extension SEO
détectée : il ne fait rien.

| Extension | Champs ouverts |
|---|---|
| Yoast SEO | `_yoast_wpseo_title`, `_yoast_wpseo_metadesc`, `_yoast_wpseo_focuskw`, `_yoast_wpseo_canonical`, `_yoast_wpseo_meta-robots-noindex` (`1` = noindex, `2` = index, vide = réglage par défaut) |
| Rank Math | `rank_math_title`, `rank_math_description`, `rank_math_focus_keyword`, `rank_math_canonical_url`, `rank_math_robots` (liste : `["noindex","follow"]`) |
| SEOPress | `_seopress_titles_title`, `_seopress_titles_desc`, `_seopress_analysis_target_kw`, `_seopress_robots_canonical`, `_seopress_robots_index` (`yes` = noindex) |

`wp.py` (title et meta description) s'en sert sans réglage : il détecte
l'extension et écrit dans ces champs. Canonique et noindex restent des
écritures de niveau **Interdit** en production : le fichier les rend
possibles, la méthode ne les fait pas sans validation.

Un type de contenu personnalisé doit déclarer le support `custom-fields`,
sinon WordPress n'affiche pas son objet `meta` dans l'API.

**Installer.** Déposer le fichier dans `wp-content/mu-plugins/` (créer le
dossier s'il n'existe pas), par FTP/SFTP ou par le gestionnaire de fichiers
de l'hébergeur. Aucune activation : un mu-plugin se charge seul et
n'apparaît que dans Extensions → « Indispensables ». Il ne se téléverse pas
en zip depuis l'administration.

**Tester.** Avec le compte et le mot de passe d'application du dispositif :

```bash
# 1. Installé, et quelle extension il a détectée (401 sans identifiants : normal)
curl -s -u "$WP_USER:$WP_APP_PASSWORD" "$WP_SITE_URL/wp-json/seo-meta-rest/v1/etat"
# → {"version":"1.0.0","extension":"yoast","champs":[…],"types":["post","page"]}

# 2. Les champs apparaissent dans la réponse d'une page (édition)
curl -s -u "$WP_USER:$WP_APP_PASSWORD" "$WP_SITE_URL/wp-json/wp/v2/pages/<id>?context=edit&_fields=meta"

# 3. Le diagnostic de la méthode
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/wp.py" verifier
# → « ✓ Champs SEO exposés dans l'API : … »
```

Puis une écriture réelle sur une page de test (`wp.py meta --url … --simuler`
d'abord), et contrôle du `<title>` dans le code source de la page publique.

**Désinstaller.** Supprimer le fichier. Les valeurs déjà écrites restent :
ce sont les champs de l'extension SEO elle-même.

## 2. `seo-crawl-fix/` — budget de crawl après un piratage

**L'incident.** Un site piraté a gardé des centaines d'URL de spam (casino,
pharmacie, en plusieurs langues) dans l'index de Google, et plus de
10 000 URL « explorée, actuellement non indexée ». Chaque URL morte
renvoyait un 404 de ~150 Ko (la page complète du thème) : près de 2 Go
téléchargés par Googlebot à chaque passage. Google, pas revenu depuis des
mois, gardait ces URL en index. `/page/9999/` répondait 200. Des pages de
panier, de compte client et de webinaires passés étaient indexables.

**Ce qu'il fait** — tout est dans `config.php`, vide ou prudent par défaut :

| Réglage | Effet | Par défaut |
|---|---|---|
| `urls_410` | 410 sur une liste **fermée** de chemins (relevée dans Search Console, vérifiée une par une) | vide |
| `motifs_410` | 410 sur des expressions régulières, pour les piratages qui génèrent des milliers d'URL de même forme | vide |
| `sitemap_410` | `/sitemap-urls-supprimees.xml` : les URL de `urls_410`, à soumettre dans Search Console pour que Google repasse lire les 410 ; à retirer quand le compteur est à zéro | actif si la liste n'est pas vide |
| `hors_index` | noindex (en-tête `X-Robots-Tag` + balise de Yoast, Rank Math ou WordPress) et sortie des sitemaps | vide |
| `redirections` | 301 chemin → URL, et sortie des sitemaps ; seulement si la cible couvre déjà l'intention | vide |
| `page_legere` | page 404/410 d'environ 1 Ko, la même pour les robots et les visiteurs (pas de cloaking) | actif |
| `pagination_404` | 404 au-delà de la dernière page réelle, y compris avec une page d'accueil statique | actif |
| `robots_txt` | robots.txt virtuel du plugin (`robots_regles`) : recherche interne, paramètres `utm_`, `attachment_id`, `replytocom`, `/wp-admin/` | **inactif** |
| `purge_elementor` | purge le cache d'Elementor quand `_elementor_data` change par l'API (sinon la page garde l'ancien rendu) | actif |

Garde-fous inscrits dans le code :

- Le 410, par liste ou par motif, n'est posé **que si WordPress répond déjà
  404** : une page qui existe n'est jamais touchée, même listée par erreur.
  Un motif reste dangereux le jour où une vraie page qui lui ressemble est
  supprimée ou renommée : testez chaque motif contre la liste de vos URL
  réelles (sitemap, `wp.py carte`) avant de l'activer.
- `Disallow` empêche l'exploration, pas l'indexation : on n'y met **jamais**
  une URL qu'on veut voir sortir de l'index (Google ne pourrait plus lire
  son 410 ni son noindex).
- Les paramètres parasites (`utm_`, `replytocom`…) sont écartés de
  l'exploration par le robots.txt, pas réécrits : les canoniques de
  l'extension SEO font le reste.

**Configurer.** Copier `config.php` en `wp-content/seo-crawl-fix-config.php`
et le remplir : ce fichier survit aux mises à jour du plugin et prime sur
celui du dossier. Chemins sans barre au début ni à la fin, décodés
(`blog/ancien-article`, pas `/blog/ancien-article/`).

**Installer.** Zipper le dossier `seo-crawl-fix/` et le téléverser par
Extensions → Ajouter → Téléverser (puis « Remplacer » pour une mise à
jour), ou le déposer dans `wp-content/plugins/` par FTP/SFTP ou le
gestionnaire de fichiers ; puis l'activer.

```bash
cd templates/wordpress/plugins && zip -r seo-crawl-fix.zip seo-crawl-fix
```

**Tester** (avant installation pour l'état de départ, puis après) :

```bash
S="$WP_SITE_URL"
curl -s -o /dev/null -w "%{http_code} %{size_download} o\n" "$S/une-url-de-la-liste/"   # 410, ~700 o
curl -s -o /dev/null -w "%{http_code} %{size_download} o\n" "$S/page-qui-n-existe-pas/"   # 404, ~700 o
curl -s -o /dev/null -w "%{http_code}\n" "$S/page/9999/"                                 # 404
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" "$S/chemin-redirige/"          # 301 + cible
curl -sI "$S/panier/" | grep -i x-robots-tag                                             # noindex, follow
curl -s "$S/sitemap-urls-supprimees.xml" | head
curl -s "$S/robots.txt" | head -2      # si robots_txt actif : la ligne « servi par le plugin »
curl -s -u "$WP_USER:$WP_APP_PASSWORD" "$S/wp-json/seo-crawl-fix/v1/etat"   # compte administrateur
```

Une vraie page du site doit toujours répondre 200 : vérifiez-en trois,
dont une qui ressemble à un motif.

**Le piège du robots.txt physique.** Si un fichier `robots.txt` existe à la
racine (souvent posé lors d'une réparation après piratage), le serveur le
sert **avant** WordPress et le réglage `robots_txt` n'a aucun effet : la
ligne « servi par le plugin » est absente. `GET …/seo-crawl-fix/v1/etat`
le signale (`robots_physique`). Certains hébergeurs ne transmettent même pas
`/robots.txt` à WordPress une fois le fichier retiré (404 du serveur) :
dans ce cas, éditer le fichier physique par FTP, à la main, après validation.

**Désinstaller.** Désactiver puis supprimer l'extension, et
`wp-content/seo-crawl-fix-config.php`. Les URL repassent en 404 ordinaire,
les pages hors index redeviennent indexables : à décider, pas à subir.
Retirer le sitemap temporaire de Search Console.

## 3. `seo-entite/` — une entité, un identifiant

**L'incident.** Audit de dix pages d'un site d'agence : l'Organisation
publiée par l'extension SEO n'avait aucun `sameAs` ; le fondateur existait
sous trois identifiants différents selon les pages ; deux URL LinkedIn
différentes circulaient. Pour un moteur, trois inconnus au lieu d'un expert
identifié.

**Ce qu'il fait.** Complète le graphe JSON-LD de Yoast ou de Rank Math (ou
publie le sien sans eux) :

- l'**Organisation** (`<site>/#organization`) : raison sociale, identifiant
  officiel, TVA, adresse, logo, domaines, `sameAs` ; les listes s'ajoutent à
  celles de l'extension, un champ déjà rempli par elle n'est pas écrasé
  (sauf un type plus précis : `LocalBusiness`…) ; créée si l'extension ne
  la publie pas (Yoast exige nom **et** logo pour la publier) ;
- la **Personne** liée (`<site>/#prenom-nom`), avec `founder` / `worksFor` ;
- `auteur_unique` : sur un site à un seul auteur, les personnes générées
  pour les comptes WordPress sont fusionnées dans cette personne, et
  `author`, `creator`… pointent vers elle ;
- sans extension SEO : un `WebSite` en plus, dans un bloc
  `<script type="application/ld+json" class="seo-entite">`.

Tant que `organisation.name` est vide, le plugin ne fait rien.

**Configurer.** Copier `config.php` en `wp-content/seo-entite-config.php`
et le remplir **uniquement avec des valeurs vérifiables** : registre
officiel des entreprises, profils réellement tenus. Mêmes valeurs que
`memoire/entites.csv` et `memoire/triplets.csv` du projet (une seule valeur
par fait). Avec Rank Math, régler aussi « Personne ou entreprise » sur
**Entreprise** dans ses réglages, sinon il publie le site comme une
personne (`#person`). Le nom d'affichage du compte WordPress auteur doit
être le nom de la personne.

**Installer.** Comme `seo-crawl-fix` : zip téléversé, ou FTP/SFTP, puis
activer.

**Tester.**

```bash
curl -s "$WP_SITE_URL/un-article/" | grep -o '"@id":"[^"]*#organization"' | sort -u   # un seul
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/schema_validate.py" "$WP_SITE_URL/un-article/"
```

Puis le test des résultats enrichis de Google et le validateur de
schema.org sur trois pages : accueil, article, page de service. Une seule
Organisation, une seule Personne, aucune référence `@id` orpheline.

**Désinstaller.** Désactiver puis supprimer, et
`wp-content/seo-entite-config.php`. Le graphe redevient celui de
l'extension SEO.

## Ce qui n'a pas été repris

- **Le `llms.txt` généré depuis la base** (présent dans l'extension
  d'origine) : la méthode écrit un `llms.txt` choisi et rédigé
  (`templates/llms.txt`, skill `geo-llms-txt`), pas la liste de toutes les
  pages.
- **Le bouton qui renomme un robots.txt physique** depuis l'administration :
  écrire à la racine du serveur depuis PHP dépend trop de l'hébergeur ;
  l'état est signalé, l'intervention reste humaine.
- **La pop-up d'invitation** (webinaire, offre) : c'est une campagne
  marketing propre à un site, pas un correctif SEO. Ses principes valent
  pour toute pop-up et sont repris ici : texte absent du HTML de la page
  (construit au moment de l'afficher, pour ne pas le répéter sur toutes les
  pages aux yeux de Google) ; sur mobile, un bandeau en bas plutôt qu'une
  fenêtre qui masque le contenu (Google déclasse les interstitiels
  intrusifs) ; une fois par visiteur ; date de fin appliquée côté serveur et
  côté navigateur ; jamais deux pop-ups empilées.
