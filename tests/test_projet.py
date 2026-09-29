"""Création de projet et synchronisation : c'est ce qui empêche les copies de diverger."""

import json
import subprocess
import sys
import unittest

from _outils import DossierIsole, environnement_propre, lancer


class TestProjet(DossierIsole):
    def creer(self, nom="projet"):
        r = lancer("projet.py", "init", nom, "--nom", "Projet Test", "--domaine", "https://www.exemple.com",
                   "--pays", "SA", "--langues", "ar,en", "--publication", "depot", cwd=self.dossier)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return self.dossier / nom

    def test_creation_complete_et_sans_champ_vide(self):
        p = self.creer()
        for f in ("CLAUDE.md", "decupler-seo.config.yml", "memoire/marque.md", "memoire/faits.md",
                  "journal/modifications.csv", "ROUTINES.md", ".mcp.json", ".gitignore",
                  ".claude/skills/projet-marque/SKILL.md", ".claude/skills/seo-cycle/SKILL.md",
                  ".claude/agents/seo-manager.md", ".claude/decupler-seo/scripts/guard.py"):
            self.assertTrue((p / f).exists(), f)
        restants = [f for f in p.rglob("*") if f.is_file() and f.suffix in {".md", ".yml"}
                    and "{{" in f.read_text(encoding="utf-8")]
        self.assertEqual(restants, [])
        self.assertIn("mode: depot", (p / "decupler-seo.config.yml").read_text(encoding="utf-8"))

    def test_les_skills_pointent_vers_les_scripts_embarques(self):
        p = self.creer()
        texte = (p / ".claude/skills/seo-cycle/SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", texte)
        self.assertIn(".claude/decupler-seo/scripts/guard.py", texte)

    def test_nouveau_projet_demarre_en_assisted(self):
        p = self.creer()
        r = lancer("guard.py", "--statut", cwd=p)
        self.assertEqual(json.loads(r.stdout)["mode"], "assisted")

    def test_resynchronisation_idempotente(self):
        p = self.creer()
        r = lancer("projet.py", "sync", ".", cwd=p)
        self.assertIn("0 ajouté(s) · 0 mis à jour", r.stdout)

    def test_modification_locale_protegee(self):
        p = self.creer()
        skill = p / ".claude/skills/seo-redaction/SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + "\nrègle ajoutée à la main\n", encoding="utf-8")
        r = lancer("projet.py", "sync", ".", cwd=p)
        self.assertEqual(r.returncode, 1)
        self.assertIn("règle ajoutée à la main", skill.read_text(encoding="utf-8"))

    def test_forcer_restaure_la_methode(self):
        p = self.creer()
        skill = p / ".claude/skills/seo-redaction/SKILL.md"
        skill.write_text("écrasé", encoding="utf-8")
        r = lancer("projet.py", "sync", ".", "--forcer", cwd=p)
        self.assertEqual(r.returncode, 0)
        self.assertNotEqual(skill.read_text(encoding="utf-8"), "écrasé")

    def test_skills_du_projet_jamais_touches(self):
        p = self.creer()
        propre = p / ".claude/skills/projet-arabe/SKILL.md"
        propre.parent.mkdir(parents=True)
        propre.write_text("---\nname: projet-arabe\ndescription: x\n---\n", encoding="utf-8")
        lancer("projet.py", "sync", ".", "--forcer", cwd=p)
        self.assertTrue(propre.exists())

    def test_memoire_jamais_touchee_par_la_synchro(self):
        p = self.creer()
        marque = p / "memoire/marque.md"
        marque.write_text("voix du client", encoding="utf-8")
        lancer("projet.py", "sync", ".", "--forcer", cwd=p)
        self.assertEqual(marque.read_text(encoding="utf-8"), "voix du client")

    def test_adoption_d_un_depot_existant(self):
        # Un dépôt qui a déjà son CLAUDE.md et une copie ancienne d'un skill de méthode.
        existant = self.dossier / "existant"
        (existant / ".claude/skills/seo-redaction").mkdir(parents=True)
        (existant / "CLAUDE.md").write_text("# Mémoire existante\n", encoding="utf-8")
        (existant / ".claude/skills/seo-redaction/SKILL.md").write_text("ancienne copie", encoding="utf-8")
        (existant / ".claude/skills/maison/SKILL.md").parent.mkdir(parents=True)
        (existant / ".claude/skills/maison/SKILL.md").write_text("skill maison", encoding="utf-8")

        r = lancer("projet.py", "adopter", ".", "--nom", "Existant", "--domaine", "https://exemple.com",
                   cwd=existant)
        self.assertEqual(r.returncode, 1, "doit s'arrêter : une copie non gérée serait écrasée")
        self.assertIn("seo-redaction", r.stdout)

        r = lancer("projet.py", "adopter", ".", "--nom", "Existant", "--domaine", "https://exemple.com",
                   "--forcer", cwd=existant)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((existant / "CLAUDE.md").read_text(encoding="utf-8"), "# Mémoire existante\n")
        self.assertEqual((existant / ".claude/skills/maison/SKILL.md").read_text(encoding="utf-8"), "skill maison")
        self.assertTrue((existant / "memoire/faits.md").exists())
        self.assertTrue((existant / "CLAUDE.decupler-seo.md").exists())
        self.assertNotEqual((existant / ".claude/skills/seo-redaction/SKILL.md").read_text(encoding="utf-8"),
                            "ancienne copie")

    def test_statut_depuis_la_copie_embarquee(self):
        # Lancé depuis .claude/decupler-seo, le script ne doit pas prendre le
        # dépôt du projet pour une source de la méthode.
        p = self.creer()
        subprocess.run(["git", "init", "-q"], cwd=p, check=True)
        r = subprocess.run([sys.executable, ".claude/decupler-seo/scripts/projet.py", "statut", "."], cwd=p,
                           env=environnement_propre(), capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("inconnue", r.stdout)
        self.assertNotIn("disponible ici", r.stdout)


if __name__ == "__main__":
    unittest.main()
