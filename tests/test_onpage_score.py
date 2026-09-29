"""Le score on-page décide de ce qu'on réécrit : ses calculs doivent être exacts."""

import datetime as dt
import importlib.util
import json
import sys
import unittest

from _outils import SCRIPTS, DossierIsole, lancer

sys.path.insert(0, str(SCRIPTS))
import onpage_score as o  # noqa: E402

BS4 = importlib.util.find_spec("bs4") is not None


class TestCalculs(unittest.TestCase):
    def test_malus_par_palier(self):
        self.assertEqual([o.malus(d) for d in (0, 3.5, 3.6, 5, 5.1, 6.5, 6.6, 12)], [0, 0, 5, 5, 8, 8, 12, 12])

    def test_feu_de_densite(self):
        self.assertEqual(o.feu_densite(1.2), o.VERT)
        self.assertEqual(o.feu_densite(3.0), o.JAUNE)
        self.assertEqual(o.feu_densite(0.4), o.JAUNE)
        self.assertEqual(o.feu_densite(4.0), o.ROUGE)
        self.assertEqual(o.feu_densite(0.1), o.ROUGE)

    def test_points_jaune_arrondi_au_superieur(self):
        self.assertEqual([o.points(f, 5) for f in (o.VERT, o.JAUNE, o.ROUGE, o.NA)], [5, 3, 0, 0])

    def test_na_redistribue_au_prorata(self):
        criteres = [{"feu": o.VERT, "points": 4, "max": 4}, {"feu": o.ROUGE, "points": 0, "max": 4},
                    {"feu": o.NA, "points": 0, "max": 2}]
        self.assertEqual(o.score_bloc(criteres, 10), (5, True))
        sans_na = [{"feu": o.VERT, "points": 4, "max": 4}, {"feu": o.JAUNE, "points": 1, "max": 2}]
        self.assertEqual(o.score_bloc(sans_na, 6), (5, False))
        self.assertEqual(o.score_bloc([{"feu": o.NA, "points": 0, "max": 3}], 3), (None, True))

    def test_bandes(self):
        self.assertEqual([o.bande(s) for s in (100, 80, 79, 55, 54, 0)],
                         [o.VERT, o.VERT, o.JAUNE, o.JAUNE, o.ROUGE, o.ROUGE])

    def test_correspondance_distribuee_sans_mots_vides(self):
        texte = "Le prix d'une pompe à chaleur dépend de la puissance. Pompe à chaleur : quel prix ?"
        d = o.densites(texte, "prix pompe à chaleur")
        self.assertEqual(d["occurrences_exactes"], 0)
        self.assertEqual(d["occurrences_distribuees"], 2)
        self.assertEqual(d["effective"], d["distribuee"])

    def test_fenetre_trop_large_ne_compte_pas(self):
        texte = "prix " + "mot " * 10 + "pompe chaleur"
        self.assertEqual(o.occurrences_distribuees(o.jetons(texte), "prix pompe chaleur"), 0)

    def test_densite_exacte_tolere_accents_et_pluriel(self):
        d = o.densites("Les pompes à chaleur. " + "texte " * 96, "pompe a chaleur")
        self.assertEqual(d["occurrences_exactes"], 1)
        self.assertAlmostEqual(d["exacte"], 1.0)

    def test_presence_champ_court(self):
        self.assertEqual(o.presence("Pompe à chaleur : les prix 2026", "prix pompe à chaleur"), "complet")
        self.assertEqual(o.presence("Installer une pompe à chaleur", "prix pompe à chaleur"), "variante")
        self.assertEqual(o.presence("Nos prestations", "prix pompe à chaleur"), "absent")

    def test_lisibilite(self):
        phrases = o.decouper_phrases(["Le devis est établi par un technicien. Ensuite, nous posons l'appareil. "
                                      "Il s'est installé à Lyon. Il est allé sur place."])
        self.assertEqual(len(phrases), 4)
        self.assertEqual(o.pct_passif(phrases), 25.0)
        self.assertEqual(o.pct_transitions(phrases), 25.0)
        self.assertEqual(o.pct_phrases_longues(["mot " * 21, "court"]), 50.0)

    def test_fraicheur(self):
        auj = dt.date(2026, 9, 1)
        self.assertEqual(o.feu_fraicheur(o.dates_trouvees(["Mis à jour le 12/03/2026"]), auj)[0], o.VERT)
        self.assertEqual(o.feu_fraicheur(o.dates_trouvees(['"dateModified": "2024-01-10"']), auj)[0], o.JAUNE)
        self.assertEqual(o.feu_fraicheur([], auj)[0], o.ROUGE)


PAGE = """<html><head><title>Plombier à Lyon : dépannage en 2 h, devis gratuit 7j/7</title>
<meta name="description" content="{meta}"><link rel="canonical" href="https://exemple.com/plombier-lyon/"></head>
<body><h1>Plombier à Lyon</h1><p>{corps}</p><h2>Tarifs d'un plombier à Lyon</h2><p>Texte.</p></body></html>"""


@unittest.skipUnless(BS4, "beautifulsoup4 non installé")
class TestNotation(DossierIsole):
    def noter(self, html, *args):
        self.ecrire("page.html", html)
        r = lancer("onpage_score.py", "page.html", "plombier lyon", "--json", *args, cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def critere(self, res, nom):
        return next(c for c in res["criteres"] if c["critere"] == nom)

    def test_bourrage_applique_le_malus(self):
        res = self.noter(PAGE.format(meta="m" * 130, corps="plombier Lyon " * 20 + "réponse " * 40))
        self.assertGreater(res["densite"]["effective"], 6.5)
        self.assertEqual(res["malus"], 12)
        self.assertEqual(res["score"], max(0, res["score_brut"] - 12))
        self.assertEqual(self.critere(res, "Densité")["feu"], o.ROUGE)

    def test_fragment_sans_head_non_applicable(self):
        res = self.noter("<h1>Plombier à Lyon</h1><p>" + "texte " * 50 + "</p>")
        self.assertEqual(self.critere(res, "Title")["feu"], o.NA)
        self.assertTrue(res["sous_reserve"])

    def test_slug_teste_tous_les_mots(self):
        res = self.noter(PAGE.format(meta="m" * 130, corps="texte " * 50).replace("plombier-lyon", "plombier"))
        c = self.critere(res, "Mot-clé dans le slug")
        self.assertEqual(c["feu"], o.JAUNE)
        self.assertIn("lyon", c["constat"])

    def test_meta_zone_verte_120_156(self):
        res = self.noter(PAGE.format(meta="Plombier à Lyon " + "m" * 125, corps="texte " * 50))
        self.assertEqual(self.critere(res, "Longueur de la meta")["feu"], o.VERT)
        res = self.noter(PAGE.format(meta="Plombier à Lyon " + "m" * 145, corps="texte " * 50))
        self.assertEqual(self.critere(res, "Longueur de la meta")["feu"], o.JAUNE)

    def test_secondaires_et_na_declares(self):
        res = self.noter(PAGE.format(meta="m" * 130, corps="Dépannage urgent. " + "texte " * 50),
                         "--secondaires", "dépannage urgent, fuite", "--na", "FAQ")
        self.assertEqual(self.critere(res, "Mots-clés secondaires")["feu"], o.JAUNE)
        self.assertEqual(self.critere(res, "FAQ")["feu"], o.NA)


if __name__ == "__main__":
    unittest.main()
