---
name: seo-programmatique
description: >
  Conçoit, génère et audite des pages SEO à l'échelle depuis une source de
  données : motifs d'URL, gabarits, variables, garde-fous anti-contenu mince,
  maillage automatique, stratégie de canonical. Bloque au-delà des seuils sans
  audit qualité. Déclencher sur "SEO programmatique", "pages à l'échelle",
  "générer des centaines de pages", "pages ville", "pages par catégorie",
  "template de page", "pSEO", "pages automatiques", "landing pages en masse".
---

# SEO programmatique — l'échelle sans le contenu mince

Le SEO programmatique fonctionne quand chaque page apporte une information
que le visiteur ne trouve pas ailleurs. Il échoue — et il fait couler le
site entier — quand les pages ne sont que des permutations de variables.

Google n'évalue pas ces pages une par une. Il évalue le **lot**. Si 60 % du
lot est vide, les 40 % utiles tombent avec.

## Garde-fous

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/guard.py" --action generer-pages --volume <N>
```

| Volume | Comportement |
|--------|--------------|
| < 100 | Autorisé |
| 100-499 | ⚠️ Validation demandée + audit d'un échantillon de 20 pages |
| ≥ 500 | 🛑 **Bloqué** tant que l'audit qualité n'est pas passé |
| Pages locales ≥ 30 | ⚠️ Risque de doorway pages |
| Pages locales ≥ 50 | 🛑 Bloqué |

Ces seuils ne sont pas désactivables. Ils existent parce que le mode d'échec
est catastrophique et différé : tout va bien pendant trois mois, puis le
site entier décroche.

## Le test de valeur unique

Avant de générer quoi que ce soit, répondez :

> **Qu'est-ce que la page « [variable A] » contient que la page
> « [variable B] » ne contient pas — au-delà du nom de la variable ?**

Si la réponse est « rien », il ne faut pas générer ces pages. Faites une
seule page avec un filtre.

| ✅ Ça marche | ❌ Ça ne marche pas |
|--------------|---------------------|
| « Vol Paris-Lisbonne » : prix réels, horaires, compagnies, durée — données propres à cette paire | « Plombier à [ville] » : le même texte avec le nom de la ville changé |
| « Salaire d'un développeur à Lyon » : données salariales locales issues d'un jeu de données | « Meilleur [produit] pour [métier] » : trois adjectifs permutés |
| « [Logiciel A] vs [Logiciel B] » : comparaison de caractéristiques réelles | « Acheter [produit] pas cher [ville] » : rien de local |

## La source de données

Elle doit être **riche**. Une bonne source de données programmatique a au
moins 8-10 champs exploitables par entrée, et de préférence des données que
personne d'autre n'a — les vôtres.

Sources possibles : votre base métier, un jeu de données public, des données
agrégées de vos clients (anonymisées), une API tierce, vos propres mesures.

Qualité : pas de champ vide sur les pages générées. Une page avec « prix :
N/A, disponibilité : N/A » est pire que pas de page. **Filtrez les entrées
incomplètes avant génération** — c'est la règle la plus importante de ce
skill.

## L'architecture

**Motif d'URL** — court, lisible, sans paramètre :
`/vols/paris-lisbonne/` et non `/search?from=CDG&to=LIS`

**Le gabarit**, avec la part de contenu unique :

| Zone | Part | Contenu |
|------|------|---------|
| H1 | unique | Variables |
| Réponse directe | unique | Générée à partir des données réelles |
| Bloc de données | **unique** | Le cœur : tableau, chiffres, graphique |
| Analyse | unique | 150-300 mots générés depuis les données, pas un texte à trous |
| Contexte | partagé | Explication générale du domaine |
| FAQ | mixte | 2 questions dynamiques, 3 statiques |
| Maillage | unique | Pages liées calculées par proximité |

**Visez au moins 60 % de contenu unique par page.** En dessous, c'est de la
duplication à l'échelle.

Mesurez-le, ne l'estimez pas — avant publication, sur le lot entier :

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/similarite_lot.py" contenus/villes/ --strict
```

