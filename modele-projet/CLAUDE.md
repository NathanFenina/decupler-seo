# {{NOM}} — mémoire du projet

Ce fichier est chargé au début de chaque session, y compris dans les
routines. Il dit **qui est ce projet** et **où se trouve le reste**. Gardez-le
court : le détail vit dans `memoire/`.

## Identité

- **Site** : {{DOMAINE}}
- **Marché** : {{PAYS}} · langues : {{LANGUES}}
- **CMS** : {{CMS}}
- **Activité** : {{ACTIVITE}}
- **Ce qui doit rapporter** : les pages listées dans `decupler-seo.config.yml` → `projet.pages_prioritaires`

## Comment travailler sur ce projet

1. **Toujours lire d'abord** : `decupler-seo.config.yml` (règles et seuils),
   puis `memoire/marque.md` (voix et interdits).
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

## Niveaux d'autonomie

| Niveau | Quoi | Règle |
|---|---|---|
| Automatique | title, meta, FAQ, schema, liens internes sur pages existantes | publié, sauvegardé, journalisé |
| Validation | nouvelles pages, réécriture de sections de pages qui rankent | brouillon CMS + ligne dans `rapports/a-valider.md` |
| Interdit | robots.txt, redirections, canonicals en prod, suppression, outreach, forums, fiche Google | proposition uniquement |

Plafond : **{{PAGES_MAX}} pages neuves par semaine**, qualité avant volume.

## Où sont les choses

- `memoire/marque.md` — voix, lexique, chiffres officiels, interdits
- `memoire/decisions.md` — décisions humaines, datées. **À lire avant de
  proposer une action** : ne pas reproposer ce qui a été refusé.
- `memoire/apprentissages.md` — ce qui a marché et échoué sur ce site,
  alimenté par la mesure à J+28
- `journal/modifications.csv` — chaque modification et son effet mesuré
- `donnees/` — instantanés Search Console hebdomadaires
- `rapports/` — rapports mensuels, `a-valider.md`, et `runs/` (journal de
  chaque exécution de routine)

@memoire/marque.md
@memoire/decisions.md
@memoire/apprentissages.md
