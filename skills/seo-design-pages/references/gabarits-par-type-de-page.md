# Gabarits par type de page

Chaque gabarit est une suite de sections dans un ordre qui a fait ses preuves.
La colonne **CTA** indique où l'action principale apparaît ; la colonne
**Composant** renvoie aux fichiers de `${CLAUDE_PLUGIN_ROOT}/templates/`.

Règles communes :

- **Bandes alternées** : jamais deux fonds identiques d'affilée, sinon deux
  sections se lisent comme une seule. Une bande sombre au plus toutes les
  trois sections, sinon la page devient lourde.
- **H2 formulés comme des questions** quand la section répond à une question
  réelle (« Combien coûte… ? », « Comment se déroule… ? ») : les moteurs
  apparient la question posée avec l'intertitre. Une étiquette marketing
  (« Notre méthodologie ») ne s'apparie avec rien.
- **Une section propre à la page.** Quand plusieurs pages partagent un
  gabarit (services, villes), chacune porte au moins une section qu'aucune
  autre n'a — une aide à la décision, un référentiel, une liste de livrables.
  C'est elle qui casse la symétrie du lot et porte la substance.
- **Aucun bloc « À découvrir aussi » en pied de page.** Les liens internes
  vont dans le fil du texte, sur des ancres naturelles (voir
  `seo-maillage-interne`). Un bloc de liens en pied est ignoré des lecteurs.

---

## 1. Page service

Colonne vertébrale : **problème → preuve → offre → action**.

| # | Section | Contenu | CTA | Composant |
|---|---|---|---|---|
| 1 | **Hero** | H1 avec le mot-clé, promesse en une phrase, une preuve chiffrée, action principale, ligne de réassurance | oui | `hero.html` |
| 2 | **Bande de preuves** | 3-4 chiffres sourcés : années, interventions, délai moyen, note avec sa source | — | `encadre-chiffres-cles.html` |
| 3 | **Le problème** | H2 en question, la situation du lecteur dans ses mots | — | — |
| 4 | **Ce que la prestation change** | 3 blocs, un bénéfice concret chacun | oui | cartes |
| 5 | **Le visuel qui prouve** | photo de chantier, capture, schéma — légendé | — | `figure-legendee.html` |
| 6 | **La méthode** | 4 à 6 étapes numérotées ; pour chacune : qui agit, combien de temps, quel livrable | — | liste d'étapes |
| 7 | **Inclus / non inclus** ou **tarifs** | tableau honnête, fourchettes et ce qui les fait varier | — | `tableau-comparatif.html` |
| 8 | **Bannière confiance** | qui intervient : photo réelle, parcours, preuves vérifiables | oui | `banniere-eeat.html` |
| 9 | **Témoignages** | 3 avis réels, attribués, sourcés — si vous en avez | — | `banniere-temoignages.html` |
| 10 | **Limites** | ce que vous ne promettez pas, dès qu'il est question de résultat, délai ou budget | — | `encadre.html` (limites) |
| 11 | **FAQ** | 6 à 8 questions d'objection commerciale | — | `composant-faq.html` |
| 12 | **Bande CTA finale** | la promesse reformulée, ce qui se passe après le clic | oui | `banniere-contact.html` |

L'encadré **limites** n'est pas de la prudence juridique seulement : les
moteurs génératifs reprennent volontiers les pages qui bornent leurs
promesses, et écartent celles qui promettent trop.

**La matière qui différencie** : trois blocs portent tout le poids d'une
page service ou locale, et aucun ne se recopie d'une page à l'autre :
- **les livrables avec leur cadence** : ce qui arrive, et quand (six items,
  chacun avec sa fréquence) ; vérifiable, donc crédible ;
- **ce qu'on fait / ce qu'on ne fait pas**, en deux colonnes : au moins un
  refus **qui coûte** (pas d'engagement de douze mois, un seul client par
  métier et par zone). Un refus sans coût se lit comme une posture ;
