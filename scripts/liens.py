#!/usr/bin/env python3
"""
liens.py — le profil de liens d'un site (API DataForSEO Backlinks), trié entre
vrais liens et spam automatique.

Beaucoup de sites reçoivent des centaines de liens de domaines générés en masse
(« seochecker.shop », « backlinkanalyzer.space »…) : ils gonflent les compteurs
sans rien apporter, et Google les ignore. Le chiffre qui compte est celui des
domaines propres, et c'est le seul que ce script met en avant.

    python3 liens.py resume --cible exemple.com
    python3 liens.py domaines --cible exemple.com
    python3 liens.py domaines --cible exemple.com --json > donnees/liens.json

Identifiants : DATAFORSEO_LOGIN (ou DATAFORSEO_USERNAME) et DATAFORSEO_PASSWORD.
Coût indicatif : 0,02 à 0,05 $ par appel.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env  # noqa: E402

SEUIL_SPAM = 30          # score de spam DataForSEO (0-100) à partir duquel un domaine est écarté


def classer(domaines: list[dict], seuil: int = SEUIL_SPAM) -> dict:
    """Sépare les domaines référents propres du spam, et compte ce qui est arrivé récemment."""
    propres = [d for d in domaines if (d.get("backlinks_spam_score") or 0) < seuil]
    spam = [d for d in domaines if (d.get("backlinks_spam_score") or 0) >= seuil]
    mois = {}
    for d in spam:
        m = (d.get("first_seen") or "")[:7]
        if m:
            mois[m] = mois.get(m, 0) + 1
    return {"total": len(domaines), "propres": propres, "spam": len(spam),
            "spam_par_mois": dict(sorted(mois.items())),
            "propres_dofollow": sum(1 for d in propres
                                    if (d.get("referring_pages") or 0) > (d.get("referring_pages_nofollow") or 0))}


def cmd_resume(a) -> int:
    import demande as D
    res, cout = D.appel("backlinks/summary/live", [{"target": a.cible, "include_subdomains": True,
                                                    "backlinks_status_type": "live"}])
    r = res[0] if res else {}
    cles = ("rank", "backlinks", "referring_domains", "referring_domains_nofollow", "backlinks_spam_score",
            "broken_backlinks", "first_seen")
    if a.json:
        print(json.dumps({k: r.get(k) for k in cles} | {"cout_usd": cout}, ensure_ascii=False, indent=1))
        return 0
    print(f"\n  {a.cible} · rang {r.get('rank')} · {r.get('referring_domains')} domaines référents · "
          f"{r.get('backlinks')} liens · score de spam {r.get('backlinks_spam_score')}/100")
    print(f"  Coût : {cout:.3f} $. Pour séparer les vrais liens du spam : liens.py domaines\n")
    return 0


def cmd_domaines(a) -> int:
    import demande as D
    res, cout = D.appel("backlinks/referring_domains/live", [{"target": a.cible, "limit": a.limite,
                                                              "order_by": ["rank,desc"],
                                                              "backlinks_status_type": "live"}])
    items = (res[0] or {}).get("items") or [] if res else []
    c = classer(items, a.seuil)
    if a.json:
        print(json.dumps({"cible": a.cible, "cout_usd": cout, **c}, ensure_ascii=False, indent=1))
        return 0
    print(f"\n  {a.cible} · {c['total']} domaines référents : {len(c['propres'])} propres "
          f"({c['propres_dofollow']} en dofollow), {c['spam']} de spam (score ≥ {a.seuil})")
    if c["spam_par_mois"]:
        print("  Spam par mois d'apparition : " + ", ".join(f"{m} : {n}" for m, n in c["spam_par_mois"].items()))
    print("\n  Domaines propres :")
    for d in c["propres"]:
        print(f"    {d.get('domain', ''):<40} rang {d.get('rank', 0):>4} · {d.get('backlinks', 0)} lien(s) · "
              f"vu le {(d.get('first_seen') or '')[:10]}")
    print(f"\n  Coût : {cout:.3f} $\n")
    return 0


def main() -> int:
    charger_env()
    ap = argparse.ArgumentParser(description="Profil de liens : vrais liens et spam automatique")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("resume", help="chiffres globaux")
    p.add_argument("--cible", required=True)
    p.add_argument("--json", action="store_true")
    p.set_defaults(f=cmd_resume)
    p = sp.add_parser("domaines", help="domaines référents, propres d'un côté, spam de l'autre")
    p.add_argument("--cible", required=True)
    p.add_argument("--limite", type=int, default=1000)
    p.add_argument("--seuil", type=int, default=SEUIL_SPAM)
    p.add_argument("--json", action="store_true")
    p.set_defaults(f=cmd_domaines)
    a = ap.parse_args()
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
