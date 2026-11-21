"""La boucle de mesure : ses verdicts décident de ce qui sera annulé."""

import csv
import unittest
from pathlib import Path

from _outils import DossierIsole, lancer


class TestJournal(DossierIsole):
    def ajouter(self, type_="title", clics="40", impressions="3000", position="11"):
        return lancer("journal.py", "ajouter", "--url", "https://exemple.com/p", "--type", type_,
                      "--avant", "ancien", "--apres", "nouveau", "--clics", clics,
                      "--impressions", impressions, "--position", position, cwd=self.dossier)

    def mesurer(self, id_, *args):
        return lancer("journal.py", "mesurer", "--id", str(id_), *args, cwd=self.dossier)

    def lignes(self):
        with open(self.dossier / "journal" / "modifications.csv", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def verdict(self, id_):
        return next(l for l in self.lignes() if l["id"] == str(id_))["verdict"]

    def test_gain(self):
        self.ajouter()
        self.mesurer(1, "--clics", "96", "--impressions", "3300", "--temoin", "0")
        self.assertEqual(self.verdict(1), "gain")

    def test_le_temoin_neutralise_la_saison(self):
        # +17 % brut, mais le site entier a pris +12 % : l'effet réel est de +5 %.
        self.ajouter(clics="60", impressions="5000")
        self.mesurer(1, "--clics", "70", "--impressions", "5100", "--temoin", "12")
        self.assertEqual(self.verdict(1), "neutre")

    def test_perte(self):
        self.ajouter(clics="50", impressions="4000")
        self.mesurer(1, "--clics", "34", "--impressions", "3900", "--temoin", "12")
        self.assertEqual(self.verdict(1), "perte")

    def test_trop_peu_d_impressions(self):
        self.ajouter(clics="5", impressions="60")
        self.mesurer(1, "--clics", "9", "--impressions", "70")
        self.assertEqual(self.verdict(1), "insuffisant")

    def test_petite_page_jugee_sur_la_position(self):
        self.ajouter(clics="8", impressions="900", position="14")
        self.mesurer(1, "--clics", "11", "--impressions", "950", "--position", "9")
        self.assertEqual(self.verdict(1), "gain")

    def test_perte_proposee_au_retour_arriere(self):
        self.ajouter(clics="50", impressions="4000")
        self.mesurer(1, "--clics", "20", "--impressions", "3800")
        r = lancer("journal.py", "a-annuler", cwd=self.dossier)
        self.assertIn("ancien", r.stdout)

    def test_pas_d_apprentissage_sur_un_cas_isole(self):
        self.ajouter()
        self.mesurer(1, "--clics", "96", "--impressions", "3300")
        r = lancer("journal.py", "bilan", cwd=self.dossier)
        self.assertNotIn("À reporter", r.stdout)

    def test_apprentissage_a_partir_de_trois_mesures(self):
        for _ in range(3):
            self.ajouter()
        for i in (1, 2, 3):
            self.mesurer(i, "--clics", "90", "--impressions", "3200")
        r = lancer("journal.py", "bilan", cwd=self.dossier)
        self.assertIn("fonctionne sur ce site", r.stdout)

    def test_mesure_sans_chiffres_refusee_hors_mode_auto(self):
        self.ajouter()
        r = self.mesurer(1)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()


class TestBilanEcrit(DossierIsole):
    """Le bilan écrit lui-même les apprentissages : avant, il les affichait et personne ne les reportait."""

    def preparer(self, verdicts):
        (self.dossier / "journal").mkdir(exist_ok=True)
        entete = ("id,date,url,requete,type,niveau,avant,apres,clics_avant,impressions_avant,position_avant,"
                  "ctr_avant,date_mesure,clics_apres,impressions_apres,position_apres,ctr_apres,"
                  "variation_temoin_pct,verdict,note\n")
        lignes = [f"{i},2026-10-01,https://exemple.com/{i},,{t},auto,,,,,,,2026-10-29,,,,,,{v},\n"
                  for i, (t, v) in enumerate(verdicts, 1)]
        (self.dossier / "journal" / "modifications.csv").write_text(entete + "".join(lignes), encoding="utf-8")
        (self.dossier / "memoire").mkdir(exist_ok=True)
        (self.dossier / "memoire" / "apprentissages.md").write_text(
            "# Apprentissages\n\nNote écrite à la main.\n\n## Ce qui marche ici\n\n"
            "_(aucun apprentissage mesuré pour l'instant)_\n\n## Ce qui ne marche pas ici\n\n"
            "_(aucun apprentissage mesuré pour l'instant)_\n", encoding="utf-8")

    def contenu(self):
        return (self.dossier / "memoire" / "apprentissages.md").read_text(encoding="utf-8")

    def test_ecrit_ce_qui_nuit_et_garde_le_manuel(self):
        self.preparer([("title", "perte")] * 3 + [("title", "gain"), ("faq", "gain")])
        lancer("journal.py", "bilan", "--ecrire", cwd=self.dossier)
        texte = self.contenu()
        self.assertIn("« title » nuit souvent", texte)
        self.assertIn("Note écrite à la main.", texte)
        self.assertNotIn("faq", texte)  # 1 seule mesure : pas d'apprentissage

    def test_reecrit_le_bloc_sans_le_dupliquer(self):
        self.preparer([("meta", "gain")] * 3)
        lancer("journal.py", "bilan", "--ecrire", cwd=self.dossier)
        lancer("journal.py", "bilan", "--ecrire", cwd=self.dossier)
        texte = self.contenu()
        self.assertEqual(texte.count("journal.py bilan : début"), 1)
        self.assertIn("« meta » fonctionne", texte)
