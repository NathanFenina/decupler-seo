<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 9 · Design de page

**Skills** : `seo-design-pages`, `seo-page-builder-html` · **Commande** : `/seo design, puis /seo page`

**Objectif** : Une page qui se lit, se cite et convertit, construite selon son type.

**Quand** : Avant d'intégrer une page neuve ou une refonte.

**Dis à Claude** : « Quel gabarit pour cette page ? Fais le plan des boutons et des images, puis génère le HTML prêt à coller. »

## Étapes

1. Typer la page : service, article, page locale, landing, comparatif, outil, lead magnet. En cas de doute, le format des trois premiers résultats tranche.
2. Le gabarit section par section, le plan de CTA (une action, ses emplacements, ses libellés) et les bannières de preuve.
3. Le plan d'images : un rôle par image, son poids, son texte `alt`.
4. Le HTML autonome, avec un CSS limité à la page, prêt pour WordPress, Elementor ou Webflow.
5. Contrôle bloquant : rendu réel à 390 et à 1 440 px, image principale jamais en `lazy`, chaque bouton mène quelque part, chaque preuve a sa source.

**MCP nécessaires** : Chrome DevTools pour le rendu réel. Un générateur d'images en option.

**Livrable** : `design-<slug>.md`, le fragment HTML et les captures à 390 et 1 440 px.

## Pièges

- Un guide construit comme une landing : la réponse se noie dans l'argumentaire.
- Vérifier le rendu en ouvrant le fichier en local (`file://`) : les animations ne se déclenchent pas.
- Un bouton « Télécharger » qui ne télécharge rien.

> Chez nous : Cette page a suivi la même méthode : HTML assemblé par script, rendu vérifié dans Chromium à 390 et 1 440 px avant publication.
