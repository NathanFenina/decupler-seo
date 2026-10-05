<!-- SOP decupler-seo · source unique : docs/sop/ · le playbook public https://decupler.com/claude-code-seo-os/ en reprend le contenu -->

# SOP 1 · Topical map

**Skills** : `seo-cartographie`, `seo-cocon-semantique` · **Commande** : `/seo cartographie, puis /seo cocon`

**Objectif** : Savoir quelle page doit gagner quel mot-clé sur Google et quelle question dans les IA, et comment les pages se tiennent en silos.

**Quand** : Au démarrage d'un site, puis une fois par mois pour le relevé.

**Dis à Claude** : « Fais la cartographie du site : une ligne par page avec son mot-clé principal et son prompt principal. Puis propose les silos et les pages piliers. »

## Étapes

1. Claude croise Search Console (90 jours, page × requête), le sitemap et ton calendrier éditorial : une ligne par page, avec son mot-clé principal et trois secondaires (`cartographie.py initialiser`).
2. Il propose un prompt principal par page : la question qu'un acheteur poserait à ChatGPT, sans le nom de ta marque, en 20 mots au plus.
3. Tu valides ligne par ligne, en commençant par les pages P1. Le bon mot-clé est celui qui amène des clients, pas seulement des clics.
4. Contrôle de cannibalisation (`cartographie.py verifier`) : deux pages sur le même mot-clé, tu tranches avant d'écrire quoi que ce soit (fusion, redirection ou nouvelle cible).
5. Les silos : une page pilier par thème, des satellites qui la soutiennent, et le plan de liens entre les niveaux.
6. Chaque mois, `cartographie.py mensuel` relève la position de chaque page sur son mot-clé et la citation de son prompt par ChatGPT, Gemini et Claude.

**MCP nécessaires** : Search Console (ou un export CSV). DataForSEO ou Ubersuggest pour les volumes. Notion en option, pour l'export.

**Livrable** : `memoire/cartographie.csv` (une ligne par page : mot-clé, prompt, silo, priorité) et le plan de silos.

## Pièges

- Un silo n'est pas un répertoire d'URL : c'est une intention commerciale.
- Un prompt qui contient ta marque mesure ta notoriété, pas ta visibilité.
- Le script propose, tu valides : la colonne `a_valider` doit être vide avant de produire.

> Chez nous : Sur decupler.com, la carte topique a croisé 143 URL du sitemap avec 12 mois de Search Console : 58 n'étaient pas indexées, et trois pages faisaient 42 % des clics (relevé du 22/09/2026).
