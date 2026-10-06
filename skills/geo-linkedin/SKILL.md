---
name: geo-linkedin
description: >
  Prépare des articles LinkedIn (page entreprise ou profil) qui servent la
  visibilité dans les moteurs IA et l'entité de la marque sans dupliquer le
  site : choix du format (article dérivé d'une page, réponse à un prompt,
  newsletter), angle différent de la page source, faits repris de
  memoire/faits.md, liens vers le site, passe d'humanisation, fiche de
  publication manuelle et post d'annonce, mesure par les prompts à J+30.
  Déclencher sur "article LinkedIn", "LinkedIn", "page entreprise",
  "newsletter LinkedIn", "republier sur LinkedIn", "Pulse", "recycler un
  article sur LinkedIn", "contenu LinkedIn pour le GEO".
---

# Articles LinkedIn — être cité, pas dupliqué

LinkedIn est l'un des domaines que les moteurs IA citent le plus. Une étude
Semrush publiée en mars 2026 (325 000 prompts, 89 000 URL LinkedIn citées) le
place 2e derrière Reddit : 11 % des citations en moyenne, dont 14 % dans
ChatGPT Search. Les **articles longs** y font 50 à 66 % des contenus cités,
surtout entre 500 et 2 000 mots. Perplexity cite surtout des pages
entreprises, ChatGPT et AI Mode surtout des membres.
(ppc.land/linkedin-ranks-2-in-ai-citations… ; BrightEdge, octobre 2025.)

Deux limites à connaître avant de commencer :
- **Aucune balise canonique** sur LinkedIn : un copier-coller d'une page du
  site, sur un domaine aussi puissant, peut passer devant l'original.
- **Aucune API** pour publier un article long ou une newsletter (ni LinkedIn,
  ni Unipile) : la rédaction s'automatise, la publication reste manuelle
  (5 minutes). Seul le post d'annonce peut partir par API.

## Profil ou page entreprise

| | Profil du dirigeant | Page entreprise |
|---|---|---|
| Portée organique | forte | faible : 1 à 2 % des abonnés (rapport van der Blom 2025) |
| Cité par | ChatGPT, AI Mode (membres : 59 %) | Perplexity (pages : 59 %) |
| Sert l'entité | la personne (Person, `sameAs`) | la marque (Organization, `sameAs`) |

Publier sur la page entreprise se défend pour l'entité et pour diversifier,
**à condition** de compenser la portée : le dirigeant partage chaque article
de la page depuis son profil, avec deux lignes à lui. Vérifier que l'URL de la
page entreprise figure dans le `sameAs` de l'Organization du site
(`seo-entites-triplets`, extension `seo-entite`).

## Les trois formats

1. **Article dérivé** d'une page du site : même sujet, **autre angle**
   (coulisses, cas concret, chiffres propres, erreur commise, opinion
   argumentée). 600 à 1 500 mots. Il ne reprend jamais plus d'un paragraphe de
   la page, cite la page et y renvoie 2 à 3 fois. Publié **après** l'indexation
   de la page source (`indexation.py suivre`).
2. **Réponse à un prompt** : une question où les IA devraient citer la marque
   et ne le font pas (cartographie : prompt principal sans citation ;
   `share_of_model.py`). Réponse directe dans les 3 premières lignes, définition
   nette, faits datés. Si le site a déjà une page sur ce mot-clé principal,
   c'est un article dérivé, pas une réponse : un mot-clé, une page.
3. **Newsletter de la page** : un des deux formats ci-dessus, envoyé aux
   abonnés (pages éligibles seulement). Même règles.

## Procédure

1. **Choisir** : une page du site qui rapporte (cartographie, pages
   prioritaires) ou un prompt sans citation. Deux articles par mois suffisent.
2. **Fiche** : `contenus/linkedin/<AAAA-MM-JJ>-<slug>.md`, avec en tête :
   ```yaml
   format: derive | reponse | newsletter
   support: page | profil
   page_source: https://…            # vide pour une réponse à un prompt
   prompt_vise: "…"                  # la question à laquelle l'article répond
   statut: brouillon | a-valider | publie
   url_linkedin: ""
   ```
3. **Rédiger** : `seo-redaction` (recherche, thèse, une donnée par
   paragraphe), dans `memoire/style.md`. Chaque chiffre vient de
   `memoire/faits.md` ; chaque fait a la même valeur que sur le site
   (`memoire/triplets.csv`). Titre : la question ou la promesse, pas le
   mot-clé du site.
4. **Contrôler** : `humanisation.py <fiche> --seuil 25` ;
   `controle_contenu.py` ; anti-duplication contre la page source (copie locale
   de la page, par `fetch_page.py`) :
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/similarite_lot.py" <fiche> <page-source> --strict`
   (code 1 au-delà de 4 phrases communes : réécrire l'angle).
5. **Préparer la publication** dans la fiche : titre, texte, 3 liens vers le
   site (URL complètes), brief d'image de couverture (1 920 × 1 080, sans texte
   illisible), et le **post d'annonce** (3 à 5 lignes, une question, le lien de
   l'article) pour la page et sa variante pour le profil du dirigeant.
6. **Publier (humain, 5 minutes)** : page entreprise → Créer → Écrire un
   article → coller, image, publier ; puis partager depuis le profil. Coller
   l'URL dans la fiche (`statut: publie`).
7. **Mesurer** : ajouter le prompt visé à la batterie de `share_of_model.py`
   et relever à J+30 si la marque est citée, et par quelle URL (le site ou
   l'article LinkedIn). La fiche garde la date de publication : c'est le
   point de départ de la mesure.

## Ce qu'on ne fait pas

- Copier un article du site sur LinkedIn, même « en attendant ».
- Piloter l'interface LinkedIn par un navigateur automatisé : aucune API ne
  couvre les articles, et le compte du dirigeant est en jeu.
- Publier un chiffre absent de `memoire/faits.md`, ou une preuve inventée.
- Promettre qu'un article sera cité : on le mesure.

## Livrables

`contenus/linkedin/<date>-<slug>.md` prêt à publier (article, liens, image,
posts d'annonce), et le prompt ajouté au suivi des citations.
