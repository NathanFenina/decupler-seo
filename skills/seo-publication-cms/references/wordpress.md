# WordPress — ce qui bloque, et comment le débloquer

Référence de `scripts/wp.py`. À lire quand `wp.py verifier` signale un
problème, ou quand une écriture échoue.

## Les champs SEO ne s'écrivent pas

WordPress **ignore sans erreur** un champ `meta` qui n'est pas déclaré dans
l'API REST : la requête renvoie 200, rien n'est écrit. `wp.py` relit la
réponse et le signale. C'est le cas par défaut de Yoast (les versions
récentes n'ouvrent title, meta et requête cible qu'aux articles, jamais aux
pages, ni la canonique ni le noindex), et souvent de SEOPress.

### Solution 1 — déclarer les champs (recommandée)

Un seul fichier, livré avec la méthode :
`${CLAUDE_PLUGIN_ROOT}/templates/wordpress/mu-plugins/seo-meta-rest.php`
(dans un projet : `.claude/decupler-seo/templates/wordpress/mu-plugins/`).
Il détecte l'extension active (Yoast, Rank Math, SEOPress) et ouvre à
l'écriture title, meta description, requête cible, canonique et noindex,
pour tous les types de contenu publics, aux seuls comptes qui peuvent
modifier le contenu concerné. À déposer dans `wp-content/mu-plugins/`
(dossier à créer s'il n'existe pas) : actif sans activation, il n'apparaît
que dans Extensions → « Indispensables ».

Installation, test (`/wp-json/seo-meta-rest/v1/etat`), désinstallation et
niveau d'autonomie : `templates/wordpress/README.md`. Ne recopiez pas de
version abrégée de ce code dans un projet : c'est ce fichier qui fait foi.

Relancez `wp.py verifier` : la ligne « Champs SEO exposés » doit apparaître.

### Solution 2 — passer par l'extrait (Yoast, sans toucher au code)

Dans Yoast → Réglages → Types de contenu → Articles (et Pages), réglez le
modèle de meta description sur `%%excerpt%%`. L'extrait WordPress, champ
natif et toujours écrivable, devient la meta description servie. Puis :

```bash
python3 wp.py meta --url … --description "…" --via-extrait
python3 wp.py publier … --meta-description "…" --via-extrait
```

Limite : le title, lui, reste le modèle Yoast. Et un extrait sert parfois
ailleurs dans le thème (listes d'articles) : vérifiez le rendu.

### Rank Math

Rank Math fournit sa propre route (`rankmath/v1/updateMeta`) : `wp.py` la
tente automatiquement quand les champs ne sont pas exposés. Si elle est
absente ou refusée selon la version installée, `seo-meta-rest.php` règle
la question (testé avec Rank Math : `wp.py meta` écrit alors directement
dans `rank_math_title` et `rank_math_description`).

## Erreurs d'accès

| Symptôme | Cause | Correctif |
|----------|-------|-----------|
| 401 avec le bon mot de passe | L'hébergeur retire l'en-tête `Authorization` (Apache en CGI/FastCGI) | Au `.htaccess` : `SetEnvIf Authorization "(.*)" HTTP_AUTHORIZATION=$1` |
| 401 | Mot de passe de connexion au lieu d'un mot de passe d'application | Utilisateurs → Profil → Mots de passe d'application |
| Pas de section « Mots de passe d'application » | Site en http, ou désactivée par une extension de sécurité | Passer en https ; réactiver dans l'extension |
| 403 `rest_cannot_create` / `rest_cannot_edit` | Rôle trop faible (un Auteur ne touche ni aux pages ni aux contenus des autres) | Rôle Éditeur pour le compte du dispositif |
| 403 sur tout `/wp-json/` | Pare-feu (extension de sécurité, Cloudflare, hébergeur) | Autoriser `/wp-json/` pour ce compte ou cette IP |
| 404 sur `/wp-json/` | Permaliens « Simple », ou API désactivée | Réglages → Permaliens : tout sauf « Simple » |
| Réponse HTML au lieu de JSON | Page de maintenance, redirection, pare-feu | Ouvrir `https://site/wp-json/` dans un navigateur |
| Coupures intermittentes | Hébergeur qui coupe sur les requêtes lourdes | `wp.py` retente 5 fois (lectures et mises à jour) ; une création n'est jamais retentée à l'aveugle — le script vérifie d'abord par le slug qu'elle n'a pas abouti |

Donnez au dispositif **son propre compte** (rôle Éditeur) et son propre mot
de passe d'application : il se révoque seul, sans toucher à vos accès, et
l'historique des révisions dit qui a écrit quoi.

## Révision (autosave) : ce que voit l'éditeur

Quand `wp.py` modifie une page déjà en ligne sans feu vert pour la mise en
ligne, il envoie une révision automatique (`/autosaves`). La page publique
ne change pas. Dans l'éditeur, WordPress affiche : « Il existe une
sauvegarde automatique de cette page plus récente que la version
ci-dessous » → **Voir la sauvegarde automatique** → **Restaurer**, relire,
**Mettre à jour**. C'est à ce moment que la modification part en ligne —
journalisez-la alors (`journal.py ajouter`).

Une révision ne porte que titre, contenu et extrait. Meta SEO, catégories,
image à la une et slug changeraient la page en ligne : le script ne les
envoie pas dans ce mode.

## wpautop

Sur un contenu classique (hors blocs Gutenberg), WordPress transforme chaque
ligne vide en `</p><p>`, y compris à l'intérieur d'un `<style>` ou d'un
`<script>`. Le navigateur abandonne alors le reste de la feuille de style,
ou le script ne s'exécute plus. `wp.py` retire ces lignes vides avant
l'envoi et remet chaque `<noscript>` sur une ligne. Un conteneur qui mélange
des enfants en ligne (`<span>`, `<a>`) et des blocs (`<div>`, `<p>`) reçoit
aussi un `</p>` orphelin qui décale grilles et flex : gardez des enfants
homogènes. Filet de sécurité côté CSS de la page : `p:empty{display:none}`
dans le conteneur. Toujours contrôler le HTML **rendu** (`?context=edit` →
`content.rendered`, ou la page servie), jamais seulement le source envoyé.

## Elementor et thèmes à page builder

- Page construite dans Elementor (`_elementor_edit_mode = builder`) : le rendu
  vient de la méta `_elementor_data`, pas de `content`. Modifier les deux, et
  sauvegarder les deux avant.
- Une écriture de `_elementor_data` par l'API est enregistrée mais **pas
  affichée** tant que le cache CSS/HTML d'Elementor n'est pas purgé :
  l'extension `templates/wordpress/plugins/seo-crawl-fix/` le purge à chaque
  modification (réglage `purge_elementor`).
- Gabarit `elementor_canvas` : pas d'en-tête ni de pied de page du site, donc
  aucun script posé dans l'en-tête ne s'y exécute.
- Double H1 : beaucoup de thèmes (Astra, etc.) affichent le titre de la page
  en plus du H1 du contenu ; le masquer par les métas du thème, page par page.
- En-tête et pied de page en templates Elementor : un correctif global (CSS,
  script) va dans ces templates, avec sauvegarde, plutôt que dans chaque page.

## Petites surprises de l'API

- Yoast n'expose pas le canonical à l'écriture par REST sans champ déclaré
  (voir plus haut) ; il ne publie l'Organisation dans son graphe que si le
  logo est réglé — `templates/wordpress/plugins/seo-entite/` la crée alors,
  avec ses `sameAs`, et donne un seul identifiant à la personne liée.
- Une politique de mots de passe (Wordfence, etc.) refuse par l'API un mot de
  passe sans symbole : à prévoir pour toute création ou réinitialisation de compte.
- **Un statut forcé déprogramme.** Un `POST` avec `"status": "draft"` sur un
  article planifié (`future`) le déprogramme sans avertissement : un script
  de mise à jour relit le statut existant et ne l'envoie pas (c'est ce que
  fait `wp.py`).
