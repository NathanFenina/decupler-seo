---
name: geo-llms-txt
description: >
  Pose l'infrastructure d'accès des IA : robots.txt par robot (OAI-SearchBot,
  Claude-SearchBot, PerplexityBot, GPTBot…), llms.txt (priorité basse),
  identité de l'entité et Wikidata. Déclencher sur « crawlers IA », « GPTBot
  », « robots.txt IA », « llms.txt », « infra GEO ». Pas pour le balisage
  JSON-LD d'une page → seo-schema-jsonld.
---

# Infrastructure GEO — poser les fondations

Avant d'optimiser le contenu pour les moteurs IA, il faut qu'ils puissent
vous lire et savoir qui vous êtes. Ce skill traite ces deux préalables. Il
se fait une fois, il sert partout.


**Sans projet configuré, sans données ni accès** (dossier vide, pas de
Search Console, pas d'outil web) : ne vous arrêtez pas sur une question.
Livrez tout de suite ce qui ne dépend pas des données — la méthode appliquée
au cas, un exemple rempli, le livrable type avec des emplacements
`[à compléter : …]` — puis, en fin de réponse, la liste de ce qu'il faut
fournir pour la version chiffrée. Aucun chiffre inventé.

## 1. Les crawlers IA dans robots.txt

Décision à prendre consciemment, pas par réflexe.

| Agent | Qui | Effet du blocage |
|-------|-----|------------------|
| `GPTBot` | OpenAI, entraînement | Vous sortez des connaissances du modèle |
| `OAI-SearchBot` | OpenAI, recherche ChatGPT | **Vous disparaissez des réponses ChatGPT.** Ne bloquez pas |
| `ChatGPT-User` | Navigation à la demande d'un utilisateur | Une personne demande explicitement votre page. La bloquer n'a aucun sens |
| `PerplexityBot` | Index Perplexity | Vous sortez de Perplexity |
| `Perplexity-User` | Navigation à la demande | Idem |
| `ClaudeBot` | Anthropic | Sortie de l'index Claude |
| `Google-Extended` | Gemini et AI Overviews | **N'affecte pas le ranking Google classique** |
| `CCBot` | Common Crawl | Alimente de nombreux modèles en amont |
| `Bytespider` | ByteDance | Réputé agressif — blocage souvent justifié |

La distinction importante : **entraînement** et **recherche** sont deux
choses différentes. Vous pouvez refuser d'alimenter l'entraînement tout en
restant citable dans les réponses. C'est une position défendable.

**Recommandé pour la plupart des sites** — être visible dans les moteurs IA :
```
User-agent: OAI-SearchBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Perplexity-User
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: Google-Extended
Allow: /

Sitemap: https://exemple.com/sitemap.xml
```

**Si vous voulez refuser l'entraînement mais rester citable**, ajoutez :
```
User-agent: GPTBot
Disallow: /
User-agent: CCBot
Disallow: /
```

⚠️ Vérifiez ce que fait déjà votre robots.txt. Beaucoup de sites ont bloqué
`GPTBot` en 2023 et se plaignent aujourd'hui de ne pas être cités.

Note honnête : robots.txt est une convention, pas une barrière technique.
Les acteurs sérieux la respectent, les autres non.

## 2. Le fichier llms.txt

Convention émergente : un fichier markdown à la racine qui présente le site
aux modèles, comme robots.txt le fait pour les crawlers.

Statut à connaître (relevé d'octobre 2026) : ce n'est **pas un standard
officiel**. Google Search l'ignore explicitement (guide IA, mai 2026), et
sur 137 210 domaines, 97 % des fichiers llms.txt n'ont reçu aucune requête
(Ahrefs, juin 2026). **Priorité basse** : utile surtout pour une
documentation développeur ou des agents. S'il est publié, il coûte dix
minutes ; ne le vendez jamais comme un levier de visibilité. Les vrais
leviers d'accès sont robots.txt (section 1), le HTML initial et
l'indexation Bing.

`https://exemple.com/llms.txt` :

```markdown
# Nom de l'entreprise

> Une phrase qui dit ce que fait l'entreprise, pour qui, et ce qui la
> distingue. C'est la phrase que les modèles reprendront.

Fondée en [année] à [lieu]. [Chiffre marquant : clients, volume, ancienneté].

## Ce que nous faisons
- [Service 1] — [en quoi ça consiste, pour qui]
- [Service 2] — [idem]

## Pages de référence
- [Titre](https://exemple.com/page) : ce qu'on y trouve
- [Titre](https://exemple.com/page) : ce qu'on y trouve

## Nos données originales
- [Étude/baromètre](url) : méthodologie, échantillon, date

## Expertise
[Nom], [fonction], [X] ans dans [domaine]. [Preuve : publications,
interventions, certifications].

## Contact
[email] · [site] · [LinkedIn]

## Utilisation du contenu
Citation autorisée avec attribution et lien vers la source.
```

Écrivez-le **factuellement**. Un llms.txt en langage marketing (« leader
innovant du secteur ») n'apporte aucune information exploitable. Des faits,
des chiffres, des dates.

Les faits viennent du registre du projet (`memoire/triplets.csv`), **mot
pour mot** : la ligne de chaque page de référence est son triplet principal
(« Le bilan annuel coûte 1 200 € HT et dure trois semaines »), et une
section « Faits clés » reprend les triplets dont le sujet est la marque. Un
llms.txt qui donne une autre valeur que la page est une contradiction de
plus. Méthode et gabarit : `seo-entites-triplets`.

Variante : `llms-full.txt` avec le contenu complet des pages clés en
markdown, pour les modèles qui l'exploitent.

## 3. La définition de l'entité

C'est ce qui décide si un modèle sait **qui vous êtes**.

### Schema Organization, sur la home
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://exemple.com/#organization",
  "name": "Nom exact et unique",
  "alternateName": "Abréviation, si utilisée",
  "url": "https://exemple.com",
  "logo": "https://exemple.com/logo.png",
  "description": "La même phrase que dans llms.txt",
  "foundingDate": "2015",
  "founder": { "@type": "Person", "name": "Prénom Nom" },
  "address": { "@type": "PostalAddress", "…": "…" },
  "sameAs": [
    "https://www.linkedin.com/company/…",
    "https://fr.wikipedia.org/wiki/…",
    "https://www.wikidata.org/wiki/…",
    "https://github.com/…"
  ]
}
```

`sameAs` est la propriété la plus importante : c'est elle qui relie toutes
vos présences en une seule entité aux yeux des machines.

### Schema Person, sur les pages auteur
Avec `jobTitle`, `worksFor` (lié à l'`@id` de l'Organization), `knowsAbout`,
`sameAs`, `alumniOf`. Puis, sur chaque article, `author` pointant vers cet
`@id`.

Cette chaîne — article → auteur → entité → profils externes — est ce qui
permet à un modèle de dire « selon [Nom], expert en [domaine] chez
[Entreprise] ». Sans elle, au mieux il cite un domaine, au pire rien.

## 4. La cohérence cross-plateformes

Les modèles recoupent les sources. Une incohérence brouille l'entité.

Vérifiez que **partout** — site, LinkedIn, Google Business Profile,
annuaires, réseaux sociaux, mentions presse — on trouve :

- Le **même nom exact** (pas « Décupler », « Decupler » et « Décupler SAS »
  selon les endroits)
- La **même description** en une phrase
- La **même adresse et le même téléphone** (le NAP du SEO local vaut aussi
  pour le GEO)
- Le **même logo**
- Les **mêmes fondateurs et dirigeants**

C'est fastidieux et sans gloire. C'est aussi l'un des correctifs les plus
efficaces.

## 5. Wikidata

Une entrée Wikidata est un signal d'entité fort, et elle est accessible sans
les critères d'admissibilité de Wikipedia.

Conditions : l'entité doit être identifiable et référencée par des sources
externes. Un site seul ne suffit pas ; deux ou trois mentions presse, oui.

Renseignez : nom, description, type d'organisation, date de création, site
officiel, secteur, fondateurs, et les identifiants externes.

N'inventez rien : Wikidata est vérifié par une communauté, et une entrée
promotionnelle sera supprimée.

## Livrables

- `llms.txt` — prêt à déposer à la racine
- `robots-ia.txt` — le bloc à intégrer, avec la décision expliquée
- `organization.jsonld` et `person.jsonld`
- `COHERENCE-ENTITE.md` — l'audit des incohérences relevées, par plateforme
- `WIKIDATA.md` — les éléments à renseigner
