<?php
/**
 * Configuration de « SEO — Entité ».
 *
 * Ce fichier est remplacé à chaque mise à jour du plugin par un zip. Pour
 * garder vos réglages, copiez-le en wp-content/seo-entite-config.php : s'il
 * existe, c'est lui qui est lu, et celui-ci est ignoré.
 *
 * Tant que organisation.name est vide, le plugin ne fait RIEN.
 *
 * Règle : aucune valeur inventée. Chaque champ vient d'une source vérifiable
 * (registre officiel des entreprises, profils réellement tenus par la
 * personne). Un champ inconnu reste vide : il n'est pas publié.
 * Les mêmes valeurs doivent figurer dans memoire/entites.csv du projet.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

return array(

	'organisation'  => array(
		// Organization, ou un sous-type plus précis : LocalBusiness,
		// ProfessionalService, Store, Restaurant…
		'@type'        => 'Organization',
		'name'         => '',
		'legalName'    => '',
		// Vide : l'adresse du site.
		'url'          => '',
		'logo'         => '',
		'description'  => '',
		'foundingDate' => '',
		// Identifiant officiel. Exemple (France) :
		// array( '@type' => 'PropertyValue', 'propertyID' => 'SIREN', 'value' => '000000000' ),
		'identifier'   => array(),
		'vatID'        => '',
		'telephone'    => '',
		'email'        => '',
		// Exemple :
		// array( '@type' => 'PostalAddress', 'streetAddress' => '…', 'postalCode' => '…',
		//        'addressLocality' => '…', 'addressCountry' => 'FR' ),
		'address'      => array(),
		// Exemple : array( '@type' => 'Country', 'name' => 'France' ),
		'areaServed'   => array(),
		'knowsAbout'   => array(),
		// Profils officiels : fiche au registre, LinkedIn de l'entreprise,
		// Wikidata, Google Business Profile… Mêmes URL partout sur le web.
		'sameAs'       => array(),
	),

	/*
	 * Personne liée (fondateur, auteur principal). Laisser name vide pour
	 * ne publier que l'organisation.
	 */
	'personne'      => array(
		// Fragment de l'identifiant : <site>/#<id>. Vide : tiré du nom.
		'id'               => '',
		'name'             => '',
		// Page « à propos » de la personne sur le site, si elle existe.
		'url'              => '',
		'jobTitle'         => '',
		'description'      => '',
		'image'            => '',
		'knowsAbout'       => array(),
		'sameAs'           => array(),
	),

	/* La personne est le fondateur de l'organisation (founder / worksFor). */
	'fondateur'     => true,

	/*
	 * Site à auteur unique : les « Person » que Yoast génère pour chaque
	 * compte auteur sont fusionnées dans la personne ci-dessus, et toutes les
	 * références (author, creator…) pointent vers elle. À laisser à false si
	 * plusieurs personnes écrivent sur le site.
	 */
	'auteur_unique' => false,

	/*
	 * Sans Yoast ni Rank Math : publier un WebSite en plus de l'organisation
	 * et de la personne (le plugin sort alors son propre bloc JSON-LD).
	 */
	'website'       => true,
);
