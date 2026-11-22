#!/usr/bin/env python3
"""Six notes sur 100 pour une page avant publication : SEO, AI Search, rédaction,
conversion, UX, design.

Chaque note vient d'une mesure, jamais d'une impression :
- SEO : onpage_score.py de la méthode (title, Hn, mot-clé, entités, maillage…) ;
- AI Search : extractabilité (réponse directe, listes, tableaux, FAQ, JSON-LD, entités) ;
- rédaction : humanisation.py (tics d'écriture générée) et controle_contenu.py ;
- conversion : copywriting.py (orientation lecteur, CTA, preuves, accroche) ;
- UX : parcours de lecture (CTA haut et bas, paragraphes courts, sommaire, rythme des H2) ;
- design : matière visuelle (images avec alt et dimensions, captures, schémas, bandes variées).

Usage :
  python3 .claude/decupler-seo/scripts/scores_page.py <page.html> "<mot-clé>" [--url URL] [--marque NOM] [--json]
      [--seuil 80] [--seuil-seo 85]
Code retour 1 si une note passe sous son seuil : la page ne part pas, on corrige le
bloc le plus faible d'abord (la sortie dit lequel et pourquoi).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
# Dans la méthode, ce script vit à côté des autres ; copié dans un projet, il les cherche dans .claude/.
METHODE = ICI if (ICI / "onpage_score.py").exists() else ICI.parents[1] / ".claude/decupler-seo/scripts"

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    print("Installer beautifulsoup4 : python3 -m pip install beautifulsoup4", file=sys.stderr)
    sys.exit(2)

CTA = re.compile(r"rendez-vous|consultation|r[ée]server|demander|appel|devis|audit (?:gratuit|offert)|"
                 r"t[ée]l[ée]charg|recevoir|essayer|parler|contact", re.I)
QUESTION = re.compile(r"\?\s*$")


def lancer(script: str, *args: str) -> dict:
    """Lance un script de la méthode en --json ; renvoie {} s'il échoue."""
    try:
        sortie = subprocess.run([sys.executable, str(METHODE / script), *args, "--json"],
                                capture_output=True, text=True, timeout=180)
        texte = sortie.stdout.strip()
        if not texte:
            return {}
        return json.JSONDecoder().raw_decode(texte)[0]
    except Exception:
        return {}


def mots(texte: str) -> int:
    return len(re.findall(r"\w+", texte))


def note_ai_search(soup) -> tuple[int, list[str]]:
    """Extractabilité pour les moteurs IA : ce qu'un moteur peut citer tel quel."""
    pts, manques = 0, []
    h1 = soup.find("h1")
    # 1. Réponse directe : un paragraphe de 30 à 80 mots dans les 3 premiers après le H1 (20)
    paras = (h1.find_all_next("p", limit=4) if h1 else soup.find_all("p", limit=4))
    if any(30 <= mots(p.get_text(" ")) <= 80 for p in paras):
        pts += 20
    else:
        manques.append("réponse directe de 30 à 80 mots juste sous le H1")
    # 2. H2 sous forme de question (au moins 30 % des H2) (10)
    h2 = [h.get_text(" ").strip() for h in soup.find_all("h2")]
    part_q = sum(bool(QUESTION.search(t)) for t in h2) / len(h2) if h2 else 0
    pts += 10 if part_q >= 0.3 else round(10 * part_q / 0.3)
    if part_q < 0.3:
        manques.append(f"H2 en question : {part_q:.0%} (cible 30 %)")
    # 3. Listes à puces ou numérotées (15) : 3 au moins
    listes = [l for l in soup.find_all(["ul", "ol"]) if len(l.find_all("li", recursive=False)) >= 3]
    pts += min(15, 5 * len(listes))
    if len(listes) < 3:
        manques.append(f"listes de 3 éléments et plus : {len(listes)} (cible 3)")
    # 4. Tableau comparatif (10)
    if soup.find("table"):
        pts += 10
    else:
        manques.append("aucun tableau (comparatif, étapes, tarifs)")
    # 5. FAQ : au moins 4 questions et un FAQPage (20)
    ld = " ".join(s.get_text() for s in soup.find_all("script", type="application/ld+json"))
    questions = len(re.findall(r'"@type"\s*:\s*"Question"', ld))
    if questions >= 4:
        pts += 20
    elif questions:
        pts += 10
        manques.append(f"FAQPage : {questions} question(s) (cible 4 à 6)")
    else:
        manques.append("pas de FAQPage")
    # 6. Graphe d'entités : nœuds reliés par @id (Organisation, Personne), about/mentions (15)
    ent = 0
    if re.search(r'"@id"\s*:\s*"[^"]*#(?:organization|org|person|[a-z]+-[a-z]+)"', ld):
        ent += 8
    if re.search(r'"(?:about|mentions)"', ld) or "wikidata.org" in ld:
        ent += 7
    pts += ent
    if ent < 15:
        manques.append("graphe incomplet (@id de l'Organisation et de la Personne, about / mentions vers Wikidata)")
    # 7. Faits chiffrés citables : au moins 5 phrases avec un chiffre (10)
    phrases = re.split(r"(?<=[.!?])\s+", soup.get_text(" "))
    chiffrees = sum(bool(re.search(r"\d", p)) and 6 <= mots(p) <= 40 for p in phrases)
    pts += min(10, 2 * chiffrees)
    if chiffrees < 5:
        manques.append(f"phrases factuelles chiffrées : {chiffrees} (cible 5)")
    return min(100, pts), manques


