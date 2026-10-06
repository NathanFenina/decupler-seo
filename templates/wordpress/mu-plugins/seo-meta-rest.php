<?php
/**
 * Plugin Name: SEO — métas en écriture par l'API REST
 * Description: Ouvre à l'écriture par l'API REST le title, la meta description, la requête cible, la canonique et le noindex de l'extension SEO active (Yoast SEO, Rank Math ou SEOPress). Sans ce fichier, WordPress répond 200 et jette ces valeurs sans rien dire.
 * Version:     1.0.0
 * License:     GPL-2.0-or-later
 * Requires PHP: 7.4
 *
 * Modèle decupler-seo (templates/wordpress/). Installation, test et
 * désinstallation : templates/wordpress/README.md.
 *
 * POURQUOI
 *
 *   WordPress ignore sans erreur un champ « meta » qui n'est pas déclaré dans
 *   l'API REST : la requête renvoie 200, la réponse a l'air normale, et rien
 *   n'est écrit. Yoast n'expose aucun de ses champs ; Rank Math et SEOPress
 *   pas toujours. Ce fichier les déclare, pour les comptes qui ont déjà le
 *   droit de modifier le contenu concerné.
 *
 * CE QU'IL FAIT
 *
 *   - Détecte l'extension SEO active au chargement (init) et ne déclare QUE
 *     ses champs. Aucune extension détectée : il ne fait rien.
 *   - Contrôle de droits par contenu : current_user_can( 'edit_post', $id ).
 *     Un mot de passe d'application hérite des droits de son compte.
 *   - Nettoie chaque valeur selon son type (texte, URL, drapeau noindex).
 *   - Expose GET /wp-json/seo-meta-rest/v1/etat (comptes éditeurs seulement)
 *     pour vérifier l'installation : extension détectée et champs ouverts.
 *
 * Installation : déposer ce fichier dans wp-content/mu-plugins/ (créer le
 * dossier s'il n'existe pas). Un mu-plugin se charge sans activation et ne
 * peut pas être désactivé par erreur depuis l'administration.
 */

defined( 'ABSPATH' ) || exit;

const SEO_META_REST_VERSION = '1.0.0';

/**
 * Extension SEO active, ou chaîne vide.
 *
 * Testée au moment de l'appel : un mu-plugin se charge AVANT les extensions,
 * leurs constantes n'existent pas encore quand ce fichier est lu.
 */
function seo_meta_rest_extension() {
	if ( defined( 'WPSEO_VERSION' ) ) {
		return 'yoast';
	}
	if ( defined( 'RANK_MATH_VERSION' ) || class_exists( 'RankMath' ) ) {
		return 'rankmath';
	}
	if ( defined( 'SEOPRESS_VERSION' ) ) {
		return 'seopress';
	}
	return '';
}

/**
 * Champs ouverts par extension : clé de méta => type de nettoyage.
 *
 * Types : texte, url, yoast_noindex (« 1 » = noindex, « 2 » = index, vide =
 * réglage du type de contenu), oui_vide (SEOPress : « yes » = noindex),
 * robots (Rank Math : liste de directives).
 */
function seo_meta_rest_champs( $extension ) {
	$champs = array(
		'yoast'    => array(
			'_yoast_wpseo_title'               => 'texte',
			'_yoast_wpseo_metadesc'            => 'texte',
			'_yoast_wpseo_focuskw'             => 'texte',
			'_yoast_wpseo_canonical'           => 'url',
			'_yoast_wpseo_meta-robots-noindex' => 'yoast_noindex',
		),
		'rankmath' => array(
			'rank_math_title'         => 'texte',
			'rank_math_description'   => 'texte',
			'rank_math_focus_keyword' => 'texte',
			'rank_math_canonical_url' => 'url',
			'rank_math_robots'        => 'robots',
		),
		'seopress' => array(
			'_seopress_titles_title'       => 'texte',
			'_seopress_titles_desc'        => 'texte',
			'_seopress_analysis_target_kw' => 'texte',
			'_seopress_robots_canonical'   => 'url',
			'_seopress_robots_index'       => 'oui_vide',
		),
	);
	$liste = isset( $champs[ $extension ] ) ? $champs[ $extension ] : array();

	/**
	 * Ajouter ou retirer un champ :
	 * add_filter( 'seo_meta_rest_champs', function ( $c, $ext ) { unset( $c['_yoast_wpseo_canonical'] ); return $c; }, 10, 2 );
	 */
	return apply_filters( 'seo_meta_rest_champs', $liste, $extension );
}

