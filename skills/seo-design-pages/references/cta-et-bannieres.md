# CTA et bannières

Un CTA est une promesse : cliquez ici, il se passera ceci. Une bannière est
une section entière au service d'un seul rôle — prouver, faire témoigner,
capturer, déclencher. Les deux échouent de la même façon : trop nombreux,
trop tôt, ou sans preuve derrière.

---

## 1. L'action principale

**Une page, une action principale.** Choisissez-la avant d'écrire : demander
un devis, réserver un appel, télécharger le guide, lancer l'essai. Elle se
répète à l'identique à chaque emplacement : même libellé, même destination,
même style. Trois actions différentes dans une page divisent la conversion
et brouillent la mesure.

**Une action secondaire au plus**, à plus faible engagement : téléphone,
WhatsApp, démo vidéo, « voir un exemple ». Elle se place à côté de la
principale, en style contour (jamais deux boutons pleins côte à côte), et
l'ordre de lecture met la principale en premier.

| Rôle | Style | Exemples |
|---|---|---|
| Principale | bouton plein, couleur d'accent | « Recevoir mon devis sous 48 h », « Réserver 30 minutes » |
| Secondaire | bouton contour ou lien fort | « Appeler le 01 23 45 67 89 », « Voir la démo (3 min) » |
| Navigation | lien dans le texte | « le détail des tarifs », « la méthode complète » |

## 2. Combien, et où

| Longueur | CTA | Emplacements |
|---|---|---|
| Courte (< 800 mots) | 2 | hero · fin |
| Moyenne (800 à 2 000 mots) | 3 | hero · après la solution ou la preuve · fin |
| Longue page commerciale | 4 à 5 | hero · après chaque bande de preuve (bénéfices, bannière confiance, tarifs) · fin |
| Article | 2 + barre latérale | encart contextuel au milieu · fin · carte collante sur ordinateur |
| Comparatif | 2 | après le tableau de synthèse · fin |
| Outil | 1 à 2 | dans le résultat · fin |

Règles de placement :

- **Dans le premier écran**, pour toute page commerciale. Le visiteur qui a
  déjà décidé ne doit pas chercher le bouton.
- **Après une preuve, jamais avant.** Un CTA insistant qui précède toute
  preuve se lit comme une demande sans raison.
- **Sur une page commerciale longue, chaque bande pleine largeur qui suit une
  preuve porte l'action.** Un visiteur convaincu au milieu de la page ne
  remontera pas au hero.
- **Dans un article, pas de CTA avant que la question du titre ait reçu sa
  réponse.** Le CTA contextuel arrive juste après la section où le besoin
  apparaît (« vous avez vu que… : nous le faisons pour vous »).
- **Jamais deux CTA dans le même écran**, sauf le couple principale +
  secondaire.

## 3. Le libellé

**Verbe + objet + bénéfice**, 2 à 6 mots, à la première personne quand c'est
naturel :

| ❌ | ✅ |
|---|---|
| En savoir plus | Voir les tarifs détaillés |
| Envoyer | Recevoir mon devis sous 48 h |
| Contactez-nous | Parler à un conseiller |
| Télécharger | Télécharger le guide (PDF, 24 pages) |
| Cliquez ici | Réserver mon créneau de 30 minutes |

**La ligne de réassurance**, sous le bouton, en petit : ce qui se passe après
le clic et ce que ça n'engage pas (« Réponse sous 24 h ouvrées · Sans
engagement »). Uniquement des promesses que l'équipe tient réellement.

**Sur mobile**, un libellé long se coupe sur deux lignes et casse le bouton.
Écrivez court, ou prévoyez une version courte affichée sous 640 px.

## 4. Les pièges

- **Le CTA qui ne mène nulle part.** Un lien vers `/devis` qui n'existe pas
  est une 404 livrée ; un bouton « Télécharger » sans fichier trompe le
  lecteur. Tant que la cible n'existe pas, le bouton n'existe pas.
- **Le contraste.** Texte blanc sur un violet ou un bleu moyen tombe
  facilement sous 4,5:1 (un blanc sur violet moyen mesuré à 4,2:1, par
  exemple). Mesurez, ne jugez pas à l'œil.
- **La cible tactile.** 44 × 44 px minimum ; sous 640 px, les boutons passent
  en pleine largeur et s'empilent.
- **`target="_blank"` sur un lien interne** : ne le faites pas. Sur un outil
  externe (agenda de réservation), gardez `rel="noopener"`.
- **Le texte en dégradé transparent** (`background-clip: text`) dans un
  bouton ou un titre d'appel : sa couleur réelle est `transparent`, ce qui
  fausse les outils de contraste, et c'est devenu une signature de page
  générée. Une couleur pleine.
- **Le CTA d'outil qui oublie le résultat.** Sur un calculateur, le bouton
  doit transporter ce que le visiteur vient de calculer (message ou
  formulaire pré-rempli). Lui faire tout ressaisir perd la moitié des
  demandes.
- **Le CSS dupliqué dans chaque page.** Un composant collé inline se corrige
  page par page : réparer le modèle ne répare rien de ce qui est déjà en
  ligne. Gardez une signature unique dans le `<style>` du composant (sa classe
  racine) pour pouvoir remplacer ce seul bloc partout, à l'identique, avec un
  contrôle « exactement une occurrence par page » et un essai à blanc d'abord.

