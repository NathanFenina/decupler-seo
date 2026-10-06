<?php
/**
 * Plugin Name:       SEO — Budget de crawl
 * Description:       Arrête de faire explorer à Google ce qui n'existe plus : 410 sur les URL de spam ou supprimées (liste fermée et motifs), sitemap temporaire pour les faire repasser, page d'erreur légère, 404 sur la pagination hors limites, pages sans valeur hors index et hors sitemap, redirections 301, robots.txt optionnel. Tout se règle dans config.php.
 * Version:           1.0.0
 * License:           GPL-2.0-or-later
 * Requires at least: 6.0
 * Requires PHP:      7.4
 *
 * Modèle decupler-seo (templates/wordpress/). Installation, test et
 * désinstallation : templates/wordpress/README.md.
 *
 * POURQUOI — un cas réel, anonymisé
 *
 *   Après un piratage, un site a gardé des milliers d'URL de spam (casino,
 *   pharmacie) dans l'index de Google, et plus de 10 000 URL « explorée,
 *   actuellement non indexée ». Trois constats :
 *   - chaque URL morte renvoyait un 404 dont le corps pesait ~150 Ko (la
 *     page complète du thème) : près de 2 Go téléchargés par Googlebot à
 *     chaque passage pour apprendre que rien n'existe ;
 *   - Google, pas revenu depuis des mois, gardait les URL en 404 dans son
 *     index : un 410 et un sitemap temporaire l'ont fait repasser ;
 *   - /page/9999/ répondait 200 avec la page d'accueil : espace d'URL infini.
 *
 * PIÈGES DÉJÀ PAYÉS
 *
 *   - Un robots.txt PHYSIQUE à la racine est servi par le serveur avant
 *     WordPress : le filtre robots_txt n'a alors aucun effet. Vérifier ce
 *     qui est réellement servi (ligne de marquage, voir README).
 *   - Yoast ajoute son propre bloc au robots.txt virtuel : ce plugin passe
 *     en dernier (PHP_INT_MAX) pour rester le seul à l'écrire.
 *   - Page d'accueil statique : /page/9999/ est une pagination de CETTE
 *     page, is_singular() est vrai. Le correctif traite ce cas.
 *   - Une écriture de _elementor_data par l'API REST est stockée mais pas
 *     affichée tant que le cache d'Elementor n'est pas purgé.
 *   - Jamais de 410 par motif sur une URL qui répond 200 : seules les URL
 *     que WordPress ne trouve déjà pas reçoivent le 410.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const SEO_CRAWL_VERSION = '1.0.0';

/** Règles du robots.txt quand la configuration n'en donne pas. */
const SEO_CRAWL_ROBOTS_DEFAUT = array(
	'Disallow: /*?s=',
	'Disallow: /*&s=',
	'Disallow: /*?utm_',
	'Disallow: /*&utm_',
	'Disallow: /*?attachment_id=',
	'Disallow: /*?replytocom=',
	'Disallow: /wp-admin/',
	'Allow: /wp-admin/admin-ajax.php',
);

/* -------------------------------------------------------------------------
 * Configuration
 * ---------------------------------------------------------------------- */

/**
 * Réglages : wp-content/seo-crawl-fix-config.php s'il existe (survit aux
 * mises à jour), sinon config.php du plugin. Filtrable par
 * seo_crawl_fix_config.
 */