- **le parti pris signé** : deux ou trois paragraphes à la première
  personne, une anecdote vraie, une position qui fait perdre des contrats.
  C'est le seul endroit où quelqu'un parle ; une fois par page, dans une
  bande à part.

---

## 2. Article / guide

Colonne vertébrale : **réponse → développement → synthèse → action**. Le
lecteur est venu chercher une réponse ; il ne clique que s'il l'a eue.

| # | Section | Contenu | CTA | Composant |
|---|---|---|---|---|
| 1 | **En-tête** | fil d'Ariane, H1, chapô qui **répond** en 2 à 4 phrases (mot-clé dans la première), auteur et date de mise à jour | — | `bloc-auteur.html` (version courte) |
| 2 | **Image de couverture** | seulement si elle informe ; sinon l'image à la une sert au partage et n'apparaît pas dans le corps | — | `figure-legendee.html` |
| 3 | **En bref** | 3 à 5 points, chacun autonome et citable | — | `encadre-en-bref.html` |
| 4 | **Sommaire** | dès 5 H2 ou 1 500 mots | — | `sommaire.html` |
| 5 | **Sections H2** | 6 à 12, en questions ; un élément riche environ tous les deux paragraphes (tableau, liste, encadré, figure) | — | `encadre.html`, `tableau-comparatif.html` |
| 6 | **Figure de corps** | au moins une, placée dans la section qu'elle explique | — | `figure-legendee.html` |
| 7 | **CTA contextuel** | au milieu, juste après la section où le besoin apparaît | oui | `bloc-cta-inline.html` |
| 8 | **Ce qu'il faut retenir** | 5-6 puces, reprise de la thèse | — | `encadre-en-bref.html` |
| 9 | **FAQ** | 5 à 10 questions, réponses autonomes de 2 à 4 phrases | — | `composant-faq.html` |
| 10 | **Sources** | liens vers les sources citées, date de vérification | — | liste |
| 11 | **Bloc auteur** | qui a écrit, pourquoi il est légitime, lien vers sa page | — | `bloc-auteur.html` |
| 12 | **CTA de fin** | l'action principale, reformulée pour ce sujet | oui | `banniere-contact.html` ou `bloc-cta-inline.html` |

**Barre latérale collante** (ordinateur uniquement, au-delà de 900 px) :
une carte CTA qui suit la lecture. En `position: sticky` natif — une version
JavaScript relâche la carte trop tôt, avant la FAQ. En dessous de 900 px, la
barre latérale disparaît et le CTA contextuel prend le relais : une carte
collante sur mobile masque le texte.

**Rythme.** Un article tout en prose ne se lit pas ; un article tout en
tableaux ne se cite pas. Visez un élément riche pour deux paragraphes.

---

## 3. Page locale (service + ville)

Même colonne que la page service, avec une exigence de plus : **ce qui est
propre à la ville est rédigé ville par ville**. Un premier jet mécanique
produit couramment 30 à 40 % de phrases identiques entre deux villes, ce qui
fait échouer tout le lot (voir `seo-programmatique`). Mesure avant publication :
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/similarite_lot.py" <dossier-du-lot> --strict`.

| # | Section | Contenu | CTA |
|---|---|---|---|
| 1 | **Hero** | H1 « [service] à [ville] », sous-titre, bande de confiance de 3-4 chiffres | oui |
| 2 | **Contexte local** | H2 « Pourquoi [service] à [ville] ? », 2-3 paragraphes propres à la ville | — |
| 3 | **Bénéfices** | formulés avec le tissu local (habitat, secteurs, contraintes) | — |
| 4 | **Méthode** | étapes, avec le piège local éventuel | — |
| 5 | **Comparatif** | prestataire local / national / interne, par exemple | — |
| 6 | **Zone d'intervention** | codes postaux en toutes lettres, 8 à 12 communes limitrophes en grille, photo réelle de la ville ou d'un chantier | oui |
| 7 | **Budget** | fourchettes et ce qui les fait varier localement | oui |
| 8 | **FAQ** | dont au moins 3 questions spécifiquement locales | — |
| 9 | **Bannière confiance** | l'équipe qui intervient réellement dans la zone | oui |
| 10 | **Bande CTA finale** | | oui |

