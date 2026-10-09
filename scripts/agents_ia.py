#!/usr/bin/env python3
"""Préparation d'un site aux agents IA : ce qu'un robot ou un agent d'IA peut lire, citer et faire.

    python3 agents_ia.py https://exemple.fr
    python3 agents_ia.py https://exemple.fr/tarifs --json

Contrôles, tous en HTTP, sans navigateur :

1. robots.txt, agent par agent (GPTBot, OAI-SearchBot, ClaudeBot,
   Claude-SearchBot, PerplexityBot, Google-Extended…), avec la sélection de
   groupe de la RFC 9309 : un groupe nommé remplace « * », rien ne s'hérite.
   Lignes Content-Signal (search, ai-input, ai-train) lues et vérifiées.
2. /llms.txt selon les règles de l'audit Lighthouse « llms-txt » : un titre
   H1, des liens Markdown, 50 caractères au moins ; une page HTML servie en
   200 à cette adresse (fausse 404) compte comme un échec.
3. Version Markdown de la page : négociation « Accept: text/markdown » (avec
   « Vary: Accept »), lien rel="alternate" type="text/markdown", ou URL .md.
4. ai-catalog.json (Agentic Resource Discovery) : signalé dans robots.txt
   (Agentmap), dans la page, ou à /.well-known/ai-catalog.json.
5. Contenu rendu côté serveur : mots visibles dans le HTML brut, signes
   d'une coquille JavaScript vide.
6. WebMCP dans le balisage : formulaires annotés (toolname /
   tooldescription) et appels registerTool( dans les scripts de la page.

Statut des normes (vérifié le 2026-09-23 par claude-seo, dont ce script
reprend la méthode, MIT, Daniel Agrici) : robots.txt est la RFC 9309 ;
llms.txt, Content-Signal, WebMCP et ARD sont des propositions ou des
brouillons. Google Search ignore llms.txt. Un « à faire » sur une
proposition reste facultatif : on le dit au client tel quel.

Codes de sortie : 0 sans échec, 1 si un contrôle échoue, 2 si le site ne
répond pas. Sans dépendance (Python 3.9+).
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlparse

UA = "Mozilla/5.0 (compatible; decupler-seo agents-ia)"
VERIFIE_LE = "2026-09-23"
MAX_OCTETS = 2_000_000
MAX_SCRIPTS = 8

# jeton robots.txt, éditeur, rôle
AGENTS = [
    ("GPTBot", "OpenAI", "entraînement"),
    ("OAI-SearchBot", "OpenAI", "recherche"),
    ("ChatGPT-User", "OpenAI", "utilisateur"),
    ("ClaudeBot", "Anthropic", "entraînement"),
    ("Claude-SearchBot", "Anthropic", "recherche"),
    ("Claude-User", "Anthropic", "utilisateur"),
    ("PerplexityBot", "Perplexity", "recherche"),
    ("Perplexity-User", "Perplexity", "utilisateur"),
    ("Google-Extended", "Google", "contrôle"),
    ("Applebot-Extended", "Apple", "contrôle"),
    ("CCBot", "Common Crawl", "entraînement"),
]
ROLES = {
    "entraînement": "entraînement des modèles",
    "recherche": "index de recherche IA et citations (c'est lui qui fait citer le site)",
    "utilisateur": "pages ouvertes à la demande d'une personne",
    "contrôle": "jeton robots.txt sans robot propre (usage IA des données par Google ou Apple)",
}
CLES_CONTENT_SIGNAL = {"search", "ai-input", "ai-train"}
COQUILLE_JS = re.compile(r'<div[^>]+id=["\'](?:root|app|__next|__nuxt)["\'][^>]*>\s*</div>', re.I)


def lire(url: str, entetes: dict | None = None, delai: int = 15) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(entetes or {})})
    try:
        with urllib.request.urlopen(req, timeout=delai) as r:
            corps = r.read(MAX_OCTETS)
            return {"statut": r.status, "entetes": {k.lower(): v for k, v in r.headers.items()},
                    "texte": corps.decode(r.headers.get_content_charset() or "utf-8", errors="replace"),
                    "url": r.geturl()}
    except urllib.error.HTTPError as e:
        return {"statut": e.code, "entetes": {k.lower(): v for k, v in (e.headers or {}).items()},
                "texte": "", "url": url}
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        return {"statut": None, "entetes": {}, "texte": "", "url": url, "erreur": str(getattr(e, "reason", e))}


def type_contenu(rep: dict) -> str:
    return rep["entetes"].get("content-type", "").lower()


def controle(ident: str, titre: str, statut: str, norme: str, detail=None, correctif: str | None = None) -> dict:
    return {"id": ident, "titre": titre, "statut": statut, "norme": norme, "detail": detail, "correctif": correctif}


# ─── robots.txt ───────────────────────────────────────────────────

def lignes_robots(texte: str) -> list[str]:
    """Découpe sur CR, LF ou CRLF seulement (RFC 9309), pas sur les séparateurs Unicode."""
    return re.split(r"\r\n|\n|\r", texte.lstrip("﻿"))


def analyser_robots(texte: str) -> dict:
    groupes, agentmap, sitemaps = [], [], []
    courant, ligne_ua = None, False
    for brute in lignes_robots(texte):
        ligne = brute.split("#", 1)[0].strip()
        if ":" not in ligne:
            continue
        champ, valeur = (p.strip() for p in ligne.split(":", 1))
        champ = champ.lower()
        if champ == "user-agent":
            if courant is None or not ligne_ua:
                courant = {"agents": [], "regles": [], "content_signal": []}
                groupes.append(courant)
            courant["agents"].append(valeur)
            ligne_ua = True
            continue
        ligne_ua = False
        if champ == "sitemap":
            sitemaps.append(valeur)
        elif champ == "agentmap":
            agentmap.append(valeur)
        elif courant is None:
            continue
        elif champ in ("allow", "disallow"):
            courant["regles"].append((champ, valeur))
        elif champ == "content-signal":
            courant["content_signal"].append(valeur)
    return {"groupes": groupes, "agentmap": agentmap, "sitemaps": sitemaps}


def groupe_de(robots: dict, jeton: str) -> dict:
    """RFC 9309 : tous les groupes qui nomment le jeton ; à défaut, tous les groupes « * »."""
    j = jeton.lower()
    nommes = [g for g in robots["groupes"] if any(a.lower() == j for a in g["agents"])]
    choisis = nommes or [g for g in robots["groupes"] if "*" in g["agents"]]
    return {"source": "nommé" if nommes else ("*" if choisis else "aucun"),
            "regles": [r for g in choisis for r in g["regles"]],
            "content_signal": [c for g in choisis for c in g["content_signal"]]}


def _motif(motif: str, chemin: str) -> bool:
    ancre = motif.endswith("$")
    corps = motif[:-1] if ancre else motif
    regex = "^" + ".*".join(re.escape(p) for p in corps.split("*")) + ("$" if ancre else "")
    return re.match(regex, chemin) is not None


def autorise(regles: list, chemin: str = "/") -> bool:
    """La règle la plus longue gagne ; à égalité, Allow gagne ; « Disallow: » vide autorise tout."""
    meilleure, ok = -1, True
    for champ, valeur in regles:
        if champ == "disallow" and valeur == "":
            continue
        if _motif(valeur, chemin) and (len(valeur) > meilleure or (len(valeur) == meilleure and champ == "allow")):
            meilleure, ok = len(valeur), champ == "allow"
    return ok


def lire_content_signal(valeur: str) -> dict:
    signaux, problemes = {}, []
    for morceau in (m.strip() for m in valeur.split(",")):
        if not morceau:
            continue
        if "=" not in morceau:
            problemes.append(f"entrée mal formée « {morceau} »")
            continue
        cle, val = (s.strip().lower() for s in morceau.split("=", 1))
        signaux[cle] = val
        if cle == "use":
            continue  # quatrième clé testée par Cloudflare, ni validée ni refusée
        if cle not in CLES_CONTENT_SIGNAL:
            problemes.append(f"clé inconnue « {cle} »")
        elif val not in ("yes", "no"):
            problemes.append(f"« {cle} » attend yes ou no")
    return {"signaux": signaux, "problemes": problemes}


def controles_robots(racine: str, chemin: str) -> tuple[list, dict]:
    rep = lire(racine + "/robots.txt")
    if rep["statut"] != 200 or "html" in type_contenu(rep):
        statut = "info" if rep["statut"] in (404, 410) else "echec"
        return [controle("robots", "robots.txt", statut, "RFC 9309", {"statut": rep["statut"]},
                         "Pas de robots.txt : tout est autorisé, mais aucun choix n'est exprimé pour les IA."
                         if statut == "info" else "robots.txt ne répond pas en texte : à corriger en priorité.")], \
            {"agentmap": []}
    robots = analyser_robots(rep["texte"])
    table, bloques_recherche, problemes_cs = [], [], []
    for jeton, editeur, role in AGENTS:
        g = groupe_de(robots, jeton)
        ok = autorise(g["regles"], chemin)
        cs = [lire_content_signal(v) for v in g["content_signal"]]
        problemes_cs += [p for c in cs for p in c["problemes"]]
        table.append({"agent": jeton, "editeur": editeur, "role": role, "groupe": g["source"],
                      "autorise": ok, "content_signal": [c["signaux"] for c in cs]})
        if role == "recherche" and not ok:
            bloques_recherche.append(jeton)
    res = [controle("robots-agents", "Accès des robots IA à la page", "echec" if bloques_recherche else "ok",
                    "RFC 9309", table,
                    f"{', '.join(bloques_recherche)} bloqué(s) : le site ne peut pas être cité par ces moteurs. "
                    "Bloquer l'entraînement (GPTBot, ClaudeBot, CCBot) est un choix ; bloquer la recherche "
                    "coûte la visibilité." if bloques_recherche else None)]
    a_cs = any(t["content_signal"] for t in table)
    res.append(controle("content-signal", "Content-Signal (usages autorisés par les IA)",
                        "alerte" if problemes_cs else ("ok" if a_cs else "info"),
                        f"proposition (contentsignals.org), lue par peu d'agents (vérifié le {VERIFIE_LE})",
                        {"problemes": problemes_cs},
                        "; ".join(problemes_cs) if problemes_cs else None if a_cs else
                        "Facultatif : « Content-Signal: search=yes, ai-input=yes, ai-train=no » dans le groupe "
                        "« * » dit qu'on accepte d'être cité mais pas de servir à l'entraînement."))
    return res, {"agentmap": robots["agentmap"]}


# ─── llms.txt ─────────────────────────────────────────────────────

def evaluer_llms(statut: int | None, texte: str) -> dict:
    """Règles de l'audit Lighthouse llms-txt, plus les conseils de llmstxt.org."""
    if statut is None or statut >= 500:
        return {"verdict": "echec", "erreurs": [f"HTTP {statut}"], "notes": []}
    if statut >= 400:
        return {"verdict": "absent", "erreurs": [], "notes": []}
    texte = texte.lstrip("﻿")
    erreurs, notes = [], []
    if re.search(r"^\s*<(!doctype|html)", texte, re.I):
        erreurs.append("page HTML servie en 200 (fausse 404), pas un fichier Markdown")
    else:
        if not re.search(r"^\s*#\s+.+", texte, re.M):
            erreurs.append("pas de titre H1 (« # Nom du site »)")
        if not re.search(r"\[.+\]\(.+\)", texte):
            erreurs.append("aucun lien Markdown")
        if len(texte) < 50:
            erreurs.append("moins de 50 caractères")
        if not re.search(r"^\s*>\s+\S", texte, re.M):
            notes.append("pas de résumé en citation (« > … »)")
        if not re.search(r"^\s*##\s+\S", texte, re.M):
            notes.append("pas de sections H2 qui regroupent les liens")
    return {"verdict": "echec" if erreurs else "ok", "erreurs": erreurs, "notes": notes}


