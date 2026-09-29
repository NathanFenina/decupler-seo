"""Lecteur de config : une clé mal lue désactive un garde-fou sans bruit."""

import os
import sys
import unittest

from _outils import SCRIPTS, DossierIsole

sys.path.insert(0, str(SCRIPTS))
import _projet  # noqa: E402

CONFIG = """# Configuration
mode: assisted                       # safe | assisted | autonomous

projet:
  nom: "Projet"
  domaine: "https://www.exemple.com"
  langues: [ar, en]
  concurrents:
    - "a.com"
    - "b.com"   # commentaire

regles:
  interdits:
    - "prix imbattable"
  mot_cle_occurrences_min:

publication:
  mode: depot
  statut_par_defaut: draft
"""


class TestLecteurConfig(DossierIsole):
    def setUp(self):
        super().setUp()
        self.ecrire("decupler-seo.config.yml", CONFIG)
        self._avant = os.getcwd()
        os.chdir(self.dossier)

    def tearDown(self):
        os.chdir(self._avant)
        super().tearDown()

    def test_mode_racine_et_mode_imbrique_sont_distincts(self):
        # Régression : publication.mode écrasait mode, et le projet passait en safe.
        self.assertEqual(_projet.lire_valeur("mode"), "assisted")
        self.assertEqual(_projet.lire_valeur("publication.mode"), "depot")

    def test_valeur_imbriquee_et_guillemets(self):
        self.assertEqual(_projet.lire_valeur("projet.domaine"), "https://www.exemple.com")

    def test_valeur_vide_renvoie_le_defaut(self):
        self.assertEqual(_projet.lire_valeur("regles.mot_cle_occurrences_min", "aucune"), "aucune")

    def test_cle_absente(self):
        self.assertEqual(_projet.lire_valeur("projet.inexistant", "x"), "x")
        self.assertEqual(_projet.lire_valeur("domaine", "x"), "x", "domaine n'est pas à la racine")

    def test_listes_en_bloc_et_en_ligne(self):
        self.assertEqual(_projet.lire_liste("projet.concurrents"), ["a.com", "b.com"])
        self.assertEqual(_projet.lire_liste("projet.langues"), ["ar", "en"])
        self.assertEqual(_projet.lire_liste("regles.interdits"), ["prix imbattable"])


if __name__ == "__main__":
    unittest.main()
