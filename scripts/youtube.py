#!/usr/bin/env python3
"""Veille vidéo : dernières vidéos d'une chaîne YouTube et transcription d'une vidéo.

    python3 youtube.py videos @agricidaniel                     # dernières vidéos (flux RSS public, 15 publications)
    python3 youtube.py videos https://youtube.com/@agricidaniel --n 5 --json
    python3 youtube.py transcription https://www.youtube.com/watch?v=NoGGXMrDPYM
    python3 youtube.py transcription NoGGXMrDPYM --langues fr,en --sortie veille/video.md

`videos` n'a besoin d'aucune dépendance ni d'aucune clé : il lit le flux RSS
public de la chaîne. `transcription` lit les sous-titres (manuels, sinon
automatiques) avec le paquet youtube-transcript-api :

    pip install youtube-transcript-api

YouTube refuse souvent les sous-titres aux adresses de centres de données
(routines cloud, serveurs) : « Sign in to confirm you're not a bot ». Lancez
alors la transcription depuis votre poste, ou passez par un proxy
résidentiel avec YOUTUBE_PROXY_URL (http://user:motdepasse@hote:port).

Une transcription est une source, pas une vérité : un conseil entendu dans
une vidéo se vérifie (documentation Google, donnée du projet) avant
d'entrer dans un skill ou une SOP.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env  # noqa: E402

UA = "Mozilla/5.0 (compatible; decupler-seo veille)"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
      "media": "http://search.yahoo.com/mrss/"}


class ErreurYouTube(Exception):
    pass


def _get(url: str, delai: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "fr,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=delai) as r:
            return r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise ErreurYouTube(f"HTTP {e.code} sur {url}") from e
    except urllib.error.URLError as e:
        raise ErreurYouTube(f"YouTube injoignable : {e.reason}") from e


def id_video(entree: str) -> str:
    """L'identifiant à 11 caractères d'une URL watch, youtu.be, shorts, embed ou live, ou l'identifiant lui-même."""
    entree = entree.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", entree):
        return entree
    m = re.search(r"(?:v=|youtu\.be/|/shorts/|/embed/|/live/)([A-Za-z0-9_-]{11})", entree)
    if not m:
        raise ErreurYouTube(f"identifiant de vidéo introuvable dans « {entree} »")
    return m.group(1)


def url_chaine(entree: str) -> str | None:
    """URL de la page de chaîne à lire pour trouver son identifiant, ou None si c'est déjà un UC…"""
    entree = entree.strip()
    if re.fullmatch(r"UC[A-Za-z0-9_-]{22}", entree):
        return None
    m = re.search(r"/channel/(UC[A-Za-z0-9_-]{22})", entree)
    if m:
        return None
    if entree.startswith("@"):
        return f"https://www.youtube.com/{entree}"
    m = re.search(r"youtube\.com/(@[^/?#]+|c/[^/?#]+|user/[^/?#]+)", entree)
    if m:
        return f"https://www.youtube.com/{m.group(1)}"
    raise ErreurYouTube(f"chaîne non reconnue : « {entree} » (attendu @pseudo, URL de chaîne ou UC…)")


def id_chaine(entree: str) -> str:
    m = re.search(r"(UC[A-Za-z0-9_-]{22})", entree)
    page = url_chaine(entree)
    if page is None and m:
        return m.group(1)
    html = _get(page)
    m = re.search(r'"(?:externalId|channelId)":"(UC[A-Za-z0-9_-]{22})"', html) or \
        re.search(r'<meta itemprop="(?:identifier|channelId)" content="(UC[A-Za-z0-9_-]{22})"', html)
    if not m:
        raise ErreurYouTube(f"identifiant de chaîne introuvable sur {page}")
    return m.group(1)


def lire_flux(xml: str) -> dict:
    racine = ET.fromstring(xml)
    videos = []
    for e in racine.findall("a:entry", NS):
        lien = e.find("a:link", NS)
        desc = e.find("media:group/media:description", NS)
        videos.append({
            "id": e.findtext("yt:videoId", "", NS),
            "titre": e.findtext("a:title", "", NS),
            "publiee": e.findtext("a:published", "", NS)[:10],
            "url": lien.get("href") if lien is not None else "",
            "short": "/shorts/" in (lien.get("href", "") if lien is not None else ""),
            "description": (desc.text or "").strip() if desc is not None else "",
        })
    return {"chaine": racine.findtext("a:title", "", NS), "videos": videos}


def cmd_videos(a) -> dict:
    ident = id_chaine(a.chaine)
    res = lire_flux(_get(f"https://www.youtube.com/feeds/videos.xml?channel_id={ident}"))
    res["shorts_masques"] = 0
    if not a.shorts:
        res["shorts_masques"] = sum(v["short"] for v in res["videos"])
        res["videos"] = [v for v in res["videos"] if not v["short"]]
    res["videos"] = res["videos"][:a.n]
    res["id_chaine"] = ident
    return res


