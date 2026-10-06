<?php
/**
 * Plugin Name:       SEO — Entité
 * Description:       Publie une entité unique et complète dans les données structurées : l'organisation (données officielles, profils sameAs), la personne liée, et un seul identifiant par entité sur tout le site. Complète le graphe de Yoast ou de Rank Math, ou publie son propre JSON-LD sans eux. Tout se règle dans config.php.
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
 *   Audit de dix pages d'un site d'agence :
 *   - l'Organisation publiée par l'extension SEO n'avait aucun sameAs : rien
 *     ne la reliait à ses profils ni au registre officiel ;
 *   - le fondateur existait sous trois identifiants différents selon les
 *     pages (#prenom-nom, #/schema/person/<empreinte>, et sans @id) ;
 *   - deux URL LinkedIn différentes circulaient.
 *   Un moteur (Google, ChatGPT, Perplexity) qui ne peut pas relier ces
 *   morceaux voit trois inconnus au lieu d'un expert identifié.
 *
 * PIÈGE DÉJÀ PAYÉ
 *
 *   Yoast ne publie l'Organisation que si son nom ET son logo sont réglés.
 *   Sans elle, founder et worksFor pointeraient dans le vide : le plugin la
 *   crée alors lui-même.
 *
 * Filtres : seo_entite_config (toute la configuration),
 * seo_entite_organisation, seo_entite_personne (les nœuds publiés).
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const SEO_ENTITE_VERSION = '1.0.0';

/* -------------------------------------------------------------------------
 * Configuration et nœuds
 * ---------------------------------------------------------------------- */

function seo_entite_config( $cle = null ) {
	static $config = null;
	if ( null === $config ) {
		$externe = WP_CONTENT_DIR . '/seo-entite-config.php';
		$lu      = include ( file_exists( $externe ) ? $externe : __DIR__ . '/config.php' );
		$config  = apply_filters(
			'seo_entite_config',
			array_merge(
				array(
					'organisation'  => array(),
					'personne'      => array(),
					'fondateur'     => true,
					'auteur_unique' => false,
					'website'       => true,
				),
				is_array( $lu ) ? $lu : array()
			)
		);
	}

	return null === $cle ? $config : ( isset( $config[ $cle ] ) ? $config[ $cle ] : null );
}

/** Retire les champs vides : un champ inconnu n'est pas publié. */
function seo_entite_sans_vides( array $noeud ) {
	return array_filter(
		$noeud,
		function ( $v ) {
			return ! ( '' === $v || null === $v || array() === $v );
		}
	);
}

function seo_entite_base() {
	return trailingslashit( home_url() );
}

function seo_entite_id_organisation() {
	return seo_entite_base() . '#organization';
}

/** Identifiant de la personne, ou chaîne vide s'il n'y en a pas. */
function seo_entite_id_personne() {
	$p = (array) seo_entite_config( 'personne' );
	if ( empty( $p['name'] ) ) {
		return '';
	}
	$fragment = ! empty( $p['id'] ) ? $p['id'] : $p['name'];

	return seo_entite_base() . '#' . sanitize_title( $fragment );
}

/** Le plugin est-il configuré ? */
function seo_entite_actif() {
	$o = (array) seo_entite_config( 'organisation' );

	return ! empty( $o['name'] );
}

/** Nœud Organisation complet, tel que configuré. */
function seo_entite_organisation() {
	$o = seo_entite_sans_vides( (array) seo_entite_config( 'organisation' ) );
	$noeud = array_merge(
		array(
			'@type' => 'Organization',
			'@id'   => seo_entite_id_organisation(),
			'url'   => seo_entite_base(),
		),
		$o
	);
	$noeud['@id'] = seo_entite_id_organisation();
	if ( isset( $noeud['logo'] ) && is_string( $noeud['logo'] ) ) {
		$noeud['logo'] = array( '@type' => 'ImageObject', 'url' => $noeud['logo'] );
	}
	if ( seo_entite_config( 'fondateur' ) && seo_entite_id_personne() ) {
		$noeud['founder'] = array( '@id' => seo_entite_id_personne() );
	}

	return apply_filters( 'seo_entite_organisation', $noeud );
}

