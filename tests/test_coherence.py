"""Cohérence du dépôt : ce qui casse une installation sans qu'aucun script ne plante."""

import json
import re
import unittest

from _outils import RACINE


class TestCoherence(unittest.TestCase):
    def test_manifestes_json_valides(self):
        for f in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json", ".mcp.json",
                  "schema/templates.json"):
            json.loads((RACINE / f).read_text(encoding="utf-8"))

    def test_plugin_json_sans_champ_de_composants(self):
        # Régression : « agents » pointait vers un dossier, ce qui fait échouer l'installation.
        plugin = json.loads((RACINE / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        for champ in ("agents", "skills", "commands"):
            self.assertNotIn(champ, plugin, "la structure standard suffit, sans liste à tenir à jour")

    def test_nom_de_skill_egal_au_dossier(self):
        for skill in (RACINE / "skills").glob("*/SKILL.md"):
            texte = skill.read_text(encoding="utf-8")
            self.assertTrue(texte.startswith("---\n"), skill)
            nom = re.search(r"^name:\s*(\S+)", texte, re.M).group(1)
            self.assertEqual(nom, skill.parent.name)
            self.assertRegex(texte.split("---", 2)[1], r"(?m)^description:")

    def test_agents_complets(self):
        for agent in (RACINE / "agents").glob("*.md"):
            entete = agent.read_text(encoding="utf-8").split("---", 2)[1]
            for champ in ("name", "description", "tools"):
                self.assertRegex(entete, rf"(?m)^{champ}:", f"{agent.name} : {champ}")

    def test_aucun_chemin_relatif_vers_les_scripts(self):
        # Régression : « python3 scripts/… » ne marche que lancé depuis le dossier du dépôt.
        for f in [*(RACINE / "skills").rglob("*.md"), *(RACINE / "agents").glob("*.md"),
                  *(RACINE / "commands").glob("*.md")]:
            self.assertNotRegex(f.read_text(encoding="utf-8"), r"python3 scripts/", str(f))

    def test_scripts_references_existent(self):
        existants = {p.name for p in (RACINE / "scripts").glob("*.py")}
        for f in RACINE.rglob("*.md"):
            if ".git" in f.parts:
                continue
            for ref in re.findall(r"scripts/([a-z_]+\.py)", f.read_text(encoding="utf-8")):
                self.assertIn(ref, existants, f"{f.relative_to(RACINE)} cite {ref}")

    def test_fiches_de_l_index_gsc(self):
        index = (RACINE / "skills/seo-gsc-analyses/SKILL.md").read_text(encoding="utf-8")
        for fiche in set(re.findall(r"`([a-z-]+\.md)`", index)):
            self.assertTrue((RACINE / "skills/seo-gsc-analyses/references" / fiche).exists(), fiche)

    def test_aucun_secret_suivi(self):
        interdits = re.compile(r"(^|/)\.env$|service-account.*\.json$|\.pem$")
        import subprocess
        suivis = subprocess.run(["git", "ls-files"], cwd=RACINE, capture_output=True, text=True).stdout.split()
        self.assertEqual([f for f in suivis if interdits.search(f)], [])


if __name__ == "__main__":
    unittest.main()
