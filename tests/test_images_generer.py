"""Génération d'images : prompt, nommage, alt et formats des API, sans jamais appeler une API payante."""

import base64
import json
import sys
import unittest

from _outils import SCRIPTS, DossierIsole, lancer

sys.path.insert(0, str(SCRIPTS))
import images_generer as ig  # noqa: E402

SANS_CLES = {"GEMINI_API_KEY": "", "OPENAI_API_KEY": ""}


class TestPrompt(unittest.TestCase):
    def test_interdits_ratio_et_contexte(self):
        prompt = ig.construire_prompt("Toiture en ardoise vue de la rue", "hero",
                                      titre="Rénover une toiture", section="Combien de temps ?",
                                      palette=["#1F4E79", " #B4531A "], langue="fr")
        self.assertIn("Aspect ratio 16:9", prompt)
        self.assertIn("Toiture en ardoise", prompt)
        self.assertIn("Rénover une toiture", prompt)
        self.assertIn("Combien de temps ?", prompt)
        self.assertIn("#1F4E79, #B4531A", prompt)
        self.assertIn("French", prompt)
        for interdit in ("No text", "No logos", "No recognizable faces", "watermarks"):
            self.assertIn(interdit, prompt)

    def test_style_par_defaut_et_style_du_site(self):
        self.assertIn(ig.STYLE_DEFAUT, ig.construire_prompt("Atelier", "contenu"))
        prompt = ig.construire_prompt("Atelier", "contenu", style="flat vector illustration, two colours")
        self.assertIn("flat vector illustration", prompt)
        self.assertNotIn(ig.STYLE_DEFAUT, prompt)

    def test_emplacements(self):
        self.assertIn("3:2", ig.construire_prompt("Atelier", "contenu"))
        self.assertIn("1200x630", ig.construire_prompt("Atelier", "og"))
        with self.assertRaises(ValueError):
            ig.construire_prompt("Atelier", "banniere")
        with self.assertRaises(ValueError):
            ig.construire_prompt("   ", "hero")


class TestNommageEtAlt(unittest.TestCase):
    def test_nom_de_fichier(self):
        self.assertEqual(ig.nom_fichier("Façade rénovée d'un immeuble haussmannien", "hero", "Ravalement Paris"),
                         "ravalement-paris-hero-facade-renovee-immeuble-haussmannien.webp")
        self.assertEqual(ig.nom_fichier("Plan de travail", "contenu", extension="png"), "contenu-plan-travail.png")

    def test_alt_propose(self):
        self.assertEqual(ig.proposer_alt("photo de la façade rénovée."), "La façade rénovée")
        self.assertEqual(ig.proposer_alt("An image of a quiet office"), "A quiet office")
        long = ig.proposer_alt("Atelier " + "très lumineux " * 20)
        self.assertLessEqual(len(long), ig.ALT_MAX)
        self.assertFalse(long.endswith(" "))

    def test_fiche_a_valider(self):
        f = ig.fiche("a.webp", "Bureau calme", "og", "prompt", "gemini", "m", "fr", True)
        self.assertTrue(f["a_valider"])
        self.assertEqual(f["dimensions_cibles"], "1200x630")
        self.assertEqual(f["alt_propose"], "Bureau calme")


class TestFormatsDesApi(unittest.TestCase):
    def test_corps(self):
        g = ig.corps_gemini("p", "16:9")
        self.assertEqual(g["generationConfig"]["imageConfig"]["aspectRatio"], "16:9")
        self.assertNotIn("imageConfig", ig.corps_gemini("p", "16:9", avec_ratio=False)["generationConfig"])
        o = ig.corps_openai("p", "1536x1024", "gpt-image-1")
        self.assertEqual((o["size"], o["output_format"]), ("1536x1024", "webp"))

    def test_extraction(self):
        png = b"\x89PNG\r\n\x1a\nxxxx"
        rep = {"candidates": [{"content": {"parts": [{"text": "voici"},
                                                     {"inlineData": {"mimeType": "image/png",
                                                                     "data": base64.b64encode(png).decode()}}]}}]}
        self.assertEqual(ig.extraire_gemini(rep), (png, "image/png"))
        with self.assertRaises(ig.ErreurImage):
            ig.extraire_gemini({"candidates": [{"content": {"parts": [{"text": "je ne peux pas"}]}}]})
        with self.assertRaises(ig.ErreurImage):
            ig.extraire_gemini({"promptFeedback": {"blockReason": "SAFETY"}})
        webp = b"RIFF\x00\x00\x00\x00WEBPVP8X"
        self.assertEqual(ig.extraire_openai({"data": [{"b64_json": base64.b64encode(webp).decode()}]}), webp)
        self.assertEqual(ig.type_mime(webp), "image/webp")
        self.assertEqual(ig.type_mime(png), "image/png")


class TestCommande(DossierIsole):
    def test_dry_run_n_appelle_rien(self):
        r = lancer("images_generer.py", "--sujet", "Bureau de cabinet de conseil", "--emplacement", "hero",
                   "--slug", "audit-financier", "--dry-run", cwd=self.dossier, **SANS_CLES)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertIn("No text", d["prompt"])
        self.assertEqual(d["fiche"]["fichier"], "audit-financier-hero-bureau-cabinet-conseil.webp")
        self.assertEqual(d["fiche"]["moteur"], "aucun")
        self.assertFalse((self.dossier / "images").exists())

    def test_sans_cle_ne_genere_rien(self):
        r = lancer("images_generer.py", "--sujet", "Bureau calme", cwd=self.dossier, **SANS_CLES)
        self.assertEqual(r.returncode, 2)
        self.assertIn("Aucune clé", r.stderr)
        self.assertFalse((self.dossier / "images").exists())

    def test_palette_et_style_lus_dans_la_config(self):
        self.ecrire("decupler-seo.config.yml", 'projet:\n  langue_cible: en\n'
                    'design:\n  palette: ["#123456", "#ABCDEF"]\n  style_images: "soft watercolour"\n')
        r = lancer("images_generer.py", "--sujet", "Quiet office", "--dry-run", cwd=self.dossier, **SANS_CLES)
        d = json.loads(r.stdout)
        self.assertIn("#123456, #ABCDEF", d["prompt"])
        self.assertIn("soft watercolour", d["prompt"])
        self.assertEqual(d["fiche"]["langue"], "en")


if __name__ == "__main__":
    unittest.main()