---

## 5. Les bannières

| Bannière | Rôle | Contenu obligatoire | Composant |
|---|---|---|---|
| **Confiance (E-E-A-T)** | prouver qui parle | photo réelle, nom, fonction, ancienneté, 2-3 preuves vérifiables, un CTA | `banniere-eeat.html` |
| **Témoignages** | faire parler les clients | 3 avis réels : prénom + initiale au minimum, fonction ou ville, date, source | `banniere-temoignages.html` |
| **Chiffres clés** | quantifier | 3-4 chiffres, chacun avec sa source et sa date | `encadre-chiffres-cles.html` |
| **Limites** | borner la promesse | ce qui n'est pas garanti, ce qui dépend du client | `encadre.html` |
| **Lead magnet** | capturer un email | visuel de la ressource, 3 points de contenu, formulaire court, mention de confidentialité | `banniere-lead-magnet.html` |
| **Contact / devis** | déclencher l'action | promesse concrète, ce qui se passe ensuite, action principale + téléphone | `banniere-contact.html` |

### L'ordre

**La preuve avant la demande.** Confiance, témoignages et chiffres précèdent
la bannière de contact. Ne fusionnez jamais confiance et contact : une
bannière qui prouve et demande à la fois fait les deux à moitié, et le
lecteur voit la demande avant la preuve.

Une bannière de chaque type par page au plus. Deux bannières pleine largeur
d'affilée se lisent comme une publicité — sauf le couple final
« confiance → contact », qui clôt naturellement une page commerciale.

### Les preuves, une par une

| Preuve | Acceptable | À proscrire |
|---|---|---|
| Témoignage | prénom + initiale, fonction ou ville, date, source (« avis Google, mars 2026 ») avec lien quand l'avis est public | avis sans auteur, avis réécrit, photo de banque d'images sur un avis |
| Note moyenne | « 4,8/5 sur 126 avis Google » avec lien et date de relevé | étoiles sans nombre d'avis ni source |
| Logo client | client réel, autorisation écrite | logos « de confiance » d'entreprises qui ne sont pas clientes |
| Chiffre | source et date sous le chiffre, ou note de bas de bannière | « +300 % », « 99 % » sans source |
| Certification | nom exact + numéro vérifiable | badge générique « expert certifié » |
| Photo d'équipe | photo réelle de l'équipe ou du chantier | banque d'images, visage généré |

Sans preuve sociale réelle, ne la simulez pas : la réassurance légitime vient
alors de la transparence — méthode montrée, sources officielles citées,
engagements écrits (délai de réponse, devis écrit), expertise réelle de
l'auteur, exemples chiffrés clairement étiquetés « exemple ».

**Avis en ligne** : qui les affiche doit dire s'ils sont contrôlés et comment
(Code de la consommation, art. L111-7-2). Une ligne sous la bannière suffit
(« Avis publiés sans tri, relevés sur Google le [date] »).

**Balisage** : les avis que vous affichez sur votre propre site à propos de
votre propre entreprise ne donnent pas d'étoiles dans Google (avis
« auto-servis » exclus des extraits enrichis). Ne balisez pas `Review` ou
`AggregateRating` sur votre `Organization` ou `LocalBusiness` en espérant
des étoiles — voir `seo-schema-jsonld`.

### La bannière confiance

- **Photo réelle** de la personne qui intervient ou écrit ; une photo de
  banque d'images sur une bannière de confiance est un contresens.
- **Titre factuel** : « [Métier] depuis [année] à [ville] », pas « l'expert
  n° 1 ».
- **2-3 preuves vérifiables** en pastilles : certification avec numéro,
  assureur, note avec sa source.
- **Un seul CTA** : téléphone cliquable, profil professionnel ou prise de
  rendez-vous.
- Sur une page service, elle vaut plus que trois paragraphes d'arguments.

### La bannière lead magnet

- La ressource montrée (couverture, aperçu de page), pas une icône.
- Trois points concrets de ce qu'elle contient.
- **Email seul** (prénom facultatif) : chaque champ supplémentaire coûte des
  inscriptions. Le `label` est visible, pas seulement un `placeholder`.
- Sous le bouton : ce qui sera envoyé, la fréquence, la désinscription en un
  clic, le lien vers la politique de confidentialité.

---

## 6. Fenêtres, barres collantes, bandeaux

| Élément | Règle |
|---|---|
| Fenêtre de capture | déclenchée par un clic ou un défilement réel, une seule fois, fermable (bouton visible + Échap), `role="dialog"` et `aria-modal="true"` ; jamais à l'arrivée sur mobile |
| Carte CTA collante | barre latérale d'article sur ordinateur uniquement, `position: sticky` natif |
| Bouton flottant (téléphone, WhatsApp) | un seul, en bas à droite, marge qui ne masque ni texte ni bouton ; seul objet de la page qui porte une ombre |
| Barre de CTA en bas d'écran mobile | acceptable sur une page commerciale si elle ne dépasse pas 64 px et ne recouvre pas la bannière cookies |
| Bandeau promotionnel en haut | évitez : il pousse le hero sous la ligne de flottaison et dégrade le LCP |
