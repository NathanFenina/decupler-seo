"""Signature RS256 en Python pur : sans elle, pas de Search Console dans les routines."""

import shutil
import subprocess
import sys
import unittest

from _outils import SCRIPTS, DossierIsole

sys.path.insert(0, str(SCRIPTS))
import gsc  # noqa: E402


@unittest.skipUnless(shutil.which("openssl"), "openssl absent")
class TestSignature(DossierIsole):
    def cle(self, nom, traditionnelle=False):
        cle = self.dossier / nom
        subprocess.run(["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048",
                        "-out", str(cle)], check=True, capture_output=True)
        if traditionnelle:
            subprocess.run(["openssl", "rsa", "-in", str(cle), "-traditional", "-out", str(cle)],
                           check=True, capture_output=True)
        return cle

    def verifier(self, cle, message, signature):
        pub, sig, msg = self.dossier / "pub.pem", self.dossier / "sig.bin", self.dossier / "msg.txt"
        subprocess.run(["openssl", "rsa", "-in", str(cle), "-pubout", "-out", str(pub)], check=True, capture_output=True)
        sig.write_bytes(signature)
        msg.write_bytes(message)
        return subprocess.run(["openssl", "dgst", "-sha256", "-verify", str(pub), "-signature", str(sig), str(msg)],
                              capture_output=True).returncode == 0

    def test_identique_a_openssl_pkcs8(self):
        # Les clés de compte de service Google sont au format PKCS#8.
        cle = self.cle("pkcs8.pem")
        message = b"eyJhbGciOiJSUzI1NiJ9.eyJ0ZXN0IjoxfQ"
        nous = gsc._signer_rs256_pur(cle.read_text(), message)
        (self.dossier / "m").write_bytes(message)
        openssl = subprocess.run(["openssl", "dgst", "-sha256", "-sign", str(cle), str(self.dossier / "m")],
                                 capture_output=True, check=True).stdout
        self.assertEqual(nous, openssl)

    def test_verifiable_pkcs1(self):
        cle = self.cle("pkcs1.pem", traditionnelle=True)
        message = b"entete.corps"
        self.assertTrue(self.verifier(cle, message, gsc._signer_rs256_pur(cle.read_text(), message)))

    def test_message_altere_rejete(self):
        cle = self.cle("k.pem")
        signature = gsc._signer_rs256_pur(cle.read_text(), b"original")
        self.assertFalse(self.verifier(cle, b"modifie", signature))


class TestCle(unittest.TestCase):
    def test_cle_base64_acceptee(self):
        import base64
        import json
        brut = json.dumps({"client_email": "a@b.iam.gserviceaccount.com", "private_key": "x"})
        self.assertEqual(gsc.lis_cle(base64.b64encode(brut.encode()).decode())["client_email"],
                         "a@b.iam.gserviceaccount.com")

    def test_cle_incomplete_refusee(self):
        with self.assertRaises(gsc.ErreurGSC):
            gsc.lis_cle('{"client_email": "a@b"}')


if __name__ == "__main__":
    unittest.main()
