#!/usr/bin/env python3
"""L'empreinte de style du client, mesurée sur ses propres pages : memoire/style.md.

    python3 style_maison.py https://www.exemple.fr/blog/a https://www.exemple.fr/blog/b …
    python3 style_maison.py contenus/*.md --json
    python3 style_maison.py --liste urls.txt
    python3 style_maison.py                      # projet.pages_prioritaires de la config

Ce que le script mesure (et seulement ça) : longueur des phrases et des
paragraphes, part de phrases courtes et longues, questions, adresse au
lecteur (vouvoiement / tutoiement), personne (nous / je / impersonnel),
lisibilité (Kandel-Moles, indicatif), listes, tableaux, gras, H2 en
question, façon d'ouvrir et de conclure, expressions et vocabulaire qui
reviennent d'une page à l'autre.

Ce qu'il ne mesure pas : le registre, la voix, ce qui rend le texte
reconnaissable. Ça se lit. La section « Lecture » de memoire/style.md se
remplit à la main (ou par Claude après lecture des mêmes pages) et est
conservée quand on relance la mesure.

Sources : URL, fichiers .html, .md ou .txt. Choisir des pages écrites par
le client lui-même (articles, pages de service), pas des pages légales ni
des fiches produits générées. 5 à 10 pages suffisent. Sans dépendance.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _contenu as C  # noqa: E402
from _projet import lire_liste, lire_valeur, racine_projet  # noqa: E402

TITRE_LECTURE = "## Lecture"
LECTURE_VIDE = """## Lecture

> À remplir après avoir lu les pages mesurées. Le script mesure ; le
> registre et la voix se lisent. Cette section est conservée quand on
> relance `style_maison.py`.

- Registre (expert, pédagogique, corporate, conversationnel…) :
- Traits de voix (direct, chaleureux, factuel, imagé…) :
- Ce qui rend le texte reconnaissable :

**À faire pour écrire comme la maison**

-

**À éviter**