function seo_crawl_config( $cle = null ) {
	static $config = null;
	if ( null === $config ) {
		$externe = WP_CONTENT_DIR . '/seo-crawl-fix-config.php';
		$fichier = file_exists( $externe ) ? $externe : __DIR__ . '/config.php';
		$lu      = include $fichier;
		$defauts = array(
			'urls_410'        => array(),
			'date_releve'     => '',
			'sitemap_410'     => true,
			'motifs_410'      => array(),
			'hors_index'      => array(),
			'redirections'    => array(),
			'page_legere'     => true,
			'pagination_404'  => true,
			'robots_txt'      => false,
			'robots_regles'   => SEO_CRAWL_ROBOTS_DEFAUT,
			'robots_sitemap'  => '/sitemap_index.xml',
			'purge_elementor' => true,
		);
		$config = apply_filters( 'seo_crawl_fix_config', array_merge( $defauts, is_array( $lu ) ? $lu : array() ) );
		foreach ( array( 'urls_410', 'hors_index' ) as $liste ) {
			$config[ $liste ] = array_values( array_filter( array_map( 'seo_crawl_normaliser', (array) $config[ $liste ] ) ) );
		}
		$redirections = array();
		foreach ( (array) $config['redirections'] as $chemin => $cible ) {
			$redirections[ seo_crawl_normaliser( $chemin ) ] = $cible;
		}
		$config['redirections'] = $redirections;
	}

	return null === $cle ? $config : ( isset( $config[ $cle ] ) ? $config[ $cle ] : null );
}

/** Chemin décodé, sans barres au début ni à la fin. */
function seo_crawl_normaliser( $chemin ) {
	return trim( rawurldecode( (string) $chemin ), "/ \t\n\r" );
}

/** Chemin de la requête courante, décodé, sans barres ni paramètres. */
function seo_crawl_chemin_courant() {
	$uri = isset( $_SERVER['REQUEST_URI'] ) ? wp_unslash( $_SERVER['REQUEST_URI'] ) : '';
	$chemin = (string) wp_parse_url( $uri, PHP_URL_PATH );
	// Site installé dans un sous-dossier : on retire le préfixe.
	$base = trim( (string) wp_parse_url( home_url(), PHP_URL_PATH ), '/' );
	$chemin = seo_crawl_normaliser( $chemin );
	if ( '' !== $base && 0 === strpos( $chemin . '/', $base . '/' ) ) {
		$chemin = trim( substr( $chemin, strlen( $base ) ), '/' );
	}

	return $chemin;
}

/* -------------------------------------------------------------------------
 * 1. Redirections 301 (avant tout rendu)
 * ---------------------------------------------------------------------- */

add_action(
	'template_redirect',
	function () {
		$carte  = seo_crawl_config( 'redirections' );
		$chemin = seo_crawl_chemin_courant();
		if ( '' !== $chemin && isset( $carte[ $chemin ] ) ) {
			// wp_redirect et non wp_safe_redirect : la cible peut être sur un
			// autre domaine (migration). Elle vient du fichier de config, pas
			// de la requête.
			wp_redirect( esc_url_raw( $carte[ $chemin ] ), 301, 'SEO Budget de crawl' );
			exit;
		}
	},
	-1
);

/* -------------------------------------------------------------------------
 * 2. 410 sur les URL supprimées ou de spam
 * ---------------------------------------------------------------------- */

/** L'URL courante (déjà en 404) doit-elle répondre 410 ? */
function seo_crawl_est_410( $chemin ) {
	if ( '' === $chemin ) {
		return false;
	}
	if ( in_array( $chemin, seo_crawl_config( 'urls_410' ), true ) ) {
		return true;
	}
	foreach ( (array) seo_crawl_config( 'motifs_410' ) as $motif ) {
		// Un motif invalide est ignoré (preg_match renvoie false), jamais fatal.
		if ( 1 === @preg_match( (string) $motif, $chemin ) ) { // phpcs:ignore WordPress.PHP.NoSilencedErrors
			return true;
		}
	}

	return false;
}

// Priorité 0 : le statut est posé avant la page légère (priorité 1).
add_action(
	'template_redirect',
	function () {
		if ( is_404() && seo_crawl_est_410( seo_crawl_chemin_courant() ) ) {
			status_header( 410 );
		}
	},
	0
);

