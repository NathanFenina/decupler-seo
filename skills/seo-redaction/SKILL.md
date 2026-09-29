---
name: seo-redaction
description: >
  Rédige un article ou une page complète à partir d'un brief, optimisé SEO et
  GEO, dans un style humain qui ne se détecte pas comme généré : recherche
  obligatoire avant écriture, une donnée par paragraphe, zéro chiffre
  inventé, règles anti-détection IA, trame des pages de service, politique
  d'occurrences du mot-clé, article GEO pour gagner un prompt IA, et
  relecture. Déclencher sur "rédige", "écris un article", "rédaction",
  "écris cette page", "produis le contenu", "article de blog", "rédige à
  partir du brief", "écris-moi un guide", "réécris cette page", "article
  GEO", "gagner un prompt".
---

# Rédaction — écrire quelque chose qui mérite d'exister

La question n'est pas « comment produire 1 500 mots optimisés ». C'est
« qu'est-ce que ce texte apporte que les dix premiers résultats n'apportent
pas ». Si vous n'avez pas de réponse, ne l'écrivez pas.

## Règle zéro — chercher avant d'écrire

Interdiction d'écrire depuis les seules connaissances du modèle.

Avant la première phrase :
1. Lire le brief, ou le produire (`/seo brief`)
2. Lire réellement le top 3 (Firecrawl) — pas le résumer de mémoire
3. Vérifier chaque chiffre à sa source, et le consigner dans
   `memoire/faits.md`
4. Récupérer le vocabulaire de l'audience (Reddit, avis, forums)
5. Lire `memoire/marque.md` : voix, vocabulaire validé, formules proscrites

**Aucun chiffre inventé. Jamais.** Un chiffre sans source ne s'écrit pas.
Si la donnée manque : soit on la trouve, soit on écrit la phrase sans elle.
« Selon une étude récente » sans référence est un aveu.

**Ordre de priorité en cas de conflit :**
- Une donnée de recherche récente et sourcée **remplace** un fait périmé du
  brief. Signalez la correction en tête du fichier.
- La voix de marque (`memoire/marque.md`) **prime sur le brief** : un brief
  ne change pas la manière dont la marque parle.

## Règle un — vérifier qu'il faut écrire (anti-cannibalisation)

Avant la première ligne, cherchez ce que le site dit déjà sur ce territoire :
pages existantes, articles du blog, titres Hn publiés, requêtes Search Console
qui y mènent déjà. Deux contenus sur la même intention se concurrencent et
**aucun des deux ne se positionne** — c'est l'incident le plus fréquent d'un
site qui publie beaucoup.

Puis tranchez, explicitement :

- **Intention différente** → écrivez, et posez un lien croisé entre les deux.
- **Même intention** → **n'écrivez pas un second contenu.** Recommandez
  d'enrichir l'existant pour couvrir aussi la nouvelle requête. C'est presque
  toujours la bonne réponse, même quand le calendrier prévoit un contenu neuf.
- **Intention voisine** (pilier et satellite) → écrivez le satellite avec un
  angle propre, un titre qui ne vise pas la requête du pilier, et un lien
  montant vers lui dès l'introduction.

Consignez l'arbitrage en tête du fichier produit : la prochaine session doit
comprendre pourquoi ce contenu existe à côté de l'autre.

## Règle deux — une thèse avant un plan

Un plan sans thèse produit un contenu « bateau » : exhaustif, exact, et
interchangeable avec les dix premiers résultats. Avant le plan, écrivez en
une phrase **ce que ce contenu soutient** et que les concurrents ne disent
pas — une position, une donnée, une méthode, un contre-pied argumenté.
Si vous ne trouvez pas de thèse, vous n'avez pas encore assez cherché.

## La structure qui fonctionne

### Le squelette — strict

- **Un seul H1.** Jamais de texte en gras utilisé comme titre : un titre est
  un Hn, sinon ni Google ni un LLM ne le lit comme tel.
- Pas de saut de niveau (H2 → H4 interdit).
- **5 à 8 H2**, 2 à 3 H3 au plus par H2. Au-delà, la page traite deux sujets.
- **H2 formulé en question**, suivi d'une **réponse directe de 1 à 3
  phrases** avant tout développement : c'est ce qu'extraient le featured
  snippet et les LLM.
- Paragraphes de **3 à 4 lignes au plus**.
- Encadrés « Conseil » et « Attention » pour ce que le lecteur ne doit pas
  manquer.