-
"""


def charger(source: str) -> dict:
    """Une source (URL ou fichier) lue comme une page. Lève C.PageIllisible."""
    if re.match(r"https?://", source):
        html, _ = C.telecharger(source)
        return C.lire_html(html, source)
    f = Path(source)
    if not f.is_file():
        raise C.PageIllisible("fichier introuvable")
    texte = f.read_text(encoding="utf-8", errors="replace")
    if f.suffix.lower() in (".html", ".htm"):
        return C.lire_html(texte, "")
    if f.suffix.lower() in (".md", ".markdown"):
        return C.lire_markdown(re.sub(r"\A---\n.*?\n---\n", "", texte, flags=re.S), "")
    return C.lire_texte_brut(texte, "")


def _pct(n: int, total: int) -> float | None:
    return round(n * 100 / total, 1) if total else None


def empreinte(pages: list[dict]) -> dict:
    """Les mesures de style agrégées sur l'ensemble des pages. Pur : aucun réseau."""
    paragraphes = [p for page in pages for p in page.get("paragraphes") or []]
    phrases = [ph for p in paragraphes for ph in C.decouper_phrases(p)]
    lp = [C.compter_mots(ph) for ph in phrases]
    lpar = [C.compter_mots(p) for p in paragraphes]
    texte = "\n".join(page.get("texte") or "" for page in pages)
    mots = sum(page.get("mots") or 0 for page in pages)
    h2 = [t for page in pages for n, t in page.get("plan") or [] if n == 2]
    ouvertures: dict[str, int] = {}
    for page in pages:
        o = C.ouverture(page)
        ouvertures[o] = ouvertures.get(o, 0) + 1
    listes = sum(p["listes"]["puces"] + p["listes"]["numerotees"] for p in pages)
    adresse = C.adresse_et_personne(texte)
    vocab, formes = C.termes(texte)
    docs: dict[str, int] = {}
    for page in pages:
        for k in set(C.termes(page.get("texte") or "")[0]):
            docs[k] = docs.get(k, 0) + 1
    seuil = 2 if len(pages) >= 2 else 1
    signature = sorted((k for k in vocab if " " not in k and docs.get(k, 0) >= seuil),
                       key=lambda k: (-docs[k], -vocab[k]))[:20]
    return {
        "pages": len(pages), "mots": mots, "phrases": len(phrases), "paragraphes": len(paragraphes),
        "phrase": {"moyenne": round(sum(lp) / len(lp), 1) if lp else None,
                   "mediane": C.mediane(lp),
                   "courtes_pct": _pct(sum(1 for n in lp if n <= 8), len(lp)),
                   "longues_pct": _pct(sum(1 for n in lp if n > 20), len(lp)),
                   "questions_pct": _pct(sum(1 for ph in phrases if ph.rstrip().endswith("?")), len(phrases)),
                   "exclamations_pct": _pct(sum(1 for ph in phrases if ph.rstrip().endswith("!")), len(phrases))},
        "paragraphe": {"mediane": C.mediane(lpar), "p75": C.centile(lpar, 75),
                       "phrases_mediane": C.mediane([len(C.decouper_phrases(p)) for p in paragraphes])},
        "lisibilite": C.lisibilite(paragraphes),
        "adresse": adresse,
        "listes_pour_1000": C.pour_mille(listes, mots),
        "gras_pour_1000": C.pour_mille(sum(p.get("gras") or 0 for p in pages), mots),
        "pages_avec_tableau": sum(1 for p in pages if p.get("tableaux")),
        "h2_questions_pct": _pct(sum(1 for t in h2 if t.rstrip().endswith("?")), len(h2)),
        "ouvertures": ouvertures,
        "clotures_avec_appel": sum(1 for p in pages if C.cloture_avec_appel(p)),
        **expressions_et_gabarit(C.ngrammes_recurrents([p.get("texte") or "" for p in pages]), len(pages)),
        "vocabulaire": [{"mot": formes[k], "pages": docs[k], "occurrences": vocab[k]} for k in signature],
        "fragile": len(pages) < 3 or mots < 1500,
    }


def expressions_et_gabarit(expressions: list[dict], nb_pages: int) -> dict:
    """Sépare les tics d'écriture des phrases posées par le gabarit du site.

    Une expression présente sur (presque) toutes les pages, à peu près une fois
    par page, vient d'un bloc répété (CTA, avertissement, pied d'article) : elle
    ne dit rien de la plume."""
    gabarit, style = [], []
    for x in expressions:
        repetee = nb_pages >= 5 and x["textes"] >= 0.85 * nb_pages and x["occurrences"] <= 2 * x["textes"]
        (gabarit if repetee else style).append(x)
    return {"expressions": style, "gabarit": gabarit}


