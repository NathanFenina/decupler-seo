"""Le contrôle qualité bloque la publication : il ne doit rater ni surbloquer."""

import json
import unittest

from _outils import DossierIsole, lancer


class TestControle(DossierIsole):
    def controler(self, *fichiers):
        r = lancer("controle_contenu.py", *fichiers, "--json", cwd=self.dossier)
        return r.returncode, json.loads(r.stdout)

    def test_contenu_propre_publiable(self):
        self.ecrire("page.html", "<html><head><title>Plombier à Lyon : dépannage en 2 h, devis gratuit</title>"
                    '<meta name="description" content="' + "x" * 150 + '"></head><body><h1>Titre</h1>'
                    '<img src="a.webp" alt="Intervention sur une fuite"><p>Texte.</p></body></html>')
        code, d = self.controler("page.html")
        self.assertEqual(code, 0, d)

    def test_title_d_un_svg_ignore(self):
        self.ecrire("page.html", '<html><head></head><body><svg role="img"><title>12</title><rect/></svg>'
                    "<title>Plombier à Lyon : dépannage en 2 h, devis gratuit</title>"
                    '<meta name="description" content="' + "x" * 150 + '"><h1>Titre</h1><p>Texte.</p></body></html>')
        code, d = self.controler("page.html")
        self.assertEqual(code, 0, d)                                    # le titre d'un graphique n'est pas le title

    def test_texte_provisoire_bloque(self):
        self.ecrire("a.md", "# Titre\n\nPrix : [à compléter].\n")
        code, d = self.controler("a.md")
        self.assertEqual(code, 1)

    def test_promesse_invérifiable_bloque(self):
        self.ecrire("a.md", "# Titre\n\nNous sommes le leader du marché, +500 clients.\n")
        code, _ = self.controler("a.md")
        self.assertEqual(code, 1)

    def test_tics_d_ecriture_seulement_signales(self):
        self.ecrire("a.md", "# Titre\n\nIl est important de noter que le délai est de 3 jours.\n")
        code, d = self.controler("a.md")
        self.assertEqual(code, 0)
        self.assertTrue(d["avertissements"])

    def test_meta_json_trop_longue(self):
        self.ecrire("fr.json", json.dumps({"meta": {"title": "t" * 82, "description": "d" * 150},
                                           "sections": [{"title": "Un titre de section très court"}]}))
        code, d = self.controler("fr.json")
        self.assertEqual(code, 1)
        self.assertTrue(any("meta.title" in e for e in d["erreurs"]))
        self.assertFalse(any("sections" in e for e in d["erreurs"]), "un titre de section n'est pas une balise title")

    def test_interdits_du_projet(self):
        self.ecrire("decupler-seo.config.yml", 'regles:\n  interdits:\n    - "prix imbattable"\n')
        self.ecrire("a.md", "# Titre\n\nUn prix imbattable pour tous.\n")
        code, d = self.controler("a.md")
        self.assertEqual(code, 1)
        self.assertTrue(any("interdit du projet" in e for e in d["erreurs"]))

    def test_image_sans_alt(self):
        self.ecrire("p.html", '<h1>T</h1><img src="a.webp">')
        code, _ = self.controler("p.html")
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
