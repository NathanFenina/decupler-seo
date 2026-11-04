#!/usr/bin/env python3
"""Mesure ce qui rend une page commerciale convaincante ou plate : la grille de `seo-copywriting`.

    python3 copywriting.py page.md
    python3 copywriting.py page.md --section "Contenu" --marque "Talent Up"
    python3 copywriting.py page.html --json

Ce que le script mesure (score /100, détail ligne par ligne) :

- tirets cadratins et demi-cadratins entre espaces : zéro attendu ;
- orientation lecteur : « vous / votre / vos » face à « nous / notre / nos / la marque » ;
- argumentaire en négatif : phrases qui vendent par ce qu'on ne fait pas ;
- rythme : longueur moyenne des phrases, part des phrases de plus de 28 mots ;
- ton explicatif : « permet de », « il est important de », « afin de », « consiste à »… ;
- promesses creuses : « innovant », « performant », « de qualité », « incontournable »… ;
- appels à l'action : au moins 3, dont un dans le premier et un dans le dernier tiers du texte ;
- accroche : le premier paragraphe parle au lecteur, en moins de 60 mots ;
- concret : marqueurs d'exemples et de cas (« par exemple », « concrètement », listes d'usages).

Il ne juge ni la vérité ni la pertinence d'un argument : c'est le travail de la relecture.
Un score haut ne dispense pas de lire la page à voix haute.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TIRET = re.compile(r"—|(?<=\s)–(?=\s)")
LECTEUR = re.compile(r"\b(?:vous|votre|vos)\b", re.I)
AUTEUR = re.compile(r"\b(?:nous|notre|nos)\b", re.I)
NEGATION = re.compile(r"\b(?:ne|n')\s*(?:\w+\s+){0,3}?(?:pas|jamais|aucun(?:e)?|rien|plus)\b|\bsans\s+(?:promesse|garantie)\b",
                      re.I)
EXPLICATIF = re.compile(
    r"\b(?:permet(?:tent)? (?:de|d')|il est (?:important|essentiel|crucial|possible|nécessaire) de|afin de|afin d'|"
    r"consiste(?:nt)? à|a pour (?:objectif|but) de|est capable de|sont capables de|il s'agit de|il s'agit d'|"
    r"de manière (?:\w+)|de façon (?:\w+)|en effet|dans le cadre de|au niveau de|en termes de)", re.I)
CREUX = re.compile(
    r"\b(?:innovant(?:e|s|es)?|performant(?:e|s|es)?|de qualité|incontournable(?:s)?|révolutionn\w+|unique(?:s)?|"
    r"optimal(?:e|es|aux)?|leader(?:s)?|clé(?:s)? en main|à la pointe|de pointe|haut de gamme|exceptionnel(?:le|s|les)?|"
    r"sans précédent|game.changer|véritable(?:s)?|parfaitement|idéal(?:e|es|aux)?)\b", re.I)
CONCRET = re.compile(r"\b(?:par exemple|concrètement|exemple|comme|cas d'usage|cas réel(?:s)?|résultat|livrable(?:s)?)\b",
                     re.I)
VERBE_CTA = re.compile(
    r"\b(?:demande[rz]?|contacte[rz]?|échange[rz]?|r[ée]serve[rz]?|obten(?:ir|ez)|découvr(?:ir|ez)|planifie[rz]?|"
    r"parle[rz]|recev(?:oir|ez)|télécharge[rz]?|construi(?:re|sez)|étudie[rz]?|prend(?:re|s)|appele[rz]?|"
    r"discut(?:er|ez)|lance[rz]?|commence[rz]?|essaye[rz]?|devis)\b", re.I)
LIGNE_CTA = re.compile(r"\[(?:CTA|BOUTON)\]|^\s*(?:\*\*)?bouton\b|<(?:button|a)\b[^>]*class=\"[^\"]*(?:btn|button|cta)", re.I)
PHRASE = re.compile(r"[^.!?…]+[.!?…]+")


def extraire_section(brut: str, section: str | None) -> str:
    if not section:
        return brut
    m = re.search(rf"^##\s+[^\n]*{re.escape(section)}[^\n]*\n(.*?)(?=^##\s|\Z)", brut, re.M | re.S | re.I)
    return m.group(1) if m else brut


def texte_markdown(brut: str) -> list[str]:
    """Les lignes de texte lisible d'un fichier Markdown : sans code, sans notes internes, sans tableaux de métadonnées."""
    brut = re.sub(r"```.*?```", "", brut, flags=re.S)
    lignes = []
    for ligne in brut.splitlines():
        s = ligne.strip()
        if not s or s.startswith(">") or s.startswith("<!--") or re.fullmatch(r"\|?[\s:|-]+\|?", s):
            continue
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
        s = re.sub(r"[*_`#]+", "", s).strip(" |")
        if s:
            lignes.append(s)
    return lignes


