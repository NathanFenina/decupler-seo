#!/usr/bin/env python3
"""Classe les cibles d'une campagne de netlinking : qui contacter, dans quel ordre.

    python3 netlinking_score.py recherche/netlinking/cibles.json
    python3 netlinking_score.py prospects.csv --offre analyse --json
    python3 netlinking_score.py cibles.json --min 50

Le score n'est pas une autorité déguisée. Un site à forte autorité qui ne
répond jamais vaut moins qu'un petit site qui dit oui la semaine suivante :
l'autorité est pondérée par la probabilité réelle d'obtenir le lien.

Score /100 = pertinence 40 + autorité 25 + accessibilité 20 + trafic 15.
  - pertinence (0-40) et accessibilité (0-20) : notées à la main, champ par
    cible, avec la donnée qui les justifie dans `preuve` ;
  - autorité (DA ou DR de l'outil, 1-100) et trafic organique estimé : en
    échelle logarithmique. Passer de 10 à 30 change tout, de 70 à 90 beaucoup
    moins ; une échelle linéaire écraserait le bas du classement, là où sont
    les liens qu'on obtient sans budget.

Écartées d'office, avec leur raison (jamais classées) :
  - autorité ≤ 1 et aucun backlink ni domaine référent : ce n'est pas un
    mauvais profil, c'est une absence de donnée (domaine mort, ou hors index
    de l'outil) ;
  - les cibles listées dans `ecartes` du fichier.

Entrée : un JSON {"mesure", "source_metriques", "cibles": [...], "ecartes": [...]}
ou un CSV dont chaque ligne est une cible. Champs d'une cible : domaine, da,
trafic (vide = inconnu, compté 0 : on ne devine pas), ref_domains, backlinks,
pertinence, accessibilite, offre, demande, page_visee, cout, preuve.

Bibliothèque standard uniquement.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

AXES = {"pertinence": 40, "autorite": 25, "accessibilite": 20, "trafic": 15}


class ErreurCibles(Exception):
    """Erreur présentable telle quelle."""


def _nombre(valeur) -> float | None:
    if valeur is None or (isinstance(valeur, str) and not valeur.strip()):
        return None
    try:
        return float(str(valeur).replace(" ", "").replace(" ", "").replace(",", "."))
    except ValueError:
        return None


def note_autorite(da) -> float:
    """Autorité 1-100 → 0-25, en log10 (DA 10 → 12,5 ; DA 100 → 25)."""
    d = max(_nombre(da) or 1.0, 1.0)
    return round(min(AXES["autorite"], AXES["autorite"] * math.log10(d) / 2.0), 1)


def note_trafic(trafic) -> float:
    """Trafic organique estimé → 0-15, en log10 (10 000 visites → 15). Inconnu = 0."""
    t = _nombre(trafic)
    if t is None:
        return 0.0
    return round(min(AXES["trafic"], AXES["trafic"] * math.log10(max(t, 1.0)) / 4.0), 1)


def _borne(valeur, maxi: int) -> float:
    return max(0.0, min(float(maxi), _nombre(valeur) or 0.0))


def score(cible: dict) -> tuple[float, dict]:
    detail = {
        "pertinence": _borne(cible.get("pertinence"), AXES["pertinence"]),
        "autorite": note_autorite(cible.get("da")),
        "accessibilite": _borne(cible.get("accessibilite"), AXES["accessibilite"]),
        "trafic": note_trafic(cible.get("trafic")),
    }
    return round(sum(detail.values()), 1), detail


def sans_donnees(cible: dict) -> bool:
    """Autorité ≤ 1 et aucun lien mesuré : l'outil ne connaît pas ce domaine."""
    da = _nombre(cible.get("da"))
    liens = [_nombre(cible.get(c)) for c in ("backlinks", "ref_domains")]
    connus = [v for v in liens if v is not None]
    return (da is None or da <= 1) and bool(connus) and all(v == 0 for v in connus)


