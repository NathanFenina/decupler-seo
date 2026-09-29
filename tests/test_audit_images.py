"""Audit des images hors ligne : il bloque ce qui dégrade le LCP et le CLS, sans crier au loup."""

import json
import struct
import sys
import unittest

from _outils import SCRIPTS, DossierIsole, lancer

sys.path.insert(0, str(SCRIPTS))
import audit_images  # noqa: E402


def webp(largeur: int, hauteur: int, remplissage: int = 0) -> bytes:
    """En-tête WebP étendu (VP8X) valide, suivi d'octets de remplissage."""
    corps = b"VP8X" + struct.pack("<I", 10) + b"\x00" * 4 \
        + (largeur - 1).to_bytes(3, "little") + (hauteur - 1).to_bytes(3, "little")
    return b"RIFF" + struct.pack("<I", 4 + len(corps)) + b"WEBP" + corps + b"\x00" * remplissage


def png(largeur: int, hauteur: int) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", largeur, hauteur) + b"\x08\x02\x00\x00\x00"


PAGE_PROPRE = """<html><body><h1>Titre</h1>
<img src="hero.webp" alt="Atelier de reliure, presse et cuirs sur l'établi" width="1200" height="800" fetchpriority="high">
<p>Texte.</p>
<img src="schema.webp" alt="Les trois étapes du devis, de la visite à la signature" width="800" height="450" loading="lazy">
</body></html>"""