def note_ux(soup) -> tuple[int, list[str]]:
    pts, manques = 0, []
    corps = soup.get_text(" ")
    # Position de chaque appel à l'action : mots lus avant lui, dans l'ordre du document
    avant, positions = 0, []
    for el in soup.find_all(string=True):
        if el.parent.name in ("script", "style"):
            continue
        parent_cta = el.find_parent(["a", "button"])
        if parent_cta is not None and CTA.search(parent_cta.get_text(" ") or ""):
            positions.append(avant)
        avant += mots(el)
    total = max(1, avant)
    # CTA en haut (300 premiers mots ou premier quart), au milieu, dans le dernier quart (30)
    zones = {"haut": any(p <= 300 or p / total < 0.25 for p in positions),
             "milieu": any(0.25 <= p / total <= 0.75 for p in positions),
             "bas": any(p / total > 0.75 for p in positions)}
    pts += 10 * sum(zones.values())
    manques += [f"pas d'appel à l'action en {z} de page" for z, ok in zones.items() if not ok]
    # Paragraphes courts : moins de 10 % au-delà de 90 mots (25)
    paras = [mots(p.get_text(" ")) for p in soup.find_all("p")]
    longs = sum(m > 90 for m in paras)
    part = longs / len(paras) if paras else 1
    pts += 25 if part <= 0.1 else max(0, round(25 * (1 - part)))
    if part > 0.1:
        manques.append(f"{longs} paragraphe(s) de plus de 90 mots")
    # Rythme : un H2 tous les 150 à 450 mots (20)
    h2 = len(soup.find_all("h2"))
    ratio = mots(corps) / h2 if h2 else 9999
    pts += 20 if 150 <= ratio <= 450 else 10 if 100 <= ratio <= 600 else 0
    if not 150 <= ratio <= 450:
        manques.append(f"un H2 tous les {ratio:.0f} mots (cible 150 à 450)")
    # Repères : sommaire / ancres internes ou fil d'Ariane (10)
    if soup.select('a[href^="#"]') or soup.find(attrs={"class": re.compile("sommaire|toc|ariane|breadcrumb", re.I)}):
        pts += 10
    else:
        manques.append("ni sommaire ni ancres internes")
    # Lisibilité : phrase moyenne sous 22 mots (15)
    phrases = [p for p in re.split(r"(?<=[.!?])\s+", corps) if mots(p) > 2]
    moy = sum(map(mots, phrases)) / len(phrases) if phrases else 99
    pts += 15 if moy <= 22 else 7 if moy <= 28 else 0
    if moy > 22:
        manques.append(f"phrase moyenne {moy:.0f} mots (cible ≤ 22)")
    return min(100, pts), manques


