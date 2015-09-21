"""
Help fuctions for public key encrytption and decryption.
"""
import logging
from servicelab.utils import service_utils

ENC_LOGGER = logging.getLogger('click_application')
logging.basicConfig()


def public_key(fname):
    """Public Key Creation via SSL.

    Args:
        fname (str): Certificate file ssl uses to create public key.

    Returns:
        returncode (int):
            0 -- Success
            1 -- Failure, can't create key (possibly invalid certificate)
        cmd_info (str): stdout/stderr log of pubkey-creation command

    Example Usage:
        >>> print publickey(public_key_pem)
        (0, "")
    """
    cmd = "openssl x509 -inform pem -in %s -pubkey -noout" % (fname)
    cmd_returncode, cmd_info = service_utils.run_this(cmd)
    if cmd_returncode > 0:
        ENC_LOGGER.error(cmd_info)
    return (cmd_returncode, cmd_info)


def encrypt(pub_fname, data):
    """Encrypts data using the public key.

    Args:
        pub_fname (str): Public Key
        data (str): data that will be encrypted by the public key
    Returns:
        returncode (int):
            0 -- Success
            1 -- Failure, can't create key (possibly invalid certificate)
        cmd_info (str): stdout/stderr log of pubkey-creation command

    Example Usage:
        >>> print encrypt(public_key_pem)
        (0, "")
            #Data encryption is also outputted
    """

    code = "\""
    code = code + "require 'openssl'; require 'base64';"
    code = code + "public_key_pem = File.read '" + pub_fname + "';"
    code = code + "public_key = OpenSSL::X509::Certificate.new(public_key_pem);"
    code = code + "cipher = OpenSSL::Cipher::AES.new(256, :CBC);"
    code = code + "enc = OpenSSL::PKCS7::encrypt([public_key], '"
    code = code + data + "', " + "cipher, OpenSSL::PKCS7::BINARY).to_der;"
    code = code + "print Base64.encode64(enc).gsub(/\n/, '');"
    code = code + "\""
    cmd = "ruby -e " + code

    cmd_returncode, cmd_info = service_utils.run_this(cmd)
    if cmd_returncode > 0:
        ENC_LOGGER.error(cmd_info)
    return (cmd_returncode, cmd_info)


def decrypt(pub_fname, priv_fname, data):
    """Decrypts data using the private key.

    Args:
        pub_fname (str): Public Key
        priv_fname (str): Private Key

        data (str): data that will be encrypted by the public key
    Returns:
        returncode (int):
            0 -- Success
            1 -- Failure, can't create key (possibly invalid certificate)
        cmd_info (str): stdout/stderr log of pubkey-creation command

    Example Usage:
        >>> print decrypt(private_key_pem)
        (0, "")
            #outputs decrypted data
    """

    code = "\""
    code = code + "require 'openssl'; require 'base64';"
    code = code + "public_key_pem = File.read '" + pub_fname + "';"
    code = code + "public_key_x509 = OpenSSL::X509::Certificate.new(public_key_pem);"
    code = code + "private_key_pem = File.read '" + priv_fname + "';"
    code = code + "private_key_rsa = OpenSSL::PKey::RSA.new(private_key_pem);"
    code = code + "enc_value = Base64.decode64('" + data + "');"
    code = code + "pkcs7 = OpenSSL::PKCS7.new(OpenSSL::ASN1::decode(enc_value));"
    code = code + "print  pkcs7.decrypt(private_key_rsa, public_key_x509);"
    code = code + "\""

    cmd = "ruby -e " + code
    cmd_returncode, cmd_info = service_utils.run_this(cmd)
    if cmd_returncode > 0:
        ENC_LOGGER.error(cmd_info)
    return (cmd_returncode, cmd_info)


if __name__ == '__main__':
    def test_fn():
        """Test function for key creation/encryption/decryption.

        Runs on Jenkins.
        Encrypts and decrypts data using a test keypair.

        pub_fname = "../.stack/services/ccs-data/keys/public_key.pkcs7.pem"
        priv_fname = "../.stack/services/ccs-data/keys/private_key.pkcs7.pem"
        """
        ipub_fname = "./test.crt"
        ipriv_fname = "./test.key"

        ret, enc_data = encrypt(ipub_fname, "alpha")
        if ret == 0:
            print "ENCRYPT['alpha']="+enc_data
        else:
            ENC_LOGGER.error("Unable to encrypt\ndescription:\n%s", enc_data)
            return

        ret, decrypt_data = decrypt(ipub_fname, ipriv_fname, enc_data)
        if ret == 0:
            print decrypt_data + "=DECRYPT["+enc_data+"]"
        else:
            ENC_LOGGER.error("Unable to decrypt:\ndescription:\n%s", decrypt_data)
            return

    test_fn()