Le script compte les phrases communes à chaque paire de pages (seuil : 4)
et la part du texte de chaque page qu'on ne retrouve nulle part ailleurs
(seuil : 60 %). Ce qui est identique par construction — en-tête, bande de
logos, bloc auteur, CTA final — se marque `data-gabarit="commun"` et sort du
calcul : sinon l'alerte sonne sur le chrome, et on finit par l'ignorer.

Le « texte à trous » (`Vous cherchez un {métier} à {ville} ? Nos {métier}s
à {ville} sont…`) est la signature du contenu mince. Générez la prose **à
partir des données** : « Sur cette liaison, le prix médian est de 89 €,
soit 23 % sous la moyenne des vols depuis Paris. »

## Le maillage automatique

Sans maillage, les pages générées sont orphelines et ne seront jamais
indexées. Prévoyez :

- Une **page index** listant toutes les pages générées, paginée par 50
- Des **liens de proximité** entre pages : mêmes catégories, valeurs
  voisines, alternatives (5-8 liens par page)
- Un lien **remontant** vers la catégorie parente
- L'inclusion dans un sitemap dédié

## Canonicals et prévention du gonflement d'index

- Chaque page générée : canonical **auto-référente**
- Les variantes de tri, de filtre ou de pagination : canonical vers la page
  principale
- Les combinaisons à faible valeur (moins de X entrées de données) :
  `noindex, follow` — la page reste accessible, elle ne pollue pas l'index
- Sitemap séparé pour les pages programmatiques : le rapport de couverture
  GSC devient exploitable par segment

## Le déploiement progressif — la seule méthode sûre

1. **Générer 20 pages.** Choisir les 20 entrées les plus riches en données.
2. **Auditer manuellement** : chaque page apporte-t-elle une valeur propre ?
   Un humain la trouverait-elle utile ?
3. **Publier** ces 20, attendre **4 à 6 semaines**.
4. **Mesurer** : combien sont indexées ? Combien reçoivent des impressions ?
   Quel est le taux d'indexation ?

| Taux d'indexation à 6 semaines | Décision |
|-------------------------------|----------|
| > 80 % avec impressions | ✅ Déployer le reste, par lots de 100 |
| 50-80 % | ⚠️ Enrichir le gabarit avant d'aller plus loin |
| < 50 % | 🛑 Arrêter. Le gabarit ne tient pas. |

Ne générez **jamais** 2 000 pages d'un coup. Si le gabarit est mauvais, vous
l'apprendrez trois mois plus tard, sur un site abîmé.

## Pages ville d'un prestataire de service

Le cas le plus fréquent, et le plus risqué : « [service] [ville] » pour un
prestataire qui n'a qu'une adresse. Les seuils de `guard.py` s'appliquent
(pages locales : alerte à 30, blocage à 50), et le gabarit section par
section est dans `seo-design-pages` (`references/gabarits-par-type-de-page.md`,
page locale). Ce qui s'ajoute, appris en production :

**Calibrer sur la SERP mesurée, pas sur une consigne a priori.** Avant
chaque lot, relever le top 5 de deux ou trois villes du lot
(`seo-serp-analysis`) : longueur, occurrences, FAQ, preuves, adresse. Sur
ces requêtes, il arrive couramment que la page n°1 fasse 600 à 900 mots,
sans FAQ ni adresse locale : **la longueur ne décide pas, la preuve si**
(missions chiffrées et liées, zone servie claire, autorité du domaine).
Une consigne maison pensée pour les articles (20 occurrences, 1 700 mots)
rend la page deux fois plus longue que la gagnante sans rien gagner.
Le relevé se date et se refait : une règle non sourcée finit par coûter.

**Jamais d'adresse inventée.** Une adresse fictive en `LocalBusiness` est un
faux signal local, sanctionné, et un mensonge envers le prospect. La seule
adresse réelle vit dans le schéma `Organization` du site ; chaque page ville
porte `areaServed` (ville, département). Le cadrage est honnête : « depuis
[ville du siège], nous intervenons à [ville] », jamais « notre agence de
[ville] ». Sur une ville voisine du siège, `areaServed` et ce cadrage
suffisent ; loin du siège, l'ancrage local n'est pas crédible et la page
d'agence seule ne gagnera pas : passez par un autre angle (comparatif,
ci-dessous).

