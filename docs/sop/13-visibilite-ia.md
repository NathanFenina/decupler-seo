<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 13 · Visibilité IA

**Skills** : `geo-share-of-model`, `geo-visibilite-ia`, `geo-citation-tracker` · **Commande** : `/seo geo <url>, ou /seo share-of-model`

**Objectif** : Savoir si ChatGPT, Gemini, Claude et Perplexity te citent, qui ils citent à ta place, et pourquoi.

**Quand** : Une fois par mois, le même jour, avec la même liste de prompts.

**Dis à Claude** : « Mesure ma part de voix dans ChatGPT et Gemini sur mes 30 prompts, et compare à mes 3 concurrents. »

## Étapes

1. La batterie : 20 à 40 questions d'acheteur, en quatre familles (découverte, comparaison, problème, marque). Les prompts principaux de ta cartographie en font partie.
2. L'interrogation (`share_of_model.py`) : ChatGPT et Gemini par API, avec la recherche web ; Claude et Perplexity si tu as leurs clés ; les AI Overviews par DataForSEO ou à la main.
3. Le relevé, prompt par prompt et moteur par moteur : cité ou non, à quel rang, avec ou sans lien, la phrase exacte, les sources, l'exactitude.
4. Le calcul : taux de citation, part de voix pondérée par le rang, par moteur, et le même calcul pour tes 3 concurrents.
5. Pour une page précise qui n'est jamais citée, `geo-citation-tracker` réécrit sa réponse directe (voir la partie GEO).

**MCP nécessaires** : Clés OpenAI et Gemini (les deux suffisent pour commencer). Anthropic et Perplexity en option. DataForSEO pour les AI Overviews.

**Livrable** : `donnees/ia-<mois>.csv` et le tableau de part de voix, par moteur et face aux concurrents.

## Pièges

- Mélanger les prompts qui nomment ta marque (ta réputation) et les autres (ta visibilité).
- Changer la liste d'un mois à l'autre : on ajoute, on ne retire jamais.
- Fêter une mention inexacte. C'est un problème à corriger.
