"""photos_libres.py : tri des réponses de Wikimedia Commons, hors ligne."""

import sys
import unittest

from _outils import SCRIPTS

sys.path.insert(0, str(SCRIPTS))
import photos_libres as pl  # noqa: E402


def page(index, titre, l=2400, h=1200, mime="image/jpeg", licence="CC BY-SA 4.0", auteur="<a href='x'>Jeanne Dupont</a>"):
    return {"index": index, "title": titre, "imageinfo": [{
        "width": l, "height": h, "mime": mime, "url": f"https://upload.example/{index}.jpg",
        "thumburl": f"https://upload.example/thumb/{index}-1920px.jpg",
        "extmetadata": {"LicenseShortName": {"value": licence}, "Artist": {"value": auteur}}}]}


REPONSE = {"query": {"pages": {
    "3": page(3, "File:Port de la ville au coucher du soleil.jpg"),
    "1": page(1, "File:Plan de la ville 1789.jpg"),
    "2": page(2, "File:Vieux port vue aérienne.jpg", l=2000, h=1900),
    "4": page(4, "File:Quai photo.jpg", licence="All rights reserved"),
    "5": page(5, "File:Logo municipal.png", mime="image/png"),
    "6": page(6, "File:Panorama du quai.jpg", auteur=""),
    "7": page(7, "File:Cathédrale.svg", mime="image/svg+xml"),
}}}


class TestFiltre(unittest.TestCase):
    def test_garde_les_photos_paysage_sous_licence_libre(self):
        titres = [c["titre"] for c in pl.filtrer(REPONSE)]
        self.assertEqual(titres, ["File:Port de la ville au coucher du soleil.jpg", "File:Panorama du quai.jpg"])

    def test_credit_et_vignette(self):
        c = pl.filtrer(REPONSE)[0]
        self.assertEqual(c["auteur"], "Jeanne Dupont")
        self.assertEqual(c["credit"], "Photo : Jeanne Dupont, CC BY-SA 4.0, via Wikimedia Commons")
        self.assertIn("1920px", c["url"])
        self.assertTrue(c["page"].startswith("https://commons.wikimedia.org/wiki/File:"))

    def test_auteur_absent_dit_comme_tel(self):
        c = pl.filtrer(REPONSE)[1]
        self.assertEqual(c["auteur"], "auteur non indiqué")

    def test_portrait_et_limite(self):
        titres = [c["titre"] for c in pl.filtrer(REPONSE, portrait=True)]
        self.assertIn("File:Vieux port vue aérienne.jpg", titres)
        self.assertEqual(len(pl.filtrer(REPONSE, n=1)), 1)

    def test_reponse_vide(self):
        self.assertEqual(pl.filtrer({}), [])
        self.assertEqual(pl.filtrer({"query": {"pages": {}}}), [])

    def test_requete_api(self):
        params = pl.requete_api("Lyon", 12, 1920)
        self.assertEqual(params["iiurlwidth"], "1920")
        self.assertTrue(params["gsrsearch"].startswith("filetype:bitmap"))
        self.assertLessEqual(int(params["gsrlimit"]), 50)


if __name__ == "__main__":
    unittest.main()
