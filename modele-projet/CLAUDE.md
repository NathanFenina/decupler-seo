# {{NOM}} — mémoire du projet

Ce fichier est chargé au début de chaque session, y compris dans les
routines. Il dit **qui est ce projet** et **où se trouve le reste**. Gardez-le
court : le détail vit dans `memoire/`.

## Identité

- **Site** : {{DOMAINE}}
- **Marché** : {{PAYS}} · langues : {{LANGUES}}
- **CMS** : {{CMS}} · publication : **{{PUBLICATION}}** (`cms` = par l'API du CMS, `depot` = fusionner c'est publier)
- **Activité** : {{ACTIVITE}}
- **Ce qui doit rapporter** : les pages listées dans `decupler-seo.config.yml` → `projet.pages_prioritaires`

## Comment travailler sur ce projet

1. **Toujours lire d'abord** : `decupler-seo.config.yml` (règles et seuils),
   puis `memoire/marque.md` (voix et interdits) ; avant d'écrire,
   `memoire/style.md` (le style mesuré sur les pages du client).
2. **Méthode** : les skills de `.claude/skills/` (synchronisés depuis
   decupler-seo — ne pas les modifier ici, ils seraient écrasés à la
   prochaine synchronisation). Ce qui est propre à ce projet vit dans
   `.claude/skills/projet-*`.
3. **Toute modification publiée** est inscrite dans `journal/modifications.csv`
   avec sa situation de départ, via `seo-journal-mesure`. Sans exception :
   une modification non journalisée ne pourra jamais être évaluée ni annulée.
4. **Avant toute écriture externe** :
   `python3 .claude/decupler-seo/scripts/guard.py --action <action> --cible <url>`
5. **Ne jamais inventer un chiffre.** Donnée absente = « nécessite tel outil ».

## Règles d'or

Chacune vient d'un incident réel sur ce projet. Quand un problème survient,
on ajoute la règle qui l'aurait évité — avec la date et ce qui s'est passé.

1. **Aucun chiffre hors de `memoire/faits.md`.** Aucune preuve inventée : ni
   témoignage, ni compteur de clients, ni logo, ni certification supposée.
2. **Avant d'écrire, vérifier que le site ne couvre pas déjà l'intention**
   (passe anti-cannibalisation de `seo-redaction`).
3. **Rien ne part sans contrôle** : `controle_contenu.py`, puis les commandes
   de `controle.commandes` dans la config.

## Niveaux d'autonomie

| Niveau | Quoi | Règle |
|---|---|---|
| Automatique | title, meta, FAQ, schema, liens internes sur pages existantes | publié, sauvegardé, journalisé |
| Validation | nouvelles pages, réécriture de sections de pages qui rankent | brouillon CMS (ou PR non fusionnée sur un site en code) + ligne dans `rapports/a-valider.md` |
| Interdit | robots.txt, redirections, canonicals en prod, suppression, outreach, forums, fiche Google | proposition uniquement |

Plafond : **{{PAGES_MAX}} pages neuves par semaine**, qualité avant volume.

## Où sont les choses

- `memoire/marque.md` — voix, lexique, chiffres officiels, interdits
- `memoire/style.md` — le style mesuré sur les pages du client (`style_maison.py`) :
  adresse, rythme, expressions ; sa section « Lecture » se remplit à la main
- `memoire/faits.md` — **la seule source des chiffres du site**, sourcés et datés
- `memoire/decisions.md` — décisions humaines, datées. **À lire avant de
  proposer une action** : ne pas reproposer ce qui a été refusé.
- `memoire/cartographie.csv` — chaque page, son mot-clé principal et son
  prompt principal, validés avec le client (`seo-cartographie`). Un mot-clé
  principal n'appartient qu'à une page.
- `memoire/entites.csv` et `memoire/triplets.csv` — les entités du site (QID
  Wikidata, sameAs) et les faits en triplets sujet — prédicat — objet, une
  seule valeur par fait sur tout le site (`seo-entites-triplets`)
- `memoire/apprentissages.md` — ce qui a marché et échoué sur ce site,
  alimenté par la mesure à J+28
- `journal/modifications.csv` — chaque modification et son effet mesuré
- `donnees/` — instantanés Search Console hebdomadaires
- `recherche/serp-*.md` — la SERP mesurée et le contenu du top, source de chaque brief
- `recherche/benchmarks/` — le benchmark « faire mieux » de chaque page
- `rapports/` — rapports mensuels, `a-valider.md`, et `runs/` (journal de
  chaque exécution de routine)

@memoire/marque.md
@memoire/faits.md
@memoire/decisions.md
@memoire/apprentissages.md