def titre_video(vid: str) -> str:
    try:
        return json.loads(_get(f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"))["title"]
    except (ErreurYouTube, ValueError, KeyError):
        return ""


def _horodatage(s: float) -> str:
    s = int(s)
    return f"{s // 3600:d}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60:d}:{s % 60:02d}"


def paragraphes(segments: list[dict], duree: float = 60) -> list[tuple[float, str]]:
    """Regroupe les segments de sous-titres en blocs d'environ `duree` secondes, horodatés."""
    blocs, debut, courant = [], None, []
    for seg in segments:
        texte = re.sub(r"\s+", " ", seg["texte"].replace("\n", " ")).strip()
        if not texte or texte in ("[Music]", "[Musique]"):
            continue
        if debut is None:
            debut = seg["debut"]
        courant.append(texte)
        if seg["debut"] - debut >= duree:
            blocs.append((debut, " ".join(courant)))
            debut, courant = None, []
    if courant:
        blocs.append((debut or 0, " ".join(courant)))
    return blocs


def transcrire(vid: str, langues: list[str]) -> dict:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError as e:
        raise ErreurYouTube("paquet manquant : pip install youtube-transcript-api") from e
    proxy = os.environ.get("YOUTUBE_PROXY_URL", "").strip()
    kwargs = {}
    if proxy:
        from youtube_transcript_api.proxies import GenericProxyConfig
        kwargs["proxy_config"] = GenericProxyConfig(http_url=proxy, https_url=proxy)
    try:
        t = YouTubeTranscriptApi(**kwargs).fetch(vid, languages=langues)
    except Exception as e:  # le paquet lève une exception par cause : on garde le message, pas la trace
        message = str(e).strip().split("\n")[0] or e.__class__.__name__
        if "bot" in str(e).lower() or "blocked" in str(e).lower() or "IpBlocked" in e.__class__.__name__:
            message = ("YouTube bloque cette adresse (centre de données). Lancez la commande depuis votre "
                       "poste, ou réglez YOUTUBE_PROXY_URL.")
        raise ErreurYouTube(message) from e
    segments = [{"debut": s.start, "texte": s.text} for s in t]
    return {"id": vid, "langue": getattr(t, "language_code", ""), "automatique": getattr(t, "is_generated", None),
            "segments": segments}


def markdown_transcription(res: dict) -> str:
    url = f"https://www.youtube.com/watch?v={res['id']}"
    sortie = [f"# {res.get('titre') or res['id']}", "",
              f"Source : {url} · langue {res['langue'] or '?'}"
              f"{' (sous-titres automatiques)' if res.get('automatique') else ''}", ""]
    for debut, texte in paragraphes(res["segments"]):
        sortie += [f"**[{_horodatage(debut)}]** {texte}", ""]
    return "\n".join(sortie)


def main() -> int:
    ap = argparse.ArgumentParser(description="Dernières vidéos d'une chaîne YouTube, transcription d'une vidéo")
    sous = ap.add_subparsers(dest="cmd", required=True)
    v = sous.add_parser("videos", help="dernières vidéos d'une chaîne (flux RSS, sans clé)")
    v.add_argument("chaine", help="@pseudo, URL de chaîne ou identifiant UC…")
    v.add_argument("--n", type=int, default=15)
    v.add_argument("--shorts", action="store_true", help="garder les shorts")
    v.add_argument("--json", action="store_true")
    t = sous.add_parser("transcription", help="sous-titres d'une vidéo, en Markdown horodaté")
    t.add_argument("video", help="URL ou identifiant de la vidéo")
    t.add_argument("--langues", default="fr,en", help="ordre de préférence (défaut fr,en)")
    t.add_argument("--sortie", help="fichier Markdown à écrire (sinon sortie standard)")
    t.add_argument("--json", action="store_true")
    a = ap.parse_args()
    charger_env()

    try:
        if a.cmd == "videos":
            res = cmd_videos(a)
            if a.json:
                print(json.dumps(res, ensure_ascii=False, indent=2))
            else:
                print(f"{res['chaine']} — {len(res['videos'])} vidéos")
                for x in res["videos"]:
                    print(f"  {x['publiee']}  {x['id']}  {x['titre']}")
                if res["shorts_masques"]:
                    print(f"  ({res['shorts_masques']} shorts masqués, --shorts pour les voir ; le flux RSS "
                          "ne donne que les 15 dernières publications)")
            return 0
        vid = id_video(a.video)
        res = transcrire(vid, [l.strip() for l in a.langues.split(",") if l.strip()])
        res["titre"] = titre_video(vid)
    except ErreurYouTube as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
    texte = json.dumps(res, ensure_ascii=False, indent=2) if a.json else markdown_transcription(res)
    if a.sortie:
        cible = Path(a.sortie)
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(texte, encoding="utf-8")
        print(f"✓ {cible} ({len(res['segments'])} segments)", file=sys.stderr)
    else:
        print(texte)
    return 0


if __name__ == "__main__":
    sys.exit(main())
