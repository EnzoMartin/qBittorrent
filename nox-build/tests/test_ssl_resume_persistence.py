"""Post-condition for the deletion of SSL parameters from fastresume data.

Shared conventions (both-halves assertions, retained-bound methods) are stated
once, in test_rce_surface.py's module docstring.

DEFECT PROOF (mutation applied and observed 2026-10-06): re-added the line
'        data["qBt-sslPrivateKey"] = resumeData.sslParameters.privateKey.toPem().toStdString();'
to src/base/bittorrent/bencoderesumedatastorage.cpp in the working tree, after
the qBt-stopCondition write. test_fastresume_ssl_keys_removed failed for
key='qBt-sslPrivateKey' and test_fastresume_ssl_load_and_save_removed failed on
"'resumeData.sslParameters' unexpectedly found"; the run reported
FAILED (failures=2). Reverting the line with the Edit tool returned both to green.
"""

import unittest

from _support import head_text, tag_text

BENCODE_STORAGE = "src/base/bittorrent/bencoderesumedatastorage.cpp"
DB_STORAGE = "src/base/bittorrent/dbresumedatastorage.cpp"


class TestSSLParametersNotPersistedInFastresume(unittest.TestCase):
    def test_fastresume_ssl_keys_removed(self):
        for key in ("qBt-sslCertificate", "qBt-sslPrivateKey", "qBt-sslDhParams"):
            with self.subTest(key=key):
                self.assertIn(key, tag_text(BENCODE_STORAGE))
                self.assertNotIn(key, head_text(BENCODE_STORAGE))

    def test_fastresume_ssl_load_and_save_removed(self):
        # The load sets sslParameters; the save reads them. Both are gone, so a
        # restored torrent starts with none and none are written to disk.
        self.assertIn("torrentParams.sslParameters", tag_text(BENCODE_STORAGE))
        self.assertNotIn("torrentParams.sslParameters", head_text(BENCODE_STORAGE))
        self.assertIn("resumeData.sslParameters", tag_text(BENCODE_STORAGE))
        self.assertNotIn("resumeData.sslParameters", head_text(BENCODE_STORAGE))

    def test_sqlite_storage_retained(self):
        # The bound on the claim: SQLite resume storage is untouched, so the
        # property holds only for the default Legacy (fastresume) storage.
        self.assertIn("resumeData.sslParameters", head_text(DB_STORAGE))


if __name__ == "__main__":
    unittest.main()