def regles(e: dict, vouvoiement_config: str = "") -> list[str]:
    """Consignes d'écriture déduites des mesures — chacune dit d'où elle vient."""
    r = []
    a = e["adresse"]
    adr = {"vouvoiement": "Vouvoyer le lecteur", "tutoiement": "Tutoyer le lecteur",
           "impersonnel": "Ne pas interpeller le lecteur : tournures impersonnelles",
           "mixte": "Adresse au lecteur non tranchée : vérifier avec le client avant d'écrire"}[a["adresse"]]
    r.append(f"{adr} (vous {a['vous']} ‰ · tu {a['tu']} ‰).")
    if vouvoiement_config in ("true", "false"):
        attendu = "vouvoiement" if vouvoiement_config == "true" else "tutoiement"
        if a["adresse"] in ("vouvoiement", "tutoiement") and a["adresse"] != attendu:
            r.append(f"⚠ La config dit {attendu}, les pages mesurées disent {a['adresse']} : à trancher avec le client.")
    per = {"nous": "Parler au nom de l'entreprise (« nous »)", "je": "Parler à la première personne (« je »)",
           "impersonnel": "Pas de « nous » ni de « je » : l'entreprise ne se met pas en scène"}[a["personne"]]
    r.append(f"{per} (nous {a['nous']} ‰ · je {a['je']} ‰).")
    ph = e["phrase"]
    if ph["moyenne"]:
        r.append(f"Phrases de {ph['moyenne']:.0f} mots en moyenne (médiane {ph['mediane']:.0f}) ; "
                 f"{ph['courtes_pct']:.0f} % de 8 mots ou moins, {ph['longues_pct']:.0f} % de plus de 20 mots. "
                 "Garder ce rythme, à ±3 mots.")
    pa = e["paragraphe"]
    if pa["mediane"]:
        r.append(f"Paragraphes de {pa['mediane']:.0f} mots en médiane ({pa['phrases_mediane']:.0f} phrases), "
                 f"{pa['p75']:.0f} au plus dans trois cas sur quatre.")
    if ph["questions_pct"] is not None:
        r.append(f"Questions au lecteur : {ph['questions_pct']:.0f} % des phrases"
                 + (" — la maison en pose peu." if ph["questions_pct"] < 3 else "."))
    if e["h2_questions_pct"] is not None:
        r.append(f"H2 formulés en question : {e['h2_questions_pct']:.0f} %.")
    r.append(f"Listes : {e['listes_pour_1000']} pour 1 000 mots · gras : {e['gras_pour_1000']} pour 1 000 mots · "
             f"tableau sur {e['pages_avec_tableau']} page(s) sur {e['pages']}.")
    if e["ouvertures"]:
        dominante = max(e["ouvertures"].items(), key=lambda x: x[1])
        r.append(f"Ouverture la plus fréquente : {dominante[0]} ({dominante[1]}/{e['pages']}).")
    r.append(f"Conclusion avec appel à l'action : {e['clotures_avec_appel']}/{e['pages']} pages.")
    return r


def fichier_style(e: dict, sources: list[str], echecs: list[dict], date: str, lecture: str,
                  vouvoiement_config: str = "") -> str:
    L = ["# Style maison — mesuré", "",
         f"Mesuré le {date} sur {e['pages']} page(s), {e['mots']} mots, par `style_maison.py`. "
         "Relancer la mesure quand le site change de plume.", ""]
    if e["fragile"]:
        L += ["> ⚠ Empreinte fragile : moins de 3 pages ou moins de 1 500 mots. Ajouter des pages avant de s'y fier.", ""]
    L += ["## Règles déduites", ""] + [f"- {x}" for x in regles(e, vouvoiement_config)] + [""]
    ph, pa = e["phrase"], e["paragraphe"]
    L += ["## Mesures", "", "| Mesure | Valeur |", "|---|---|",
          f"| Phrase moyenne / médiane (mots) | {ph['moyenne']} / {ph['mediane']} |",
          f"| Phrases ≤ 8 mots / > 20 mots | {ph['courtes_pct']} % / {ph['longues_pct']} % |",
          f"| Questions / exclamations | {ph['questions_pct']} % / {ph['exclamations_pct']} % |",
          f"| Paragraphe médian / 3e quartile (mots) | {pa['mediane']} / {pa['p75']} |",
          f"| Lisibilité Kandel-Moles (indicatif) | {e['lisibilite'] if e['lisibilite'] is not None else 'n.d.'} |",
          f"| vous · tu · nous · je (pour 1 000 mots) | {e['adresse']['vous']} · {e['adresse']['tu']} · "
          f"{e['adresse']['nous']} · {e['adresse']['je']} |",
          f"| Ouvertures | {', '.join(f'{k} {v}' for k, v in e['ouvertures'].items())} |", ""]
    L += ["## Expressions qui reviennent", ""]
    L += [f"- « {x['expression']} » — {x['textes']} page(s), {x['occurrences']} fois" for x in e["expressions"]] \
        or ["- aucune expression récurrente détectée"]
    L += ["", "Les reprendre quand elles portent la marque ; les éviter quand ce sont des tics.", ""]
    if e.get("gabarit"):
        L += ["## Répété par le gabarit (hors style)", "",
              "Présent sur presque toutes les pages, une fois par page : CTA, avertissements, blocs communs. "
              "Ne pas l'imiter dans le texte.", ""]
        L += [f"- « {x['expression']} » — {x['textes']} page(s)" for x in e["gabarit"]] + [""]
    L += [
          "## Vocabulaire de la maison", "",
          ", ".join(f"{x['mot']} ({x['pages']})" for x in e["vocabulaire"]) or "—", ""]
    L += [lecture.rstrip(), "", "## Pages mesurées", ""] + [f"- {s}" for s in sources]
    if echecs:
        L += ["", "Non lues : " + " · ".join(f"{x['source']} ({x['raison']})" for x in echecs)]
    return "\n".join(L) + "\n"


