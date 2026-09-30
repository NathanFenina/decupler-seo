"""Tableau de bord partagé : l'état de la page et les décisions du client ne se perdent jamais."""

import json
import sys
import unittest
from pathlib import Path

from _outils import SCRIPTS, DossierIsole, lancer

sys.path.insert(0, str(SCRIPTS))
import pilotage as P  # noqa: E402

GABARIT = (Path(SCRIPTS).parent / "templates" / "pilotage.html").read_text(encoding="utf-8")


class TestEtat(unittest.TestCase):
    def test_aller_retour_sans_toucher_au_reste(self):
        etat = {"maj": "2026-10-01", "projets": [{"id": "atlas", "nom": "Atlas </script> Conseil", "actions": []}]}
        html = P.ecrire_etat(GABARIT, etat)
        self.assertEqual(P.lire_etat(html), etat)
        self.assertNotIn("Atlas </script>", html)                      # le JSON ne ferme jamais la balise
        self.assertEqual(html.replace(html[html.index('id="etat">'):html.index("</script>", html.index('id="etat">'))], ""),
                         GABARIT.replace(GABARIT[GABARIT.index('id="etat">'):GABARIT.index("</script>", GABARIT.index('id="etat">'))], ""))

    def test_les_decisions_ne_sont_jamais_ecrasees(self):
        existantes = [{"id": "a", "titre": "Ancien", "statut": "validee", "note": "go"},
                      {"id": "b", "titre": "Refusée", "statut": "refusee"},
                      {"id": "c", "titre": "Proposée", "statut": "proposee", "gain": "+3 clics/mois"}]
        nouvelles = [{"id": "a", "titre": "Nouveau titre"}, {"id": "b", "titre": "Revient ?"},
                     {"id": "c", "titre": "Proposée", "gain": "+9 clics/mois"}, {"id": "d", "titre": "Neuve"}]
        actions, n = P.fusionner_actions(existantes, nouvelles, "2026-10-01")
        par = {a["id"]: a for a in actions}
        self.assertEqual(n, 1)
        self.assertEqual((par["a"]["titre"], par["a"]["statut"], par["a"]["note"]), ("Ancien", "validee", "go"))
        self.assertEqual(par["b"]["statut"], "refusee")
        self.assertEqual(par["c"]["gain"], "+9 clics/mois")               # une proposition se rafraîchit
        self.assertEqual(par["d"]["statut"], "proposee")

    def test_marquer(self):
        p = {"id": "atlas", "actions": [{"id": "a", "titre": "T", "statut": "validee"}]}
        P.marquer_action(p, "a", "faite", lien="https://exemple.test/pr/1", date="2026-10-02")
        self.assertEqual((p["actions"][0]["statut"], p["actions"][0]["lien"]), ("faite", "https://exemple.test/pr/1"))
        with self.assertRaises(SystemExit):
            P.marquer_action(p, "zz", "faite")
        with self.assertRaises(SystemExit):
            P.marquer_action(p, "a", "inconnu")


