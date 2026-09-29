# Déploiement — socle généré, nœuds injectés côté serveur

## Générer le socle

`schema/socle-source.json` est le seul fichier qu'on édite : les données de
l'organisation, recopiées des mentions légales et de la page contact.

```json
{
  "site": "https://exemple.com",
  "nom": "Exemple",
  "raison_sociale": "Exemple SARL",
  "identifiant": { "propertyID": "SIREN", "value": "A_CONFIRMER" },
  "tva": "A_CONFIRMER",
  "logo_sombre": "https://exemple.com/wp-content/uploads/logo-sombre.png",
  "telephone": "+33…",
  "adresse": { "streetAddress": "…", "postalCode": "…", "addressLocality": "…", "addressCountry": "FR" },
  "profils": ["https://www.linkedin.com/company/…"],
  "wikidata": null
}
```

L'agent en tire `schema/socle-global.json` : un `@graph` avec
`Organization` (`@id` `{site}/#organization`, `legalName`, `identifier` en
`PropertyValue`, `vatID`, `logo` → `{site}/#logo`, `sameAs`), l'`ImageObject`
du logo et `WebSite` (`@id` `{site}/#website`, `publisher` →
`#organization`). Tant qu'un `A_CONFIRMER` reste dans la source, le socle
n'est pas livré.

Le contrôle de chaque page compare ensuite ses nœuds au socle :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/schema_validate.py" https://exemple.com/page/ \
  --socle schema/socle-global.json --strict
```

## WordPress + Yoast

Le plugin produit déjà un graphe : on y ajoute nos nœuds et on remplace ses
nœuds `Organization`/`WebSite` par ceux du socle.

```php
add_filter( 'wpseo_schema_graph', function ( $graph, $context ) {
    $dossier = get_stylesheet_directory() . '/schema/';
    $socle   = json_decode( file_get_contents( $dossier . 'socle-global.json' ), true )['@graph'];
    $ids     = array_column( $socle, '@id' );
    // Retirer les nœuds du plugin qui portent les mêmes @id que le socle.
    $graph = array_values( array_filter( $graph, fn( $n ) => ! in_array( $n['@id'] ?? '', $ids, true ) ) );
    $graph = array_merge( $socle, $graph );

    $slug    = get_post_field( 'post_name', get_queried_object_id() );
    $fichier = $dossier . $slug . '.json';
    if ( is_readable( $fichier ) ) {
        $graph = array_merge( $graph, json_decode( file_get_contents( $fichier ), true ) );
    }
    return $graph;
}, 20, 2 );
```

Vérifier ensuite que le `WebPage` du plugin et le nôtre ne coexistent pas
(même `@id` `{canonical}#webpage`, ou désactiver la pièce du plugin).

## WordPress + Rank Math

```php
add_filter( 'rank_math/json_ld', function ( $data, $jsonld ) {
    $slug    = get_post_field( 'post_name', get_queried_object_id() );
    $fichier = get_stylesheet_directory() . '/schema/' . $slug . '.json';
    if ( is_readable( $fichier ) ) {
        foreach ( json_decode( file_get_contents( $fichier ), true ) as $i => $noeud ) {
            $data[ 'decupler_' . $i ] = $noeud;
        }
    }
    return $data;
}, 99, 2 );
```

## Sans plugin (site statique, framework)

Le gabarit de page assemble `socle-global.json` + `schema/<slug>.json` en
un seul `@graph`, rendu dans le `<head>` côté serveur ou au build.

## Interdits

- **GTM ou tout script client** : absent du HTML initial, invisible pour les
  robots qui ne rendent pas le JavaScript.
- **Deux balises** (plugin + la nôtre à côté) : deux `Organization`, Google
  ignore les deux.
- **Socle retouché dans une page** : il diverge, `--socle` le signale.