def note_design(soup) -> tuple[int, list[str]]:
    pts, manques = 0, []
    imgs = soup.find_all("img")
    # Matière visuelle : 4 images au moins (25)
    pts += min(25, round(25 * len(imgs) / 4))
    if len(imgs) < 4:
        manques.append(f"{len(imgs)} image(s) (cible 4 : captures réelles, schéma, photo, logos)")
    # Alt et dimensions sur chaque image (20)
    if imgs:
        ok = sum(bool(i.get("alt", "").strip()) and bool(i.get("width")) and bool(i.get("height")) for i in imgs)
        pts += round(20 * ok / len(imgs))
        if ok < len(imgs):
            manques.append(f"{len(imgs) - ok} image(s) sans alt ou sans width/height (CLS)")
    # Captures ou schémas légendés (figure/figcaption, svg) (20)
    figures = len(soup.find_all("figure")) + len(soup.find_all("svg"))
    pts += min(20, 10 * figures)
    if figures < 2:
        manques.append("moins de 2 figures légendées ou schémas")
    # Variété des bandes : classes de sections distinctes (20)
    sections = soup.find_all(["section"]) or soup.find_all("div", attrs={"class": True}, recursive=True)
    classes = {" ".join(s.get("class", [])[:2]) for s in sections if s.get("class")}
    pts += min(20, 4 * len(classes))
    if len(classes) < 5:
        manques.append(f"{len(classes)} types de bandes (cible 5 : hero, preuve, étapes, FAQ, CTA…)")
    # Pas de style inline massif ni de classes Elementor (15)
    inline = len(soup.select("[style]"))
    elem = len(soup.select('[class*="elementor"]'))
    pts += 15 if inline <= 40 and not elem else 7 if not elem else 0
    if elem:
        manques.append("classes Elementor dans le contenu")
    elif inline > 40:
        manques.append(f"{inline} styles inline (préférer les classes du gabarit)")
    return min(100, pts), manques


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("fichier")
    p.add_argument("motcle")
    p.add_argument("--url")
    p.add_argument("--entites", help="entités du top 5, séparées par des virgules")
    p.add_argument("--marque", default="", help="nom de la marque (orientation lecteur de copywriting.py)")
    p.add_argument("--seuil", type=int, default=80)
    p.add_argument("--seuil-seo", type=int, default=85)
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    html = Path(a.fichier).read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    args_seo = [a.fichier, a.motcle] + (["--url", a.url] if a.url else []) + (["--entites", a.entites] if a.entites else [])
    seo = lancer("onpage_score.py", *args_seo)
    hum = lancer("humanisation.py", a.fichier)
    copy = lancer("copywriting.py", a.fichier, *(["--marque", a.marque] if a.marque else []))
    ctrl = lancer("controle_contenu.py", a.fichier)

    # humanisation : 0 à 10 = 100 ; 25 (seuil de seo-copywriting) = 80 ; au-delà, chute rapide
    h = hum.get("score", 50)
    redac = 100 if h <= 10 else round(100 - (h - 10) * 20 / 15) if h <= 25 else max(0, round(80 - (h - 25) * 4))
    redac_manques = [f"humanisation {h} ({hum.get('niveau', '?')}) : sous 25 exigé, 10 visé (seo-humanisation)"] if h > 10 else []
    bloquants = [e for e in (ctrl.get("erreurs") or ctrl.get("bloquants") or []) if e]
    if bloquants or ctrl.get("bloquant"):
        redac = min(redac, 50)
        redac_manques.append("controle_contenu.py bloque : " + "; ".join(map(str, bloquants[:3])))

    ai, ai_m = note_ai_search(soup)
    ux, ux_m = note_ux(soup)
    de, de_m = note_design(soup)
    seo_m = [f"{c['critere']} : {c.get('constat', '')}" for c in seo.get("criteres", [])
             if c.get("feu") in ("🔴", "🟠")][:6]
    copy_m = [f"{k} : {v.get('mesure', '')}" for k, v in (copy.get("criteres") or {}).items()
              if v.get("points", 0) < v.get("sur", 0) * 0.7][:6]

    notes = {
        "seo": (seo.get("score", 0), a.seuil_seo, seo_m),
        "ai_search": (ai, a.seuil, ai_m),
        "redaction": (redac, a.seuil, redac_manques),
        "conversion": (copy.get("score", 0), a.seuil, copy_m),
        "ux": (ux, a.seuil, ux_m),
        "design": (de, a.seuil, de_m),
    }
    echecs = [k for k, (n, s, _) in notes.items() if n < s]
    if a.json:
        print(json.dumps({k: {"note": n, "seuil": s, "a_reprendre": m} for k, (n, s, m) in notes.items()}
                         | {"publiable": not echecs, "plus_faible": min(notes, key=lambda k: notes[k][0])},
                         ensure_ascii=False, indent=1))
    else:
        for k, (n, s, m) in notes.items():
            print(f"{'✓' if n >= s else '✗'} {k:<11} {n:>3}/100 (seuil {s})")
            for x in m:
                print(f"     · {x}")
        print("Publiable." if not echecs else f"À reprendre d'abord : {min(notes, key=lambda k: notes[k][0])}.")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
