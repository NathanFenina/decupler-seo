# Checklist design avant publication

Bloquante : une case non cochée = la page ne part pas, ou part avec la
réserve écrite dans le livrable. Les contrôles automatiques d'abord, le
regard ensuite.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/controle_contenu.py" page-<slug>.html
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/audit_images.py" page-<slug>.html --strict
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/schema_validate.py" page-<slug>.html --strict
```

---

## Structure

- [ ] Le type de page est identifié et le gabarit du type est suivi (ou
      l'écart est justifié dans `design-<slug>.md`)
- [ ] Un seul H1, qui correspond au title ; pas de H1 en double avec le thème
- [ ] Hiérarchie des titres sans saut (pas de H4 sous un H2)
- [ ] Le premier écran contient le H1, la réponse directe ou la promesse
      chiffrée, et (page commerciale) l'action principale
- [ ] Au moins une section propre à cette page, absente des pages sœurs
- [ ] Bandes alternées : jamais deux fonds identiques d'affilée
- [ ] Aucun bloc de liens en pied de page ; liens internes dans le texte
- [ ] FAQ en `<details>`, contenu dans le HTML initial

## CTA et bannières

- [ ] Une action principale, même libellé et même destination partout
- [ ] Nombre et emplacements conformes au plan (hero, après la preuve, fin)
- [ ] Libellés verbe + objet, pas de « En savoir plus » / « Envoyer »
- [ ] Chaque lien de CTA répond en 200 (aucune 404, aucun bouton sans cible)
- [ ] La bannière de confiance précède la bannière de contact ; elles sont
      distinctes
- [ ] Chaque preuve a sa source : chiffre, note, avis, logo, certification
- [ ] Aucun témoignage, logo, compteur ou badge inventé
- [ ] Fenêtre de capture (s'il y en a une) fermable, jamais à l'arrivée sur
      mobile, `role="dialog"`

## Images

- [ ] Chaque image a un rôle (prouver, expliquer, montrer, situer)
- [ ] L'image LCP : pas de `loading="lazy"`, `fetchpriority="high"`,
      dimensions explicites, < 200 Ko
- [ ] Toutes les images : `width` et `height`, `alt` pertinent (ou `alt=""`
      si décorative), `loading="lazy"` sous la ligne de flottaison
- [ ] WebP ou AVIF (repli JPEG dans `<picture>` si besoin)
- [ ] Noms de fichiers descriptifs ; aucune image répétée dans la page
- [ ] Hébergées sur le site, aucune en base64, aucun marqueur provisoire
- [ ] Légende qui interprète ; crédit pour toute photo tierce
- [ ] Images générées : relues en taille réelle, `alt` réécrit d'après le
      résultat, jamais utilisées comme preuve

## Accessibilité

- [ ] Contraste ≥ 4,5:1 sur tout texte courant, y compris texte secondaire
      sur fond sombre et texte des boutons ; mesuré sur le rendu
- [ ] Focus clavier visible sur liens, boutons, `summary`, champs
- [ ] Ordre de tabulation logique ; tout est atteignable au clavier
- [ ] Formulaires : `<label>` visibles, `autocomplete`, erreurs annoncées
- [ ] Tableaux : `<th scope>`, `<caption>` ou titre associé ; conteneur
      défilant atteignable au clavier (`tabindex="0"` + `aria-label`)
- [ ] Aucun état signalé par la couleur seule
- [ ] Animations neutralisées sous `prefers-reduced-motion`
- [ ] Langue de la page (`lang`) et sens d'écriture (`dir`) corrects

## Performance

- [ ] LCP < 2,5 s et CLS < 0,1 sur mobile (Lighthouse ou PageSpeed)
- [ ] Aucune police ni feuille chargée depuis un domaine tiers dans un
      fragment ; au plus deux familles, `font-display: swap`
- [ ] Aucun script bloquant ; JavaScript seulement là où il est utile
      (outil, menu), jamais pour afficher du contenu
- [ ] Contenu visible si le JavaScript échoue (pas d'`opacity: 0` en attente
      d'un script)
- [ ] Pas de carrousel en hero, pas de vidéo en lecture automatique au-dessus
      de la ligne de flottaison

## Mobile (390 px)

- [ ] Aucun défilement horizontal
- [ ] Tableaux dans un conteneur défilant, lisibles
- [ ] H1 et sous-titres non tronqués ; boutons en pleine largeur, 44 px
- [ ] Rien de collant ne masque le texte ou un bouton
- [ ] Champs à 16 px minimum

## Plateforme

- [ ] WordPress : aucune ligne vide dans le contenu ni dans `<style>`/
      `<script>`, pas d'élément en ligne orphelin entre deux blocs
- [ ] CSS scopé sous une classe racine préfixée
- [ ] Webflow : chaque embed < 50 000 caractères
- [ ] Next.js : `npm run build` passe, `priority` sur la seule image LCP
- [ ] Rendu vérifié servi en HTTP, dans le vrai thème, aux deux largeurs,
      captures jointes au livrable