/** Nœud Personne complet, ou tableau vide. */
function seo_entite_personne() {
	$id = seo_entite_id_personne();
	if ( '' === $id ) {
		return array();
	}
	$p = seo_entite_sans_vides( (array) seo_entite_config( 'personne' ) );
	unset( $p['id'] );
	$noeud = array_merge( array( '@type' => 'Person', '@id' => $id ), $p );
	if ( ! empty( $noeud['url'] ) ) {
		$noeud['mainEntityOfPage'] = $noeud['url'];
	}
	if ( seo_entite_config( 'fondateur' ) ) {
		$noeud['worksFor'] = array( '@id' => seo_entite_id_organisation() );
	}

	return apply_filters( 'seo_entite_personne', $noeud );
}

/* -------------------------------------------------------------------------
 * Fusion dans un graphe existant
 * ---------------------------------------------------------------------- */

/**
 * Fusionne deux listes sans doublon, en gardant l'ordre. Un sameAs vers le
 * site lui-même (champ « site web » d'un profil auteur) est écarté : sameAs
 * relie l'entité à d'AUTRES sources.
 */
function seo_entite_union( $a, $b ) {
	$a = is_array( $a ) ? $a : ( $a ? array( $a ) : array() );
	$b = is_array( $b ) ? $b : ( $b ? array( $b ) : array() );
	$site = untrailingslashit( seo_entite_base() );

	return array_values( array_filter(
		array_unique( array_merge( $a, $b ), SORT_REGULAR ),
		function ( $v ) use ( $site ) {
			return ! is_string( $v ) || untrailingslashit( $v ) !== $site;
		}
	) );
}

/** Remplace récursivement les références {"@id": ancien} par le nouvel identifiant. */
function seo_entite_repointe( $noeud, array $anciens, $nouveau ) {
	if ( ! is_array( $noeud ) ) {
		return $noeud;
	}
	foreach ( $noeud as $cle => $valeur ) {
		if ( '@id' === $cle && is_string( $valeur ) && in_array( $valeur, $anciens, true ) ) {
			$noeud[ $cle ] = $nouveau;
		} elseif ( is_array( $valeur ) ) {
			$noeud[ $cle ] = seo_entite_repointe( $valeur, $anciens, $nouveau );
		}
	}

	return $noeud;
}

function seo_entite_est_type( $noeud, $type ) {
	return in_array( $type, isset( $noeud['@type'] ) ? (array) $noeud['@type'] : array(), true );
}

/** Personne générée par l'extension SEO pour un compte auteur ? */
function seo_entite_est_auteur_genere( $noeud ) {
	if ( ! seo_entite_est_type( $noeud, 'Person' ) || empty( $noeud['@id'] ) || ! is_string( $noeud['@id'] ) ) {
		return false;
	}

	global $wp_rewrite;
	$base_auteur = seo_entite_base() . ( ! empty( $wp_rewrite->author_base ) ? $wp_rewrite->author_base : 'author' ) . '/';

	// Yoast : <site>/#/schema/person/<empreinte> ; Rank Math : l'URL de la
	// page auteur (<site>/author/<identifiant>/).
	return false !== strpos( $noeud['@id'], '#/schema/person/' )
		|| 0 === strpos( $noeud['@id'], $base_auteur );
}

/**
 * Complète un graphe (liste ou tableau associatif de nœuds) : enrichit
 * l'Organisation existante ou la crée, fusionne les auteurs générés si le
 * site est à auteur unique, ajoute la Personne une seule fois.
 */