def controles_llms(racine: str) -> list:
    rep = lire(racine + "/llms.txt")
    ev = evaluer_llms(rep["statut"], rep["texte"])
    statut = {"ok": "ok", "echec": "echec", "absent": "info"}[ev["verdict"]]
    correctif = {"absent": "Facultatif : publier un llms.txt (skill geo-llms-txt). Lighthouse ne le compte pas s'il "
                           "est absent ; il compte un échec s'il est invalide.",
                 "echec": "À corriger : " + "; ".join(ev["erreurs"])}.get(ev["verdict"])
    if ev["verdict"] == "ok" and ev["notes"]:
        correctif = "Améliorer : " + "; ".join(ev["notes"])
    return [controle("llms-txt", "llms.txt", statut,
                     "proposition (llmstxt.org) ; vérifié par Lighthouse, ignoré par Google Search", ev, correctif)]


# ─── Page : rendu, Markdown, WebMCP, ARD ──────────────────────────

def texte_visible(html: str) -> str:
    html = re.sub(r"<(script|style|noscript|svg|template)\b.*?</\1>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", html))).strip()


def liens(html: str, base: str) -> dict:
    alt_md, catalogues = [], []
    for balise in re.findall(r"<link\b[^>]*>", html, re.I):
        rel = (re.search(r'rel=["\']([^"\']+)', balise, re.I) or [None, ""])[1].lower()
        typ = (re.search(r'type=["\']([^"\']+)', balise, re.I) or [None, ""])[1].lower()
        href = (re.search(r'href=["\']([^"\']+)', balise, re.I) or [None, ""])[1]
        if not href:
            continue
        if "alternate" in rel.split() and "text/markdown" in typ:
            alt_md.append(urljoin(base, href))
        if "ai-catalog" in rel.split():
            catalogues.append(urljoin(base, href))
    return {"markdown": alt_md, "ai_catalog": catalogues}


