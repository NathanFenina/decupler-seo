"""copywriting.py : la grille mesurable d'une page commerciale (tirets, orientation lecteur, CTA…)."""

import sys
import unittest

from _outils import SCRIPTS

sys.path.insert(0, str(SCRIPTS))
import copywriting as CW  # noqa: E402

PLAT = """# Offre

Notre cabinet propose un accompagnement — complet et innovant — afin de répondre aux besoins des entreprises.
Cette prestation permet de comprendre les obligations. Il est important de noter que nous ne garantissons rien.
Nous ne faisons pas de prestations génériques. Nous n'avons aucun engagement de résultat.
"""

VENDEUR = """# Offre

Vous savez en une demi-journée ce que votre entreprise doit corriger, et dans quel ordre.

Bouton : [Demander un devis](/contact)

Votre équipe repart avec un registre à jour et une procédure claire. Par exemple, la veille d'un salon,
votre commercial sait quelles données il peut collecter.

[Échanger sur votre projet](/contact)

Vos questions trouvent une réponse sous 48 h. Concrètement, vous gardez la main sur chaque décision.

Bouton : [Contactez-nous](/contact)
"""


class Grille(unittest.TestCase):
    def mesure(self, texte):
        return CW.mesurer(CW.texte_markdown(texte), texte, "Cabinet")

    def test_texte_plat_penalise(self):
        r = self.mesure(PLAT)
        self.assertEqual(r["criteres"]["tirets"]["points"], 5)
        self.assertGreaterEqual(len(r["a_reprendre"]["explicatif"]), 3)
        self.assertGreaterEqual(len(r["a_reprendre"]["negations"]), 3)
        self.assertEqual(r["criteres"]["appels_a_l_action"]["points"], 0)

    def test_texte_vendeur_bien_note(self):
        r = self.mesure(VENDEUR)
        self.assertEqual(r["criteres"]["tirets"]["points"], 15)
        self.assertEqual(r["criteres"]["appels_a_l_action"]["points"], 15)
        self.assertEqual(r["criteres"]["accroche"]["points"], 5)
        self.assertGreater(r["score"], self.mesure(PLAT)["score"])

    def test_section_et_notes_ignorees(self):
        brut = "## Fiche\n\nNotre texte — interne.\n\n## Contenu\n\n> Note — interne.\n\nVous gagnez du temps.\n"
        lignes = CW.texte_markdown(CW.extraire_section(brut, "Contenu"))
        self.assertEqual(lignes, ["Vous gagnez du temps."])


if __name__ == "__main__":
    unittest.main()