class TestAuditImagesLocal(DossierIsole):
    def auditer(self, *args):
        r = lancer("audit_images.py", *args, "--json", cwd=self.dossier)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        return r.returncode, json.loads(r.stdout)

    def messages(self, donnees, cle="erreurs"):
        return [m for p in donnees["pages"] for i in p["images"] for m in i[cle]]

    def test_page_propre_passe_en_strict(self):
        (self.dossier / "hero.webp").write_bytes(webp(1200, 800))
        (self.dossier / "schema.webp").write_bytes(webp(800, 450))
        self.ecrire("page.html", PAGE_PROPRE)
        code, d = self.auditer("page.html", "--strict")
        self.assertEqual(code, 0, d)
        self.assertEqual((d["erreurs"], d["avertissements"]), (0, 0), d)
        self.assertEqual(d["pages"][0]["images"][0]["reelles"], "1200x800")

    def test_lazy_sur_l_image_lcp_bloque(self):
        self.ecrire("page.html", '<body><h1>T</h1><img src="https://exemple.com/a.webp" alt="Façade rénovée" '
                                 'width="1200" height="800" loading="lazy"></body>')
        code, d = self.auditer("page.html", "--strict")
        self.assertEqual(code, 1)
        self.assertTrue(any("LCP" in m for m in self.messages(d)))

    def test_sans_strict_le_code_reste_zero(self):
        self.ecrire("page.html", '<body><h1>T</h1><img src="a.webp"></body>')
        code, d = self.auditer("page.html")
        self.assertEqual(code, 0)
        self.assertGreater(d["erreurs"], 0)

    def test_alt_absent_generique_et_dimensions(self):
        self.ecrire("page.html", '<body><h1>T</h1><img src="https://exemple.com/a.webp" fetchpriority="high">'
                                 '<img src="https://exemple.com/b.webp" alt="image" loading="lazy"></body>')
        _, d = self.auditer("page.html")
        erreurs = self.messages(d)
        self.assertTrue(any("alt absent" in m for m in erreurs))
        self.assertTrue(any("alt générique" in m for m in erreurs))
        self.assertTrue(any("width/height" in m for m in erreurs))

    def test_aspect_ratio_css_remplace_les_dimensions(self):
        self.ecrire("page.html", '<img src="https://exemple.com/a.webp" alt="Salle de réunion vide" '
                                 'style="aspect-ratio: 16/9" loading="lazy">')
        _, d = self.auditer("page.html")
        self.assertFalse(any("width/height" in m for m in self.messages(d)))

    def test_marqueur_provisoire_bloque(self):
        self.ecrire("page.html", '<body><h1>T</h1><img src="__IMG_HERO__" alt="Vue du chantier terminé" '
                                 'width="1200" height="800" fetchpriority="high"></body>')
        code, d = self.auditer("page.html", "--strict")
        self.assertEqual(code, 1)
        self.assertTrue(any("marqueur provisoire" in m for m in self.messages(d)))

    def test_fichier_trop_lourd(self):
        (self.dossier / "lourde.webp").write_bytes(webp(1200, 800, remplissage=320 * 1024))
        self.ecrire("page.html", '<body><h1>T</h1><img src="lourde.webp" alt="Bureau d\'accueil du cabinet" '
                                 'width="1200" height="800" fetchpriority="high"></body>')
        code, d = self.auditer("page.html", "--strict")
        self.assertEqual(code, 1)
        self.assertTrue(any("au-dessus du seuil de 200 Ko" in m for m in self.messages(d)))

    def test_format_ancien_accepte_dans_un_picture_moderne(self):
        seul = ('<img src="https://exemple.com/a.jpg" alt="Toiture en ardoise après réfection" '
                'width="800" height="600" loading="lazy">')
        self.ecrire("seul.html", seul)
        self.ecrire("picture.html", '<picture><source type="image/webp" srcset="a.webp">' + seul + "</picture>")
        _, d = self.auditer("seul.html")
        self.assertTrue(any("format jpeg" in m for m in self.messages(d, "avertissements")))
        _, d = self.auditer("picture.html")
        self.assertFalse(any("format jpeg" in m for m in self.messages(d, "avertissements")))

    def test_fragment_sans_h1_aucune_image_lcp(self):
        self.ecrire("figure.html", '<figure><img src="https://exemple.com/a.webp" alt="Plan de la zone" '
                                   'width="800" height="600" loading="lazy"></figure>')
        code, d = self.auditer("figure.html", "--strict")
        self.assertEqual(code, 0, d)
        self.assertFalse(d["pages"][0]["images"][0]["lcp"])

    def test_nom_non_descriptif_image_repetee_et_ratio(self):
        (self.dossier / "IMG_4837.png").write_bytes(png(3000, 1000))
        img = '<img src="IMG_4837.png" alt="Terrasse en bois exotique" width="800" height="600" loading="lazy">'
        self.ecrire("page.html", "<p>x</p>" + img + img)
        _, d = self.auditer("page.html")
        avert = self.messages(d, "avertissements")
        self.assertTrue(any("non descriptif" in m for m in avert))
        self.assertTrue(any("déjà utilisée" in m for m in avert))
        self.assertTrue(any("ratio déclaré" in m for m in avert))
        self.assertTrue(any("sans srcset" in m for m in avert))

    def test_image_hors_domaine(self):
        self.ecrire("page.html", '<img src="https://cdn.ailleurs.example/a.webp" alt="Vitrine de la boutique" '
                                 'width="800" height="600" loading="lazy">')
        _, d = self.auditer("page.html", "--domaine", "atlas-conseil.example")
        self.assertTrue(any("hébergée sur" in m for m in self.messages(d, "avertissements")))

    def test_dossier_et_chemins_racine(self):
        (self.dossier / "site" / "images").mkdir(parents=True)
        (self.dossier / "site" / "images" / "photo-equipe.webp").write_bytes(webp(800, 600))
        self.ecrire("site/a/index.html", '<img src="/images/photo-equipe.webp" alt="L\'équipe au complet" '
                                         'width="800" height="600" loading="lazy">')
        self.ecrire("site/b/index.html", PAGE_PROPRE)
        _, d = self.auditer("site")
        self.assertEqual(len(d["pages"]), 2)
        page_a = next(p for p in d["pages"] if p["page"].endswith("a/index.html"))
        self.assertEqual(page_a["images"][0]["reelles"], "800x600")

    def test_introuvable(self):
        r = lancer("audit_images.py", "absent.html", cwd=self.dossier)
        self.assertEqual(r.returncode, 2)


class TestDimensions(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(audit_images.dimensions(png(640, 480)), (640, 480))
        self.assertEqual(audit_images.dimensions(webp(1920, 1080)), (1920, 1080))
        self.assertEqual(audit_images.dimensions(b"GIF89a" + struct.pack("<HH", 32, 16)), (32, 16))
        jpeg = b"\xff\xd8" + b"\xff\xe0" + struct.pack(">H", 16) + b"\x00" * 14 \
            + b"\xff\xc0" + struct.pack(">HBHH", 17, 8, 600, 800) + b"\x00" * 10
        self.assertEqual(audit_images.dimensions(jpeg), (800, 600))
        self.assertIsNone(audit_images.dimensions(b"pas une image"))

    def test_alt(self):
        base = {"_dans_figure": False}
        self.assertTrue(audit_images.controler_alt({**base})[0])
        self.assertTrue(audit_images.controler_alt({**base, "alt": "IMG_1234.jpg"})[0])
        self.assertEqual(audit_images.controler_alt({**base, "alt": ""}), ([], []))
        self.assertTrue(audit_images.controler_alt({**base, "alt": "Photo de la façade"})[1])
        bourre = "plombier paris plombier urgence plombier pas cher"
        self.assertTrue(any("répétitif" in m for m in audit_images.controler_alt({**base, "alt": bourre})[1]))


if __name__ == "__main__":
    unittest.main()