function seo_entite_completer( $graphe ) {
	if ( ! is_array( $graphe ) || ! seo_entite_actif() ) {
		return $graphe;
	}
	$id_org      = seo_entite_id_organisation();
	$id_personne = seo_entite_id_personne();
	$personne    = seo_entite_personne();
	$org         = seo_entite_organisation();
	$anciens     = array();
	$trouvee     = false;
	// Yoast passe une liste, Rank Math un tableau associatif (publisher, …).
	$liste       = ! $graphe || array_keys( $graphe ) === range( 0, count( $graphe ) - 1 );

	foreach ( $graphe as $i => $noeud ) {
		if ( ! is_array( $noeud ) ) {
			continue;
		}
		$id = isset( $noeud['@id'] ) && is_string( $noeud['@id'] ) ? $noeud['@id'] : '';
		if ( $id === $id_org ) {
			// Les listes s'additionnent ; un champ déjà rempli par
			// l'extension n'est pas écrasé, sauf le fondateur et un type
			// plus précis qu'« Organization » (LocalBusiness…).
			foreach ( $org as $cle => $valeur ) {
				$precis = ( '@type' === $cle && 'Organization' !== $valeur );
				if ( in_array( $cle, array( 'sameAs', 'knowsAbout' ), true ) ) {
					$noeud[ $cle ] = seo_entite_union( isset( $noeud[ $cle ] ) ? $noeud[ $cle ] : array(), $valeur );
				} elseif ( empty( $noeud[ $cle ] ) || 'founder' === $cle || $precis ) {
					$noeud[ $cle ] = $valeur;
				}
			}
			$graphe[ $i ] = $noeud;
			$trouvee      = true;
			continue;
		}
		if ( ! $personne ) {
			continue;
		}
		if ( $id === $id_personne ) {
			// Déjà publiée par une autre source : on la complète.
			$personne = array_merge( $noeud, $personne );
			unset( $graphe[ $i ] );
		} elseif ( seo_entite_config( 'auteur_unique' ) && seo_entite_est_auteur_genere( $noeud ) ) {
			$anciens[] = $id;
			foreach ( array( 'sameAs', 'knowsAbout' ) as $cle ) {
				if ( ! empty( $noeud[ $cle ] ) ) {
					$personne[ $cle ] = seo_entite_union( isset( $personne[ $cle ] ) ? $personne[ $cle ] : array(), $noeud[ $cle ] );
				}
			}
			unset( $graphe[ $i ] );
		}
	}

	if ( ! $trouvee ) {
		if ( $liste ) {
			$graphe[] = $org;
		} else {
			$graphe['seoEntiteOrganisation'] = $org;
		}
	}
	if ( $anciens ) {
		$graphe = seo_entite_repointe( $graphe, $anciens, $id_personne );
	}
	if ( $personne ) {
		if ( $liste ) {
			$graphe[] = $personne;
		} else {
			$graphe['seoEntitePersonne'] = $personne;
		}
	}

	return $liste ? array_values( $graphe ) : $graphe;
}

/* -------------------------------------------------------------------------
 * Branchements : Yoast, Rank Math, ou JSON-LD autonome
 * ---------------------------------------------------------------------- */

add_filter( 'wpseo_schema_graph', 'seo_entite_completer', 20 );

// Rank Math : tableau associatif de nœuds. Priorité 100 : après sa propre
// mise en relation des entités (priorité 99).
add_filter(
	'rank_math/json_ld',
	function ( $donnees ) {
		return seo_entite_completer( $donnees );
	},
	100
);

// Sans extension SEO qui publie un graphe : notre propre bloc.
add_action(
	'wp_head',
	function () {
		if ( defined( 'WPSEO_VERSION' ) || defined( 'RANK_MATH_VERSION' ) || ! seo_entite_actif() ) {
			return;
		}
		$graphe = array();
		if ( seo_entite_config( 'website' ) ) {
			$graphe[] = array(
				'@type'     => 'WebSite',
				'@id'       => seo_entite_base() . '#website',
				'url'       => seo_entite_base(),
				'name'      => get_bloginfo( 'name' ),
				'publisher' => array( '@id' => seo_entite_id_organisation() ),
				'inLanguage' => get_bloginfo( 'language' ),
			);
		}
		$graphe = seo_entite_completer( $graphe );
		echo '<script type="application/ld+json" class="seo-entite">'
			. wp_json_encode( array( '@context' => 'https://schema.org', '@graph' => $graphe ), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_HEX_TAG | JSON_HEX_AMP )
			. '</script>' . "\n";
	},
	20
);
