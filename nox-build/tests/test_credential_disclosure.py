"""Post-condition for the credential-disclosure deletion in SSLParametersAction.

Shared conventions (both-halves assertions, retained-bound methods) are stated
once, in test_rce_surface.py's module docstring.

DEFECT PROOF (mutation applied and observed 2026-09-01): re-added the line
"        {KEY_PROP_SSL_PRIVATEKEY, QString::fromLatin1(sslParams.privateKey.toPem())},"
to src/webui/api/torrentscontroller.cpp in the working tree (between the
certificate entry and the dhParams entry in SSLParametersAction).
test_ssl_private_key_not_disclosed failed on the assertNotIn at line 30,
reporting: AssertionError: 'sslParams.privateKey.toPem()' unexpectedly found
in [full file text]. Reverting the line returned that test to green. The
mutation was made and reversed with the Edit tool, not with git, as head_text
reads the working tree -- a git-based read would have left the mutation
invisible to the assertion.
"""

import unittest

from _support import head_text, tag_text

TORRENTSCTL = "src/webui/api/torrentscontroller.cpp"


class TestSSLPrivateKeyNotDisclosed(unittest.TestCase):
    def test_ssl_private_key_not_disclosed(self):
        # The disclosure call is present at the upstream tag (GET response).
        self.assertIn("sslParams.privateKey.toPem()", tag_text(TORRENTSCTL))
        # The working tree no longer serialises the private key in the response.
        self.assertNotIn("sslParams.privateKey.toPem()", head_text(TORRENTSCTL))

    def test_ssl_private_key_write_paths_retained(self):
        # The bound on the claim: the constant and the setter paths survive, so
        # the key can still be written via setSSLParameters. The claimable
        # property is that the GET no longer discloses it, not that it is absent.
        self.assertIn("KEY_PROP_SSL_PRIVATEKEY", tag_text(TORRENTSCTL))
        self.assertIn("KEY_PROP_SSL_PRIVATEKEY", head_text(TORRENTSCTL))


if __name__ == "__main__":
    unittest.main()