def controles_page(url: str, page: dict, agentmap: list) -> list:
    res = []
    mots = len(texte_visible(page["texte"]).split())
    coquille = bool(COQUILLE_JS.search(page["texte"]))
    res.append(controle("rendu-serveur", "Contenu présent dans le HTML brut",
                        "echec" if mots < 50 else ("alerte" if mots < 150 and coquille else "ok"),
                        "les robots IA n'exécutent pas, ou peu, le JavaScript",
                        {"mots_visibles": mots, "coquille_js": coquille},
                        "Le HTML brut est presque vide : rendu serveur ou pré-rendu nécessaire, sinon les IA "
                        "ne lisent rien." if mots < 50 else None))

    ln = liens(page["texte"], url)
    neg = lire(url, {"Accept": "text/markdown"})
    negocie = neg["statut"] == 200 and "text/markdown" in type_contenu(neg)
    vary = "accept" in neg["entetes"].get("vary", "").lower()
    p = urlparse(url)
    voisin = f"{p.scheme}://{p.netloc}" + (p.path.rstrip("/") + ".md" if p.path.strip("/") else "/index.md")
    rep_voisin = lire(voisin)
    voisin_ok = rep_voisin["statut"] == 200 and not type_contenu(rep_voisin).startswith("text/html")
    alt_ok = []
    for alt in ln["markdown"][:3]:
        r = lire(alt)
        alt_ok.append(r["statut"] == 200 and not type_contenu(r).startswith("text/html"))
    ok = negocie or voisin_ok or any(alt_ok)
    probleme = negocie and not vary
    res.append(controle("markdown", "Version Markdown de la page",
                        "alerte" if probleme else ("ok" if ok else "info"),
                        f"négociation HTTP (RFC 9110) et usage communautaire ; aucun agent grand public "
                        f"confirmé ne la demande (vérifié le {VERIFIE_LE})",
                        {"negociation": negocie, "vary_accept": vary, "url_md": voisin if voisin_ok else None,
                         "liens_alternate": ln["markdown"]},
                        "Ajouter « Vary: Accept », sinon un cache peut servir le Markdown aux navigateurs."
                        if probleme else None if ok else
                        "Facultatif : servir la page en Markdown sur « Accept: text/markdown » (avec Vary: Accept), "
                        "ou un lien rel=\"alternate\" type=\"text/markdown\"."))

    candidats = [urljoin(url, a) for a in agentmap] + ln["ai_catalog"]
    signale = bool(candidats)
    cible = candidats[0] if candidats else f"{p.scheme}://{p.netloc}/.well-known/ai-catalog.json"
    cat = lire(cible)
    norme = f"Agentic Resource Discovery 1.0, audit Lighthouse ard-schema (vérifié le {VERIFIE_LE})"
    if cat["statut"] == 200 and type_contenu(cat).startswith("text/html"):
        res.append(controle("ai-catalog", "ai-catalog.json", "echec", norme, {"url": cible},
                            "L'adresse renvoie une page HTML en 200 (fausse 404) : Lighthouse compte un échec. "
                            "Renvoyer une vraie 404 aux adresses inconnues."))
    elif cat["statut"] == 200:
        try:
            doc = json.loads(cat["texte"])
            valide = isinstance(doc, dict)
        except ValueError:
            valide = False
        res.append(controle("ai-catalog", "ai-catalog.json", "ok" if valide else "echec", norme, {"url": cible},
                            None if valide else "Le catalogue n'est pas un objet JSON valide."))
    else:
        res.append(controle("ai-catalog", "ai-catalog.json", "echec" if signale else "info", norme,
                            {"url": cible, "statut": cat["statut"]},
                            "Le catalogue est signalé mais ne se charge pas." if signale else
                            "Seulement si le site a des ressources pour agents (serveur MCP, agent A2A) : sinon rien à faire."))

    formulaires = re.findall(r"<form\b[^>]*>", page["texte"], re.I)
    annotes = [f for f in formulaires if re.search(r"\btool(name|description)\s*=", f, re.I)]
    scripts = re.findall(r"<script\b(?![^>]*\bsrc=)[^>]*>(.*?)</script>", page["texte"], re.S | re.I)
    for src in re.findall(r'<script\b[^>]*\bsrc=["\']([^"\']+)', page["texte"], re.I)[:MAX_SCRIPTS]:
        absolu = urljoin(url, src)
        if urlparse(absolu).netloc == p.netloc:
            scripts.append(lire(absolu)["texte"])
    appels = len(re.findall(r"\bregisterTool\s*\(", "\n".join(scripts)))
    outils = appels > 0 or bool(annotes)
    res.append(controle("webmcp", "WebMCP : actions offertes aux agents", "ok" if outils else "info",
                        f"brouillon du groupe communautaire W3C, Chrome seulement (vérifié le {VERIFIE_LE})",
                        {"formulaires": len(formulaires), "annotes": len(annotes), "appels_registerTool": appels},
                        None if outils or not formulaires else
                        "Facultatif : annoter (toolname, tooldescription) les formulaires qu'un agent peut remplir "
                        "sans risque (devis, contact, recherche)."))
    return res