// Sitemap temporaire des URL en 410, à soumettre dans Search Console.
add_action(
	'init',
	function () {
		if ( ! seo_crawl_config( 'sitemap_410' ) || ! seo_crawl_config( 'urls_410' ) ) {
			return;
		}
		if ( 'sitemap-urls-supprimees.xml' !== seo_crawl_chemin_courant() ) {
			return;
		}
		$date = seo_crawl_config( 'date_releve' );
		$date = preg_match( '/^\d{4}-\d{2}-\d{2}$/', (string) $date ) ? $date : gmdate( 'Y-m-d' );
		status_header( 200 );
		header( 'Content-Type: application/xml; charset=utf-8' );
		header( 'X-Robots-Tag: noindex' );
		echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
		echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n";
		foreach ( seo_crawl_config( 'urls_410' ) as $chemin ) {
			$url = home_url( '/' . implode( '/', array_map( 'rawurlencode', explode( '/', $chemin ) ) ) . '/' );
			echo '<url><loc>' . esc_url( $url ) . '</loc><lastmod>' . esc_html( $date ) . '</lastmod></url>' . "\n";
		}
		echo '</urlset>';
		exit;
	},
	1
);

/* -------------------------------------------------------------------------
 * 3. Pagination hors limites → 404
 * ---------------------------------------------------------------------- */

add_action(
	'template_redirect',
	function () {
		global $wp_query, $post;

		if ( ! seo_crawl_config( 'pagination_404' ) || is_admin() || is_404() ) {
			return;
		}
		// 'paged' = pagination d'une liste ; 'page' = contenu découpé par
		// <!--nextpage-->. Avec une page d'accueil statique, /page/9999/
		// alimente l'un ou l'autre, et is_singular() est vrai.
		$demandee = max( (int) get_query_var( 'paged' ), (int) get_query_var( 'page' ) );
		if ( $demandee < 2 ) {
			return;
		}
		$max_liste = isset( $wp_query->max_num_pages ) ? (int) $wp_query->max_num_pages : 0;
		if ( is_singular() || is_front_page() ) {
			$dispo = 1;
			if ( $post instanceof WP_Post ) {
				$dispo = 1 + (int) preg_match_all( '/<!--nextpage-->/', (string) $post->post_content );
			}
			if ( $demandee <= $dispo || ( $max_liste > 1 && $demandee <= $max_liste ) ) {
				return;
			}
		} elseif ( $max_liste > 0 && $demandee <= $max_liste ) {
			return;
		}

		$wp_query->set_404();
		status_header( 404 );
		nocache_headers();
	},
	0
);

/* -------------------------------------------------------------------------
 * 4. Page « disparue » légère
 * ---------------------------------------------------------------------- */

/**
 * Corps minimal sur les 404 et 410, au lieu de la page complète du thème.
 * Même page pour les robots et les visiteurs : servir un corps différent
 * selon le user-agent serait du cloaking. Le statut déjà posé est conservé.
 */
add_action(
	'template_redirect',
	function () {
		if ( ! seo_crawl_config( 'page_legere' ) || is_admin() || wp_doing_ajax() || wp_doing_cron() || ! is_404() ) {
			return;
		}
		$code = http_response_code();
		if ( ! in_array( $code, array( 404, 410 ), true ) ) {
			$code = 404;
		}
		$nom    = get_bloginfo( 'name' );
		$titre  = ( 410 === $code ) ? 'Cette page n\'existe plus' : 'Page introuvable';
		$phrase = ( 410 === $code )
			? 'Cette adresse a été supprimée définitivement.'
			: 'Cette adresse n\'existe pas ou plus sur ce site.';

		status_header( $code );
		nocache_headers();
		header( 'Content-Type: text/html; charset=utf-8' );
		header( 'X-Robots-Tag: noindex' );
		echo '<!doctype html><html lang="' . esc_attr( get_bloginfo( 'language' ) ) . '"><head><meta charset="utf-8">'
			. '<meta name="viewport" content="width=device-width,initial-scale=1">'
			. '<meta name="robots" content="noindex">'
			. '<title>' . esc_html( $titre . ' — ' . $nom ) . '</title>'
			. '<style>body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;'
			. 'background:#fff;color:#333;font:16px/1.6 system-ui,-apple-system,sans-serif;padding:24px}'
			. 'main{max-width:34rem}h1{margin:0 0 .5rem;font-size:1.4rem;color:#111}p{margin:0 0 1.25rem}</style>'
			. '</head><body><main>'
			. '<h1>' . esc_html( $titre ) . '</h1>'
			. '<p>' . esc_html( $phrase ) . '</p>'
			. '<p><a href="' . esc_url( home_url( '/' ) ) . '">Retour à l\'accueil de ' . esc_html( $nom ) . '</a></p>'
			. '</main></body></html>';
		exit;
	},
	1
);