def lecture_existante(chemin: Path) -> str:
    """La section « Lecture » d'un style.md existant : écrite à la main, elle ne s'écrase pas."""
    if not chemin.is_file():
        return LECTURE_VIDE
    texte = chemin.read_text(encoding="utf-8")
    m = re.search(rf"^{TITRE_LECTURE}\s*$(.*?)(?=^## |\Z)", texte, re.M | re.S)
    return f"{TITRE_LECTURE}\n{m.group(1).rstrip()}\n" if m else LECTURE_VIDE


def sources_par_defaut() -> list[str]:
    domaine = lire_valeur("projet.domaine").rstrip("/")
    pages = lire_liste("projet.pages_prioritaires")
    return [p if re.match(r"https?://", p) else f"{domaine}/{p.lstrip('/')}" for p in pages if p and domaine]


def main() -> int:
    from _projet import charger_env
    charger_env()
    ap = argparse.ArgumentParser(description="Empreinte de style mesurée sur les pages du client")
    ap.add_argument("sources", nargs="*", help="URL ou fichiers .html / .md / .txt")
    ap.add_argument("--liste", help="fichier texte : une URL ou un chemin par ligne")
    ap.add_argument("--max", type=int, default=12, help="pages lues au plus (défaut 12)")
    ap.add_argument("--sortie", help="défaut : memoire/style.md du projet")
    ap.add_argument("--json", action="store_true", help="mesures en JSON, sans écrire le fichier")
    a = ap.parse_args()

    sources = list(a.sources)
    if a.liste:
        sources += [l.strip() for l in Path(a.liste).read_text(encoding="utf-8").splitlines()
                    if l.strip() and not l.startswith("#")]
    sources = sources or sources_par_defaut()
    if not sources:
        print("✗ aucune source : passez des URL ou des fichiers, ou renseignez projet.pages_prioritaires",
              file=sys.stderr)
        return 2
    pages, lues, echecs = [], [], []
    for s in sources[:a.max]:
        try:
            p = charger(s)
        except C.PageIllisible as exc:
            echecs.append({"source": s, "raison": str(exc)})
            print(f"  · {s} — {exc}", file=sys.stderr)
            continue
        if p["mots"] < 150:
            echecs.append({"source": s, "raison": f"{p['mots']} mots lus"})
            print(f"  · {s} — {p['mots']} mots lus, ignorée", file=sys.stderr)
            continue
        pages.append(p)
        lues.append(s)
        print(f"  ✓ {s} — {p['mots']} mots", file=sys.stderr)
    if not pages:
        print("✗ aucune page lisible", file=sys.stderr)
        return 1
    e = empreinte(pages)
    vouv = lire_valeur("projet.vouvoiement").lower()
    if a.json:
        print(json.dumps({"empreinte": e, "regles": regles(e, vouv), "sources": lues, "echecs": echecs},
                         ensure_ascii=False, indent=1))
        return 0
    cible = Path(a.sortie) if a.sortie else racine_projet() / "memoire" / "style.md"
    cible.parent.mkdir(parents=True, exist_ok=True)
    cible.write_text(fichier_style(e, lues, echecs, dt.date.today().isoformat(), lecture_existante(cible), vouv),
                     encoding="utf-8")
    print(f"  ✓ {cible}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
