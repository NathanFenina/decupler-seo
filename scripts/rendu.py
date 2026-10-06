#!/usr/bin/env python3
"""Rend une page dans Chromium sans interface, et mesure les débordements dans le DOM.

    python3 rendu.py page.html                      # 1 440 px de large
    python3 rendu.py page.html 390 12000            # largeur, hauteur de capture
    python3 rendu.py fragment.html 390 --cache ./loc --sortie captures/page-390.png
    python3 rendu.py http://127.0.0.1:8000/page.html 1440 --chrome /chemin/chrome

Pourquoi : lire le HTML ne suffit pas (une photo rendue à 2 000 px et
rognée en silence par un overflow:hidden, une colonne vide, un texte
illisible sur une photo ne se voient qu'au rendu). Et la capture ne suffit
pas non plus : Chromium sans interface peut mettre en page à une largeur
et photographier à une autre, donc une capture montre parfois un défaut qui
n'existe pas, ou cache celui qui existe. D'où la sonde : injectée dans la
page, elle compte, après chargement des images, les éléments dont le bord
droit dépasse la largeur de la fenêtre. C'est elle qui fait foi.

Code de sortie 0 si scrollWidth == clientWidth et zéro débordement, 1 sinon,
2 si le navigateur est introuvable.

Un fragment (sans <html>) est enveloppé dans un document minimal. --cache
pointe vers un dossier d'images et de polices rapatriées en local : sans
lui, un rendu hors ligne part sans les visuels ni les polices du site, et on
juge une page qui n'est pas la sienne. Si le cache contient `fonts.css`, il
remplace les feuilles Google Fonts de la page.

Limite connue : Chromium sans interface ne descend pas sous une fenêtre
d'environ 500 px. Une demande à 390 px est rendue à ~500 : le script le
signale. Pour une vraie largeur mobile, émulation d'appareil (MCP Chrome
DevTools, Playwright) ; la sonde à 500 px attrape déjà l'essentiel.

Navigateur : --chrome, sinon la variable CHROME, sinon chromium/chrome du
PATH, sinon un Chromium installé par Playwright. Bibliothèque standard.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

SONDE = """<script>window.addEventListener('load',function(){
var r=document.documentElement,n=0,pires=[];
document.querySelectorAll('body *').forEach(function(e){
  var b=e.getBoundingClientRect();
  if(b.right>r.clientWidth+1){n++;
    if(pires.length<5)pires.push(e.tagName+'.'+(String(e.className)||'(sans classe)')
      +' right='+Math.round(b.right)+' w='+Math.round(b.width));}});
var d=document.createElement('div');d.id='SONDE';
d.setAttribute('data-v',r.clientWidth);d.setAttribute('data-s',r.scrollWidth);
d.setAttribute('data-n',n);d.setAttribute('data-h',document.body.scrollHeight);
d.setAttribute('data-q',pires.join(' || '));
d.style.display='none';document.body.appendChild(d);});</script>"""

MOTIF_SONDE = re.compile(r'<div id="SONDE" data-v="(\d+)" data-s="(\d+)" data-n="(\d+)" data-h="(\d+)" data-q="([^"]*)"')


def trouver_chrome(explicite: str | None = None) -> str | None:
    for candidat in (explicite, os.environ.get("CHROME")):
        if candidat and Path(candidat).is_file():
            return candidat
    for nom in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome"):
        if chemin := shutil.which(nom):
            return chemin
    motifs = ["/opt/pw-browsers/chromium-*/chrome-linux*/chrome",
              str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux*/chrome")]
    trouves = sorted(f for m in motifs for f in glob.glob(m))
    return trouves[-1] if trouves else None


def localiser(html: str, cache: str | None) -> tuple[str, list[str]]:
    """Remplace les images distantes par leur copie du cache, et Google Fonts par cache/fonts.css."""
    if not cache or not os.path.isdir(cache):
        return html, []
    manquantes = []
    for url in sorted(set(re.findall(r'src="(https?://[^"]+)"', html))):
        nom = os.path.basename(urllib.parse.unquote(url.split("?")[0]))
        local = os.path.join(cache, nom)
        if os.path.exists(local):
            html = html.replace(f'src="{url}"', f'src="{Path(local).resolve().as_uri()}"')
        else:
            manquantes.append(nom)
    css = os.path.join(cache, "fonts.css")
    if os.path.exists(css):
        feuille = Path(css).read_text(encoding="utf-8")
        html = re.sub(r"<link[^>]+fonts\.googleapis\.com[^>]*>", lambda _: f"<style>{feuille}</style>", html)
    return html, manquantes


def envelopper(html: str, langue: str = "fr") -> str:
    """Pose la sonde ; un fragment reçoit un document minimal autour de lui."""
    if re.search(r"<html[\s>]", html, re.I):
        if re.search(r"</head>", html, re.I):
            return re.sub(r"</head>", lambda _: SONDE + "</head>", html, count=1, flags=re.I)
        return re.sub(r"(<html[^>]*>)", lambda m: m.group(1) + "<head>" + SONDE + "</head>", html, count=1, flags=re.I)
    return (f'<!doctype html><html lang="{langue}"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'{SONDE}</head><body style="margin:0;background:#fff">{html}</body></html>')


def lire_sonde(dom: str) -> dict | None:
    m = MOTIF_SONDE.search(dom or "")
    if not m:
        return None
    v, s, n, h, q = m.groups()
    return {"largeur": int(v), "scroll": int(s), "debordements": int(n), "hauteur": int(h),
            "coupables": [c for c in q.split(" || ") if c], "ok": v == s and n == "0"}


def rendre(source: str, largeur: int, hauteur: int, chrome: str, cache: str | None, sortie: str) -> dict | None:
    if re.match(r"https?://", source):
        cible = source
        print("   URL distante : la sonde n'est posée que sur un fichier local (servez-le en HTTP sinon).")
    else:
        html, manquantes = localiser(Path(source).read_text(encoding="utf-8"), cache)
        if manquantes:
            print(f"   images absentes du cache (rendues vides) : {manquantes[:6]}")
        tempo = Path(sortie).resolve().parent / "_rendu.html"
        tempo.write_text(envelopper(html), encoding="utf-8")
        cible = tempo.as_uri()
    base = [chrome, "--headless", "--disable-gpu", "--no-sandbox"]
    dom = subprocess.run(base + [f"--window-size={largeur},900", "--virtual-time-budget=9000", "--dump-dom", cible],
                         capture_output=True, text=True, timeout=180).stdout
    mesure = lire_sonde(dom)
    subprocess.run(base + ["--hide-scrollbars", f"--window-size={largeur},{hauteur}", f"--screenshot={sortie}",
                           "--virtual-time-budget=11000", cible], capture_output=True, timeout=180)
    return mesure


def main() -> int:
    ap = argparse.ArgumentParser(description="Rendu Chromium + sonde de débordement dans le DOM")
    ap.add_argument("source", help="fichier HTML (page ou fragment) ou URL")
    ap.add_argument("largeur", nargs="?", type=int, default=1440)
    ap.add_argument("hauteur", nargs="?", type=int, default=16000)
    ap.add_argument("--cache", help="dossier d'images et de polices rapatriées en local")
    ap.add_argument("--sortie", help="capture PNG (défaut : <nom>-<largeur>.png)")
    ap.add_argument("--chrome", help="chemin du navigateur")
    a = ap.parse_args()
    chrome = trouver_chrome(a.chrome)
    if not chrome:
        print("  ✗ Chromium introuvable : --chrome, variable CHROME, ou `npx playwright install chromium`.",
              file=sys.stderr)
        return 2
    nom = Path(urllib.parse.urlparse(a.source).path).stem or "page"
    sortie = a.sortie or f"{nom}-{a.largeur}.png"
    Path(sortie).resolve().parent.mkdir(parents=True, exist_ok=True)
    mesure = rendre(a.source, a.largeur, a.hauteur, chrome, a.cache, sortie)
    print(f"   capture : {sortie}")
    if not mesure:
        print("   ⚠️ sonde muette : la page n'a pas fini de charger, ou c'est une URL distante.")
        return 1
    if mesure["largeur"] > a.largeur:
        print(f"   ! fenêtre réelle {mesure['largeur']} px au lieu de {a.largeur} : plancher du mode sans interface.")
    etat = "✓" if mesure["ok"] else "✗"
    print(f"   sonde {a.largeur}px : fenêtre={mesure['largeur']} scrollWidth={mesure['scroll']} "
          f"débordements={mesure['debordements']} hauteur={mesure['hauteur']}  {etat}")
    for c in mesure["coupables"]:
        print(f"      coupable : {c}")
    return 0 if mesure["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
