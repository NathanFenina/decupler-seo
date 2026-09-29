---
name: geo-share-of-model
description: >
  Mesure et suit dans le temps la part de voix d'une marque dans les réponses
  des moteurs IA : batterie de prompts, relevé des citations par moteur,
  calcul du share of model, benchmark concurrentiel, suivi mensuel.
  Déclencher sur "share of model", "part de voix IA", "suivi des citations",
  "monitoring GEO", "mesurer ma visibilité IA", "est-ce que ChatGPT me cite",
  "baromètre IA", "tracking LLM".
---

# Share of Model — mesurer la part de voix dans les IA

Ce qui ne se mesure pas ne s'améliore pas. Le share of model est au GEO ce
que le suivi de positions est au SEO : l'indicateur qui dit si le travail
paye.

## 1. Construire la batterie de prompts

**20 à 40 questions**, celles que pose réellement un acheteur. Pas vos
mots-clés — des questions formulées comme on parle à un assistant.

Quatre familles, à équilibrer :

| Famille | Exemple | Ce que ça mesure |
|---------|---------|------------------|
| **Découverte** (30 %) | « Quels sont les meilleurs [catégorie] en France ? » | Êtes-vous dans l'ensemble de considération |
| **Comparaison** (25 %) | « [Concurrent] ou [vous], lequel choisir ? » | Comment êtes-vous positionné |
| **Problème** (25 %) | « Comment résoudre [problème que vous adressez] ? » | Êtes-vous cité comme solution |
| **Marque** (20 %) | « Que vaut [votre marque] ? » | Que disent les modèles de vous |

Les prompts de marque sont les plus révélateurs : ils montrent ce que les
modèles ont retenu de vous, y compris les erreurs. Il arrive qu'un modèle
attribue à une entreprise des services qu'elle ne rend pas.

Figez la liste. **Elle ne doit pas changer** d'un mois à l'autre, sinon la
comparaison n'a aucun sens. Ajoutez des prompts sans jamais en retirer.

## 2. Interroger les moteurs

| Moteur | Méthode |
|--------|---------|
| Perplexity | MCP ou API Sonar — automatisable |
| ChatGPT | API avec recherche activée, ou manuellement |
| Google AI Overviews | Recherche manuelle, ou DataForSEO (feature AIO) |
| Claude | Avec recherche web |
| Gemini | Manuellement |

Conditions à respecter pour que la mesure soit comparable :
- **Session neuve**, sans historique ni personnalisation
- **Même langue et même pays** à chaque relevé
- Une seule réponse par prompt — pas de relance, pas de reformulation
- Même jour du mois, autant que possible

## 3. Relever

Par prompt et par moteur :

| Champ | Valeur |
|-------|--------|
| Cité ? | oui / non |
| Rang de la mention | 1re source, 2e, 3e… |
| Type de mention | citation avec lien / mention sans lien / recommandation explicite |
| Formulation | le passage exact vous concernant |
| Autres sources citées | les domaines, dans l'ordre |
| Exactitude | ce qui est dit de vous est-il juste ? |

Ce dernier champ compte : une mention inexacte est un problème à corriger,
pas une victoire.

## 4. Calculer

**Taux de citation** = prompts où vous êtes cité ÷ prompts totaux
```
Vous : 11 / 40 = 27,5 %
```

**Share of model pondéré** — une 1re place vaut plus qu'une 4e :
```
poids : 1re = 1,0 · 2e = 0,6 · 3e = 0,4 · 4e et + = 0,2
share = Σ(poids de vos mentions) ÷ Σ(poids de toutes les mentions)
```

**Par moteur** — les écarts sont souvent énormes :
```
Perplexity     42 %  🟢
ChatGPT        22 %  🟠
AI Overviews    8 %  🔴
Claude         18 %  🟠
Gemini         12 %  🔴
─────────────────────
Global       27,5 %
```

Un score fort sur Perplexity et faible sur les AI Overviews est le profil
type d'un site bien structuré mais faible en autorité organique : Perplexity
cherche en temps réel, les AIO reprennent le top 10.

**Benchmark** — les mêmes calculs pour vos 3 concurrents, sur les mêmes
prompts. C'est le chiffre qui parle en réunion.

## 5. Interpréter

| Constat | Cause probable | Action |
|---------|---------------|--------|
| Cité nulle part | Entité inconnue des modèles | Autorité externe (`/seo reddit`, presse, Wikidata) |
| Cité par Perplexity seulement | Bon contenu, faible autorité | Travail hors site |
| Cité mais en dernier | Présent mais pas prioritaire | Données originales, réponses directes |
| Cité avec des erreurs | Sources anciennes ou contradictoires | Cohérence de l'entité, `llms.txt`, correction à la source |
| Concurrent cité partout | Il a une longueur d'avance sur l'autorité | Analyser d'où viennent ses mentions |

Quand un concurrent domine, la question utile est : **d'où sortent ses
citations ?** Cherchez son nom sur Reddit, dans la presse sectorielle, dans
les comparatifs. Vous obtiendrez sa recette.

## 6. Suivre dans le temps

Mensuel, même protocole, même liste de prompts.

```
        Jan   Fév   Mar   Avr
Vous    12%   18%   24%   27%   ↗
Conc.A  38%   36%   35%   33%   ↘
Conc.B  22%   24%   23%   25%   →
```

Ordres de grandeur réalistes : Perplexity bouge en 2-4 semaines après un
travail de structure. ChatGPT en recherche, 4-8 semaines. Les AI Overviews
suivent le ranking organique, donc plusieurs mois. Les connaissances
d'entraînement des modèles, elles, ne bougent qu'aux nouvelles versions.

Ne promettez jamais un résultat rapide sur les modèles d'entraînement.

## 7. Automatiser

Avec Perplexity en MCP, la mesure est scriptable :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/share_of_model.py" --prompts prompts.csv --moteurs perplexity
```

Et pour un suivi automatique :
```
/loop 30d /seo share-of-model
```

Consignez chaque relevé dans Notion (base « Objectifs & KPI ») ou dans
`historique-som.csv`. L'historique est la valeur du dispositif : un chiffre
isolé ne dit rien.

## Livrables

- `SHARE-OF-MODEL.md` — le rapport du mois
- `prompts.csv` — la batterie figée
- `releves-AAAA-MM.csv` — le détail prompt × moteur
- `historique-som.csv` — la série temporelle
- `CONCURRENCE-IA.md` — le benchmark et l'origine de leurs citations
