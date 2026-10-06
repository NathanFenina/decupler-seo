<?php
/**
 * Configuration de « SEO — Budget de crawl ».
 *
 * Ce fichier est remplacé à chaque mise à jour du plugin par un zip. Pour
 * garder vos réglages, copiez-le en wp-content/seo-crawl-fix-config.php :
 * s'il existe, c'est lui qui est lu, et celui-ci est ignoré.
 *
 * Tout est vide ou prudent par défaut : installé tel quel, le plugin ne sert
 * qu'une page d'erreur légère et un 404 sur la pagination hors limites.
 *
 * Les chemins s'écrivent SANS barre au début ni à la fin, décodés (UTF-8) :
 * « ancienne-page », « blog/ancien-article », pas « /ancienne-page/ ».
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

return array(

	/*
	 * 410 « supprimée définitivement » sur une liste FERMÉE de chemins :
	 * pages de spam laissées par un piratage, anciennes pages supprimées
	 * volontairement. Google lâche un 410 plus vite qu'un 404.
	 *
	 * Le 410 n'est posé que si WordPress répond DÉJÀ 404 : une page qui
	 * existe n'est jamais touchée, même listée par erreur.
	 *
	 * Source de la liste : Search Console (pages indexées, exports), relevée
	 * et vérifiée en 404 une par une. Exemple :
	 *   'casino-bonus-sans-depot-2026',
	 *   'replica-montres-pas-cher',
	 */
	'urls_410'      => array(),

	/*
	 * Date du relevé de la liste ci-dessus (AAAA-MM-JJ), servie en <lastmod>
	 * du sitemap temporaire. Vide : date du jour.
	 */
	'date_releve'   => '',

	/*
	 * Sitemap temporaire des URL en 410 : /sitemap-urls-supprimees.xml.
	 * À soumettre dans Search Console pour que Google repasse lire les 410,
	 * puis à retirer de Search Console quand le compteur est à zéro.
	 * Ne liste que « urls_410 » (un motif ne se liste pas).
	 */
	'sitemap_410'   => true,

	/*
	 * Motifs (expressions régulières PHP, avec délimiteurs) qui posent aussi
	 * un 410, sur les URL qui répondent DÉJÀ 404. Pour un piratage qui a
	 * généré des milliers d'URL de même forme. Testez chaque motif contre la
	 * liste de vos vraies URL (sitemap) avant de l'activer : un motif trop
	 * large (« #casino# ») peut viser une future page légitime le jour où
	 * elle est supprimée ou renommée.
	 * Exemples :
	 *   '#^[a-z0-9-]*-casino-[a-z0-9-]*$#',
	 *   '#^[0-9]{6,}\.html$#',
	 */
	'motifs_410'    => array(),

	/*
	 * Pages sans valeur de recherche à sortir de l'index ET du sitemap :
	 * panier, commande, compte client, remerciements, événements passés.
	 * Noindex par l'extension SEO (Yoast, Rank Math) ET par l'en-tête HTTP
	 * X-Robots-Tag : le noindex ne dépend pas d'un seul plugin.
	 * Exemple : 'panier', 'commander', 'mon-compte', 'merci',
	 */
	'hors_index'    => array(),

	/*
	 * Redirections 301 : chemin => URL absolue de destination. Seulement
	 * quand la cible couvre DÉJÀ l'intention de la page redirigée. Les
	 * chemins redirigés sortent aussi du sitemap.
	 * Exemple : 'ancien-guide' => 'https://www.exemple.fr/nouveau-guide/',
	 */
	'redirections'  => array(),

	/* Page 404/410 légère (~1 Ko) au lieu de la page complète du thème. */
	'page_legere'   => true,

	/* 404 sur la pagination au-delà de la dernière page réelle (/page/9999/). */
	'pagination_404' => true,

	/*
	 * robots.txt servi par ce plugin (robots.txt VIRTUEL de WordPress).
	 * Désactivé par défaut : modifier le robots.txt d'un site en production
	 * se valide d'abord. Sans effet si un fichier robots.txt physique existe
	 * à la racine : le serveur le sert avant WordPress.
	 */
	'robots_txt'    => false,

	/*
	 * Règles du robots.txt. « Disallow » empêche l'exploration, PAS
	 * l'indexation : n'y mettez jamais une URL que vous voulez désindexer
	 * (Google ne pourrait plus lire son noindex ni son 410).
	 */
	'robots_regles' => array(
		'# Recherche interne : espace d\'URL infini.',
		'Disallow: /*?s=',
		'Disallow: /*&s=',
		'',
		'# Paramètres de suivi et d\'attachement : doublons de pages existantes.',
		'Disallow: /*?utm_',
		'Disallow: /*&utm_',
		'Disallow: /*?attachment_id=',
		'Disallow: /*?replytocom=',
		'',
		'# Administration, hors l\'endpoint ajax dont le front a besoin.',
		'Disallow: /wp-admin/',
		'Allow: /wp-admin/admin-ajax.php',
	),

	/*
	 * URL du sitemap déclaré dans le robots.txt, relative au site.
	 * Yoast : /sitemap_index.xml ; Rank Math : /sitemap_index.xml ;
	 * WordPress seul : /wp-sitemap.xml.
	 */
	'robots_sitemap' => '/sitemap_index.xml',

	/*
	 * Purge du cache d'Elementor quand _elementor_data change (écriture par
	 * l'API REST). Sans effet si Elementor n'est pas installé.
	 */
	'purge_elementor' => true,
);
