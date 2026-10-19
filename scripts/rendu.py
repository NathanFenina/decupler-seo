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
2 si le navigateur est introuvable. La sonde relève aussi les textes sous
12 px (plancher de lisibilité) et la suite des bandes pleine largeur, claires
ou non (règle d'alternance : deux claires de suite au plus) ; `--strict` fait
échouer sur ces deux mesures.

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

SONDE = """<script>window.addEventListener('load',function(){setTimeout(function(){
var r=document.documentElement,n=0,pires=[],W=r.clientWidth;
document.querySelectorAll('body *').forEach(function(e){
  var b=e.getBoundingClientRect();
  if(b.right>W+1){n++;
    if(pires.length<5)pires.push(e.tagName+'.'+(String(e.className)||'(sans classe)')
      +' right='+Math.round(b.right)+' w='+Math.round(b.width));}});
var p=0,pp=[];
document.querySelectorAll('body *').forEach(function(e){
  if(e.closest('svg,script,style,noscript')||!e.offsetParent)return;
  var t=Array.prototype.some.call(e.childNodes,function(c){return c.nodeType===3&&c.textContent.trim();});
  if(!t)return;var f=parseFloat(getComputedStyle(e).fontSize);
  if(f<12){p++;if(pp.length<5)pp.push(e.tagName+'.'+(String(e.className)||'-')+' '+f.toFixed(1)+'px');}});
function fond(e){for(;e&&e!==document.documentElement;e=e.parentElement){var s=getComputedStyle(e);
  if(s.backgroundImage&&s.backgroundImage!=='none')return 'R';
  var m=s.backgroundColor.match(/[\\d.]+/g);if(m&&(m.length<4||+m[3]>0.5)){
    var l=(0.2126*m[0]+0.7152*m[1]+0.0722*m[2])/255;return l>0.75?'C':'R';}}return 'C';}
function aImage(e){var i=e.querySelector('img');if(!i)return false;var b=i.getBoundingClientRect(),c=e.getBoundingClientRect();
  return b.width>=0.9*c.width&&b.height>=0.5*c.height;}
var best=null,bn=0;
document.querySelectorAll('body *').forEach(function(e){var k=0;
  for(var i=0;i<e.children.length;i++){var c=e.children[i].getBoundingClientRect();if(c.width>=0.9*W&&c.height>60)k++;}
  if(k>bn){bn=k;best=e;}});
var seq='';if(best){for(var i=0;i<best.children.length;i++){var c=best.children[i],q=c.getBoundingClientRect();
  if(q.width>=0.9*W&&q.height>60)seq+=aImage(c)?'R':fond(c);}}
var d=document.createElement('div');d.id='SONDE';
d.setAttribute('data-v',W);d.setAttribute('data-s',r.scrollWidth);
d.setAttribute('data-n',n);d.setAttribute('data-h',document.body.scrollHeight);
d.setAttribute('data-q',pires.join(' || '));
d.setAttribute('data-p',p);d.setAttribute('data-pq',pp.join(' || '));d.setAttribute('data-b',seq);
d.style.display='none';document.body.appendChild(d);},1500);});</script>"""

MOTIF_SONDE = re.compile(r'<div id="SONDE" data-v="(\d+)" data-s="(\d+)" data-n="(\d+)" data-h="(\d+)" data-q="([^"]*)"'
                         r'(?: data-p="(\d+)" data-pq="([^"]*)" data-b="([CR]*)")?')


def plus_longue_suite_claire(sequence: str) -> int:
    """Nombre maximal de bandes claires consécutives (C) dans une suite « CCRCC… ».

    Règle d'alternance (seo-design-pages, design-tokens § rythme) : jamais plus
    de deux bandes claires de suite sans une bande photo, sombre ou un ruban."""
    return max((len(m) for m in re.findall(r"C+", sequence or "")), default=0)


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
    v, s, n, h, q, p, pq, b = m.groups()
    return {"largeur": int(v), "scroll": int(s), "debordements": int(n), "hauteur": int(h),
            "coupables": [c for c in q.split(" || ") if c], "ok": v == s and n == "0",
            "petits": int(p or 0), "petits_exemples": [c for c in (pq or "").split(" || ") if c],
            "bandes": b or "", "suite_claire": plus_longue_suite_claire(b or "")}


def rendre(source: str, largeur: int, hauteur: int, chrome: str, cache: str | None, sortie: str) -> dict | None:
    if re.match(r"https?://", source):
        cible = source
        print("   URL distante : la sonde n'est posée que sur un fichier local (servez-le en HTTP sinon).")
    else:
        html, manquantes = localiser(Path(source).read_text(encoding="utf-8"), cache)
        if manquantes:
            print(f"   images absentes du cache (rendues vides) : {manquantes[:6]}")
        # À côté de la source, pas de la capture : une page qui charge ses
        # feuilles et ses images en chemins relatifs (un miroir local) les perd
        # si le fichier temporaire change de dossier, et la sonde mesure alors
        # une page sans styles.
        tempo = Path(source).resolve().parent / "_rendu.html"
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
    ap.add_argument("--strict", action="store_true",
                    help="échouer aussi sur un texte sous 12 px ou plus de 2 bandes claires de suite")
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
    print(f"   textes sous 12 px : {mesure['petits']}" + (f"  ({' ; '.join(mesure['petits_exemples'])})"
                                                          if mesure["petits_exemples"] else ""))
    if mesure["bandes"]:
        print(f"   bandes pleine largeur : {mesure['bandes']} (C claire, R rupture : photo, sombre, ruban) · "
              f"{mesure['suite_claire']} claire(s) de suite au plus"
              + ("  ✗ (2 au plus)" if mesure["suite_claire"] > 2 else "  ✓"))
    lisible = mesure["petits"] == 0 and mesure["suite_claire"] <= 2
    return 0 if mesure["ok"] and (lisible or not a.strict) else 1


if __name__ == "__main__":
    sys.exit(main())