**Jamais de clientèle locale inventée non plus.** « Nos clients [gentilé] »,
« les entreprises que je vois ici » affirment une présence qu'on ne peut
pas prouver. Écrire ce qui est vrai **du marché** (« une entreprise de
[ville] part rarement d'un site vierge »), pas une expérience supposée.
Relecture dédiée de tout le lot sur ce seul point.

**Ce qui fait la profondeur locale** : codes postaux cités en toutes
lettres, 8 à 12 communes limitrophes, le gentilé au moins une fois, les
secteurs économiques réels de la ville, une vraie photo du lieu (crédit
affiché). Et un bloc de **résultats chiffrés** (une ou deux missions, avec
lien vers l'étude de cas complète) : c'est lui qui remplace l'adresse
absente.

**Deux registres, deux entités.** Une page « agence [ville] » parle au
« nous » et se rattache à l'`Organization` ; une page « consultant [ville] »
parle au « je » et se rattache à la `Person`. Ne pas mélanger les deux dans
une même page, ni le schéma.

**Intention mixte sur les grosses villes.** Quand une partie du top est
faite de comparatifs (« les 15 meilleurs [prestataires] à [ville] »), la
page d'agence ne couvre pas toute la SERP. Une page comparatif distincte
cite les concurrents nommément, avec leurs vrais points forts, et place la
marque à sa juste place (pas première par défaut), sans note ni classement
chiffré inventé. C'est l'angle où l'absence d'adresse locale ne pénalise
pas.

**Maillage d'une page ville : cinq liens, pas plus.** Un lien montant vers
le pilier local dans les 150 premiers mots ; deux ou trois latéraux vers
les villes voisines du même département (au-delà, la grille de communes
devient une ferme de liens) ; un lien croisé vers la page sœur de la même
ville (autre service) si elle existe ; un lien de preuve vers une étude de
cas du même secteur ; un lien descendant vers une ressource pratique.

**Données et texte séparés.** Un fichier de **données** par ville (slug,
gentilé, département, codes postaux, communes, secteurs, photo, registre)
et un fichier de **blocs rédigés** ville par ville : accroche, contexte,
points propres à la ville, piège local, introduction et note de la zone,
second paragraphe du budget, CTA final, au moins deux questions de FAQ.
Le gabarit assemble ; il ne rédige pas. Puis `similarite_lot.py --strict`
sur le lot entier.

**Une carte de zone en SVG plutôt qu'une capture** : quelques kilo-octets,
du texte lisible par les moteurs, chaque point à sa vraie place
(coordonnées réelles, distance au siège calculée, la même que dans le
texte). Trois pièges : un cadrage par région (cadrer tout le réseau écrase
les villes proches dans un coin) ; moins de repères au grand cadrage (les
noms se chevauchent) ; la géométrie **découpée au cadre** du `viewBox`
(un tracé qui déborde fait déborder la page en mobile).

**Après la publication**, relire le rendu servi (`seo-publication-cms`,
`references/wordpress.md`) : contenu identique au build, aucun `<p>` ni
`<br>` parasite, JSON-LD valide, images en 200.

## Auditer un déploiement existant

Si des pages programmatiques existent déjà :

1. Taux d'indexation par segment (GSC)
2. Pages sans aucune impression depuis 6 mois → candidates au `noindex` ou
   à la suppression du sitemap
3. Cannibalisation : plusieurs pages sur la même requête
4. Contenu mince : comptage de mots uniques hors gabarit
5. Orphelines : pages générées sans lien entrant

Le correctif le plus fréquent : passer 70 % des pages en `noindex` et
enrichir les 30 % qui ont du potentiel. Un index plus petit et plus dense
performe mieux qu'un index gonflé.

## Livrables

- `PROGRAMMATIQUE-PLAN.md` — motif d'URL, gabarit, source de données, seuils
- `gabarit.html` — le template
- `echantillon/` — les 20 premières pages, à auditer
- `AUDIT-QUALITE.md` — le verdict sur l'échantillon
- `maillage-programmatique.csv` — le plan de liens
