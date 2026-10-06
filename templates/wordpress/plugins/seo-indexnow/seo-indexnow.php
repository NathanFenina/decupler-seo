<?php
/**
 * Plugin Name: SEO IndexNow
 * Description: Publie la clé IndexNow à la racine du site et prévient IndexNow (Bing, Yandex, Seznam, Naver, Yep) à chaque publication ou mise à jour d'un contenu public. Ne touche pas à Google : pour Google, sitemap et Search Console.
 * Version: 1.0.0
 * Author: decupler-seo
 * License: MIT
 *
 * Clé : la constante INDEXNOW_KEY (wp-config.php) si elle existe, sinon une
 * clé générée à l'activation et gardée en option. Elle est servie à
 * https://<site>/<clé>.txt. Pour les scripts du projet (indexation.py),
 * mettez la même valeur dans la variable d'environnement INDEXNOW_KEY ;
 * un compte éditeur la lit sur GET /wp-json/seo-indexnow/v1/etat.
 */

if (!defined('ABSPATH')) {
    exit;
}

const SEO_INDEXNOW_OPTION = 'seo_indexnow_cle';
const SEO_INDEXNOW_JOURNAL = 'seo_indexnow_journal';
const SEO_INDEXNOW_API = 'https://api.indexnow.org/indexnow';

function seo_indexnow_cle(): string
{
    if (defined('INDEXNOW_KEY') && preg_match('/^[A-Za-z0-9-]{8,128}$/', (string) INDEXNOW_KEY)) {
        return (string) INDEXNOW_KEY;
    }
    $cle = (string) get_option(SEO_INDEXNOW_OPTION, '');
    if ($cle === '') {
        $cle = bin2hex(random_bytes(16));
        update_option(SEO_INDEXNOW_OPTION, $cle, false);
    }
    return $cle;
}

register_activation_hook(__FILE__, 'seo_indexnow_cle');

/* La clé à la racine : /<clé>.txt, en texte brut. */
add_action('parse_request', function () {
    $chemin = trim((string) parse_url($_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH), '/');
    $cle = seo_indexnow_cle();
    if ($chemin !== $cle . '.txt') {
        return;
    }
    status_header(200);
    header('Content-Type: text/plain; charset=utf-8');
    header('X-Robots-Tag: noindex');
    echo $cle;
    exit;
}, 0);

/* À chaque publication ou mise à jour d'un contenu public et indexable. */
add_action('transition_post_status', function ($nouveau, $ancien, $post) {
    if ($nouveau !== 'publish' || wp_is_post_revision($post) || wp_is_post_autosave($post)) {
        return;
    }
    $type = get_post_type_object($post->post_type);
    if (!$type || !$type->public || $post->post_type === 'attachment' || post_password_required($post)) {
        return;
    }
    if (seo_indexnow_noindex($post->ID)) {
        return;
    }
    $url = get_permalink($post);
    if ($url) {
        /* Envoi groupé en fin de requête : une mise à jour en masse = un seul appel. */
        $GLOBALS['seo_indexnow_file'][$url] = true;
    }
}, 10, 3);

add_action('shutdown', function () {
    $urls = array_keys($GLOBALS['seo_indexnow_file'] ?? []);
    if ($urls) {
        seo_indexnow_envoyer($urls);
    }
});

function seo_indexnow_noindex(int $id): bool
{
    if (get_post_meta($id, '_yoast_wpseo_meta-robots-noindex', true) === '1') {
        return true;
    }
    $rank = get_post_meta($id, 'rank_math_robots', true);
    if (is_array($rank) && in_array('noindex', $rank, true)) {
        return true;
    }
    return get_post_meta($id, '_seopress_robots_index', true) === 'yes';
}

function seo_indexnow_envoyer(array $urls): void
{
    if (wp_get_environment_type() !== 'production' && !defined('SEO_INDEXNOW_FORCER')) {
        seo_indexnow_noter(count($urls), 'non envoyé : environnement ' . wp_get_environment_type());
        return;
    }
    $hote = (string) parse_url(home_url('/'), PHP_URL_HOST);
    $cle = seo_indexnow_cle();
    $reponse = wp_remote_post(SEO_INDEXNOW_API, [
        'timeout' => 10,
        'blocking' => true,
        'headers' => ['Content-Type' => 'application/json; charset=utf-8'],
        'body' => wp_json_encode([
            'host' => $hote,
            'key' => $cle,
            'keyLocation' => home_url('/' . $cle . '.txt'),
            'urlList' => array_values(array_slice($urls, 0, 10000)),
        ]),
    ]);
    $code = is_wp_error($reponse) ? $reponse->get_error_message() : (string) wp_remote_retrieve_response_code($reponse);
    seo_indexnow_noter(count($urls), $code);
}

/* Les 20 derniers envois, lisibles par la route d'état. */
function seo_indexnow_noter(int $nombre, string $resultat): void
{
    $journal = (array) get_option(SEO_INDEXNOW_JOURNAL, []);
    array_unshift($journal, ['date' => gmdate('c'), 'urls' => $nombre, 'resultat' => $resultat]);
    update_option(SEO_INDEXNOW_JOURNAL, array_slice($journal, 0, 20), false);
}

add_action('rest_api_init', function () {
    register_rest_route('seo-indexnow/v1', '/etat', [
        'methods' => 'GET',
        'permission_callback' => function () {
            return current_user_can('edit_others_posts');
        },
        'callback' => function () {
            $cle = seo_indexnow_cle();
            return [
                'cle' => $cle,
                'fichier' => home_url('/' . $cle . '.txt'),
                'environnement' => wp_get_environment_type(),
                'derniers_envois' => get_option(SEO_INDEXNOW_JOURNAL, []),
            ];
        },
    ]);
});