**Visuels.** Faites tourner les visuels secondaires entre les villes : deux
villes voisines ne doivent pas se ressembler au premier coup d'œil, ni dans
la page ni dans les partages.

---

## 4. Landing (campagne, produit, offre)

Colonne vertébrale : **promesse → démonstration → preuve → action**. Une
landing ne cherche pas à tout expliquer ; elle lève les objections dans
l'ordre où elles arrivent.

| # | Section | Contenu | CTA |
|---|---|---|---|
| 1 | **Hero** | H1 = le bénéfice, sous-titre, action principale + action secondaire (voir la démo), ligne de réassurance | oui |
| 2 | **Démonstration** | vidéo courte, capture annotée ou animation qui montre le produit tourner | oui |
| 3 | **Preuves** | logos clients **réels et autorisés**, chiffres sourcés | — |
| 4 | **Le problème et son coût** | ce que coûte le statu quo, chiffré et sourcé | — |
| 5 | **Bénéfices** | 3 à 6, un par carte, pas de liste de fonctionnalités | — |
| 6 | **Comparaison** | avant / après, ou votre approche face aux alternatives | — |
| 7 | **Déroulé** | 3 à 4 étapes, de l'inscription au premier résultat | oui |
| 8 | **Témoignages** | réels et attribués | — |
| 9 | **Tarifs** | s'ils sont publics | oui |
| 10 | **FAQ** | objections | — |
| 11 | **CTA final** | | oui |

Une landing de campagne payante peut être en `noindex` ; une landing qui vise
une requête organique suit les mêmes règles de contenu qu'une page service
(réponse directe, H2 en questions, FAQ).

---

## 5. Comparatif (« X vs Y », « alternative à X », « meilleur… »)

Colonne vertébrale : **verdict → tableau → critères → méthode**. Celui qui
compare a déjà lu les pages concurrentes : il veut le verdict tout de suite.
Le cadre juridique et le ton : `seo-comparatifs`.

| # | Section | Contenu | CTA |
|---|---|---|---|
| 1 | **Hero** | H1, verdict en deux phrases : pour qui chaque option est le meilleur choix | — |
| 2 | **Tableau de synthèse** | dans le premier ou deuxième écran, option recommandée marquée par un libellé (pas seulement une couleur) | — |
| 3 | **Critère par critère** | un H2 par critère décisif, avec les preuves | — |
| 4 | **Quand choisir l'autre** | les cas où le concurrent convient mieux | — |
| 5 | **Méthodologie** | ce qui a été testé, comment, à quelle date | — |
| 6 | **FAQ** | | — |
| 7 | **CTA** | à faible engagement : essai, démo, devis | oui |

Deux CTA suffisent (après le tableau, en fin de page). Un comparatif qui
pousse un bouton à chaque section se lit comme une publicité et perd la
confiance qu'il prétend construire.

---

## 6. Outil ou calculateur

Colonne vertébrale : **l'outil → le résultat → la méthode**. Le visiteur est
venu utiliser l'outil ; tout ce qui le retarde est de trop.