/* -------------------------------------------------------------------------
 * 5. Pages hors index et hors sitemap
 * ---------------------------------------------------------------------- */

function seo_crawl_hors_index_courant() {
	return in_array( seo_crawl_chemin_courant(), seo_crawl_config( 'hors_index' ), true );
}

/** Identifiants des contenus visés par une liste de chemins (cache 1 h). */
function seo_crawl_ids_pour( array $chemins ) {
	if ( ! $chemins ) {
		return array();
	}
	$cle = 'seo_crawl_ids_' . md5( SEO_CRAWL_VERSION . implode( '|', $chemins ) );
	$ids = get_transient( $cle );
	if ( is_array( $ids ) ) {
		return $ids;
	}
	$ids = array();
	foreach ( $chemins as $chemin ) {
		$p = get_page_by_path( $chemin, OBJECT, array( 'page', 'post' ) );
		if ( $p ) {
			$ids[] = (int) $p->ID;
		}
	}
	set_transient( $cle, $ids, HOUR_IN_SECONDS );

	return $ids;
}

/** Contenus à sortir des sitemaps : hors index et redirigés. */
function seo_crawl_ids_hors_sitemap() {
	return seo_crawl_ids_pour( array_merge(
		seo_crawl_config( 'hors_index' ),
		array_keys( seo_crawl_config( 'redirections' ) )
	) );
}

// En-tête HTTP : indépendant de toute extension SEO.
add_action(
	'template_redirect',
	function () {
		if ( seo_crawl_hors_index_courant() ) {
			header( 'X-Robots-Tag: noindex, follow' );
		}
	},
	5
);

// Balise robots : WordPress seul, Yoast, Rank Math.
add_filter(
	'wp_robots',
	function ( $robots ) {
		if ( seo_crawl_hors_index_courant() ) {
			$robots['noindex'] = true;
			unset( $robots['index'] );
		}
		return $robots;
	}
);
add_filter(
	'wpseo_robots_array',
	function ( $robots ) {
		if ( seo_crawl_hors_index_courant() ) {
			$robots['index'] = 'noindex';
		}
		return $robots;
	}
);
add_filter(
	'rank_math/frontend/robots',
	function ( $robots ) {
		if ( seo_crawl_hors_index_courant() ) {
			$robots['index'] = 'noindex';
		}
		return $robots;
	}
);

// Sitemaps : WordPress, Yoast, Rank Math. Un sitemap qui annonce une URL
// redirigée ou en noindex fait explorer pour rien.
add_filter(
	'wp_sitemaps_posts_query_args',
	function ( $args ) {
		$args['post__not_in'] = array_merge( isset( $args['post__not_in'] ) ? (array) $args['post__not_in'] : array(), seo_crawl_ids_hors_sitemap() );
		return $args;
	}
);
add_filter(
	'wpseo_exclude_from_sitemap_by_post_ids',
	function ( $ids ) {
		return array_values( array_unique( array_merge( (array) $ids, seo_crawl_ids_hors_sitemap() ) ) );
	}
);
add_filter(
	'rank_math/sitemap/entry',
	function ( $url, $type, $objet ) {
		if ( 'post' === $type && isset( $objet->ID ) && in_array( (int) $objet->ID, seo_crawl_ids_hors_sitemap(), true ) ) {
			return false;
		}
		return $url;
	},
	10,
	3
);

/* -------------------------------------------------------------------------
 * 6. robots.txt (désactivé par défaut)
 * ---------------------------------------------------------------------- */

