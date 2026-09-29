#!/usr/bin/env python3
"""Audit des images — une page en ligne, ou des pages produites avant publication.

    python3 audit_images.py https://exemple.com/page                  # en ligne, poids réels
    python3 audit_images.py https://exemple.com/page --exporter images.csv
    python3 audit_images.py page-slug.html                           # fragment ou page, hors ligne
    python3 audit_images.py build/ --strict                          # tout un dossier ; code 1 si erreur
    python3 audit_images.py build/ --json --domaine exemple.com

Hors ligne, sans dépendance ni réseau : les images référencées en chemin
relatif sont lues sur le disque (poids, dimensions réelles) ; un chemin qui
commence par « / » se résout depuis --racine (par défaut le dossier audité).
Un fragment sans <body> ni <h1> est traité comme un composant posé plus bas
dans la page : ses images doivent être en loading="lazy", aucune n'est LCP.

Erreurs (bloquantes avec --strict) : alt absent ou générique, width/height
absents, loading="lazy" sur la première image (candidate LCP), marqueur
provisoire oublié (__IMG_…__, [crochets], {{ }}), image en base64 lourde,
fichier local au-dessus du seuil de poids.

Avertissements : format ancien sans source WebP/AVIF, fetchpriority absent
sur l'image LCP, lazy absent plus bas, alt trop long ou répétitif, nom de
fichier non descriptif, image beaucoup plus large que son affichage sans
srcset, ratio déclaré différent du ratio réel, même image répétée, image
hébergée hors du --domaine, plusieurs fetchpriority="high".
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import struct
import sys
import unicodedata
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

AGENT = "ClaudeCodeSEODecupler/2.0 (+https://decupler.com)"
MODERNES = {"webp", "avif", "svg"}
SEUIL_KO = 150
SEUIL_HERO_KO = 200
SEUIL_BASE64_KO = 2
ALT_MAX = 125
EXTENSIONS_HTML = {".html", ".htm"}
DOSSIERS_IGNORES = {"node_modules", ".git", ".next", "__pycache__"}

ALT_GENERIQUES = {
    "image", "images", "photo", "photos", "img", "picture", "hero", "banner", "banniere", "bannière",
    "illustration", "visuel", "cover", "cover image", "image de couverture", "untitled", "sans titre",
    "placeholder", "thumbnail", "vignette", "featured image", "image à la une",
}
MARQUEURS = re.compile(r"__IMG|\[[^\]]*\]|\{\{|(?-i:XXX)|placeholder", re.I)
NOM_NON_DESCRIPTIF = re.compile(
    r"^(img|dsc|dscn|dcim|pxl|mvimg|screenshot|screen[-_ ]?shot|capture[-_ ]d[-_ ]?[ée]cran|untitled|sans[-_ ]titre)"
    r"([-_ ]|\d|$)|^(image|photo|img|capture)[-_ ]?\d*$|^[\d_ -]+$", re.I)


# ─── Lecture des dimensions réelles, sans dépendance ───────────────

def dimensions(octets: bytes) -> tuple[int, int] | None:
    """(largeur, hauteur) d'une image PNG, GIF, JPEG, WebP ou AVIF, ou None."""
    try:
        if octets[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", octets[16:24])
        if octets[:6] in (b"GIF87a", b"GIF89a"):
            return struct.unpack("<HH", octets[6:10])
        if octets[:4] == b"RIFF" and octets[8:12] == b"WEBP":
            bloc = octets[12:16]
            if bloc == b"VP8X":
                l = int.from_bytes(octets[24:27], "little") + 1
                h = int.from_bytes(octets[27:30], "little") + 1
                return l, h
            if bloc == b"VP8 ":
                l, h = struct.unpack("<HH", octets[26:30])
                return l & 0x3FFF, h & 0x3FFF
            if bloc == b"VP8L":
                b = octets[21:25]
                l = 1 + (((b[1] & 0x3F) << 8) | b[0])
                h = 1 + (((b[3] & 0x0F) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
                return l, h
        if octets[:2] == b"\xff\xd8":
            i = 2
            while i + 9 < len(octets):
                if octets[i] != 0xFF:
                    i += 1
                    continue
                marqueur = octets[i + 1]
                if marqueur in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h, l = struct.unpack(">HH", octets[i + 5:i + 9])
                    return l, h
                if marqueur in (0xD8, 0x01) or 0xD0 <= marqueur <= 0xD7:
                    i += 2
                    continue
                i += 2 + struct.unpack(">H", octets[i + 2:i + 4])[0]
        if octets[4:8] == b"ftyp" and octets[8:12] in (b"avif", b"avis", b"mif1"):
            j = octets.find(b"ispe")
            if j > 0:
                return struct.unpack(">II", octets[j + 8:j + 16])
    except (struct.error, IndexError):
        return None
    return None


def format_de(src: str) -> str:
    if src.startswith("data:image/"):
        return src[11:].split(";", 1)[0].split("+", 1)[0].replace("jpg", "jpeg")
    chemin = urlparse(src).path.lower()
    for ext in ("avif", "webp", "svg", "jpeg", "jpg", "png", "gif"):
        if chemin.endswith("." + ext):
            return "jpeg" if ext == "jpg" else ext
    return "inconnu"


# ─── Extraction des images d'un document ──────────────────────────

class ExtracteurImages(HTMLParser):
    """Relève chaque <img> avec son contexte : <picture>, <figure>, <a>, <noscript>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.images: list[dict] = []
        self._sources: list[str] | None = None
        self._figure = 0
        self._noscript = 0
        self._srcset_picture = False
        self.est_une_page = False   # <body> ou <h1> : la première image est candidate LCP

    def handle_starttag(self, balise, attrs):
        a = {k: (v if v is not None else "") for k, v in attrs}
        if balise in ("body", "h1"):
            self.est_une_page = True
        if balise == "picture":
            self._sources, self._srcset_picture = [], False
        elif balise == "source" and self._sources is not None:
            self._sources.append((a.get("type") or format_de(a.get("srcset", "").split(" ")[0])).lower())
            self._srcset_picture = self._srcset_picture or "," in a.get("srcset", "")
        elif balise == "figure":
            self._figure += 1
        elif balise == "noscript":
            self._noscript += 1
        elif balise == "img" and not self._noscript:
            a["_sources"] = list(self._sources or [])
            a["_srcset_picture"] = self._srcset_picture if self._sources is not None else False
            a["_dans_figure"] = self._figure > 0
            a["_rang"] = len(self.images) + 1
            self.images.append(a)

    def handle_startendtag(self, balise, attrs):
        self.handle_starttag(balise, attrs)

    def handle_endtag(self, balise):
        if balise == "picture":
            self._sources = None
        elif balise == "figure":
            self._figure = max(0, self._figure - 1)
        elif balise == "noscript":
            self._noscript = max(0, self._noscript - 1)


def extraire(html: str) -> tuple[list[dict], bool]:
    """(images, est_une_page). Un fragment sans <body> ni <h1> est un composant
    posé plus bas dans une page : aucune de ses images n'est candidate LCP."""
    p = ExtracteurImages()
    p.feed(html)
    p.close()
    return p.images, p.est_une_page


def _entier(valeur: str) -> int | None:
    m = re.match(r"\s*(\d+)", valeur or "")
    return int(m.group(1)) if m else None


def _sans_accents(texte: str) -> str:
    return unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()


def controler_alt(img: dict) -> tuple[list[str], list[str]]:
    erreurs, avert = [], []
    if "alt" not in img:
        erreurs.append("alt absent — les lecteurs d'écran lisent le nom du fichier")
        return erreurs, avert
    alt = img["alt"].strip()
    if not alt:
        if img["_dans_figure"]:
            avert.append("alt vide sur une image de figure : est-elle vraiment décorative ?")
        return erreurs, avert
    norm = _sans_accents(alt.lower()).strip(" .")
    if norm in {_sans_accents(g) for g in ALT_GENERIQUES} or re.search(r"\.(jpe?g|png|webp|gif|avif|svg)$", norm) \
            or re.match(r"^(img|dsc|image|photo)[-_ ]?\d+$", norm):
        erreurs.append(f"alt générique (« {alt[:40]} ») — décrivez ce que montre l'image")
    elif re.match(r"^(image|photo|illustration|picture) (de|d'|du|des|of)\b", norm):
        avert.append("alt qui commence par « image de » / « photo de » — commencez par le sujet")
    if len(alt) > ALT_MAX:
        avert.append(f"alt de {len(alt)} caractères, au-delà de {ALT_MAX}")
    mots = [m for m in re.findall(r"\w+", norm) if len(m) >= 4]
    if mots and max(mots.count(m) for m in set(mots)) >= 3:
        avert.append("alt répétitif, probablement bourré de mots-clés")
    return erreurs, avert


def controler_nom(src: str) -> list[str]:
    if src.startswith("data:"):
        return []
    nom = unquote(Path(urlparse(src).path).name)
    tige = nom.rsplit(".", 1)[0]
    if not tige:
        return []
    avert = []
    if NOM_NON_DESCRIPTIF.search(tige):
        avert.append(f"nom de fichier non descriptif ({nom}) — [page]-[rôle].webp")
    elif tige != _sans_accents(tige) or re.search(r"[A-Z _]", tige):
        avert.append(f"nom de fichier à normaliser ({nom}) — minuscules, tirets, sans accents")
    return avert


def fichier_local(src: str, base: Path, racine: Path) -> Path | None:
    if not src or src.startswith(("data:", "http://", "https://", "//")) or MARQUEURS.search(src):
        return None
    chemin = unquote(src.split("?", 1)[0].split("#", 1)[0])
    return (racine / chemin.lstrip("/")) if chemin.startswith("/") else (base / chemin)


def analyser_images(images: list[dict], *, page: bool = True, base: Path | None = None,
                    racine: Path | None = None, domaine: str = "",
                    poids_distants: dict | None = None) -> tuple[list[dict], list[str]]:
    """Contrôle chaque image. Renvoie (lignes, avertissements de page)."""
    lignes, vus = [], {}
    lcp_trouvee = not page
    for img in images:
        src = (img.get("src") or "").strip()
        lazy_js = False
        if (not src or src.startswith("data:image/gif") or src.startswith("data:image/svg")) and img.get("data-src"):
            src, lazy_js = img["data-src"].strip(), True
        largeur, hauteur = _entier(img.get("width", "")), _entier(img.get("height", ""))
        petite = largeur is not None and largeur <= 64
        est_lcp = not lcp_trouvee and not petite
        lcp_trouvee = lcp_trouvee or est_lcp
        fmt = format_de(src)
        erreurs, avert = controler_alt(img)

        if not src or MARQUEURS.search(src):
            erreurs.append(f"marqueur provisoire ou src vide (« {src[:40]} ») — remplacez par l'URL réelle")
        if lazy_js:
            avert.append("chargement par data-src : sans JavaScript, l'image n'existe pas — préférez loading=\"lazy\"")
        if src.startswith("data:") and len(src) * 3 // 4 // 1024 > SEUIL_BASE64_KO:
            erreurs.append(f"image en base64 de {len(src) * 3 // 4 // 1024} Ko dans le HTML — hébergez-la")
        style = (img.get("style") or "").replace(" ", "").lower()
        if (largeur is None or hauteur is None) and "aspect-ratio" not in style:
            erreurs.append("width/height absents — l'espace n'est pas réservé, la page saute (CLS)")
        loading = (img.get("loading") or "").lower()
        if est_lcp and loading == "lazy":
            erreurs.append("loading=\"lazy\" sur la première image (candidate LCP) — retarde l'affichage")
        if est_lcp and (img.get("fetchpriority") or "").lower() != "high":
            avert.append("fetchpriority=\"high\" absent sur la première image (candidate LCP)")
        if not est_lcp and not petite and (img["_rang"] > 2 or not page) and loading != "lazy":
            avert.append("loading=\"lazy\" absent sur une image sous la ligne de flottaison")
        if fmt not in MODERNES and fmt != "inconnu" and not src.startswith("data:"):
            if not any(("webp" in t or "avif" in t) for t in img["_sources"]):
                avert.append(f"format {fmt} — servez du WebP ou de l'AVIF (au besoin dans un <picture>)")
        if src and not MARQUEURS.search(src):
            avert += controler_nom(src)
        a_srcset = bool(img.get("srcset")) or img["_srcset_picture"]
        if src in vus and src:
            avert.append(f"image déjà utilisée plus haut (image n° {vus[src]}) — un visuel par emplacement")
        vus.setdefault(src, img["_rang"])
        hote = urlparse(src).netloc.lower().removeprefix("www.")
        if domaine and hote and not hote.endswith(domaine.lower().removeprefix("www.")):
            avert.append(f"image hébergée sur {hote} — hébergez-la sur le site")

        ko, reelles = None, None
        local = fichier_local(src, base, racine or base) if base else None
        if local is not None:
            if local.is_file():
                octets = local.read_bytes()
                ko, reelles = len(octets) // 1024, dimensions(octets[:256 * 1024])
            else:
                avert.append(f"fichier introuvable sur le disque ({local.name}) — poids non vérifié")
        elif poids_distants is not None:
            ko = poids_distants.get(src)
        seuil = SEUIL_HERO_KO if est_lcp else SEUIL_KO
        if ko is not None and ko > seuil:
            erreurs.append(f"{ko} Ko, au-dessus du seuil de {seuil} Ko")
        if reelles and largeur:
            if reelles[0] > 2.5 * largeur and not a_srcset:
                avert.append(f"image de {reelles[0]} px affichée en {largeur} px sans srcset — redimensionnez")
            if hauteur and reelles[1] and abs(reelles[0] / reelles[1] - largeur / hauteur) > 0.03 * (largeur / hauteur):
                avert.append(f"ratio déclaré {largeur}×{hauteur} ≠ ratio réel {reelles[0]}×{reelles[1]}")
        elif not a_srcset and ((ko or 0) > 100 or (largeur or 0) >= 1000):
            avert.append("pas de srcset — le mobile télécharge l'image desktop")

        lignes.append({
            "rang": img["_rang"], "src": src, "format": fmt, "poids_ko": ko,
            "width": img.get("width", ""), "height": img.get("height", ""),
            "reelles": f"{reelles[0]}x{reelles[1]}" if reelles else "",
            "alt": img.get("alt"), "loading": loading, "fetchpriority": img.get("fetchpriority", ""),
            "srcset": a_srcset, "lcp": est_lcp, "erreurs": erreurs, "avertissements": avert,
        })
    page = []
    if sum(1 for i in images if (i.get("fetchpriority") or "").lower() == "high") > 1:
        page.append("plusieurs images en fetchpriority=\"high\" — une seule image est l'élément LCP")
    return lignes, page


# ─── Modes ────────────────────────────────────────────────────────

def pages_locales(cible: Path) -> list[Path]:
    if cible.is_file():
        return [cible]
    return sorted(p for p in cible.rglob("*") if p.suffix.lower() in EXTENSIONS_HTML
                  and not DOSSIERS_IGNORES.intersection(p.parts))


def auditer_local(cible: Path, racine: Path | None, domaine: str) -> list[dict]:
    racine = racine or (cible if cible.is_dir() else cible.parent)
    resultats = []
    for page in pages_locales(cible):
        images, est_une_page = extraire(page.read_text(encoding="utf-8", errors="replace"))
        lignes, avert_page = analyser_images(images, page=est_une_page, base=page.parent, racine=racine,
                                             domaine=domaine)
        resultats.append({"page": str(page), "images": lignes, "avertissements_page": avert_page})
    return resultats


def _requete(url: str, methode: str = "GET") -> urllib.request.Request:
    return urllib.request.Request(url, method=methode, headers={"User-Agent": AGENT})


def poids_distant(url: str) -> int | None:
    """Poids en Ko : HEAD d'abord, GET en repli."""
    try:
        with urllib.request.urlopen(_requete(url, "HEAD"), timeout=15) as rep:
            taille = rep.headers.get("Content-Length")
        if taille:
            return int(taille) // 1024
        with urllib.request.urlopen(_requete(url), timeout=20) as rep:
            return len(rep.read()) // 1024
    except (urllib.error.URLError, OSError, ValueError):
        return None


def auditer_url(url: str, domaine: str, sans_poids: bool) -> list[dict]:
    with urllib.request.urlopen(_requete(url), timeout=30) as rep:
        html = rep.read().decode(rep.headers.get_content_charset() or "utf-8", errors="replace")
    images, _ = extraire(html)
    for img in images:
        for cle in ("src", "data-src"):
            if img.get(cle) and not img[cle].startswith("data:") and not MARQUEURS.search(img[cle]):
                img[cle] = urljoin(url, img[cle].strip())
    poids = {}
    if not sans_poids:
        for img in images:
            src = img.get("src") or img.get("data-src") or ""
            if src.startswith("http") and src not in poids:
                poids[src] = poids_distant(src)
    domaine = domaine or urlparse(url).netloc
    lignes, avert_page = analyser_images(images, domaine=domaine, poids_distants=poids)
    return [{"page": url, "images": lignes, "avertissements_page": avert_page}]


# ─── Sorties ──────────────────────────────────────────────────────

def totaux(resultats: list[dict]) -> tuple[int, int]:
    e = sum(len(i["erreurs"]) for r in resultats for i in r["images"])
    a = sum(len(i["avertissements"]) for r in resultats for i in r["images"]) \
        + sum(len(r["avertissements_page"]) for r in resultats)
    return e, a


def exporter_csv(resultats: list[dict], chemin: str) -> None:
    champs = ["page", "rang", "src", "format", "poids_ko", "width", "height", "reelles", "alt",
              "loading", "fetchpriority", "srcset", "lcp", "erreurs", "avertissements"]
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        for r in resultats:
            for i in r["images"]:
                w.writerow({**{k: i.get(k, "") for k in champs}, "page": r["page"],
                            "erreurs": " · ".join(i["erreurs"]), "avertissements": " · ".join(i["avertissements"])})


def afficher(resultats: list[dict]) -> None:
    erreurs, avert = totaux(resultats)
    nb = sum(len(r["images"]) for r in resultats)
    total_ko = sum(i["poids_ko"] or 0 for r in resultats for i in r["images"])
    print(f"\n{'═' * 62}")
    print(f"  {len(resultats)} page(s) · {nb} image(s)" + (f" · {total_ko} Ko au total" if total_ko else ""))
    print(f"  {'🔴' if erreurs else '🟢'} {erreurs} erreur(s)   {'🟠' if avert else '🟢'} {avert} avertissement(s)")
    print(f"{'═' * 62}\n")
    for r in resultats:
        a_dire = [i for i in r["images"] if i["erreurs"] or i["avertissements"]]
        if not a_dire and not r["avertissements_page"]:
            continue
        print(f"── {r['page']}")
        for message in r["avertissements_page"]:
            print(f"   🟠 {message}")
        for i in a_dire[:20]:
            print(f"   #{i['rang']} {(i['src'] or '(sans src)')[-60:]}{'  [LCP]' if i['lcp'] else ''}")
            for m in i["erreurs"]:
                print(f"      🔴 {m}")
            for m in i["avertissements"]:
                print(f"      🟠 {m}")
        if len(a_dire) > 20:
            print(f"   … et {len(a_dire) - 20} autres images")
        print()


def main() -> int:
    p = argparse.ArgumentParser(description="Audit des images : page en ligne, fichier HTML ou dossier")
    p.add_argument("cible", help="URL, fichier .html ou dossier")
    p.add_argument("--exporter", help="CSV détaillé (par défaut images.csv pour une URL)")
    p.add_argument("--sans-poids", action="store_true", help="URL : ne télécharge pas les images")
    p.add_argument("--racine", help="dossier servi à la racine du site, pour les chemins « /… »")
    p.add_argument("--domaine", default="", help="domaine du site : signale les images hébergées ailleurs")
    p.add_argument("--json", action="store_true", help="sortie JSON")
    p.add_argument("--strict", action="store_true", help="code de sortie 1 s'il y a au moins une erreur")
    args = p.parse_args()

    if args.cible.startswith(("http://", "https://")):
        try:
            resultats = auditer_url(args.cible, args.domaine, args.sans_poids)
        except (urllib.error.URLError, OSError) as exc:
            print(f"Page inaccessible : {exc}", file=sys.stderr)
            return 2
        exporter = args.exporter or "images.csv"
    else:
        cible = Path(args.cible)
        if not cible.exists():
            print(f"Introuvable : {cible}", file=sys.stderr)
            return 2
        resultats = auditer_local(cible, Path(args.racine) if args.racine else None, args.domaine)
        exporter = args.exporter

    if exporter:
        exporter_csv(resultats, exporter)
    erreurs, avert = totaux(resultats)
    if args.json:
        print(json.dumps({"pages": resultats, "erreurs": erreurs, "avertissements": avert},
                         ensure_ascii=False, indent=2))
    else:
        afficher(resultats)
        if exporter:
            print(f"Détail complet dans {exporter}\n")
    return 1 if args.strict and erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