### L'ouverture — les 100 premiers mots
1. **Une situation concrète** du lecteur, avec le mot-clé dans la première
   phrase.
2. **La réponse directe**, en 40-60 mots, dans ces 100 mots. Elle sert au
   lecteur pressé, au featured snippet et aux LLM à la fois.
3. Ce que le contenu couvre, pour qui, et ce qui le distingue : une donnée
   propre, une expérience de terrain, une méthode.

Jamais : une définition de dictionnaire en guise d'intro, une introduction
théorique, « Dans un monde où le digital prend une place croissante… ».
Entrez dans le sujet à la première phrase.

### Le corps
- Un H2 = une question que le lecteur se pose vraiment
- **Un paragraphe = une idée + une preuve.** Donnée, exemple, chiffre,
  cas concret ou méthode. Un paragraphe sans preuve se supprime.
- **Tableau obligatoire** dès que l'information est comparative ou chiffrée
  (comparaison, avantages / inconvénients, tarifs, délais, seuils). Un
  tableau est lu, extrait et cité ; la même information en prose ne l'est
  pas.
- **Listes : 6 puces au plus**, une ligne chacune, qui commencent toutes par
  un infinitif ou toutes par un nom.
- Répondez au « comment », pas seulement au « quoi ». La profondeur
  technique est ce qui vous distingue du contenu générique.

### La conclusion
Pas de résumé moralisateur. Une conclusion utile rappelle les points clés en
quelques lignes, donne la prochaine action concrète, et porte le CTA (avec
le mot-clé) et un lien interne vers l'étape suivante.

## Page de service — la trame narrative

**Le problème métier avant la solution.** Le visiteur d'une page de service
cherche d'abord à être compris ; l'offre ne l'intéresse qu'ensuite.

1. **Contexte du marché** : ce qui change, ce qui presse, chiffré.
2. **La douleur, en « vous »** : la situation du lecteur, dans ses mots.
3. **La définition** : « X est un… qui… » — une phrase autonome, citable.
4. **Le corps** : méthode, étapes, livrables, délais, tarifs si publics.
5. **La preuve chiffrée** : résultats mesurés, sourcés. Un témoignage
   **seulement s'il existe réellement** — jamais inventé, jamais reformulé
   au point de changer son sens.
6. **Le positionnement** : pourquoi ce prestataire plutôt qu'un autre, sans
   superlatif invérifiable.
7. **FAQ**, puis **CTA**.

Jamais d'ouverture en « [Marque] vous propose… » : la page parle du lecteur
avant de parler d'elle.

## Le test anti-remplissage — sur chaque paragraphe

> « Est-ce qu'un lecteur qui pratique le sujet apprend quelque chose ici, ou
> est-ce qu'il lit ce qu'il sait déjà ? »

Si c'est la seconde réponse : supprimez ou creusez. Un paragraphe qui
pourrait figurer tel quel sur le site d'un concurrent ne défend pas la
marque, il la banalise.