/**
 * Types de contenu concernés : tous les types publics servis par l'API REST,
 * sauf les médias. Un type personnalisé doit aussi déclarer le support
 * « custom-fields », sinon WordPress n'affiche pas son objet « meta ».
 */
function seo_meta_rest_types() {
	$types = get_post_types( array( 'public' => true, 'show_in_rest' => true ) );
	unset( $types['attachment'] );

	return apply_filters( 'seo_meta_rest_types', array_values( $types ) );
}

/** Directives robots acceptées pour Rank Math. */
const SEO_META_REST_ROBOTS = array( 'index', 'noindex', 'follow', 'nofollow', 'noarchive', 'noimageindex', 'nosnippet' );

/** Nettoie une valeur selon le type du champ. */
function seo_meta_rest_nettoyer( $valeur, $type ) {
	switch ( $type ) {
		case 'url':
			return esc_url_raw( trim( (string) $valeur ) );
		case 'yoast_noindex':
			$valeur = (string) $valeur;
			return in_array( $valeur, array( '1', '2' ), true ) ? $valeur : '';
		case 'oui_vide':
			return 'yes' === (string) $valeur ? 'yes' : '';
		case 'robots':
			$liste = is_array( $valeur ) ? $valeur : explode( ',', (string) $valeur );
			$liste = array_map( 'sanitize_key', array_map( 'trim', $liste ) );
			return array_values( array_unique( array_intersect( $liste, SEO_META_REST_ROBOTS ) ) );
		default:
			return sanitize_text_field( (string) $valeur );
	}
}

/**
 * Déclaration des champs. Priorité 99 : si l'extension SEO déclare elle-même
 * un de ces champs (sans show_in_rest), notre déclaration passe après.
 */
add_action(
	'init',
	function () {
		$extension = seo_meta_rest_extension();
		if ( '' === $extension ) {
			return;
		}
		foreach ( seo_meta_rest_types() as $type_contenu ) {
			foreach ( seo_meta_rest_champs( $extension ) as $cle => $type ) {
				$liste = ( 'robots' === $type );
				register_post_meta(
					$type_contenu,
					$cle,
					array(
						'type'              => $liste ? 'array' : 'string',
						'single'            => true,
						'show_in_rest'      => $liste
							? array( 'schema' => array( 'type' => 'array', 'items' => array( 'type' => 'string' ) ) )
							: true,
						'sanitize_callback' => function ( $valeur ) use ( $type ) {
							return seo_meta_rest_nettoyer( $valeur, $type );
						},
						// Réservé aux comptes qui peuvent déjà modifier CE contenu.
						'auth_callback'     => function ( $autorise, $cle_meta, $id ) {
							return current_user_can( 'edit_post', $id );
						},
					)
				);
			}
		}
	},
	99
);

/**
 * Contrôle d'installation : GET /wp-json/seo-meta-rest/v1/etat.
 * Ne renvoie que des noms de champs, jamais de valeur.
 */
add_action(
	'rest_api_init',
	function () {
		register_rest_route(
			'seo-meta-rest/v1',
			'/etat',
			array(
				'methods'             => 'GET',
				'permission_callback' => function () {
					return current_user_can( 'edit_posts' );
				},
				'callback'            => function () {
					$extension = seo_meta_rest_extension();
					return array(
						'version'    => SEO_META_REST_VERSION,
						'extension'  => $extension ? $extension : null,
						'champs'     => array_keys( seo_meta_rest_champs( $extension ) ),
						'types'      => seo_meta_rest_types(),
					);
				},
			)
		);
	}
);