- **Les médias ne se dédoublonnent pas.** Un second envoi de
  `image-guide.webp` devient `image-guide-1.webp`, et le slug du média
  d'origine peut glisser en `-2`. Chercher le média par son slug avant tout
  envoi, et le réutiliser.
- **Une URL supprimée répond souvent 410, pas 404.** Un contrôle de liens
  qui ne cherche que 404 la croit vivante : comptez 404 et 410 comme mortes,
  et ne les utilisez jamais en maillage.
- **Pas de rafale.** Au-delà d'une dizaine de requêtes concurrentes,
  beaucoup d'hébergements renvoient des réponses incohérentes (des comptes
  qui changent d'un appel à l'autre) : un audit par l'API est séquentiel,
  quitte à être lent.
- Site piraté : chercher les comptes administrateurs créés directement en base
  (sans email, date d'inscription incohérente) ; les rétrograder et changer
  leur mot de passe avant de supprimer, et **ne jamais** écrire leurs
  identifiants dans un dépôt public. Les URL de spam restées dans l'index
  se traitent par un 410 et un sitemap temporaire :
  `templates/wordpress/plugins/seo-crawl-fix/` (niveau Interdit : proposé,
  installé par une personne).

## Extensions prêtes à installer

`templates/wordpress/` regroupe les extensions écrites après ces incidents,
génériques et réglables par un fichier de configuration :

| Extension | Pour |
|-----------|------|
| `mu-plugins/seo-meta-rest.php` | Champs SEO écrivables par l'API (Yoast, Rank Math, SEOPress) |
| `plugins/seo-crawl-fix/` | 410 du spam, page d'erreur légère, pagination hors limites, pages hors index, redirections, robots.txt, cache Elementor |
| `plugins/seo-entite/` | Organisation, personne, `sameAs` et identifiants uniques dans le JSON-LD |

Le `README.md` du dossier donne pour chacune l'incident d'origine,
l'installation (FTP/SFTP, gestionnaire de fichiers ou zip), le test, la
désinstallation et le niveau d'autonomie. Rien ne s'installe en production
sans sauvegarde et validation humaine.

## Carte de contenu

`donnees/carte-contenu.csv` : une ligne par contenu publié.

| Colonne | Contenu |
|---------|---------|
| `id`, `type`, `statut`, `url`, `modifie` | Identité du contenu (`type` = base REST : `posts`, `pages`) |
| `titre` | Titre WordPress |
| `meta_titre`, `meta_description` | Servis (Yoast), ou champs de l'extension, ou page publique avec `--head` |
| `h1`, `h2` | Titres du corps (un `h1` ici est un doublon du titre du thème) |
| `termes` | Les 25 mots les plus fréquents du corps |
| `nb_mots` | Mots du corps, sans script ni style |
| `liens_internes`, `nb_liens_internes` | Liens du **corps** vers le site — pas le menu ni le pied de page |
| `liens_entrants` | Nombre de contenus de la carte dont le corps lie celui-ci |
| `nb_liens_externes` | Liens du corps vers d'autres domaines |

Elle se relit avec le crawl (`crawl_site.py`), qui voit aussi menus et pied
de page : la carte dit où est le maillage contextuel, le crawl où est le
maillage total.
