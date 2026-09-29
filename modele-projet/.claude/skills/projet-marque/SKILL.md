---
name: projet-marque
description: >
  Applique la voix, le lexique, les chiffres officiels et les interdits de
  {{NOM}} ({{DOMAINE}}) à tout contenu produit pour ce site. Déclencher dès
  qu'on rédige, réécrit, optimise ou relit un contenu de {{DOMAINE}} — en
  complément des skills de méthode (seo-redaction, seo-optimisation-onpage,
  seo-brief, seo-faq-paa), jamais à leur place.
---

# Marque {{NOM}}

Les skills de méthode disent **comment** faire du bon SEO. Celui-ci dit
**comment le faire pour ce client-là**. Il ne contient pas de méthode : s'il
en contient un jour, elle doit remonter dans decupler-seo.

## À appliquer à chaque contenu

1. Lire `memoire/marque.md` en entier avant d'écrire la première phrase.
2. Utiliser **uniquement** les chiffres de la section « Chiffres officiels ».
   Tout autre chiffre sur la marque est interdit, même plausible.
3. Respecter le lexique : remplacer chaque terme de la colonne « Éviter ».
4. Vérifier les interdits avant de livrer.
5. Consulter `memoire/apprentissages.md` : si un format ou un angle a déjà
   échoué sur ce site, ne pas le reproduire.

## Règles propres à ce projet

Elles priment sur les valeurs par défaut de la méthode. Elles sont aussi
déclarées dans `decupler-seo.config.yml` → `regles`, que les scripts lisent.

- Occurrences du mot-clé principal : voir `regles.mot_cle_occurrences_min`
  (vide = placement naturel : H1, 100 premiers mots, un H2, conclusion)

## Contrôle final

- [ ] Aucune phrase ne pourrait figurer telle quelle sur le site d'un concurrent
- [ ] Chiffres de marque : tous issus de la liste officielle
- [ ] Aucun terme de la colonne « Éviter »
- [ ] Aucun interdit enfreint