def auditer(url: str) -> dict:
    if not re.match(r"https?://", url):
        url = "https://" + url
    page = lire(url)
    if page["statut"] is None or page["statut"] >= 400:
        return {"url": url, "erreur": f"la page ne répond pas ({page.get('erreur') or page['statut']})", "controles": []}
    p = urlparse(page["url"])
    racine = f"{p.scheme}://{p.netloc}"
    chemin = p.path or "/"
    robots, extra = controles_robots(racine, chemin)
    controles = robots + controles_llms(racine) + controles_page(page["url"], page, extra["agentmap"])
    compte = {s: sum(c["statut"] == s for c in controles) for s in ("ok", "alerte", "echec", "info")}
    return {"url": page["url"], "verifie_le": VERIFIE_LE, "controles": controles, "bilan": compte}


SYMBOLES = {"ok": "✓", "alerte": "!", "echec": "✗", "info": "·"}


def texte_rapport(r: dict) -> str:
    sortie = [f"Agents IA — {r['url']}", ""]
    for c in r["controles"]:
        sortie.append(f"{SYMBOLES[c['statut']]} {c['titre']}  ({c['norme']})")
        if c["id"] == "robots-agents":
            for t in c["detail"]:
                etat = "autorisé" if t["autorise"] else "BLOQUÉ"
                sortie.append(f"    {t['agent']:<18} {etat:<9} groupe {t['groupe']:<6} {ROLES[t['role']]}")
        if c["correctif"]:
            sortie.append(f"    → {c['correctif']}")
    b = r["bilan"]
    sortie += ["", f"{b['ok']} ok · {b['alerte']} alerte(s) · {b['echec']} échec(s) · {b['info']} facultatif(s)"]
    return "\n".join(sortie)


def main() -> int:
    ap = argparse.ArgumentParser(description="Préparation d'un site aux robots et agents IA")
    ap.add_argument("url")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = auditer(a.url)
    if r.get("erreur"):
        print(f"✗ {r['erreur']}", file=sys.stderr)
        return 2
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else texte_rapport(r))
    return 1 if r["bilan"]["echec"] else 0


if __name__ == "__main__":
    sys.exit(main())
