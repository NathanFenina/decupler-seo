#!/usr/bin/env python3
"""Génère une image pour un emplacement de page, avec le style du site et un alt proposé.

    python3 images_generer.py --sujet "Bureau de cabinet de conseil, dossiers ouverts" \\
        --emplacement hero --slug audit-financier --dry-run
    python3 images_generer.py --sujet "Toiture en ardoise vue de la rue" --emplacement contenu \\
        --titre "Rénover une toiture en ardoise" --section "Combien de temps dure le chantier ?" \\
        --palette "#1F4E79,#B4531A" --sortie images/

Moteurs, dans cet ordre (--moteur pour forcer) :

    gemini   GEMINI_API_KEY   modèle IMAGES_MODELE_GEMINI (défaut gemini-2.5-flash-image)
    openai   OPENAI_API_KEY   modèle IMAGES_MODELE_OPENAI (défaut gpt-image-1)

Emplacements : hero (16:9), contenu (3:2), og (16:9, à recadrer en 1200×630),
carre (1:1), portrait (4:5).

Le prompt impose les interdits d'une image de site professionnel : aucun
texte dans l'image (il va dans le HTML), aucun logo ni filigrane, aucun
visage reconnaissable (personne ne doit passer pour un salarié ou un
client). Style et palette : --style / --palette, ou `design.style_images` et
`design.palette` dans decupler-seo.config.yml.

Sortie : WebP quand c'est possible (OpenAI le produit ; Gemini via Pillow
s'il est installé), sinon PNG avec la commande de conversion. À côté, un
fichier .json : prompt, modèle, dimensions cibles, alt proposé dans la
langue de la page — à valider après avoir regardé l'image.

--dry-run (ou aucune clé) : affiche le prompt et la fiche, n'appelle rien,
ne facture rien. Sans dépendance ; Pillow facultatif.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _projet import charger_env, lire_liste, lire_valeur  # noqa: E402

EMPLACEMENTS = {
    "hero": {"ratio": "16:9", "cible": (1920, 1080), "openai": "1536x1024",
             "composition": "wide banner composition, main subject slightly off-centre, a calm uncluttered area "
                            "on one side, still readable when displayed small on a phone"},
    "contenu": {"ratio": "3:2", "cible": (1200, 800), "openai": "1536x1024",
                "composition": "editorial image for an article section, one clear focal subject, medium shot"},
    "og": {"ratio": "16:9", "cible": (1200, 630), "openai": "1536x1024",
           "composition": "social sharing card, subject centred with generous safe margins on every side, "
                          "it will be cropped to 1200x630"},
    "carre": {"ratio": "1:1", "cible": (1080, 1080), "openai": "1024x1024",
              "composition": "square composition, subject centred"},
    "portrait": {"ratio": "4:5", "cible": (1080, 1350), "openai": "1024x1536",
                 "composition": "vertical composition, subject centred, suited to a narrow column"},
}

STYLE_DEFAUT = ("clean contemporary editorial photography, natural light, realistic materials and textures, "
                "calm composition with negative space, professional but warm")

INTERDITS = [
    "No text of any kind: no letters, words, numbers, captions, labels, signage or handwriting.",
    "No logos, brand marks, trademarks, product packaging brands or watermarks.",
    "No recognizable faces: if people appear, show them from behind, at a distance, or only their hands at "
    "work. Never a portrait that could pass for a real employee, expert or customer.",
    "No user-interface screenshots, fake charts or dashboards, certificates, badges, awards or star ratings.",
    "No distorted anatomy or objects, no surreal elements, no clutter.",
]

LANGUES = {"fr": "French", "en": "English", "es": "Spanish", "de": "German", "it": "Italian",
           "pt": "Portuguese", "nl": "Dutch", "ar": "Arabic"}

PREFIXES_ALT = re.compile(
    r"^(une?\s+|la\s+|le\s+|les\s+)?(image|photo|photographie|illustration|visuel|picture|an?\s+image|"
    r"an?\s+photo|an?\s+picture)\s+(de\s+|d'|du\s+|des\s+|of\s+|showing\s+|représentant\s+)?", re.I)

ALT_MAX = 125


class ErreurImage(RuntimeError):
    pass


# ─── Fonctions pures (testées hors ligne) ─────────────────────────

def emplacement(nom: str) -> dict:
    if nom not in EMPLACEMENTS:
        raise ValueError(f"emplacement inconnu « {nom} » — choisir parmi : {', '.join(EMPLACEMENTS)}")
    return EMPLACEMENTS[nom]


def construire_prompt(sujet: str, nom_emplacement: str, *, titre: str = "", section: str = "",
                      style: str = "", palette: list[str] | tuple[str, ...] = (), langue: str = "fr") -> str:
    """Prompt en anglais (les modèles d'image le suivent mieux), sujet dans la langue de la page."""
    sujet = " ".join(sujet.split())
    if not sujet:
        raise ValueError("le sujet est vide : décrivez ce que l'image doit montrer")
    e = emplacement(nom_emplacement)
    lignes = [f"Create one photographic-quality image for a professional website ({nom_emplacement} slot).",
              f"Subject: {sujet}"]
    if titre.strip():
        lignes.append(f"Page it illustrates: {titre.strip()}")
    if section.strip():
        lignes.append(f"Section it illustrates: {section.strip()}")
    nom_langue = LANGUES.get(langue.lower(), langue)
    lignes.append(f"The descriptions above may be written in {nom_langue}: interpret them, never render them as text.")
    lignes.append(f"Composition: {e['composition']}. Aspect ratio {e['ratio']}.")
    lignes.append(f"Visual style: {style.strip() or STYLE_DEFAUT}.")
    couleurs = [c.strip() for c in palette if c.strip()]
    if couleurs:
        lignes.append("Colour palette: harmonise the scene with " + ", ".join(couleurs)
                      + " as natural accents in objects and light, not as flat overlays or filters.")
    lignes.append("Constraints:")
    lignes += [f"- {i}" for i in INTERDITS]
    return "\n".join(lignes)


def slugifier(texte: str, max_mots: int = 6) -> str:
    ascii_ = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode().lower()
    ascii_ = re.sub(r"[’']", " ", ascii_)
    mots = [m for m in re.findall(r"[a-z0-9]+", ascii_)
            if m not in {"de", "du", "des", "la", "le", "les", "un", "une", "et", "a", "au", "aux", "en",
                         "d", "l", "the", "of", "and", "with", "sur", "pour", "par"}]
    return "-".join(mots[:max_mots])


def nom_fichier(sujet: str, nom_emplacement: str, slug: str = "", extension: str = "webp") -> str:
    """[slug-de-la-page]-[emplacement]-[sujet court].webp : descriptif, unique, sans accents."""
    emplacement(nom_emplacement)
    parties = [slugifier(slug, 8) if slug else "", nom_emplacement, slugifier(sujet, 4)]
    return "-".join(p for p in parties if p) + "." + extension


def proposer_alt(sujet: str) -> str:
    """Alt de départ tiré du sujet : à réécrire d'après ce que l'image montre vraiment."""
    alt = PREFIXES_ALT.sub("", " ".join(sujet.split())).strip(" .;:")
    if not alt:
        return ""
    alt = alt[0].upper() + alt[1:]
    if len(alt) > ALT_MAX:
        alt = alt[:ALT_MAX].rsplit(" ", 1)[0].rstrip(",;:")
    return alt


def corps_gemini(prompt: str, ratio: str, avec_ratio: bool = True) -> dict:
    corps = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
             "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}}
    if avec_ratio:
        corps["generationConfig"]["imageConfig"] = {"aspectRatio": ratio}
    return corps


def corps_openai(prompt: str, taille: str, modele: str) -> dict:
    return {"model": modele, "prompt": prompt, "size": taille, "quality": "high", "n": 1,
            "output_format": "webp", "output_compression": 82}


def extraire_gemini(reponse: dict) -> tuple[bytes, str]:
    candidats = reponse.get("candidates") or []
    if not candidats:
        raise ErreurImage("aucune image renvoyée : " + json.dumps(reponse.get("promptFeedback") or {})[:300])
    textes = []
    for part in (candidats[0].get("content") or {}).get("parts") or []:
        donnees = part.get("inlineData") or part.get("inline_data")
        if donnees and donnees.get("data"):
            return base64.b64decode(donnees["data"]), donnees.get("mimeType") or donnees.get("mime_type") or "image/png"
        if part.get("text"):
            textes.append(part["text"])
    raise ErreurImage("le modèle a répondu sans image" + (f" : {' '.join(textes)[:300]}" if textes else ""))


def extraire_openai(reponse: dict) -> bytes:
    donnees = (reponse.get("data") or [{}])[0]
    if donnees.get("b64_json"):
        return base64.b64decode(donnees["b64_json"])
    raise ErreurImage("réponse OpenAI sans image")


def type_mime(octets: bytes) -> str:
    if octets[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if octets[:2] == b"\xff\xd8":
        return "image/jpeg"
    if octets[:4] == b"RIFF" and octets[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"


def fiche(fichier: str, sujet: str, nom_emplacement: str, prompt: str, moteur: str, modele: str,
          langue: str, recadrage: bool) -> dict:
    e = emplacement(nom_emplacement)
    return {
        "fichier": fichier, "emplacement": nom_emplacement, "ratio": e["ratio"],
        "dimensions_cibles": f"{e['cible'][0]}x{e['cible'][1]}", "recadrage_a_faire": recadrage,
        "moteur": moteur, "modele": modele, "langue": langue, "sujet": sujet,
        "alt_propose": proposer_alt(sujet), "legende": "", "a_valider": True,
        "consignes": [
            "Regarder l'image en taille réelle : mains, objets, perspective, texte parasite.",
            "Réécrire l'alt d'après ce que l'image montre réellement.",
            "Écrire une légende qui interprète l'image, si elle est dans le corps.",
            "Ne jamais l'utiliser comme preuve (équipe, client, chantier, résultat).",
        ],
        "date": date.today().isoformat(),
    }


# ─── Appels réseau ────────────────────────────────────────────────

def _post(url: str, corps: dict, entetes: dict, timeout: int = 240) -> dict:
    requete = urllib.request.Request(url, data=json.dumps(corps).encode(), method="POST",
                                     headers={"Content-Type": "application/json", **entetes})
    try:
        with urllib.request.urlopen(requete, timeout=timeout) as rep:
            return json.loads(rep.read())
    except urllib.error.HTTPError as exc:
        # Le corps d'erreur ne contient jamais la clé ; on le tronque quand même.
        raise ErreurImage(f"HTTP {exc.code} {exc.read()[:300].decode('utf-8', 'replace')}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ErreurImage(str(exc)[:200]) from None


def generer_gemini(prompt: str, ratio: str) -> tuple[bytes, str]:
    modele = os.environ.get("IMAGES_MODELE_GEMINI", "").strip() or "gemini-2.5-flash-image"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent"
    entetes = {"x-goog-api-key": os.environ["GEMINI_API_KEY"].strip()}
    try:
        reponse = _post(url, corps_gemini(prompt, ratio), entetes)
    except ErreurImage as exc:
        if "HTTP 400" not in str(exc):
            raise
        # Modèle qui ne connaît pas imageConfig : le ratio reste demandé dans le prompt.
        reponse = _post(url, corps_gemini(prompt, ratio, avec_ratio=False), entetes)
    octets, _ = extraire_gemini(reponse)
    return octets, modele


def generer_openai(prompt: str, taille: str) -> tuple[bytes, str]:
    modele = os.environ.get("IMAGES_MODELE_OPENAI", "").strip() or "gpt-image-1"
    reponse = _post("https://api.openai.com/v1/images/generations", corps_openai(prompt, taille, modele),
                    {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY'].strip()}"})
    return extraire_openai(reponse), modele


def en_webp(octets: bytes, cible: tuple[int, int], recadrer: bool) -> bytes | None:
    """Conversion WebP (et recadrage aux dimensions cibles) si Pillow est installé."""
    try:
        from PIL import Image
    except ImportError:
        return None
    image = Image.open(io.BytesIO(octets)).convert("RGB")
    if recadrer:
        l, h = image.size
        ratio_cible = cible[0] / cible[1]
        if l / h > ratio_cible:
            nl = int(h * ratio_cible)
            image = image.crop(((l - nl) // 2, 0, (l - nl) // 2 + nl, h))
        else:
            nh = int(l / ratio_cible)
            image = image.crop((0, (h - nh) // 2, l, (h - nh) // 2 + nh))
        image = image.resize(cible)
    elif image.size[0] > cible[0]:
        image = image.resize((cible[0], round(image.size[1] * cible[0] / image.size[0])))
    sortie = io.BytesIO()
    image.save(sortie, "WEBP", quality=82, method=6)
    return sortie.getvalue()


def choisir_moteur(demande: str) -> str | None:
    cles = {"gemini": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY"}
    ordre = [demande] if demande in cles else ["gemini", "openai"]
    return next((m for m in ordre if os.environ.get(cles[m], "").strip()), None)


# ─── Commande ─────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(description="Génère une image de page avec le style du site et un alt proposé")
    p.add_argument("--sujet", required=True, help="ce que l'image doit montrer, dans la langue de la page")
    p.add_argument("--emplacement", default="contenu", choices=list(EMPLACEMENTS))
    p.add_argument("--titre", default="", help="titre de la page illustrée")
    p.add_argument("--section", default="", help="intertitre de la section illustrée")
    p.add_argument("--style", default="", help="style visuel du site (sinon design.style_images)")
    p.add_argument("--palette", default="", help="couleurs du site, séparées par des virgules (sinon design.palette)")
    p.add_argument("--langue", default="", help="langue de la page (défaut : projet.langue_cible, sinon fr)")
    p.add_argument("--slug", default="", help="slug de la page : préfixe du nom de fichier")
    p.add_argument("--sortie", default="images", help="dossier de sortie (défaut : images/)")
    p.add_argument("--moteur", default="auto", choices=["auto", "gemini", "openai"])
    p.add_argument("--dry-run", action="store_true", help="affiche le prompt et la fiche, n'appelle aucune API")
    args = p.parse_args()

    charger_env()
    style = args.style or lire_valeur("design.style_images")
    palette = [c for c in args.palette.split(",") if c.strip()] or lire_liste("design.palette")
    langue = args.langue or lire_valeur("projet.langue_cible", "fr") or "fr"
    e = emplacement(args.emplacement)
    try:
        prompt = construire_prompt(args.sujet, args.emplacement, titre=args.titre, section=args.section,
                                   style=style, palette=palette, langue=langue)
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2
    recadrage = args.emplacement == "og"
    moteur = None if args.dry_run else choisir_moteur(args.moteur)

    if moteur is None:
        f = fiche(nom_fichier(args.sujet, args.emplacement, args.slug), args.sujet, args.emplacement, prompt,
                  "aucun", "", langue, recadrage)
        print(json.dumps({"prompt": prompt, "fiche": f}, ensure_ascii=False, indent=2))
        if not args.dry_run:
            print("\nAucune clé d'image configurée (GEMINI_API_KEY ou OPENAI_API_KEY) : rien n'a été généré.\n"
                  "Le prompt ci-dessus peut être collé tel quel dans un autre outil.", file=sys.stderr)
            return 2
        return 0

    try:
        if moteur == "gemini":
            octets, modele = generer_gemini(prompt, e["ratio"])
        else:
            octets, modele = generer_openai(prompt, e["openai"])
    except ErreurImage as exc:
        print(f"❌ {moteur} : {exc}", file=sys.stderr)
        return 1

    conversion = None
    if type_mime(octets) != "image/webp" or recadrage:
        conversion = en_webp(octets, e["cible"], recadrage)
    if conversion:
        octets, extension = conversion, "webp"
    else:
        extension = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}.get(type_mime(octets), "png")

    dossier = Path(args.sortie)
    dossier.mkdir(parents=True, exist_ok=True)
    nom = nom_fichier(args.sujet, args.emplacement, args.slug, extension)
    (dossier / nom).write_bytes(octets)
    f = fiche(nom, args.sujet, args.emplacement, prompt, moteur, modele, langue, recadrage and not conversion)
    (dossier / nom).with_suffix(".json").write_text(json.dumps(f, ensure_ascii=False, indent=2) + "\n",
                                                   encoding="utf-8")

    print(f"✅ {dossier / nom} · {len(octets) // 1024} Ko · {moteur} ({modele})")
    print(f"   alt proposé, à valider : {f['alt_propose']}")
    if extension != "webp":
        print(f"   Converti en WebP avant publication : cwebp -q 82 {dossier / nom} -o "
              f"{(dossier / nom).with_suffix('.webp')}  (ou pip install Pillow et relancez)")
    if f["recadrage_a_faire"]:
        print(f"   Recadrez en {f['dimensions_cibles']} pour le partage social.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
