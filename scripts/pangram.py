#!/usr/bin/env python3
"""Détecteur d'IA Pangram : part du texte jugée écrite ou assistée par une IA, passages à reprendre.

    python3 pangram.py contenus/guide.md
    python3 pangram.py page.html --json
    cat brouillon.txt | python3 pangram.py -
    python3 pangram.py contenus/guide.md --seuil 0.2     # code 1 si IA + assistée > 20 %

Complète humanisation.py : humanisation.py repère les tics d'écriture ligne
par ligne, sans rien envoyer ; Pangram est un classifieur externe qui dit si
le texte, dans son ensemble et passage par passage, se lit comme généré, et
s'il a été « humanisé » par un outil de reformulation. Pangram ne réécrit
rien : la réécriture reste la passe seo-humanisation.

Le texte part chez Pangram (text.external-api.pangram.com) : ne l'utilisez
pas sur un contenu confidentiel sans l'accord du client. Coût indicatif :
0,05 $ par tranche de 100 mots (tarif public Pangram, à vérifier sur
pangram.com). Clé : PANGRAM_API_KEY (.env ou environnement).

Codes de sortie : 0 sous le seuil, 1 au-dessus, 2 erreur (clé absente,
API en échec, texte vide).
Sans dépendance (Python 3.9+).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env  # noqa: E402
from humanisation import lignes_texte, lire_source  # noqa: E402

API = "https://text.external-api.pangram.com"
MODELE = "pangram-4"
PRIX_100_MOTS = 0.05
SEUIL_CONSEILLE = 0.2
LIBELLES = {"AI-Generated": "IA", "AI-Assisted": "assisté par IA", "Human Written": "humain"}


class ErreurAPI(Exception):
    pass


def texte_lisible(brut: str, fmt: str) -> str:
    """Le texte tel qu'un lecteur le lit : sans balises, front matter, code ni URL de liens."""
    lignes = [l.strip() for l in lignes_texte(brut, fmt)]
    texte = "\n".join(lignes)
    return re.sub(r"\n{3,}", "\n\n", texte).strip()


def nb_mots(texte: str) -> int:
    return len(re.findall(r"\w+", texte))


