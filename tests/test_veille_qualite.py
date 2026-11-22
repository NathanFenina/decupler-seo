"""veille_qualite.py : historique des notes, classement, corrélation avec les mesures J+28."""
import json
import unittest

from _outils import DossierIsole, lancer


class TestVeilleQualite(DossierIsole):
    def noter(self, url, a, b, c, d, e, date):
        r = lancer("veille_qualite.py", "ajouter", "--url", url, "--motcle", "m",
                   "--a", str(a), "--b", str(b), "--c", str(c), "--d", str(d), "--e", str(e),
                   "--date", date, cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_classement_plus_faibles_dabord_avec_evolution(self):
        self.noter("https://ex.fr/a", 18, 18, 18, 18, 18, "2026-10-01")
        self.noter("https://ex.fr/b", 10, 12, 8, 4, 15, "2026-10-01")
        self.noter("https://ex.fr/b/", 12, 14, 10, 9, 15, "2026-11-01")
        r = lancer("veille_qualite.py", "classement", "--json", cwd=self.dossier)
        rang = json.loads(r.stdout)
        self.assertEqual(rang[0]["url"], "https://ex.fr/b/")  # la plus faible, URL normalisée
        self.assertEqual(rang[0]["total"], 60)
        self.assertEqual(rang[0]["evolution"], 11)
        self.assertEqual(rang[0]["bloc_faible"], "GEO")
        self.assertIsNone(rang[1]["evolution"])

    def test_refuse_un_bloc_hors_bareme(self):
        r = lancer("veille_qualite.py", "ajouter", "--url", "u", "--motcle", "m", "--a", "25",
                   "--b", "1", "--c", "1", "--d", "1", "--e", "1", cwd=self.dossier)
        self.assertNotEqual(r.returncode, 0)

    def test_correlation_avec_le_journal(self):
        self.noter("https://ex.fr/haute", 18, 17, 17, 17, 17, "2026-09-01")  # 86
        self.noter("https://ex.fr/basse", 10, 10, 10, 10, 10, "2026-09-01")  # 50
        (self.dossier / "journal").mkdir()
        lignes = ["id,date,url,verdict"]
        lignes += [f"{i},2026-09-10,https://ex.fr/haute,gain" for i in range(3)]
        lignes += [f"{i},2026-09-10,https://ex.fr/basse,perte" for i in range(3, 6)]
        lignes += ["9,2026-08-01,https://ex.fr/haute,perte"]  # avant toute note : ignorée
        (self.dossier / "journal" / "modifications.csv").write_text("\n".join(lignes) + "\n", encoding="utf-8")
        r = json.loads(lancer("veille_qualite.py", "correler", "--json", cwd=self.dossier).stdout)
        self.assertEqual(r["taux_gain_haute"], 100)
        self.assertEqual(r["taux_gain_basse"], 0)
        self.assertIn("prédit", r["lecture"])


if __name__ == "__main__":
    unittest.main()