def classer(cibles: list[dict], offre: str | None = None, minimum: float = 0.0) -> tuple[list[dict], list[dict]]:
    """→ (cibles classées par score décroissant, cibles écartées avec raison)."""
    classees, ecartees = [], []
    for c in cibles:
        if offre and c.get("offre") != offre:
            continue
        if sans_donnees(c):
            ecartees.append({"domaine": c.get("domaine", "?"),
                             "raison": "aucune donnée (autorité 1, aucun lien) : domaine mort ou hors index de l'outil"})
            continue
        s, detail = score(c)
        avertissements = [] if str(c.get("preuve") or "").strip() else ["sans preuve mesurée"]
        if s < minimum:
            ecartees.append({"domaine": c.get("domaine", "?"), "raison": f"score {s} sous le minimum {minimum:g}"})
            continue
        classees.append({**c, "score": s, "detail": detail, "avertissements": avertissements})
    classees.sort(key=lambda c: (-c["score"], str(c.get("domaine", ""))))
    return classees, ecartees


def lire(fichier: Path) -> dict:
    if not fichier.is_file():
        raise ErreurCibles(f"Fichier introuvable : {fichier}")
    texte = fichier.read_text(encoding="utf-8-sig")
    if fichier.suffix.lower() == ".json" or texte.lstrip().startswith(("{", "[")):
        doc = json.loads(texte)
        if isinstance(doc, list):
            doc = {"cibles": doc}
        if not isinstance(doc.get("cibles"), list):
            raise ErreurCibles("Le JSON doit contenir une liste « cibles ».")
        return doc
    lignes = list(csv.DictReader(texte.splitlines()))
    if lignes and "domaine" not in lignes[0]:
        raise ErreurCibles("Le CSV doit contenir au moins une colonne « domaine ».")
    return {"cibles": lignes}


def rendre(doc: dict, classees: list[dict], ecartees: list[dict]) -> str:
    lignes = []
    if doc.get("mesure") or doc.get("source_metriques"):
        lignes.append(f"  Mesures du {doc.get('mesure', '?')} · {doc.get('source_metriques', 'source non précisée')}")
    lignes.append("  Autorité et trafic : valeurs d'UN outil, estimations, jamais comparées à celles d'un autre outil.\n")
    lignes.append(f"  {'#':>2}  {'Domaine':<30} {'Score':>5}  {'Aut.':>4} {'Trafic':>8}  Demande")
    for i, c in enumerate(classees, 1):
        trafic = "?" if _nombre(c.get("trafic")) is None else f"{_nombre(c.get('trafic')):,.0f}".replace(",", " ")
        da = _nombre(c.get("da"))
        alerte = "  ! " + ", ".join(c["avertissements"]) if c["avertissements"] else ""
        lignes.append(f"  {i:>2}  {str(c.get('domaine', '?')):<30} {c['score']:>5}  {'?' if da is None else f'{da:.0f}':>4} "
                      f"{trafic:>8}  {c.get('demande') or ''}{alerte}")
    if classees:
        lignes.append("\n  Détail (pertinence 40 · autorité 25 · accessibilité 20 · trafic 15), 5 premières :")
        for c in classees[:5]:
            d = c["detail"]
            lignes.append(f"  {str(c.get('domaine', '?')):<30} pert {d['pertinence']:>4}  aut {d['autorite']:>4}  "
                          f"acc {d['accessibilite']:>4}  traf {d['trafic']:>4}")
    toutes = ecartees + [e for e in doc.get("ecartes", []) if isinstance(e, dict)]
    if toutes:
        lignes.append(f"\n  Écartées ({len(toutes)}) :")
        lignes += [f"    · {e.get('domaine', '?')} : {e.get('raison', '')}" for e in toutes]
    return "\n".join(lignes)


def main() -> int:
    ap = argparse.ArgumentParser(description="Classe les cibles d'une campagne de netlinking")
    ap.add_argument("fichier", help="JSON {cibles: [...]} ou CSV, une cible par ligne")
    ap.add_argument("--offre", help="ne garder que les cibles de cette contrepartie")
    ap.add_argument("--min", type=float, default=0.0, help="score minimum pour être classée")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        doc = lire(Path(a.fichier))
    except (ErreurCibles, json.JSONDecodeError, OSError) as exc:
        print(f"  ✗ {exc}", file=sys.stderr)
        return 1
    classees, ecartees = classer(doc["cibles"], a.offre, a.min)
    if not classees and not ecartees:
        print("  ✗ Aucune cible ne correspond.", file=sys.stderr)
        return 1
    if a.json:
        print(json.dumps({"mesure": doc.get("mesure"), "cibles": classees,
                          "ecartees": ecartees + doc.get("ecartes", [])}, ensure_ascii=False, indent=1))
    else:
        print("\n" + rendre(doc, classees, ecartees) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