Obligatoires : une position assumée par section ; le *comment*, pas seulement
le *quoi* ; la contrepartie de chaque recommandation (ce qu'elle coûte, quand
elle ne s'applique pas) ; et au moins une chose que le lecteur **ne fera plus**
après avoir lu. Le marqueur le plus fiable d'un bon contenu : il dit aussi
**quand s'abstenir**.

## Deux pages d'un même gabarit ne se lisent jamais pareil

Un gabarit partagé est un acquis (une correction se fait une fois). Mais si
chaque page remplit les mêmes emplacements dans le même ordre, avec les mêmes
trois chiffres, le lecteur qui en ouvre deux voit un formulaire rempli deux
fois — et Google aussi. Chaque page porte au moins **un bloc qui n'existe que
chez elle**, d'un type que ses voisines n'emploient pas : grille de
diagnostic, tableau de livrables, aide à la décision, référentiel de formats,
routeur « votre situation → par où commencer ».

## Le style — ne pas écrire comme une IA

### Les 10 règles anti-détection

1. **Varier la structure des phrases** : pas trois phrases sujet-verbe-
   complément d'affilée.
2. **Injecter du vécu** : une micro-anecdote, un cas daté, une erreur
   constatée sur le terrain.
3. **Alterner très court et long** : une phrase de 5 à 8 mots après une
   phrase développée. Ça casse le rythme mécanique.
4. **Bannir les tournures de notice** : « elle permet de… », « cette méthode
   propose de… », « il est important de… ». Dites ce que la chose fait.
5. **Des tournures orales, dosées** : « Concrètement ? », « Et c'est là que
   ça coince. » Une ou deux par section, pas plus.
6. **Des mots simples pour les émotions** : « inquiet », « soulagé », pas
   « en proie à une appréhension ».
7. **Remplacer l'énumération didactique** par une image ou un exemple
   quand trois puces abstraites disent moins qu'un cas concret.
8. **Poser des questions ouvertes au lecteur** : « Combien de devis avez-vous
   comparés ? »
9. **Accepter la phrase incomplète** : « Résultat : deux semaines perdues. »
10. **La reformulation en écho** : reprendre une idée clé avec d'autres
    mots (« Autrement dit : … ») pour l'ancrer.

Les scores des détecteurs d'IA sont **indicatifs seulement** : ces outils
se trompent dans les deux sens. On vise un texte qu'un lecteur du métier
signerait, pas un score.

### Interdits éditoriaux

| ❌ À proscrire | ✅ À la place |
|----------------|---------------|
| Conditionnel de distance : « cela pourrait permettre » | L'indicatif : « cela permet », ou la condition explicite |
| Tournure impersonnelle : « on peut considérer que » | Une position assumée, avec sa raison |
| « Il est important de noter que » | Notez-le, sans l'annoncer |
| Introduction théorique, définition de dictionnaire | Une situation concrète du lecteur |
| « Dans le monde d'aujourd'hui » | Entrez dans le sujet |
| « Que vous soyez X ou Y, … » | Parlez à une personne précise |
| « [Marque] vous propose… » en ouverture | Le problème du lecteur d'abord |
| Conclusion moralisatrice, « En conclusion, il apparaît que » | La prochaine action |
| Anglicisme gratuit (« process », « insights ») | Le mot français, sauf terme métier établi |
| « plonger », « exploiter tout le potentiel », « révolutionner » | Des verbes ordinaires |
| Trois adjectifs par nom | Un, ou aucun |
| Une liste à puces toutes les 200 mots | Des listes quand il y a une liste |

`controle_contenu.py` bloque déjà les tics les plus fréquents ; les
expressions propres au projet vont dans `regles.interdits`.

Les marqueurs d'humain, à cultiver : une opinion assumée avec sa raison ;
un exemple précis, daté, chiffré, vécu ; la mention de ce qui **ne marche
pas** ou de ce qu'on ne sait pas ; un contre-argument honnête. Ce dernier
point est le plus efficace : « cette méthode ne convient pas si vous êtes
dans ce cas » rend un texte immédiatement plus crédible.

## Optimisation SEO — la politique d'occurrences

Le mot-clé se pilote **par la densité**, pas par un compte fixe : un compte
fixe sur-optimise un texte court et sous-optimise un long.

- **Densité cible : 1,5 à 2,5 %** du mot-clé principal (au moins 1 % si le
  texte est court).
- **Comptez séparément** la correspondance exacte, la partielle (mots
  séparés ou dans le désordre) et les variantes ; la densité se lit sur
  l'ensemble, l'exacte ne porte pas tout.
- **Emplacements obligatoires** : H1, première phrase, au moins un H2,
  conclusion, **CTA final**, et un `alt` d'image.
- **15 à 20 occurrences exactes** seulement si la longueur le permet
  (environ 1 000 mots et plus) : c'est alors la même densité, pas une règle
  de plus.
- **Plafond** : `regles.densite_max_pct` du projet (3 % par défaut), jamais
  au-delà de **3,5 %** — c'est de la sur-optimisation, visible par le
  lecteur comme par Google.
- Si le client a validé un minimum, il est dans
  `regles.mot_cle_occurrences_min` (`decupler-seo.config.yml`) et s'applique
  — sous le plafond. Si le texte est trop court pour l'atteindre sans le
  dépasser, allongez avec un angle utile (voir « Longueur ») ou signalez-le.

Mesure : `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/onpage_score.py" page.html "<mot-clé>"`
donne occurrences et densité.

Le reste : variantes et synonymes répartis naturellement, entités du brief
mentionnées, ancres de liens internes descriptives, `alt` qui décrit
vraiment l'image.

## Optimisation GEO — être citable

Un LLM cite ce qu'il peut extraire proprement :

- **Réponse directe** en haut, autonome hors contexte
- **Définitions explicites** : « Le X est un Y qui permet de Z. » Une
  phrase, complète, sans référence au paragraphe précédent
- **Données chiffrées sourcées** : les LLM privilégient le vérifiable
- **Structure lisible par machine** : titres explicites, listes, tableaux
- **FAQ en fin d'article** avec des réponses de 40-60 mots
- **Cohérence de l'entité** : nommez votre marque, votre auteur, vos
  produits de la même façon partout, sur tout le site

## Article GEO — gagner un prompt IA

Un contenu écrit pour qu'un moteur IA cite la marque sur un prompt précis,
là où il cite aujourd'hui des concurrents.

**Entrées, avant d'écrire :**
- le **prompt suivi**, tiré des relevés de `geo-share-of-model`
  (`share_of_model.py`, fichier `releves-ia-<mois>.csv`) ;
- la **visibilité actuelle** sur ce prompt : citée, nommée, absente, et par
  quels moteurs ;
- les **marques concurrentes citées** et les sources que les moteurs
  mobilisent ;
- les **sujets** que couvrent les réponses actuelles, et ceux qu'elles
  ratent.

**Règles :**
- La marque parle **à la première personne du pluriel** (« nous ») et
  apparaît dans le H1, l'introduction, chaque section et la conclusion.
- Des **paragraphes autonomes et citables** qui nomment la marque : chacun
  doit pouvoir être extrait seul et rester vrai.
- **INTERDIT : un classement de type « top 5 »** où les concurrents sont la
  réponse. On offre alors au moteur la liste qu'il cite déjà.
- Chaque affirmation sur la marque est vérifiable (`memoire/faits.md`).

Mesure : relancer le relevé du prompt à J+28 et journaliser l'écart.

## E-E-A-T — le prouver, pas l'affirmer

- **Expérience** : « sur les 40 audits que nous avons menés en 2025 »,
  pas « nous avons une grande expérience »
- **Expertise** : la précision du vocabulaire, les nuances, les cas limites
- **Autorité** : sources externes reconnues citées, données propres
- **Confiance** : auteur identifié avec ses credentials, date de mise à
  jour, sources vérifiables, conflits d'intérêts déclarés

## Longueur

**Le nombre de mots n'est pas un facteur de classement.** Écrivez ce que le
sujet exige ; le top 3 donne un ordre de grandeur, pas un objectif. Un
article de 900 mots qui répond complètement bat un article de 2 500 mots
dont 1 600 sont du remplissage.

- N'allongez qu'avec des **angles à valeur réelle** : réglementation, aides
  et financements, spécificités locales, cas particuliers.
- S'il faut raccourcir, coupez **le milieu** : jamais la FAQ, jamais la
  conclusion ni le CTA.
- **Réécriture d'un existant** : +15 % de longueur au plus ; tout H2 ajouté
  fait au moins 250 mots ; **100 % du plan d'audit** (brief section 9) est
  intégré — une décision non appliquée se signale, elle ne s'oublie pas.

## Relecture avant remise

- [ ] Chaque chiffre a sa source, reliée dans `memoire/faits.md`
- [ ] Aucune réalisation sur-attribuée : ce qui a été fait par d'autres, ou
      en partie, est dit comme tel
- [ ] Le vocabulaire est celui validé par le client (`memoire/marque.md`)
- [ ] Les citations sont entières, jamais coupées pour servir le propos
- [ ] Aucun terme déclaré « inexistant » ou « faux » sans vérification
- [ ] Aucun lien interne existant supprimé : on en ajoute
- [ ] Chaque paragraphe apporte une idée nouvelle
- [ ] La réponse directe fonctionne sortie de son contexte
- [ ] Aucune formule des interdits, `controle_contenu.py` passe
- [ ] Densité du mot-clé dans la cible, sous le plafond
- [ ] Les liens internes du brief sont posés
- [ ] Un lecteur du métier apprendrait quelque chose
- [ ] Vous seriez à l'aise de le signer de votre nom

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/controle_contenu.py" contenus/<slug>.md
```

## Livrables

- `article-<slug>.md` — le texte
- `article-<slug>.html` — si destiné à un CMS (`/seo page`)
- `sources.md` — chaque affirmation chiffrée et son lien
- Le schema JSON-LD correspondant (`/seo schema`)

Enchaînez : `/seo publish` pour la mise en ligne en brouillon.