class TestPropositions(unittest.TestCase):
    def test_opportunites_hors_pages_en_mesure(self):
        res = {"opportunites": [
            {"requete": "tva atlas", "page": "https://a.example/tva", "action": "ctr", "score": 40, "position": 3.1,
             "impressions_mois": 900, "gain_clics_mois": 22},
            {"requete": "sci", "page": "https://a.example/sci", "action": "page-1", "score": 30, "position": 7,
             "impressions_mois": 300, "gain_clics_mois": 9, "en_mesure_jusqu_au": "2026-10-20"},
            {"requete": "holding", "page": "", "action": "a-creer", "score": 12, "position": None, "volume_mois": 480,
             "gain_clics_mois": 14}]}
        a = P.depuis_opportunites(res, "atlas")
        self.assertEqual([x["type"] for x in a], ["optimisation", "contenu"])
        self.assertEqual(a[0]["page"], "/tva")
        self.assertIn("+22", a[0]["gain"])

    def test_points_ouverts_et_journal(self):
        pts = P.depuis_points_ouverts("# À traiter\n- [ ] Fusionner /a et /b\n- [x] Fait\n", "atlas")
        self.assertEqual([p["titre"] for p in pts], ["Fusionner /a et /b"])
        j = P.depuis_journal([{"id": "4", "url": "https://a.example/x", "type": "title", "verdict": "perte"},
                              {"id": "5", "url": "https://a.example/y", "type": "meta", "verdict": "gain"}], "atlas")
        self.assertEqual(len(j), 1)
        self.assertIn("n° 4", j[0]["titre"])

    def test_priorite_decisions_puis_gain(self):
        a = [{"id": "1", "type": "optimisation", "gain": "+5 clics/mois", "effort": "S"},
             {"id": "2", "type": "contenu", "gain": "+50 clics/mois", "effort": "L"},
             {"id": "3", "type": "decision", "gain": "", "effort": "M"},
             {"id": "4", "type": "optimisation", "gain": "+20 clics/mois", "effort": "M"},
             {"id": "4", "type": "optimisation", "gain": "+20 clics/mois", "effort": "M"}]
        self.assertEqual([x["id"] for x in P.prioriser(a, 3)], ["3", "2", "4"])
        beaucoup = [{"id": f"d{i}", "type": "decision", "gain": "", "effort": "M"} for i in range(6)] + a[:2]
        self.assertEqual([x["id"] for x in P.prioriser(beaucoup, 5)], ["d0", "d1", "d2", "2", "1"])

    def test_point_ouvert_sur_plusieurs_lignes_et_doublon(self):
        texte = "- [ ] Vérifier dans Search Console qu'aucune\n      action n'est en cours.\n- [ ] « tva » : /a et /b\n"
        pts = P.depuis_points_ouverts(texte, "atlas")
        self.assertEqual(pts[0]["titre"], "Vérifier dans Search Console qu'aucune action n'est en cours.")
        canni = P.depuis_cartographie({"cannibalisation": {"tva": ["/a", "/b"]}}, "atlas")
        self.assertEqual([x["titre"] for x in P.sans_doublons(canni + pts)],
                         ["Trancher la cannibalisation — tva", "Vérifier dans Search Console qu'aucune action n'est en cours."])

    def test_serie_hebdo(self):
        lignes = [{"keys": ["2026-09-21"], "clicks": 2, "impressions": 10},
                  {"keys": ["2026-09-22"], "clicks": 3, "impressions": 20},
                  {"keys": ["2026-09-28"], "clicks": 1, "impressions": 5}]
        self.assertEqual(P.serie_hebdo(lignes), [{"semaine": "2026-09-21", "clics": 5, "impressions": 30},
                                                 {"semaine": "2026-09-28", "clics": 1, "impressions": 5}])


class TestCommandes(DossierIsole):
    def test_injecter_puis_marquer(self):
        page = self.dossier / "tableau.html"
        page.write_text(GABARIT, encoding="utf-8")
        (self.dossier / "actions.json").write_text(json.dumps([{"id": "x1", "titre": "Réécrire le title", "type": "optimisation"}]),
                                                   encoding="utf-8")
        (self.dossier / "donnees.json").write_text(json.dumps({"nom": "Atlas Conseil", "kpis": {"clics_4s": 12}}),
                                                   encoding="utf-8")
        r = lancer("pilotage.py", "injecter", "--html", "tableau.html", "--projet-id", "atlas", "--donnees", "donnees.json",
                   "--actions", "actions.json", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = lancer("pilotage.py", "marquer", "--html", "tableau.html", "--projet-id", "atlas", "--id", "x1",
                   "--statut", "validee", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = lancer("pilotage.py", "etat", "--html", "tableau.html", "--projet-id", "atlas", "--statut", "validee", "--json",
                   cwd=self.dossier)
        self.assertEqual([a["id"] for a in json.loads(r.stdout)], ["x1"])
        etat = P.lire_etat(page.read_text(encoding="utf-8"))
        self.assertEqual(etat["projets"][0]["nom"], "Atlas Conseil")

    def test_titre_et_action_consignee_depuis_une_conversation(self):
        page = self.dossier / "tableau.html"
        page.write_text(GABARIT, encoding="utf-8")
        r = lancer("pilotage.py", "injecter", "--html", "tableau.html", "--projet-id", "atlas", "--titre", "Pilotage Atlas Conseil",
                   cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stderr)
        for _ in range(2):                                   # consignée deux fois : une seule ligne
            r = lancer("pilotage.py", "ajouter", "--html", "tableau.html", "--projet-id", "atlas", "--titre",
                       "Refonte de la page TVA", "--statut", "faite", "--lien", "https://exemple.test/pr/3", cwd=self.dossier)
            self.assertEqual(r.returncode, 0, r.stderr)
        html = page.read_text(encoding="utf-8")
        self.assertIn("<title>Pilotage Atlas Conseil</title>", html)
        actions = P.lire_etat(html)["projets"][0]["actions"]
        self.assertEqual([(a["statut"], a["source"]) for a in actions], [("faite", "conversation")])


if __name__ == "__main__":
    unittest.main()
