"""Profil de liens : le spam automatique ne doit jamais passer pour de vrais liens."""

import sys
import unittest

from _outils import SCRIPTS

sys.path.insert(0, str(SCRIPTS))
import liens  # noqa: E402


class TestClasser(unittest.TestCase):
    def test_spam_ecarte_et_date(self):
        domaines = [
            {"domain": "vrai-media.fr", "backlinks_spam_score": 0, "referring_pages": 2, "referring_pages_nofollow": 0},
            {"domain": "annuaire.fr", "backlinks_spam_score": 10, "referring_pages": 1, "referring_pages_nofollow": 1},
            {"domain": "seochecker.shop", "backlinks_spam_score": 55, "first_seen": "2026-10-06 01:00:00"},
            {"domain": "backlinks.space", "backlinks_spam_score": 45, "first_seen": "2026-09-30 01:00:00"},
        ]
        c = liens.classer(domaines)
        self.assertEqual((c["total"], len(c["propres"]), c["spam"], c["propres_dofollow"]), (4, 2, 2, 1))
        self.assertEqual(c["spam_par_mois"], {"2026-09": 1, "2026-10": 1})

    def test_seuil(self):
        self.assertEqual(len(liens.classer([{"backlinks_spam_score": 30}], seuil=31)["propres"]), 1)


if __name__ == "__main__":
    unittest.main()
