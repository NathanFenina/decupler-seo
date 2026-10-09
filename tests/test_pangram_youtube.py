import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import pangram  # noqa: E402
import youtube  # noqa: E402


class TestPangram(unittest.TestCase):
    def test_texte_lisible_sans_front_matter_ni_url(self):
        brut = "---\ntitre: x\n---\n# Titre\n\nUn [lien](https://exemple.fr) ici.\n\n```\ncode\n```\n"
        texte = pangram.texte_lisible(brut, "md")
        self.assertNotIn("titre: x", texte)
        self.assertNotIn("https://", texte)
        self.assertNotIn("code", texte)
        self.assertIn("Un lien ici.", texte)

    def test_cout_par_tranche_de_100_mots(self):
        self.assertEqual(pangram.cout_estime(1), 0.05)
        self.assertEqual(pangram.cout_estime(100), 0.05)
        self.assertEqual(pangram.cout_estime(101), 0.10)

    def test_synthese_garde_les_passages_ia_et_humanises(self):
        texte = "Ligne humaine.\nLigne générée.\nLigne reformulée."
        res = {"stage": "STAGE_SUCCESS", "text": texte, "version": "4.0", "prediction_short": "Mixed",
               "headline": "Mixed", "fraction_ai": 0.3, "fraction_ai_assisted": 0.2, "fraction_human": 0.5,
               "windows": [
                   {"text": "Ligne humaine.", "label": "Human Written", "start_index": 0, "is_humanized": False},
                   {"text": "Ligne générée.", "label": "AI-Generated", "start_index": 15,
                    "ai_assistance_score": 0.97, "confidence": "High"},
                   {"text": "Ligne reformulée.", "label": "Human Written", "start_index": 30, "is_humanized": True},
               ]}
        s = pangram.synthese(res)
        self.assertEqual(s["part_ia_totale"], 0.5)
        self.assertTrue(s["humanise"])
        self.assertEqual([(p["ligne"], p["label"]) for p in s["passages"]], [(2, "IA"), (3, "humain")])

    def test_analyser_attend_la_fin_de_la_tache(self):
        appels = []

        def faux(methode, chemin, cle, corps=None, delai=60):
            appels.append((methode, chemin))
            if methode == "POST":
                self.assertEqual(corps["model"], "pangram-4")
                return {"task_id": "t1"}
            return {"stage": "STAGE_SUCCESS" if len(appels) > 2 else "STAGE_RUNNING", "text": "x"}

        origine = pangram.requete
        pangram.requete = faux
        try:
            res = pangram.analyser("x", "cle", pause=0)
        finally:
            pangram.requete = origine
        self.assertEqual(res["stage"], "STAGE_SUCCESS")
        self.assertEqual(appels, [("POST", "/task"), ("GET", "/task/t1"), ("GET", "/task/t1")])

    def test_echec_de_tache_leve_une_erreur(self):
        origine = pangram.requete
        pangram.requete = lambda m, c, k, corps=None, delai=60: (
            {"task_id": "t"} if m == "POST" else {"stage": "STAGE_FAILED", "headline": "texte trop court"})
        try:
            with self.assertRaises(pangram.ErreurAPI):
                pangram.analyser("x", "cle", pause=0)
        finally:
            pangram.requete = origine


FLUX = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/"
      xmlns="http://www.w3.org/2005/Atom">
 <title>Chaîne test</title>
 <entry><yt:videoId>AAAAAAAAAAA</yt:videoId><title>Vidéo longue</title>
  <link rel="alternate" href="https://www.youtube.com/watch?v=AAAAAAAAAAA"/>
  <published>2026-10-01T10:00:00+00:00</published>
  <media:group><media:description>Résumé</media:description></media:group></entry>
 <entry><yt:videoId>BBBBBBBBBBB</yt:videoId><title>Un short</title>
  <link rel="alternate" href="https://www.youtube.com/shorts/BBBBBBBBBBB"/>
  <published>2026-10-02T10:00:00+00:00</published></entry>
</feed>"""


class TestYouTube(unittest.TestCase):
    def test_id_video_depuis_toutes_les_formes_d_url(self):
        for entree in ("NoGGXMrDPYM", "https://www.youtube.com/watch?v=NoGGXMrDPYM&t=3",
                       "https://youtu.be/NoGGXMrDPYM?si=x", "https://www.youtube.com/shorts/NoGGXMrDPYM",
                       "https://www.youtube.com/live/NoGGXMrDPYM"):
            self.assertEqual(youtube.id_video(entree), "NoGGXMrDPYM")
        with self.assertRaises(youtube.ErreurYouTube):
            youtube.id_video("pas une vidéo")

    def test_chaine(self):
        self.assertEqual(youtube.url_chaine("@agricidaniel"), "https://www.youtube.com/@agricidaniel")
        self.assertEqual(youtube.url_chaine("https://youtube.com/@agricidaniel?si=x"),
                         "https://www.youtube.com/@agricidaniel")
        uc = "UCuCpyjRfW157950O5VBaWlw"
        self.assertIsNone(youtube.url_chaine(uc))
        self.assertEqual(youtube.id_chaine(f"https://www.youtube.com/channel/{uc}"), uc)

    def test_lire_flux_distingue_les_shorts(self):
        res = youtube.lire_flux(FLUX)
        self.assertEqual(res["chaine"], "Chaîne test")
        self.assertEqual([(v["id"], v["short"]) for v in res["videos"]],
                         [("AAAAAAAAAAA", False), ("BBBBBBBBBBB", True)])
        self.assertEqual(res["videos"][0]["publiee"], "2026-10-01")
        self.assertEqual(res["videos"][0]["description"], "Résumé")

    def test_paragraphes_horodates(self):
        segs = [{"debut": 0, "texte": "Bonjour"}, {"debut": 30, "texte": "[Music]"},
                {"debut": 61, "texte": "suite"}, {"debut": 70, "texte": "fin"}]
        self.assertEqual(youtube.paragraphes(segs), [(0, "Bonjour suite"), (70, "fin")])
        self.assertEqual(youtube._horodatage(3725), "1:02:05")


if __name__ == "__main__":
    unittest.main()