def texte_html(brut: str) -> list[str]:
    brut = re.sub(r"<(script|style|noscript)\b.*?</\1>", "", brut, flags=re.S | re.I)
    brut = re.sub(r"<(?:br|/p|/h\d|/li|/div|/tr)\b[^>]*>", "\n", brut, flags=re.I)
    return [s.strip() for s in re.sub(r"<[^>]+>", " ", brut).splitlines() if s.strip()]


def mesurer(lignes: list[str], brut: str, marque: str | None = None) -> dict:
    texte = "\n".join(lignes)
    mots = len(re.findall(r"\w+", texte))
    mille = max(mots, 1) / 1000
    phrases = [p.strip() for p in PHRASE.findall(texte.replace("\n", ". ")) if len(p.split()) >= 3]
    longueurs = [len(p.split()) for p in phrases] or [0]
    longues = [p for p in phrases if len(p.split()) > 28]

    def releve(motif: re.Pattern, maxi: int = 12) -> list[dict]:
        out = []
        for i, l in enumerate(lignes):
            for m in motif.finditer(l):
                out.append({"ligne": i + 1, "extrait": l[max(0, m.start() - 40):m.end() + 40].strip()})
        return out[:maxi] if maxi else out

    lecteur = len(LECTEUR.findall(texte))
    auteur = len(AUTEUR.findall(texte)) + (len(re.findall(re.escape(marque), texte, re.I)) if marque else 0)
    tirets = releve(TIRET, 0)
    negations = releve(NEGATION, 0)
    explicatif = releve(EXPLICATIF, 0)
    creux = releve(CREUX, 0)
    concret = len(CONCRET.findall(texte))

    # appels à l'action : lignes marquées (bouton, [CTA]) ou liens dont le libellé commence par un verbe d'action
    brut_lignes = brut.splitlines()
    ctas = []
    for i, l in enumerate(brut_lignes):
        libelles = re.findall(r"\[([^\]]{3,60})\]\([^)]*\)", l) + re.findall(r"`([^`]{3,60})`\s*→", l)
        if LIGNE_CTA.search(l) or any(VERBE_CTA.match(x.strip()) for x in libelles):
            ctas.append({"position": i / max(len(brut_lignes), 1), "ligne": l.strip()[:110]})
    haut = any(c["position"] <= 0.33 for c in ctas)
    bas = any(c["position"] >= 0.67 for c in ctas)

    # l'accroche : le premier vrai paragraphe (pas un libellé de gabarit « Sur-titre : », ni un fil d'Ariane)
    premier = next((l for l in lignes if len(l.split()) >= 12 and "›" not in l and "|" not in l and not l.startswith("[")
                    and not re.match(r"^[\w'’ -]{2,30} ?:", l)), "")
    accroche_ok = bool(premier) and len(premier.split()) <= 60 and bool(LECTEUR.search(premier))

    ratio = lecteur / max(auteur, 1)
    moy = sum(longueurs) / len(longueurs)
    part_longues = len(longues) / max(len(phrases), 1)
    criteres = {
        "tirets": (15, 15 if not tirets else max(0, 15 - 5 * len(tirets)),
                   f"{len(tirets)} tiret(s) cadratin(s) ou demi-cadratin(s) : zéro attendu"),
        "orientation_lecteur": (15, round(15 * min(1, ratio / 1.5)),
                                f"vous / votre / vos : {lecteur} · nous / notre / marque : {auteur} "
                                f"(ratio {ratio:.1f}, cible ≥ 1,5)"),
        "argumentaire_positif": (10, max(0, 10 - round(10 * (len(negations) / mille) / 6)),
                                 f"{len(negations)} négation(s), {len(negations) / mille:.1f} pour 1 000 mots "
                                 f"(au-delà de 6, le discours se vend par ce qu'il ne fait pas)"),
        "rythme": (15, round(15 * min(1, max(0, (26 - moy) / 8)) * (1 - min(1, part_longues / 0.3))),
                   f"phrase moyenne {moy:.1f} mots (cible 14 à 18) · {len(longues)} phrase(s) de plus de 28 mots "
                   f"({part_longues:.0%})"),
        "ton_vendeur": (15, max(0, 15 - round(15 * (len(explicatif) / mille) / 8)),
                        f"{len(explicatif)} tournure(s) explicative(s), {len(explicatif) / mille:.1f} pour 1 000 mots "
                        f"(« permet de », « afin de »… : cible ≤ 3)"),
        "promesses_concretes": (10, max(0, 10 - 2 * len(creux)),
                                f"{len(creux)} adjectif(s) creux (« innovant », « de qualité »…)"),
        "appels_a_l_action": (15, (5 if len(ctas) >= 3 else len(ctas) * 1) + (5 if haut else 0) + (5 if bas else 0),
                              f"{len(ctas)} appel(s) à l'action · en haut de page : {'oui' if haut else 'non'} · "
                              f"en fin de page : {'oui' if bas else 'non'}"),
        "accroche": (5, 5 if accroche_ok else 0,
                     "premier paragraphe : moins de 60 mots et adressé au lecteur" if accroche_ok
                     else f"premier paragraphe à reprendre : « {premier[:90]}… »"),
    }
    score = sum(v[1] for v in criteres.values())
    return {"score": score, "mots": mots, "concret_pour_1000": round(concret / mille, 1),
            "criteres": {k: {"sur": v[0], "points": v[1], "mesure": v[2]} for k, v in criteres.items()},
            "a_reprendre": {"tirets": tirets[:20], "negations": negations[:12], "explicatif": explicatif[:12],
                            "creux": creux[:12], "phrases_longues": longues[:8]},
            "appels_a_l_action": ctas}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("fichier", help="page .md ou .html")
    ap.add_argument("--section", help="ne mesurer que la section Markdown ## dont le titre contient ce texte")
    ap.add_argument("--marque", help="nom de la marque (compté avec « nous » dans l'orientation)")
    ap.add_argument("--seuil", type=int, default=80, help="score minimal attendu (défaut 80) : code retour 1 en dessous")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    brut = Path(a.fichier).read_text(encoding="utf-8")
    html = a.fichier.endswith((".html", ".htm"))
    if not html:
        brut = extraire_section(brut, a.section)
    lignes = texte_html(brut) if html else texte_markdown(brut)
    r = mesurer(lignes, brut, a.marque)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(f"Copywriting : {r['score']}/100 · {r['mots']} mots · exemples et cas : {r['concret_pour_1000']} pour 1 000 mots")
        for k, v in r["criteres"].items():
            print(f"  {'✓' if v['points'] >= v['sur'] * 0.8 else '✗'} {k.replace('_', ' '):<22} {v['points']:>2}/{v['sur']:<2} "
                  f"{v['mesure']}")
        for famille, items in r["a_reprendre"].items():
            if items:
                print(f"\n  À reprendre · {famille.replace('_', ' ')} :")
                for x in items[:8]:
                    print(f"    - {x['extrait'] if isinstance(x, dict) else x[:140]}")
    return 0 if r["score"] >= a.seuil else 1


if __name__ == "__main__":
    sys.exit(main())