/** Le robots.txt voulu, avec une ligne de marquage pour savoir qui le sert. */
function seo_crawl_robots_voulu() {
	$lignes = array_merge(
		array(
			'# robots.txt servi par le plugin « SEO — Budget de crawl » v' . SEO_CRAWL_VERSION . '.',
			'# Si cette ligne est absente, un fichier robots.txt physique est servi à la place.',
			'',
			'User-agent: *',
		),
		array_map( 'strval', (array) seo_crawl_config( 'robots_regles' ) )
	);
	$sitemap = (string) seo_crawl_config( 'robots_sitemap' );
	if ( '' !== $sitemap ) {
		$lignes[] = '';
		$lignes[] = 'Sitemap: ' . home_url( $sitemap );
	}
	if ( seo_crawl_config( 'sitemap_410' ) && seo_crawl_config( 'urls_410' ) ) {
		$lignes[] = 'Sitemap: ' . home_url( '/sitemap-urls-supprimees.xml' );
	}

	return implode( "\n", $lignes ) . "\n";
}

add_filter(
	'robots_txt',
	function ( $sortie, $public ) {
		// Site réglé sur « Demander aux moteurs de ne pas indexer » : on ne
		// rouvre pas ce que l'administrateur a fermé.
		if ( ! $public || ! seo_crawl_config( 'robots_txt' ) ) {
			return $sortie;
		}
		return seo_crawl_robots_voulu();
	},
	PHP_INT_MAX,
	2
);

/* -------------------------------------------------------------------------
 * 7. Cache d'Elementor
 * ---------------------------------------------------------------------- */

function seo_crawl_purge_elementor( $meta_id, $post_id, $cle ) {
	if ( '_elementor_data' !== $cle || ! seo_crawl_config( 'purge_elementor' ) ) {
		return;
	}
	delete_post_meta( $post_id, '_elementor_element_cache' );
	delete_post_meta( $post_id, '_elementor_css' );
	$upload = wp_upload_dir();
	$css    = trailingslashit( $upload['basedir'] ) . 'elementor/css/post-' . (int) $post_id . '.css';
	if ( file_exists( $css ) ) {
		wp_delete_file( $css );
	}
}
add_action( 'updated_post_meta', 'seo_crawl_purge_elementor', 10, 3 );
add_action( 'added_post_meta', 'seo_crawl_purge_elementor', 10, 3 );

/* -------------------------------------------------------------------------
 * 8. Contrôle : GET /wp-json/seo-crawl-fix/v1/etat (administrateurs)
 * ---------------------------------------------------------------------- */

add_action(
	'rest_api_init',
	function () {
		register_rest_route(
			'seo-crawl-fix/v1',
			'/etat',
			array(
				'methods'             => 'GET',
				'permission_callback' => function () {
					return current_user_can( 'manage_options' );
				},
				'callback'            => function () {
					$c = seo_crawl_config();
					return array(
						'version'          => SEO_CRAWL_VERSION,
						'config'           => file_exists( WP_CONTENT_DIR . '/seo-crawl-fix-config.php' ) ? 'wp-content/seo-crawl-fix-config.php' : 'config.php du plugin',
						'urls_410'         => count( $c['urls_410'] ),
						'motifs_410'       => count( (array) $c['motifs_410'] ),
						'hors_index'       => count( $c['hors_index'] ),
						'redirections'     => count( $c['redirections'] ),
						'robots_txt'       => (bool) $c['robots_txt'],
						'robots_physique'  => file_exists( ABSPATH . 'robots.txt' ),
						'page_legere'      => (bool) $c['page_legere'],
						'pagination_404'   => (bool) $c['pagination_404'],
					);
				},
			)
		);
	}
);

// Les identifiants résolus changent avec la configuration : purge à la
// (dés)activation.
function seo_crawl_purge_transients() {
	global $wpdb;
	$wpdb->query( "DELETE FROM {$wpdb->options} WHERE option_name LIKE '\\_transient\\_seo\\_crawl\\_%' OR option_name LIKE '\\_transient\\_timeout\\_seo\\_crawl\\_%'" ); // phpcs:ignore WordPress.DB.DirectDatabaseQuery
}
register_activation_hook( __FILE__, 'seo_crawl_purge_transients' );
register_deactivation_hook( __FILE__, 'seo_crawl_purge_transients' );
