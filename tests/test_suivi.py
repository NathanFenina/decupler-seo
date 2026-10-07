import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import suivi  # noqa: E402


class TestPosition(unittest.TestCase):
    SERP = [{"rang": 1, "url": "https://concurrent.fr/a"},
            {"rang": 2, "url": "https://autre.fr/b"},
            {"rang": 3, "url": "https://www.client.fr/mauvaise-page/"},
            {"rang": 4, "url": "https://client.fr/bonne-page/"}]

    def test_premiere_position_et_concurrent_devant(self):
        r = suivi.position_dans_serp(self.SERP, "https://client.fr", "/mauvaise-page/")
        self.assertEqual(r["position"], 3)
        self.assertEqual(r["bonne_page"], "oui")
        self.assertEqual(r["devant"], "concurrent.fr")

    def test_autre_page_signalee(self):
        r = suivi.position_dans_serp(self.SERP, "client.fr", "/bonne-page/")
        self.assertEqual(r["bonne_page"], "non")

    def test_absent(self):
        r = suivi.position_dans_serp(self.SERP[:2], "client.fr", "/x/")
        self.assertEqual(r["position"], "")


class TestPrompts(unittest.TestCase):
    def test_fusion_ajoute_sans_retirer_ni_dupliquer(self):
        existants = [{"id": "P001", "prompt": "Quelle agence ?", "statut": "refuse"}]
        out = suivi.fusionner_prompts(existants, [{"prompt": "quelle agence ?"}, {"prompt": "Quel conférencier IA ?", "funnel": "MOFU"}])
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["statut"], "refuse")
        self.assertEqual(out[1]["statut"], "propose")
        self.assertEqual(out[1]["poids"], "2")
        self.assertEqual(out[1]["id"], "P002")

    def test_comparaison_mensuelle(self):
        hist = [{"mois": "2026-09", "id": "P1", "moteur": "openai", "cite": "False", "nomme": "False"},
                {"mois": "2026-10", "id": "P1", "moteur": "openai", "cite": "True", "nomme": "False"}]
        out = suivi.comparer_prompts(hist, "2026-10")
        self.assertEqual(out[0]["evolution"], "gagné")

    def test_delta_positions(self):
        hist = [{"mois": "2026-09", "mot_cle": "a", "position": "12"}, {"mois": "2026-10", "mot_cle": "a", "position": "4"}]
        self.assertEqual(suivi.comparer_positions(hist, "2026-10")[0]["delta"], 8)
        self.assertEqual(suivi.mois_precedent("2027-01"), "2026-12")


if __name__ == "__main__":
    unittest.main()
