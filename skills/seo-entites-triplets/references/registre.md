# Le registre — entites.csv et triplets.csv

Deux fichiers CSV dans `memoire/`, en UTF-8, avec une ligne d'en-tête. Une
ligne qui commence par `#` est un commentaire (le gabarit du projet en
contient une, pour l'exemple). Les colonnes à plusieurs valeurs les
séparent par `|`.

## memoire/entites.csv

```csv
entite,type,qid,sameAs,definition,alias
Atlas Conseil,Organization,,https://www.atlas-conseil.example/#organization | https://www.atlas-conseil.example/,Cabinet d'expertise comptable à Lyon,Atlas
Expertise comptable,Thing,Q…,https://fr.wikipedia.org/wiki/Expertise_comptable,Profession réglementée qui tient et certifie les comptes des entreprises,expert-comptable | experts-comptables
Lyon,City,Q…,https://fr.wikipedia.org/wiki/Lyon,Commune française,
Liasse fiscale,DefinedTerm,,,Ensemble des formulaires fiscaux joints à la déclaration de résultat,
```

| Colonne | Contenu |
|---------|---------|
| `entite` | Le nom exact, tel qu'il apparaît dans le texte |
| `type` | `Thing`, `City`, `Country`, `Person`, `DefinedTerm`, `Organization`… |
| `qid` | `Q…` (ou l'URL Wikidata complète). Vide tant que non vérifié |
| `sameAs` | Wikipédia, site officiel, profils. **Une URL avec `#`** (`…/#organization`) est l'`@id` d'un nœud du graphe : `jsonld` pose alors une référence `{"@id"}` au lieu de recopier l'entité |
| `definition` | La définition **telle que la page l'écrit** — sert de `description` au `DefinedTerm` |
| `alias` | Les autres formes à reconnaître dans le texte (pluriel, sigle, forme courte). Optionnelle |

Règles :

- Un QID n'entre qu'après lecture de la description Wikidata
  (`triplets.py wikidata`). Pour une organisation, `--site` vérifie que son
  site officiel (P856) est bien le domaine.
- Une organisation tierce, un logiciel **cité** : `type` libre au registre,
  mais `jsonld` les pose en `Thing` avec `sameAs` — une seconde
  `Organization` ou un `SoftwareApplication` dans la page déclencherait des
  erreurs de données structurées.
- La propre organisation du site : son `@id` du socle en `sameAs`, pour
  que toutes les pages s'y réfèrent sans la recopier.
- L'ancien registre JSON (`memoire/entites.json`) est encore lu par le
  script ; migrez-le vers le CSV à la prochaine mise à jour.

## memoire/triplets.csv

```csv
sujet,predicat,objet,source,date_verif,pages
Atlas Conseil,est situé à,Lyon,mentions légales,2026-09-01,*
Le bilan annuel,coûte,1 200 € HT,grille tarifaire 2026,2026-09-01,/offres/bilan-annuel/ | /tarifs/
Le bilan annuel,dure,3 semaines,grille tarifaire 2026,2026-09-01,/offres/bilan-annuel/
Le taux normal de TVA,est,20 %,impots.gouv.fr,2026-09-01,/tarifs/
La liasse fiscale,désigne,l'ensemble des formulaires joints à la déclaration de résultat,impots.gouv.fr,2026-09-01,/glossaire/
```

| Colonne | Contenu |
|---------|---------|
| `sujet` | Le sujet tel qu'il doit être écrit. S'il correspond à une entité (ou un alias), le script reconnaît aussi ses autres formes |
| `predicat` | Un prédicat du lexique (`est`, `coûte`, `dure`, `est situé à`…) de préférence : c'est lui qui permet de comparer les pages |
| `objet` | **La valeur canonique**, avec son unité et HT/TTC. C'est cette chaîne qu'on recopie dans les pages |
| `source` | Document officiel, page du client, texte de loi — ce qui permet de revérifier |
| `date_verif` | AAAA-MM-JJ. Un fait réglementaire se revérifie au moins une fois par an |
| `pages` | Où le fait **doit** être affirmé : `*` pour toutes, sinon chemins ou slugs séparés par `|` |

Règles :

- **Une seule ligne par sujet + prédicat à valeur unique** (coûte, dure,
  est situé à, fondé en, désigne…). Deux lignes « Le bilan annuel — coûte »
  avec deux montants, c'est la contradiction qu'on cherche à éviter sur le
  site : elle commence ici. Deux offres différentes = deux sujets
  différents (« Le bilan annuel TPE », « Le bilan annuel SAS »).
- Un fait incertain s'écrit en fourchette (« 1 000 à 1 500 € HT ») avec
  « à confirmer » dans `source`, jamais en valeur précise inventée.
- Une ancienne valeur ne reste pas au registre : elle part dans la source
  de la nouvelle (« grille 2026 ; 1 000 € HT jusqu'en 2025 »), et les pages
  qui l'évoquent la datent explicitement.
- Chaque chiffre de `memoire/faits.md` a sa ligne ici, à l'identique.

## Quand un fait change

1. Corriger la ligne (valeur, source, `date_verif`), et `memoire/faits.md`.
2. `triplets.py coherence contenus/ --triplets memoire/triplets.csv` : la
   liste des pages qui portent encore l'ancienne valeur (« écart au
   registre »).
3. Corriger chaque page, puis `verifier --strict` sur chacune.
4. Mettre à jour le JSON-LD qui porte la valeur (`Offer.price`,
   `FAQPage`), le `llms.txt`, et les profils hors site.
5. Journaliser (`seo-journal-mesure`).

## Démarrer le registre sur un site existant

1. `triplets.py coherence <contenus|--urls crawl.csv> --textes --json` :
   les contradictions existantes.
2. `triplets.py extraire` sur les pages prioritaires : les triplets
   candidats, triés à la main. On garde ceux qui répondent aux questions des
   clients (prix, délai, périmètre, localisation, obligations).
3. Chaque valeur retenue est vérifiée à sa source, puis inscrite avec la
   date. Les contradictions sont tranchées par la source, pas par la page
   la plus récente.
4. Les entités des pages prioritaires passent par `wikidata`, une par une.
