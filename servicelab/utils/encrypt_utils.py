import os
import logging
from servicelab.utils import service_utils

encrypt_utils_logger = logging.getLogger('click_application')
logging.basicConfig()


def public_key(fname):
    cmd = "openssl x509 -inform pem -in %s -pubkey -noout" % (fname)
    cmd_returncode, cmd_info = service_utils.run_this(cmd)
    if cmd_returncode > 0:
        encrypt_utils_logger.error(cmd_info)
    return (cmd_returncode, cmd_info)


def encrypt(pub_fname, data):
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
        encrypt_utils_logger.error(cmd_info)
    return (cmd_returncode, cmd_info)


def decrypt(pub_fname, priv_fname, data):
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
        encrypt_utils_logger.error(cmd_info)
    return (cmd_returncode, cmd_info)


if __name__ == '__main__':
    """
    for running on the jenkins
    pub_fname = "../.stack/services/ccs-data/keys/public_key.pkcs7.pem"
    priv_fname = "../.stack/services/ccs-data/keys/private_key.pkcs7.pem"
    """
    pub_fname = "./test.crt"
    priv_fname = "./test.key"

    ret, enc_data = encrypt(pub_fname, "alpha")
    if ret == 0:
        print "ENCRYPT['alpha']="+enc_data
    else:
        encrypt_utils_logger.error("Unable to encrypt\ndescription:\n%s" % (enc_data))

    ret, decrypt_data = decrypt(pub_fname, priv_fname, enc_data)
    if ret == 0:
        print decrypt_data + "=DECRYPT["+enc_data+"]"
    else:
        encrypt_utils_logger.error("Unable to decrypt:\n")
        encrypt_utils_logger.error("description:\n%s" % (decrypt_data))
