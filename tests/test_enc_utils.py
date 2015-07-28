import os
import unittest
from servicelab.stack import Context
from servicelab.utils import encrypt_utils


class TestEncUtils(unittest.TestCase):
    """TestEncUtils is a unittest.TestCase class for doing unit test
    for encryppting and decrypting data. It uses a  test generated
    certificate files to validate the encryption and decryption.


    Attributes:
        test.crt : test certificate file available in the test directory.
        test.pem : the private key file.


    """
    PUBLIC_CERT = "tests/test.crt"
    PRIVATE_KEY = "tests/test.key"

    def setUp(self):
        """ setUp function for Ruby Utils test, this setsup the ruby version as
        defined in RUBY_VERSION_FILE and GEMS list as defined in Root and
        CCS directories.

        """
        ctx = Context()
        self.public_cert = os.path.join(ctx.reporoot_path(),
                                        TestEncUtils.PUBLIC_CERT)
        self.private_key = os.path.join(ctx.reporoot_path(),
                                        TestEncUtils.PRIVATE_KEY)
        self.data = "alpha"

        if(not os.path.isfile(self.public_cert)):
            self.fail("Setup FAILS as the test public cert is unavilable")

        if(not os.path.isfile(self.private_key)):
            self.fail("Setup FAILS as the test private key is unavilable")

    def test_enc_decrypt(self):
        """ Test encryption and decryption.

        """
        ret, encrypt = encrypt_utils.encrypt(self.public_cert, self.data)
        self.assertEqual(0, ret,
                         "Unable to encrypt the data.\nDescription:\n%s" % (encrypt))

        ret, decrypt = encrypt_utils.decrypt(self.public_cert, self.private_key, encrypt)
        self.assertEqual(0, ret,
                         "Unable to decrypt the data.\nDescription:\n%s" % (decrypt))

        self.assertEqual(decrypt, self.data,
                         "The decrypted data not same as actual data")


if __name__ == '__main__':
    unittest.main()