| # | Section | Contenu | CTA |
|---|---|---|---|
| 1 | **En-tête** | H1 « Calculateur [X] : [ce qu'il calcule] », chapô d'une phrase sur ce que fait l'outil, fiche (périmètre couvert, source officielle, date de vérification) | — |
| 2 | **En bref** | la formule ou la règle en clair, les cas où l'outil ne s'applique pas | — |
| 3 | **L'outil** | dans le premier écran sur ordinateur, juste après l'en-tête sur mobile | — |
| 4 | **Le résultat** | lisible, avec l'interprétation ; **le CTA transporte le résultat** (formulaire ou message pré-rempli) | oui |
| 5 | **Avertissement** | « résultat indicatif », source officielle, lien vers l'outil officiel s'il existe | — |
| 6 | **Méthode de calcul** | la formule, les règles appliquées en tableau, chaque règle avec sa source | — |
| 7 | **Exemples** | 2-3 cas chiffrés, étiquetés « exemple » | — |
| 8 | **FAQ** | | — |
| 9 | **Sources et CTA final** | | oui |

Règles propres à l'outil :

- **La méthode est dans le HTML**, pas dans le script. C'est elle qui se
  positionne et qui se fait citer ; l'outil seul est une boîte noire pour un
  moteur.
- **Accessibilité** : chaque champ a un `<label>` visible, les choix groupés
  sont dans un `<fieldset>` avec `<legend>`, le résultat est dans une zone
  `aria-live="polite"`, une erreur de saisie en `role="alert"`, les champs
  numériques en `inputmode="numeric"` et à 16 px minimum (sinon iOS zoome).
- **Aucune donnée inventée** : coefficients, barèmes et seuils viennent d'une
  source officielle datée, affichée sous l'outil.
- **Le résultat se partage** : un paramètre d'URL ou un bouton « copier le
  résultat » transforme un calcul en lien que le visiteur transmet.

---

## 7. Lead magnet (ressource contre un email)

Colonne vertébrale : **ce que vous obtenez → la preuve que ça vaut l'email →
le formulaire → la suite**.

| # | Section | Contenu | CTA |
|---|---|---|---|
| 1 | **Hero** | ce que contient la ressource, format et longueur (« guide de 24 pages », « modèle tableur »), visuel de la ressource | oui (ancre vers le formulaire) |
| 2 | **Aperçu réel** | le sommaire et un extrait utile **en clair** | — |
| 3 | **Pour qui, pour quoi faire** | 3 situations où la ressource sert | — |
| 4 | **Formulaire** | email seul (prénom facultatif), mention de ce qui sera envoyé, désinscription en un clic, lien vers la politique de confidentialité | oui |
| 5 | **Auteur** | qui a produit la ressource, pourquoi il est légitime | — |
| 6 | **FAQ** | | — |
| 7 | **CTA de sortie** | vers l'offre, pour ceux qui ont déjà la ressource | oui |

Règles de capture qui tiennent :

- **La partie publique se suffit à elle-même.** C'est elle qui se positionne.
  Le contenu verrouillé n'est jamais indexé ; s'il porte toute la valeur, la
  page ne rankera pas.
- **Pas de fenêtre bloquante sans bouton de fermeture**, pas d'interstitiel
  qui couvre le contenu à l'arrivée sur mobile : Google pénalise les
  interstitiels intrusifs, et un lecteur coincé part. Une fenêtre de capture
  se déclenche sur une demande explicite (clic) ou après un défilement réel,
  une seule fois, avec `role="dialog"`, `aria-modal="true"`, fermeture au
  clavier (Échap) et focus placé dans la fenêtre.
- **Sans JavaScript, les liens restent de vrais liens.** Un visiteur non
  capturé vaut mieux qu'un visiteur devant une porte que rien n'ouvre.
- **Ne redemandez pas l'email** à qui l'a déjà donné : une clé commune à tout
  le site (stockage local ou cookie) évite de punir les abonnés.
- **Le succès livre immédiatement** : lien de téléchargement ou ouverture de
  la ressource dans la foulée, pas « vérifiez vos emails » sans rien d'autre.
- **Vérifiez l'arrivée réelle** de l'email dans l'outil d'emailing avant de
  lancer : un formulaire qui poste dans un iframe caché ne lit pas la réponse,
  et un refus passe pour un succès.
