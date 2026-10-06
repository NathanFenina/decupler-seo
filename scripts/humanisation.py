#!/usr/bin/env python3
"""Mesure les tics d'écriture générée d'un texte français : score sur 100 et signaux à réécrire.

    python3 humanisation.py contenus/guide.md
    python3 humanisation.py page.html --json
    cat brouillon.txt | python3 humanisation.py -
    python3 humanisation.py contenus/guide.md --seuil 25        # code 1 si score > 25
    python3 humanisation.py --avant v1.md --apres v2.md         # comparatif avant / après

Le score va de 0 (aucun tic relevé) à 100. Il additionne huit familles :
vocabulaire de modèle, structures (triades, « ce n'est pas X, c'est Y »,
questions en série, titres en Majuscule Initiale), ponctuation (tirets
cadratins, deux-points en cascade, emojis), mise en forme (puces qui
commencent par du gras), rythme (phrases de longueur uniforme), flou
(sources vagues, superlatifs, pourcentages ronds sans source), ton (promo,
précautions réflexes) et ouvertures / conclusions génériques. Chaque signal
porte sa ligne et son extrait : c'est la liste de ce qu'il faut réécrire.

Ce n'est pas un détecteur d'IA et il ne dit pas si un texte « passera » un
détecteur : il repère des tournures qui affaiblissent un texte, quelle que
soit sa plume. Un score bas ne prouve rien sur l'origine du texte.

Les marqueurs vivent dans config/marqueurs-ia-fr.json (méthode, remplacé à
chaque synchronisation). Un projet ajoute ou ignore des marqueurs dans
memoire/marqueurs-ia.json :

    {"ignorer": ["levier"], "ajouter": {"vocabulaire": ["\\\\bbest-seller\\\\b"]},
     "familles_ignorees": ["ponctuation"]}

En comparatif, les nombres présents après et absents avant sont signalés et
le code de sortie vaut 1 : une passe d'humanisation n'ajoute aucun chiffre.
Sans dépendance (Python 3.9+).
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _contenu as C  # noqa: E402
from _projet import racine_projet  # noqa: E402

MARQUEURS = Path(__file__).resolve().parent.parent / "config" / "marqueurs-ia-fr.json"
MARQUEURS_PROJET = Path("memoire") / "marqueurs-ia.json"

POINTS = {"vocabulaire": 20, "structures": 15, "ponctuation": 15, "mise_en_forme": 10,
          "rythme": 10, "flou": 10, "ton": 10, "ouverture_cloture": 10}
LIBELLES = {"structures": "Structures répétitives", "ponctuation": "Ponctuation",
            "mise_en_forme": "Mise en forme", "rythme": "Rythme"}
CONSEILS = {
    "structures": "Garder une énumération quand il y a vraiment trois choses ; dire Y directement "
                  "plutôt que « ce n'est pas X » ; une question au plus, suivie de sa réponse ; "
                  "titres en minuscules à la française.",
    "ponctuation": "Remplacer le tiret cadratin par une virgule, des parenthèses ou un point ; "
                   "un deux-points par phrase au plus ; aucun emoji dans un contenu éditorial.",
    "mise_en_forme": "Transformer les puces « **Terme** : explication » en phrases ; "
                     "le gras pour un mot qu'on doit voir, pas pour chaque début de ligne.",
    "rythme": "Alterner phrases courtes et longues, au rythme mesuré dans memoire/style.md ; "
              "couper ou fusionner les paragraphes qui ont tous la même taille.",
}
NIVEAUX = ((15, "faible"), (35, "modéré"), (101, "élevé"))

MOTS_OUTILS = {"le", "la", "les", "un", "une", "des", "du", "de", "et", "ou", "en", "à", "au", "aux",
               "pour", "par", "sur", "dans", "avec", "son", "sa", "ses", "vos", "votre", "nos", "notre",
               "qui", "que", "est", "sont"}
TRIADE = re.compile(r"\b[\w'-]+(?: [\w'-]+){0,2}, [\w'-]+(?: [\w'-]+){0,2},? et [\w'-]+", re.I)
NEGATION = re.compile(
    r"\b(?:n'est|n'était|ne sont|ne s'agit) pas\b[^\n]{0,100}?"
    r"(?:[,.;:]\s*(?:c'est|ce sont|il s'agit|mais)\b)"
    r"|\bnon seulement\b[^\n]{0,120}?\bmais (?:aussi|également|encore)\b"
    r"|\bpas (?:seulement|uniquement|simplement)\b[^\n]{0,120}?\bmais\b", re.I)
TIRET = re.compile(r"—|\s–\s")
DEUX_POINTS = re.compile(r"(?<!\d):(?!//)|(?<=\d):(?![\d/])")
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF⭐⬆⬇↔-↪]")
POURCENTAGE_ROND = re.compile(r"\b(?:[1-9][05]|100)\s?%")
SOURCE = re.compile(r"https?://|\]\(|\bsources?\b|\bd'après\b|\b(?:19|20)\d{2}\b|\bétude (?:de|du|d')\b",
                    re.I)
SOURCE_SELON = re.compile(r"\bselon [A-ZÀ-Ý]")
GUILLEMETS = re.compile(r"«[^»]*»|“[^”]*”")
NOMBRE = re.compile(r"\d+(?:[.,   ]\d+)*")
A_COMPLETER = re.compile(r"\[à compléter", re.I)


# ─── Lecture ──────────────────────────────────────────────────────

def lire_source(chemin: str) -> tuple[str, str]:
    """(format, contenu brut) d'un fichier ou de l'entrée standard (« - »)."""
    if chemin == "-":
        brut = sys.stdin.read()
        fmt = "html" if re.search(r"<(?:p|div|h[1-6]|li|article|main|body)\b", brut, re.I) else "md"
        return fmt, brut
    f = Path(chemin)
    if not f.is_file():
        raise FileNotFoundError(chemin)
    brut = f.read_text(encoding="utf-8", errors="replace")
    suffixe = f.suffix.lower()
    if suffixe in (".html", ".htm"):
        return "html", brut
    if suffixe in (".md", ".markdown"):
        return "md", brut
    return "txt", brut


def _garder_lignes(m: re.Match) -> str:
    return "\n" * m.group(0).count("\n")


def lignes_texte(brut: str, fmt: str) -> list[str]:
    """Le texte lisible, ligne pour ligne : la ligne n du résultat est la ligne n du fichier."""
    texte = brut.replace("’", "'")
    if fmt == "html":
        texte = re.sub(r"<(script|style|noscript|svg)\b.*?</\1>", _garder_lignes, texte, flags=re.S | re.I)
        texte = re.sub(r"<!--.*?-->", _garder_lignes, texte, flags=re.S)
        texte = re.sub(r"<[^>]+>", lambda m: " " + _garder_lignes(m), texte)
        return [html_lib.unescape(l) for l in texte.split("\n")]
    lignes = texte.split("\n")
    if fmt == "md":
        if lignes and lignes[0].strip() == "---":
            for i in range(1, len(lignes)):
                if lignes[i].strip() == "---":
                    lignes[:i + 1] = [""] * (i + 1)
                    break
        dans_code = False
        for i, l in enumerate(lignes):
            if l.lstrip().startswith("```"):
                dans_code = not dans_code
                lignes[i] = ""
            elif dans_code:
                lignes[i] = ""
            else:
                l = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", l)
                lignes[i] = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", l)
    return lignes


def lire_page(brut: str, fmt: str) -> dict:
    if fmt == "html":
        return C.lire_html(brut, "")
    if fmt == "md":
        return C.lire_markdown(re.sub(r"\A---\n.*?\n---\n", "", brut, flags=re.S), "")
    return C.lire_texte_brut(brut, "")


def charger_marqueurs(fichier: Path | None = None) -> dict:
    """Les marqueurs de la méthode, complétés par ceux du projet (memoire/marqueurs-ia.json)."""
    base = json.loads((fichier or MARQUEURS).read_text(encoding="utf-8"))
    projet = racine_projet() / MARQUEURS_PROJET
    base.setdefault("ignorer", [])
    base.setdefault("familles_ignorees", [])
    if projet.is_file():
        extra = json.loads(projet.read_text(encoding="utf-8"))
        base["ignorer"] += [t.lower() for t in extra.get("ignorer", [])]
        base["familles_ignorees"] += extra.get("familles_ignorees", [])
        for famille, motifs in (extra.get("ajouter") or {}).items():
            if famille in base["familles"]:
                base["familles"][famille].setdefault("motifs", []).extend({"motif": m} for m in motifs)
    return base


# ─── Repérage ─────────────────────────────────────────────────────

def _extrait(ligne: str, debut: int, fin: int, marge: int = 35) -> str:
    a, b = max(0, debut - marge), min(len(ligne), fin + marge)
    s = re.sub(r"\s+", " ", ligne[a:b]).strip()
    return ("…" if a else "") + s + ("…" if b < len(ligne) else "")


def _cite(ligne: str, debut: int) -> bool:
    """Le passage est-il entre guillemets (une expression citée, pas employée) ?"""
    return any(m.start() < debut < m.end() for m in GUILLEMETS.finditer(ligne))


def _normal(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*_`#>]", "", s)).strip().lower()


def ligne_de(lignes: list[str], extrait: str) -> int | None:
    """La première ligne qui contient le début d'un paragraphe ou d'un titre (numérotée à partir de 1)."""
    cle = _normal(extrait)[:30]
    mots = " ".join(cle.split()[:3])
    for cible in (cle, mots):
        if not cible:
            continue
        for i, l in enumerate(lignes):
            if cible in _normal(l):
                return i + 1
    return None


def signal(famille: str, ligne: int | None, extrait: str, raison: str) -> dict:
    return {"famille": famille, "ligne": ligne, "extrait": extrait, "raison": raison}


def chercher_motifs(lignes: list[str], famille: str, motifs: list[dict], ignorer: list[str]) -> tuple[float, list]:
    poids_total, trouves = 0.0, []
    compiles = []
    for m in motifs:
        try:
            compiles.append((re.compile(m["motif"], re.I), float(m.get("poids", 1))))
        except re.error as exc:
            print(f"  ! motif ignoré « {m['motif']} » : {exc}", file=sys.stderr)
    for n, ligne in enumerate(lignes, 1):
        pris: list[tuple[int, int]] = []
        for motif, poids in compiles:
            for m in motif.finditer(ligne):
                if _cite(ligne, m.start()) or any(a < m.end() and m.start() < b for a, b in pris):
                    continue
                if any(t in m.group(0).lower() for t in ignorer):
                    continue
                pris.append((m.start(), m.end()))
                poids_total += poids
                trouves.append(signal(famille, n, _extrait(ligne, m.start(), m.end()), f"« {m.group(0)} »"))
    return poids_total, trouves


def _borne(x: float) -> float:
    return max(0.0, min(1.0, x))


def titre_a_l_anglaise(titre: str) -> bool:
    """« Comment Choisir Son Expert-Comptable » : Majuscule Initiale à chaque mot."""
    mots = re.findall(r"[^\W\d_][\w'-]*", titre)[1:]
    if any(m.lower() in MOTS_OUTILS and m[0].isupper() and not m.isupper() for m in mots):
        return True
    pleins = [m for m in mots if len(m) > 3 and not m.isupper()]
    return len(pleins) >= 3 and sum(m[0].isupper() for m in pleins) / len(pleins) >= 0.75


# ─── Familles ─────────────────────────────────────────────────────

def familles_lexicales(lignes, marqueurs, base) -> dict:
    res = {}
    seuils = {"vocabulaire": 8, "flou": 5, "ton": 5}
    for nom in ("vocabulaire", "flou", "ton"):
        f = marqueurs["familles"][nom]
        poids, sig = chercher_motifs(lignes, nom, f.get("motifs", []), marqueurs["ignorer"])
        detail = {"occurrences": len(sig)}
        if nom == "flou":
            ronds = 0
            for n, l in enumerate(lignes, 1):
                for m in POURCENTAGE_ROND.finditer(l):
                    if not (SOURCE.search(l) or SOURCE_SELON.search(l)) and not _cite(l, m.start()):
                        ronds += 1
                        sig.append(signal(nom, n, _extrait(l, m.start(), m.end()),
                                          f"pourcentage rond sans source « {m.group(0)} »"))
            poids += 0.5 * ronds
            detail["pourcentages_ronds_sans_source"] = ronds
        if nom == "ton":
            excl = 0
            for n, l in enumerate(lignes, 1):
                k = l.count("!")
                if k:
                    excl += k
                    sig.append(signal(nom, n, _extrait(l, l.index("!"), l.index("!") + 1), "point d'exclamation"))
            poids += 0.5 * excl
            detail["exclamations"] = excl
        detail["pour_1000_mots"] = round(poids / base, 1)
        res[nom] = {"intensite": _borne(poids / base / seuils[nom]), "detail": detail, "signaux": sig}
    return res


def famille_structures(lignes, page, base) -> dict:
    sig, triades, negations = [], 0, 0
    for n, l in enumerate(lignes, 1):
        if l.lstrip().startswith(("#", "|")):
            continue
        for m in TRIADE.finditer(l):
            triades += 1
            sig.append(signal("structures", n, _extrait(l, m.start(), m.end(), 15), "énumération en trois"))
        for m in NEGATION.finditer(l):
            if not _cite(l, m.start()):
                negations += 1
                sig.append(signal("structures", n, _extrait(l, m.start(), m.end(), 10),
                                  "« ce n'est pas X, c'est Y » : dire Y directement"))
    series = 0
    for p in page["paragraphes"]:
        questions = [ph for ph in C.decouper_phrases(p) if ph.rstrip().endswith("?")]
        if len(questions) >= 2:
            series += 1
            sig.append(signal("structures", ligne_de(lignes, p), _extrait(questions[0], 0, len(questions[0]), 0),
                              f"{len(questions)} questions rhétoriques dans le même paragraphe"))
    titres = [t for _, t in page["plan"] if len(t.split()) >= 3]
    anglais = [t for t in titres if titre_a_l_anglaise(t)]
    for t in anglais:
        sig.append(signal("structures", ligne_de(lignes, t), t, "titre en Majuscule Initiale À L'Anglaise"))
    part_titres = len(anglais) / len(titres) if titres else 0.0
    triades_1000 = triades / base
    intensite = (_borne((triades_1000 - 3) / 7) + 0.3 * negations + 0.3 * series + 0.6 * part_titres)
    return {"intensite": _borne(intensite), "signaux": sig,
            "detail": {"triades": triades, "triades_pour_1000_mots": round(triades_1000, 1),
                       "ce_n_est_pas_c_est": negations, "questions_en_serie": series,
                       "titres_majuscules": f"{len(anglais)}/{len(titres)}"}}


def famille_ponctuation(lignes, base) -> dict:
    sig, tirets, deux_points, cascades, emojis = [], 0, 0, 0, 0
    for n, l in enumerate(lignes, 1):
        for m in TIRET.finditer(l):
            tirets += 1
            sig.append(signal("ponctuation", n, _extrait(l, m.start(), m.end(), 25), "tiret cadratin"))
        k = len(DEUX_POINTS.findall(l))
        deux_points += k
        if k >= 2:
            cascades += 1
            sig.append(signal("ponctuation", n, _extrait(l, 0, 0, 70), f"{k} deux-points sur la même ligne"))
        for m in EMOJI.finditer(l):
            emojis += 1
            sig.append(signal("ponctuation", n, _extrait(l, m.start(), m.end(), 15), "emoji"))
    t1000, d1000 = tirets / base, deux_points / base
    intensite = (0.6 * _borne((t1000 - 1) / 5) + 0.4 * _borne((d1000 - 5) / 12)
                 + 0.1 * cascades + 0.15 * emojis)
    return {"intensite": _borne(intensite), "signaux": sig,
            "detail": {"tirets_cadratins": tirets, "tirets_pour_1000_mots": round(t1000, 1),
                       "deux_points": deux_points, "deux_points_pour_1000_mots": round(d1000, 1),
                       "lignes_a_plusieurs_deux_points": cascades, "emojis": emojis}}


PUCE_MD = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
PUCE_MD_GRAS = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?:\*\*|__)[^*_]+(?:\*\*|__)\s*:?")
PUCE_HTML = re.compile(r"<li\b[^>]*>", re.I)
PUCE_HTML_GRAS = re.compile(r"<li\b[^>]*>\s*(?:<p\b[^>]*>\s*)?<(?:strong|b)\b", re.I)
GRAS = re.compile(r"\*\*[^*\n]+\*\*|<(?:strong|b)\b", re.I)


def famille_mise_en_forme(brut, fmt, lignes, base) -> dict:
    sources = brut.replace("’", "'").split("\n")
    items = gras_tete = 0
    sig = []
    for n, l in enumerate(sources, 1):
        if fmt == "html":
            items += len(PUCE_HTML.findall(l))
            k = len(PUCE_HTML_GRAS.findall(l))
        else:
            items += 1 if PUCE_MD.match(l) else 0
            k = 1 if PUCE_MD_GRAS.match(l) else 0
        if k:
            gras_tete += k
            texte = lignes[n - 1] if n - 1 < len(lignes) else l
            sig.append(signal("mise_en_forme", n, _extrait(texte.strip(), 0, 0, 60), "puce qui commence par du gras"))
    gras = sum(len(GRAS.findall(l)) for l in sources)
    part = gras_tete / items if items >= 3 else 0.0
    g1000 = gras / base
    intensite = part + 0.5 * _borne((g1000 - 10) / 20)
    return {"intensite": _borne(intensite), "signaux": sig if items >= 3 else [],
            "detail": {"puces": items, "puces_en_gras": gras_tete, "part_puces_en_gras": round(part, 2),
                       "gras_pour_1000_mots": round(g1000, 1)}}


def famille_rythme(lignes, page) -> dict:
    paragraphes = page["paragraphes"]
    longueurs = [C.compter_mots(ph) for p in paragraphes for ph in C.decouper_phrases(p)]
    sig, detail = [], {"phrases": len(longueurs)}
    i_phrases = i_paras = 0.0
    if len(longueurs) >= 8:
        moyenne = statistics.mean(longueurs)
        ecart = statistics.pstdev(longueurs)
        cv = ecart / moyenne if moyenne else 0.0
        detail.update({"phrase_moyenne": round(moyenne, 1), "ecart_type": round(ecart, 1),
                       "variation": round(cv, 2)})
        i_phrases = _borne((0.5 - cv) / 0.25)
    tailles = [C.compter_mots(p) for p in paragraphes]
    if len(tailles) >= 4:
        moyenne_p = statistics.mean(tailles)
        cvp = statistics.pstdev(tailles) / moyenne_p if moyenne_p else 0.0
        detail["variation_paragraphes"] = round(cvp, 2)
        i_paras = _borne((0.3 - cvp) / 0.2)
    for p in paragraphes:
        l = [C.compter_mots(ph) for ph in C.decouper_phrases(p)]
        if len(l) >= 3 and max(l) - min(l) <= 4:
            sig.append(signal("rythme", ligne_de(lignes, p), _extrait(p, 0, 0, 70),
                              f"{len(l)} phrases de même longueur ({min(l)} à {max(l)} mots)"))
    if i_paras > 0.5:
        sig.append(signal("rythme", None, f"paragraphes de {min(tailles)} à {max(tailles)} mots",
                          "paragraphes de taille quasi identique"))
    return {"intensite": _borne(0.7 * i_phrases + 0.3 * i_paras), "signaux": sig, "detail": detail}


def famille_ouverture_cloture(lignes, page, marqueurs) -> dict:
    f = marqueurs["familles"]["ouverture_cloture"]
    ouv = re.compile(r"^\W*(?:" + "|".join(f.get("ouvertures", [])) + r")\b", re.I)
    clo = re.compile(r"^\W*(?:" + "|".join(f.get("clotures", [])) + r")(?!\w)", re.I)
    paragraphes = [p.replace("’", "'") for p in page["paragraphes"]]
    sig = []
    for p in paragraphes[:2]:
        if m := ouv.search(p):
            sig.append(signal("ouverture_cloture", ligne_de(lignes, p), _extrait(p, 0, m.end(), 50),
                              "ouverture générique"))
    for p in paragraphes[-3:]:
        for ph in C.decouper_phrases(p):
            if m := clo.search(ph):
                sig.append(signal("ouverture_cloture", ligne_de(lignes, ph), _extrait(ph, 0, m.end(), 50),
                                  "conclusion-résumé"))
    noms = {t.lower() for t in f.get("titres_conclusion", [])}
    for _, t in page["plan"]:
        if t.strip().lower().rstrip(" :") in noms:
            sig.append(signal("ouverture_cloture", ligne_de(lignes, t), t, "titre « Conclusion »"))
    return {"intensite": _borne(0.5 * len(sig)), "signaux": sig, "detail": {"occurrences": len(sig)}}


# ─── Analyse ──────────────────────────────────────────────────────

def phrase_moyenne_maison() -> float | None:
    """La phrase moyenne mesurée par style_maison.py dans memoire/style.md, si le projet en a une."""
    f = racine_projet() / "memoire" / "style.md"
    if not f.is_file():
        return None
    m = re.search(r"Phrase moyenne / médiane \(mots\)\s*\|\s*([\d.]+)", f.read_text(encoding="utf-8"))
    return float(m.group(1)) if m else None


def niveau(score: int) -> str:
    return next(nom for borne, nom in NIVEAUX if score <= borne)


def analyser(brut: str, fmt: str, marqueurs: dict | None = None) -> dict:
    """Score, détail par famille et signaux d'un texte. Pur : aucun réseau, aucune écriture."""
    marqueurs = marqueurs or charger_marqueurs()
    lignes = lignes_texte(brut, fmt)
    page = lire_page(brut, fmt)
    mots = C.compter_mots("\n".join(lignes))
    base = max(mots, 300) / 1000
    resultats = familles_lexicales(lignes, marqueurs, base)
    resultats["structures"] = famille_structures(lignes, page, base)
    resultats["ponctuation"] = famille_ponctuation(lignes, base)
    resultats["mise_en_forme"] = famille_mise_en_forme(brut, fmt, lignes, base)
    resultats["rythme"] = famille_rythme(lignes, page)
    resultats["ouverture_cloture"] = famille_ouverture_cloture(lignes, page, marqueurs)
    familles, signaux = {}, []
    for nom, maxi in POINTS.items():
        r = resultats[nom]
        ignoree = nom in marqueurs["familles_ignorees"]
        points = 0 if ignoree else round(r["intensite"] * maxi, 1)
        libelle = marqueurs["familles"].get(nom, {}).get("libelle") or LIBELLES[nom]
        conseil = marqueurs["familles"].get(nom, {}).get("conseil") or CONSEILS[nom]
        familles[nom] = {"libelle": libelle, "points": points, "max": maxi, "ignoree": ignoree,
                         "detail": r["detail"], "conseil": conseil}
        if not ignoree:
            signaux += r["signaux"]
    signaux.sort(key=lambda s: (s["ligne"] is None, s["ligne"] or 0))
    score = round(sum(f["points"] for f in familles.values()))
    maison = phrase_moyenne_maison()
    moyenne = familles["rythme"]["detail"].get("phrase_moyenne")
    return {"score": score, "niveau": niveau(score), "mots": mots,
            "phrases": familles["rythme"]["detail"]["phrases"], "familles": familles, "signaux": signaux,
            "a_completer": len(A_COMPLETER.findall(brut)),
            "style_maison": {"phrase_moyenne_maison": maison, "phrase_moyenne_texte": moyenne,
                             "ecart": round(moyenne - maison, 1) if maison and moyenne else None}}


