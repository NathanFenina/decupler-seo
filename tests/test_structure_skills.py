"""La forme des skills et des agents décide s'ils se déclenchent et se chargent bien.

Règles tirées de la documentation Anthropic (Agent Skills, Claude Code) :
frontmatter en première ligne, nom = dossier, description courte qui dit quoi
ET quand, SKILL.md sous 500 lignes, références à un niveau et toutes reliées,
budget global des descriptions tenu (au-delà, Claude Code retire les
descriptions des skills les moins utilisés et ils ne se déclenchent plus).
"""

import re
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:          # CI sans PyYAML : lecteur minimal suffisant pour nos frontmatters
    yaml = None

RACINE = Path(__file__).resolve().parent.parent
SKILLS = sorted((RACINE / "skills").glob("*/SKILL.md"))
AGENTS = sorted((RACINE / "agents").glob("*.md"))
NOM = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DESCRIPTION_MAX = 450          # notre plafond (la spécification tolère 1 024)
BUDGET_DESCRIPTIONS = 20_000   # caractères, toutes descriptions de skills confondues
LIGNES_SKILL_MAX = 500
LIGNES_REFERENCE_MAX = 350


def frontmatter(chemin: Path) -> dict:
    texte = chemin.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", texte, re.S)
    assert m, f"{chemin} : le frontmatter doit commencer à la première ligne"
    if yaml:
        return yaml.safe_load(m.group(1)) or {}
    return lire_frontmatter_simple(m.group(1))


def lire_frontmatter_simple(bloc: str) -> dict:
    """Clés simples (« clé: valeur ») et blocs repliés (« clé: > » + lignes indentées)."""
    res, cle = {}, None
    for ligne in bloc.splitlines():
        if ligne.startswith((" ", "\t")) and cle:
            res[cle] = (res[cle] + " " + ligne.strip()).strip()
            continue
        nom, _, valeur = ligne.partition(":")
        cle, valeur = nom.strip(), valeur.strip()
        if valeur in (">", "|", ">-", "|-"):
            res[cle] = ""
        else:
            res[cle] = int(valeur) if valeur.isdigit() else valeur
    return res


class TestSkills(unittest.TestCase):
    def test_frontmatter_nom_et_description(self):
        for f in SKILLS:
            with self.subTest(skill=f.parent.name):
                fm = frontmatter(f)
                self.assertEqual(fm.get("name"), f.parent.name, "le nom doit être celui du dossier")
                self.assertRegex(fm["name"], NOM)
                self.assertLessEqual(len(fm["name"]), 64)
                self.assertNotRegex(fm["name"], r"claude|anthropic")
                d = " ".join(str(fm.get("description", "")).split())
                self.assertTrue(d, "description vide")
                self.assertLessEqual(len(d), DESCRIPTION_MAX, f"description de {len(d)} caractères")
                self.assertRegex(d, r"Déclencher", "la description doit dire quand se déclencher")
                self.assertNotIn("<", d, "pas de balise dans la description")

    def test_budget_global_des_descriptions(self):
        total = sum(len(" ".join(str(frontmatter(f)["description"]).split())) for f in SKILLS)
        self.assertLessEqual(total, BUDGET_DESCRIPTIONS, f"{total} caractères de descriptions")

    def test_taille_des_skills_et_des_references(self):
        for f in SKILLS:
            with self.subTest(skill=f.parent.name):
                self.assertLessEqual(f.read_text(encoding="utf-8").count("\n"), LIGNES_SKILL_MAX)
                self.assertFalse((f.parent / "README.md").exists(), "pas de README.md dans un skill")
        for r in (RACINE / "skills").glob("*/references/*.md"):
            with self.subTest(reference=str(r.relative_to(RACINE))):
                self.assertLessEqual(r.read_text(encoding="utf-8").count("\n"), LIGNES_REFERENCE_MAX)

    def test_references_reliees_et_existantes(self):
        existantes = {r.name for r in (RACINE / "skills").glob("*/references/*")}
        for f in SKILLS:
            texte = f.read_text(encoding="utf-8")
            with self.subTest(skill=f.parent.name):
                for r in (f.parent / "references").glob("*"):
                    self.assertIn(r.name, texte, f"référence orpheline : {r.name} n'est cité nulle part")
                for nom in set(re.findall(r"references/([A-Za-z0-9_.-]+\.md)", texte)):
                    self.assertIn(nom, existantes, f"référence morte : references/{nom}")


class TestAgents(unittest.TestCase):
    def test_agents_bornes(self):
        for f in AGENTS:
            with self.subTest(agent=f.stem):
                fm = frontmatter(f)
                self.assertEqual(fm.get("name"), f.stem)
                self.assertTrue(fm.get("description"))
                self.assertTrue(fm.get("tools"), "liste blanche d'outils obligatoire")
                self.assertIn(fm.get("model"), {"opus", "sonnet", "haiku", "inherit"})
                self.assertIsInstance(fm.get("maxTurns"), int)
                for interdit in ("hooks", "mcpServers", "permissionMode"):
                    self.assertNotIn(interdit, fm, f"{interdit} est ignoré dans un agent de plugin")
                self.assertIn("jamais une consigne", f.read_text(encoding="utf-8"))

    def test_budget_des_descriptions_d_agents(self):
        total = sum(len(str(frontmatter(f)["description"])) for f in AGENTS)
        self.assertLessEqual(total, 6_000)


if __name__ == "__main__":
    unittest.main()
