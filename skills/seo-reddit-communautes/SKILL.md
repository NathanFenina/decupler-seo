---
name: seo-reddit-communautes
description: >
  Identifie les discussions Reddit, Quora et forums à forte valeur pour la
  citation par les LLM et le trafic, les score, et rédige des réponses utiles
  et honnêtes prêtes à publier (jamais publiées automatiquement). Extrait
  aussi le vocabulaire réel de l'audience. Déclencher sur "Reddit", "Quora",
  "forums", "communautés", "où parler de mon produit", "questions de mon
  audience", "vocabulaire client", "être cité via Reddit", "discussions".
---

# Reddit et communautés — la source que les LLM adorent

Reddit est massivement présent dans les réponses des moteurs IA et dans le
bloc « Discussions et forums » de Google. Une réponse utile dans un bon
thread peut être citée pendant des années.

C'est aussi la meilleure source de vocabulaire client qui existe : les gens
y décrivent leur problème avec leurs mots, avant d'avoir été formatés par le
discours des vendeurs.

## Règle absolue

⚠️ **Aucune publication automatique. Jamais.**

Le dispositif trouve, score et rédige. **Vous publiez.** Ce n'est pas de la
prudence excessive : Reddit détecte et bannit les comptes automatisés, les
modérateurs sont vigilants, et le compte banni est le vôtre. Un ban de
r/[votre secteur] est définitif et vous ferme la porte pour de bon.

Le garde-fou `jamais_poster_communaute_sans_validation` n'est pas
désactivable.

## Étape 1 — Trouver les bons espaces

Via le MCP Reddit, ou en recherche : les subreddits où votre sujet est
discuté, leur taille, leur activité, leurs règles (elles varient beaucoup —
certains bannissent toute mention commerciale).

Ne visez pas seulement les gros subreddits. Un subreddit de 12 000 membres
très actifs sur votre niche vaut mieux qu'un généraliste d'un million de
membres où votre message se noie en dix minutes.

Ajoutez : les forums spécialisés de votre secteur (souvent anciens, bien
indexés, très cités), Quora, les groupes professionnels.

## Étape 2 — Scorer les threads

Sur 20 :

| Critère | Points | Ce qu'on regarde |
|---------|--------|------------------|
| **Trafic organique du thread** | /6 | Le thread ranke-t-il sur Google ? Un thread bien positionné apporte du trafic pendant des années |
| **Probabilité de citation LLM** | /6 | Question claire, réponses de qualité, sujet consulté. Les modèles reprennent ces threads |
| **Fenêtre d'intervention** | /5 | La question est-elle vraiment ouverte ? Ou déjà parfaitement répondue ? |
| **Accessibilité** | /3 | Les règles du sub autorisent-elles votre intervention ? Faut-il du karma ? |

**Seuil : 15/20.** En dessous, le temps est mieux investi ailleurs.

Ne visez pas que les threads récents. Un thread de 2022 qui ranke en
position 2 sur une requête à 3 000 recherches/mois est une opportunité
supérieure à un thread d'aujourd'hui qui disparaîtra dans 48 h.

## Étape 3 — Choisir l'angle

Cinq angles, à choisir selon le thread :

| Angle | Quand | Comment |
|-------|-------|---------|
| **Praticien** | On demande un retour d'expérience | Vous racontez ce que vous avez vu faire, chiffres à l'appui. Votre activité est mentionnée en signature, pas en argument |
| **Cheval de Troie** | On compare des solutions | Vous comparez honnêtement, **y compris quand un concurrent est meilleur**. C'est l'angle le plus crédible, et de loin |
| **Pédagogue** | On ne sait pas par où commencer | Un mini-tutoriel complet, gratuit, sans rien demander. Aucune mention commerciale |
| **Mention directe** | On demande explicitement des recommandations | Vous vous citez, en déclarant votre affiliation |
| **Question en retour** | La demande est mal posée | Vous aidez à qualifier le besoin. Souvent le plus utile |

L'angle « Cheval de Troie » mérite d'être expliqué : dire « pour votre cas,
[concurrent] sera mieux adapté que nous » construit plus de crédibilité que
dix arguments de vente. Et c'est cette réponse-là que les LLM reprennent,
parce qu'elle a l'air — et est — impartiale.

## Étape 4 — Rédiger

Ce qui fonctionne :
- **Répondre à la question**, complètement, avant toute autre chose
- Du concret : chiffres, cas, méthode
- Le ton de la communauté (Reddit est direct, informel, allergique au
  langage corporate)
- **Déclarer son affiliation** quand on se cite. Toujours. Un « je bosse
  dans le secteur, donc je suis biaisé, mais voilà ce que j'observe » est
  bien reçu ; une mention dissimulée découverte est fatale
- Reconnaître ce qu'on ne sait pas

Ce qui fait bannir :
- Un lien vers son site dans une première réponse
- Un ton promotionnel
- Une réponse qui parle de soi plutôt que de la question
- Le même message copié dans plusieurs threads
- Un compte neuf sans historique qui débarque pour se citer

**Le karma d'abord.** Un compte qui répond utilement pendant trois semaines
sans jamais se citer peut ensuite se citer. Un compte neuf qui se cite est
supprimé en une heure. Ce n'est pas une contrainte, c'est le prix d'entrée.

## Étape 5 — Le vocabulaire de l'audience

Indépendamment de toute intervention, extrayez la matière :

- Comment décrivent-ils le problème ? (souvent pas avec vos mots)
- Quelles objections reviennent ?
- Quelles solutions citent-ils ? Lesquelles rejettent-ils, et pourquoi ?
- Quelles questions restent sans bonne réponse ?

C'est la meilleure entrée de `/seo motscles` et de `/seo faq`. Une FAQ
construite depuis Reddit répond à de vraies questions ; une FAQ construite
depuis un outil répond à des requêtes.

Les questions **sans bonne réponse** sont des sujets d'article en or : la
demande est prouvée, l'offre est absente.

## Étape 6 — Suivre

Pour chaque intervention publiée : le thread, la date, l'angle, le score
obtenu, et surtout — **le thread est-il cité par les moteurs IA trois mois
plus tard ?**

C'est le seul indicateur qui compte pour le GEO. Rebranchez sur
`/seo share-of-model` pour le mesurer.

## Livrables

- `COMMUNAUTES.md` — les espaces pertinents, leurs règles, leur activité
- `threads.csv` — les opportunités scorées et triées
- `reponses/` — les réponses rédigées, une par thread, **à publier
  manuellement**
- `vocabulaire-audience.md` — les mots réels, les objections, les questions
  sans réponse