def nombres(brut: str, fmt: str) -> set[str]:
    texte = "\n".join(lignes_texte(brut, fmt))
    return {re.sub(r"[   ]", "", n).replace(",", ".") for n in NOMBRE.findall(texte)}


def comparer(avant: tuple[str, str], apres: tuple[str, str], marqueurs: dict) -> dict:
    a, b = analyser(avant[1], avant[0], marqueurs), analyser(apres[1], apres[0], marqueurs)
    na, nb = nombres(avant[1], avant[0]), nombres(apres[1], apres[0])
    return {"avant": a, "apres": b, "delta": b["score"] - a["score"],
            "familles": {k: [a["familles"][k]["points"], b["familles"][k]["points"]] for k in POINTS},
            "mots": [a["mots"], b["mots"]],
            "chiffres": {"disparus": sorted(na - nb), "apparus": sorted(nb - na)}}


# ─── Sortie ───────────────────────────────────────────────────────

def _virgule(x: float) -> str:
    return f"{x:g}".replace(".", ",")


def texte_rapport(r: dict, nom: str, maxi_signaux: int) -> str:
    L = [f"Tics IA · {nom} : {r['score']}/100 ({r['niveau']}) · {r['mots']} mots · {r['phrases']} phrases", ""]
    for k, f in r["familles"].items():
        d = " · ".join(f"{c.replace('_', ' ')} {v}" for c, v in f["detail"].items())
        etat = "ignorée" if f["ignoree"] else f"{_virgule(f['points'])}/{f['max']}"
        L.append(f"  {f['libelle']:<45} {etat:>8}   {d}")
    sm = r["style_maison"]
    if sm["phrase_moyenne_maison"] and sm["phrase_moyenne_texte"]:
        ecart = sm["ecart"]
        L += ["", f"  Rythme maison (memoire/style.md) : {_virgule(sm['phrase_moyenne_maison'])} mots par phrase ; "
                  f"texte : {_virgule(sm['phrase_moyenne_texte'])}"
              + (" (écart > 3 mots : à corriger)" if abs(ecart) > 3 else " (dans la cible)")]
    if r["a_completer"]:
        L += ["", f"  {r['a_completer']} marqueur(s) [À COMPLÉTER] : matière à demander au client."]
    if r["signaux"]:
        L += ["", f"Signaux à réécrire ({len(r['signaux'])}) :"]
        for s in r["signaux"][:maxi_signaux]:
            ligne = f"L{s['ligne']}" if s["ligne"] else "  —"
            L.append(f"  {ligne:>5}  {s['famille']:<17} {s['raison']} · {s['extrait']}")
        if len(r["signaux"]) > maxi_signaux:
            L.append(f"  … {len(r['signaux']) - maxi_signaux} autre(s) : --json pour la liste complète")
        conseils = [f"{r['familles'][k]['libelle']} : {r['familles'][k]['conseil']}"
                    for k in POINTS if r["familles"][k]["points"] >= 0.3 * r["familles"][k]["max"]]
        if conseils:
            L += ["", "À faire :"] + [f"  - {c}" for c in conseils]
    else:
        L += ["", "Aucun signal relevé."]
    return "\n".join(L)


