---
name: seo-faq-paa
description: >
  Génère une FAQ qui vise les People Also Ask, les featured snippets et la
  citation par les LLM, avec le schema FAQPage correspondant. Puise dans les
  PAA réels, Reddit, les objections commerciales et les comparaisons.
  Déclencher sur "FAQ", "questions fréquentes", "People Also Ask", "PAA",
  "questions à ajouter", "schema FAQ", "featured snippet", "quelles questions
  se posent mes clients".
---

# FAQ — le format le plus rentable pour la citation

Une FAQ bien faite occupe trois terrains à la fois : les PAA de Google, les
featured snippets, et les réponses des LLM. C'est le meilleur rapport
effort/visibilité de la production de contenu.

Une FAQ mal faite — cinq questions inventées auxquelles personne ne pense —
n'occupe rien du tout.

## Les 4 sources de questions (dans cet ordre)

### 1. People Also Ask — les questions que Google a validées
Via DataForSEO ou en dépliant les PAA de la SERP cible. Ce sont des
questions réellement posées, avec un volume avéré.

Astuce : déplier un PAA en fait apparaître de nouveaux. Descendez sur deux
niveaux, vous obtenez 15-20 questions au lieu de 4.

### 2. Reddit, forums, avis clients — le vocabulaire réel
La façon dont les gens formulent leur problème est rarement celle des
outils SEO. « Est-ce que ça vaut le coup de » ne sortira jamais d'un outil
de mots-clés, et c'est pourtant une requête massive.

C'est aussi la meilleure source d'**objections** — celles qu'on ne vous dit
pas en face.

### 3. Les objections commerciales — les plus rentables
« C'est cher ? », « combien de temps ça prend ? », « et si ça ne marche
pas ? », « quelle différence avec X ? ». Ces questions ont peu de volume de
recherche et une valeur commerciale énorme : celui qui les pose est en fin
de parcours.

Demandez-les à l'équipe commerciale si elle existe. C'est cinq minutes de
conversation pour la meilleure matière du site.

### 4. Les comparaisons
« X ou Y ? », « alternative à Z », « faut-il faire soi-même ou déléguer ».
Fortes en intention, souvent citées par les LLM parce qu'elles appellent une
réponse structurée.

## Le format de réponse

C'est là que tout se joue.

**La première phrase répond.** Complètement, sans préambule, et de façon
autonome — elle doit fonctionner sortie du contexte de la page, parce que
c'est exactement ce qu'en fera un LLM ou un featured snippet.

```
❌ « C'est une excellente question, et la réponse dépend de plusieurs
   facteurs qu'il convient d'examiner. »

✅ « Un audit SEO complet coûte entre 2 000 et 8 000 € selon la taille du
   site. Comptez 2 000-3 500 € pour un site vitrine de moins de 50 pages,
   et 5 000-8 000 € pour un e-commerce de plusieurs milliers d'URL. »
```

Ensuite : 2-3 phrases de contexte, de nuance ou d'exemple.

**Longueur : 40 à 120 mots.** En dessous, la réponse est creuse. Au-dessus,
elle n'est plus extractible — et c'est le seuil qui compte pour les
featured snippets comme pour les LLM.

## Le volume

**10 à 20 questions** pour une page pilier, 5 à 8 pour un article.

Au-delà de 20, la valeur marginale s'effondre et la page devient une liste
sans hiérarchie. Mieux vaut 12 questions bien répondues que 30 expédiées.

## Marquer les questions prioritaires pour les LLM

Toutes les questions ne se valent pas pour la citation IA. Signalez celles
qui cumulent :

- Une réponse **factuelle et vérifiable** (un prix, une durée, une norme)
- Un **chiffre ou une donnée** dans la réponse
- Une formulation **autonome** de la question
- Une réponse que les concurrents traitent mal ou pas du tout

Ce sont celles-là qu'il faut soigner en priorité et placer en haut.

## Le schema FAQPage

⚠️ **Avertissement important.** Depuis août 2023, Google a restreint
l'affichage des rich results FAQ aux sites gouvernementaux et de santé
reconnus. Sur un site commercial, le schema FAQPage **n'affichera pas de
rich result**.

Faut-il le poser quand même ? Oui, et voici pourquoi : il reste lu par les
moteurs IA et les crawlers pour comprendre la structure question/réponse.
Mais annoncez la limite plutôt que de laisser croire à des étoiles dans la
SERP.

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [{
    "@type": "Question",
    "name": "Combien coûte un audit SEO complet ?",
    "acceptedAnswer": {
      "@type": "Answer",
      "text": "Un audit SEO complet coûte entre 2 000 et 8 000 € selon la taille du site…"
    }
  }]
}
```

Règles : le texte du schema doit correspondre **exactement** au texte visible
sur la page. Pas de HTML autre que les balises autorisées. Une seule
FAQPage par page.

## Le rendu HTML

Un composant autonome, sans dépendance, qui fonctionne partout (Elementor,
Webflow, WordPress, une page statique). Utilisez `<details>`/`<summary>` :
c'est accessible nativement, ça fonctionne sans JavaScript, et le contenu
reste dans le DOM donc lisible par les crawlers.

Ne cachez jamais les réponses derrière du JavaScript qui les charge à la
demande : ni Google ni les LLM ne les verront.

## Livrables

- `FAQ-<slug>.md` — les questions et réponses
- `faq-<slug>.html` — le composant prêt à coller
- `faq-<slug>.jsonld` — le schema
- La liste des questions marquées « prioritaire LLM »
