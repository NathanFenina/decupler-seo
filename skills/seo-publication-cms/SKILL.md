---
name: seo-publication-cms
description: >
  Publie et met à jour du contenu sur WordPress, Webflow ou un CMS générique
  via API REST : création d'articles et de pages, mise à jour de balises,
  catégories, images, schema, avec sauvegarde préalable et publication en
  brouillon par défaut. Déclencher sur "publie", "mets en ligne", "envoie sur
  WordPress", "Webflow", "publier l'article", "mettre à jour la page",
  "pousser le contenu", "créer le brouillon".
---

# Publication — mettre en ligne sans casser

C'est l'étape où une erreur coûte le plus cher, parce qu'elle est visible
publiquement et parfois irréversible.

## Étape 0 — Le garde-fou, systématiquement

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/guard.py" --action publier --cible <url>
```

| Verdict | Comportement |
|---------|--------------|
| `AUTORISE` | On publie, selon le statut par défaut de la config |
| `DEMANDE_VALIDATION` | On présente ce qui va être écrit, on attend le oui |
| `BLOQUE` | On produit le fichier en local et on explique comment le poser |

**Le statut par défaut est `draft`**, y compris en mode autonomous. Ce n'est
pas une limitation : Claude fait tout le travail, vous gardez le dernier
clic. Changez-le dans la config si vous voulez publier directement.

## Étape 1 — Sauvegarder avant d'écrire

Sur toute mise à jour d'un contenu existant :

```
.seo-decupler/backups/AAAA-MM-JJ-HHMM-<slug>.json
```

Contenu de la sauvegarde : titre, contenu, extrait, balises SEO, catégories,
statut, date. Tout ce qui permet de revenir en arrière.

Le garde-fou `toujours_sauvegarder_avant_ecriture` est activé par défaut.
Ne le désactivez pas.

## WordPress

Via le MCP `wordpress` ou l'API REST directement.

**Authentification** : un **mot de passe d'application** (Utilisateurs →
Profil → Mots de passe d'application), jamais le mot de passe de connexion.

**Créer un article**
```
POST /wp-json/wp/v2/posts
{
  "title": "…", "content": "…", "excerpt": "…",
  "status": "draft", "categories": [12], "tags": [4, 9],
  "slug": "url-propre", "featured_media": 340
}
```

**Mettre à jour** — `POST /wp-json/wp/v2/posts/<id>` avec les seuls champs
modifiés. N'envoyez jamais le contenu complet si vous ne changez que le
titre : vous écraseriez des modifications faites entre-temps.

**Les balises SEO** dépendent du plugin. Elles ne sont pas dans le champ
`content` :

| Plugin | Champ meta |
|--------|-----------|
| Yoast | `_yoast_wpseo_title`, `_yoast_wpseo_metadesc` |
| Rank Math | `rank_math_title`, `rank_math_description` |
| SEOPress | `_seopress_titles_title`, `_seopress_titles_desc` |

Ces champs doivent être exposés dans l'API REST — ce n'est pas toujours le
cas par défaut. Si l'écriture échoue silencieusement, c'est presque toujours
ça. Détectez le plugin actif avant d'écrire.

**Les images** : les téléverser dans la médiathèque
(`POST /wp-json/wp/v2/media`) puis référencer l'ID. Ne référencez jamais une
image hébergée ailleurs.

**Attention au formatage.** WordPress applique `wpautop` et des filtres de
contenu qui peuvent supprimer certaines balises. Testez le rendu après
publication, surtout pour les tableaux et les `<details>`.

## Webflow

**Authentification** : jeton d'API (Site settings → Apps & integrations).

Le modèle est différent : le contenu vit dans des **CMS Collections** dont
les champs sont définis à l'avance. Vous ne pouvez écrire que dans les
champs existants.

1. Lister les collections, récupérer le schéma des champs
2. Créer l'item avec les `slug` de champs exacts
3. Publier — la création ne publie pas, c'est une étape séparée

Contraintes à connaître : le champ Rich Text n'accepte pas n'importe quel
HTML ; les embeds sont limités à 50 000 caractères ; les champs de référence
attendent des IDs.

## CMS générique

Si ni l'un ni l'autre, l'adaptateur générique produit :

- Le HTML complet (`/seo page`)
- Le markdown
- Un JSON structuré avec tous les champs
- Des instructions de pose : où coller, dans quel ordre, quoi vérifier

C'est le mode de repli, et il fonctionne partout.

## Étape 2 — Vérifier après publication

Ne considérez jamais une publication comme réussie parce que l'API a
renvoyé 200.

- [ ] L'URL répond en 200
- [ ] Le contenu s'affiche entièrement (comparez le nombre de mots)
- [ ] Les balises title et meta sont bien celles envoyées
- [ ] Le schema JSON-LD est présent et valide
- [ ] Les images s'affichent
- [ ] Le rendu mobile tient (Chrome DevTools)
- [ ] Les liens internes fonctionnent
- [ ] Pas de doublon de schema (plugin + votre bloc)

Sur une mise à jour de page existante et positionnée, ajoutez : le contenu
d'origine n'a pas été perdu, l'URL n'a pas changé, la canonical est intacte.

## Étape 3 — Après la mise en ligne

1. Soumettre l'URL dans Search Console (inspection → demander l'indexation)
2. Poser les liens internes entrants prévus dans le brief — **c'est l'étape
   la plus souvent oubliée**, et c'est celle qui décide de la vitesse
   d'indexation
3. Consigner la publication dans le suivi (Notion, base « Briefs & Contenus »)
4. Noter la date pour la mesure à J+30

## Revenir en arrière

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/cms_restore.py" .seo-decupler/backups/<fichier>.json
```

Restaure l'état sauvegardé. Fonctionne pour WordPress et Webflow.

## Livrables

- L'URL publiée
- `PUBLICATION-<slug>.md` — ce qui a été envoyé, où, quand, avec quel statut
- La sauvegarde de l'état antérieur
- La liste des vérifications, avec leur résultat