def texte_comparatif(c: dict, noms: tuple[str, str], maxi_signaux: int) -> str:
    a, b = c["avant"], c["apres"]
    L = [f"Avant · {noms[0]} : {a['score']}/100 ({a['niveau']})",
         f"Après · {noms[1]} : {b['score']}/100 ({b['niveau']})  →  {c['delta']:+d} points", ""]
    for k, (pa, pb) in c["familles"].items():
        L.append(f"  {a['familles'][k]['libelle']:<45} {_virgule(pa):>5} → {_virgule(pb):<5}")
    variation = (c["mots"][1] - c["mots"][0]) * 100 / c["mots"][0] if c["mots"][0] else 0
    L += ["", f"  Mots : {c['mots'][0]} → {c['mots'][1]} ({variation:+.0f} %)"
          + ("  ! beaucoup de texte retiré : vérifier qu'aucune information n'a disparu" if variation < -30 else "")]
    if c["chiffres"]["apparus"]:
        L.append("  ✗ Chiffres apparus après la passe (interdit sans source) : " + ", ".join(c["chiffres"]["apparus"]))
    if c["chiffres"]["disparus"]:
        L.append("  ! Chiffres disparus (vérifier que le fond est intact) : " + ", ".join(c["chiffres"]["disparus"]))
    if not c["chiffres"]["apparus"] and not c["chiffres"]["disparus"]:
        L.append("  ✓ Mêmes chiffres avant et après")
    L += ["", texte_rapport(b, noms[1], maxi_signaux)]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description="Score des tics d'écriture générée d'un texte français (0 = aucun)")
    ap.add_argument("fichier", nargs="?", help="fichier .md, .html ou .txt ; « - » pour l'entrée standard")
    ap.add_argument("--avant", help="comparatif : version avant la passe")
    ap.add_argument("--apres", help="comparatif : version après la passe")
    ap.add_argument("--seuil", type=float, help="code de sortie 1 si le score (après) dépasse ce seuil")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--marqueurs", help="autre fichier de marqueurs (défaut : config/marqueurs-ia-fr.json)")
    ap.add_argument("--max-signaux", type=int, default=40, help="signaux affichés en texte (défaut 40)")
    a = ap.parse_args()

    if bool(a.avant) != bool(a.apres):
        ap.error("--avant et --apres vont ensemble")
    if not a.avant and not a.fichier:
        if sys.stdin.isatty():
            ap.error("passez un fichier, « - » pour l'entrée standard, ou --avant / --apres")
        a.fichier = "-"
    try:
        marqueurs = charger_marqueurs(Path(a.marqueurs) if a.marqueurs else None)
        if a.avant:
            c = comparer(lire_source(a.avant), lire_source(a.apres), marqueurs)
            print(json.dumps(c, ensure_ascii=False, indent=1) if a.json
                  else texte_comparatif(c, (a.avant, a.apres), a.max_signaux))
            score, invente = c["apres"]["score"], bool(c["chiffres"]["apparus"])
        else:
            fmt, brut = lire_source(a.fichier)
            r = analyser(brut, fmt, marqueurs)
            print(json.dumps(r, ensure_ascii=False, indent=1) if a.json
                  else texte_rapport(r, "entrée standard" if a.fichier == "-" else a.fichier, a.max_signaux))
            score, invente = r["score"], False
    except FileNotFoundError as exc:
        print(f"✗ fichier introuvable : {exc}", file=sys.stderr)
        return 2
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"✗ fichier de marqueurs illisible : {exc}", file=sys.stderr)
        return 2
    if a.seuil is not None and score > a.seuil:
        print(f"✗ score {score} > seuil {a.seuil:g} : passe d'humanisation à refaire", file=sys.stderr)
        return 1
    if invente:
        print("✗ des chiffres sont apparus pendant la passe : à sourcer ou à retirer", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