def cout_estime(mots: int) -> float:
    return round(-(-mots // 100) * PRIX_100_MOTS, 2)


def requete(methode: str, chemin: str, cle: str, corps: dict | None = None, delai: int = 60) -> dict:
    donnees = json.dumps(corps).encode() if corps is not None else None
    req = urllib.request.Request(f"{API}{chemin}", data=donnees, method=methode,
                                 headers={"x-api-key": cle, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=delai) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        raise ErreurAPI(f"HTTP {e.code} sur {chemin} : {detail}") from e
    except urllib.error.URLError as e:
        raise ErreurAPI(f"Pangram injoignable : {e.reason}") from e


def analyser(texte: str, cle: str, modele: str = MODELE, attente_max: float = 180, pause: float = 2) -> dict:
    """Crée la tâche, attend son résultat et le renvoie tel que Pangram le donne."""
    tache = requete("POST", "/task", cle, {"text": texte, "model": modele, "public_dashboard_link": False})
    ident = tache.get("task_id")
    if not ident:
        raise ErreurAPI(f"pas de task_id dans la réponse : {str(tache)[:200]}")
    fin = time.monotonic() + attente_max
    while True:
        res = requete("GET", f"/task/{ident}", cle)
        etape = res.get("stage", "")
        if etape == "STAGE_SUCCESS":
            return res
        if etape == "STAGE_FAILED":
            raise ErreurAPI(f"analyse en échec : {res.get('headline') or res}")
        if time.monotonic() > fin:
            raise ErreurAPI(f"pas de résultat après {attente_max:g} s (tâche {ident})")
        time.sleep(pause)


def _ligne_de(texte: str, index: int) -> int:
    return texte.count("\n", 0, max(index, 0)) + 1


def synthese(res: dict) -> dict:
    """Ce qui sert à la passe d'humanisation : parts, verdict, passages à reprendre avec leur ligne."""
    texte = res.get("text", "")
    passages = []
    for w in res.get("windows") or []:
        label = w.get("label", "")
        humanise = bool(w.get("is_humanized"))
        if label == "Human Written" and not humanise:
            continue
        extrait = re.sub(r"\s+", " ", w.get("text", "")).strip()
        passages.append({
            "ligne": _ligne_de(texte, w.get("start_index", 0)),
            "label": LIBELLES.get(label, label),
            "score": w.get("ai_assistance_score"),
            "confiance": w.get("confidence"),
            "humanise": humanise,
            "mots": w.get("word_count"),
            "extrait": extrait[:160] + ("…" if len(extrait) > 160 else ""),
        })
    ia, assiste = float(res.get("fraction_ai") or 0), float(res.get("fraction_ai_assisted") or 0)
    return {
        "verdict": res.get("prediction_short", ""),
        "titre": res.get("headline", ""),
        "part_ia": ia,
        "part_assistee": assiste,
        "part_humaine": float(res.get("fraction_human") or 0),
        "part_ia_totale": round(ia + assiste, 4),
        "humanise": any(p["humanise"] for p in passages),
        "version": res.get("version", ""),
        "passages": passages,
    }


def _pct(x: float) -> str:
    return f"{x * 100:.0f} %"


def texte_rapport(s: dict, nom: str, mots: int, seuil: float | None) -> str:
    lignes = [f"Pangram {s['version']} — {nom} ({mots} mots)",
              f"  Verdict : {s['verdict'] or '?'} — {s['titre']}",
              f"  IA {_pct(s['part_ia'])} · assisté {_pct(s['part_assistee'])} · humain {_pct(s['part_humaine'])}"]
    if s["humanise"]:
        lignes.append("  ! Passages signalés comme « humanisés » par un outil de reformulation : "
                      "réécrire le fond de la phrase, pas les mots un à un.")
    if seuil is not None:
        etat = "au-dessus" if s["part_ia_totale"] > seuil else "sous"
        lignes.append(f"  IA + assisté {_pct(s['part_ia_totale'])} : {etat} du seuil {_pct(seuil)}")
    if s["passages"]:
        lignes.append("\nPassages à reprendre :")
        for p in s["passages"]:
            score = f" {p['score']:.2f}" if isinstance(p["score"], (int, float)) else ""
            drap = " · humanisé" if p["humanise"] else ""
            lignes.append(f"  l.{p['ligne']:<4} {p['label']}{score} ({p['confiance'] or '?'}){drap} — {p['extrait']}")
    return "\n".join(lignes)


def main() -> int:
    ap = argparse.ArgumentParser(description="Part du texte jugée générée par IA selon Pangram, passage par passage")
    ap.add_argument("fichier", help="fichier .md, .html ou .txt ; « - » pour l'entrée standard")
    ap.add_argument("--seuil", type=float,
                    help=f"code 1 si IA + assisté dépasse cette part (0-1, conseillé {SEUIL_CONSEILLE:g})")
    ap.add_argument("--modele", default=MODELE, help=f"modèle Pangram (défaut {MODELE})")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--cout", action="store_true", help="affiche le nombre de mots et le coût estimé, sans appel")
    a = ap.parse_args()

    try:
        fmt, brut = lire_source(a.fichier)
    except FileNotFoundError:
        print(f"✗ fichier introuvable : {a.fichier}", file=sys.stderr)
        return 2
    texte = texte_lisible(brut, fmt)
    mots = nb_mots(texte)
    if not mots:
        print("✗ texte vide", file=sys.stderr)
        return 2
    if a.cout:
        print(f"{mots} mots · coût estimé {cout_estime(mots):.2f} $ (0,05 $ / 100 mots)")
        return 0

    charger_env()
    cle = os.environ.get("PANGRAM_API_KEY", "").strip()
    if not cle:
        print("✗ PANGRAM_API_KEY absente : clé sur https://www.pangram.com (tableau de bord → API), "
              "à mettre dans .env", file=sys.stderr)
        return 2
    print(f"… {mots} mots envoyés à Pangram (≈ {cout_estime(mots):.2f} $)", file=sys.stderr)
    try:
        s = synthese(analyser(texte, cle, a.modele))
    except ErreurAPI as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2

    s["mots"] = mots
    if a.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
    else:
        print(texte_rapport(s, "entrée standard" if a.fichier == "-" else a.fichier, mots, a.seuil))
    if a.seuil is not None and s["part_ia_totale"] > a.seuil:
        print(f"✗ IA + assisté {_pct(s['part_ia_totale'])} > seuil {_pct(a.seuil)} : passe d'humanisation à refaire",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
