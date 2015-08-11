
**README : Generating Self-Signed CERTIFICATE AND PRIVATE ENCRYPTION KEY**
**======================================================================**

If a user would like to obtain an SSL certificate from a certificate authority 
(CA), user must generate a certificate signing request (CSR). A CSR consists 
mainly of the public key of a key pair, and some additional information. Both of 
these components are inserted into the certificate when it is signed.

A common type of certificate that one can issue oneself is a self-signed 
certificate that is signed with its own private key. Self-signed certificates 
can be used to encrypt data just as well as CA-signed certificates, but users 
of the certificate will be displayed a warning that says that the issuer of the
certificate is not trusted by their computer or browser. Therefore 
self-signed certificates should only be used if one does not need to prove ones 
service's identity to its users (e.g. non-production or non-public servers).

A user can generate a 2048-bit private key and a self signed certificate  from
scratch using openssl. The private key is a PEM formatted file.

PEM format is used for several type of data including encryption, authentication 
and key management. The X.509 certificate is one of them.When viewed it is  DER 
(distinguished encoding rules) encoded in base 64, stuck between plain-text 
anchor lines (BEGIN CERTIFICATE and END CERTIFICATE). Below is an example of 
PEM File:

    -----BEGIN CERTIFICATE-----
    MIIEczCCA1ugAwIBAgIBADANBgkqhkiG9w0BAQQFAD..AkGA1UEBhMCR0Ix
    EzARBgNVBAgTClNvbWUtU3RhdGUxFDASBgNVBAoTC0..0EgTHRkMTcwNQYD
    VQQLEy5DbGFzcyAxIFB1YmxpYyBQcmltYXJ5IENlcn..XRpb24gQXV0aG9y
    aXR5MRQwEgYDVQQDEwtCZXN0IENBIEx0ZDAeFw0wMD..TUwMTZaFw0wMTAy
    MDQxOTUwMTZaMIGHMQswCQYDVQQGEwJHQjETMBEGA1..29tZS1TdGFW0ZTEU
    MBIGA1UEChMLQmVzdCBDQSBMdGQxNzA1BgNVBAsTLk..DEgUHVibGljIFBy
    aW1hcnkgQ2VydGlmaWNhdGlvbiBBdXRob3JpdHkxFD..AMTC0Jlc3QgQ0Eg
    THRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCg..Tz2mr7SZiAMfQyu
    vBjM9OiJjRazXBZ1BjP5CE/Wm/Rr500PRK+Lh9x5eJ../ANBE0sTK0ZsDGM
    ak2m1g7oruI3dY3VHqIxFTz0Ta1d+NAjwnLe4nOb7/..k05ShhBrJGBKKxb
    8n104o/5p8HAsZPdzbFMIyNjJzBM2o5y5A13wiLitE..fyYkQzaxCw0Awzl
    kVHiIyCuaF4wj571pSzkv6sv+4IDMbT/XpCo8L6wTa..sh+etLD6FtTjYbb
    rvZ8RQM1tlKdoMHg2qxraAV++HNBYmNWs0duEdjUbJ..XI9TtnS4o1Ckj7P
    OfljiQIDAQABo4HnMIHkMLB0GA1UdDgQWBBQ8urMCRL..5AkIp9NJHJw5TCB
    tAYDVR0jBIGsMIGpgBQ8urMCRLYYMHUKU5AkIp9NJH..aSBijCBhzELMAkG
    A1UEBhMCR0IxEzARBgNVBAgTClNvbWUtU3RhdGUxFD..AoTC0Jlc3QgQ0Eg
    THRkMTcwNQYDVQQLEy5DbGFzcyAxIFB1YmxpYyBQcm..ENlcnRpZmljYXRp
    b24gQXV0aG9yaXR5MRQwEgYDVQQDEwtCZXN0IENBIE..DAMBgNVHRMEISP01AD
    AQH/MA0GCSqGSIb3DQEBBAUAA4IBAQC1uYBcsSncwA..DCsQer772C2ucpX
    xQUE/C0pWWm6gDkwd5D0DSMDJRqV/weoZ4wC6B73f5..bLhGYHaXJeSD6Kr
    XcoOwLdSaGmJYslLKZB3ZIDEp0wYTGhgteb6JFiTtn..sf2xdrYfPCiIB7g
    BMAV7Gzdc4VspS6ljrAhbiiawdBiQlQmsBeFz9JkF4..b3l8BoGN+qMa56Y
    It8una2gY4l2O//on88r5IWJlm1L0oA8e4fR2yrBHX..adsGeFKkyNrwGi/
    7vQMfXdGsRrXNGRGnX+vWDZ3/zWI0joDtCkNnqEpVn..HoX
    -----END CERTIFICATE-----

Data that is not between such lines is ignored, and is sometimes used for 
comments, or for a human-readable dump of the encoded data.

The following command creates a 2048-bit private key (domain.key) in PEM format 
and a self-signed certificate (domain.crt) from scratch:

openssl req \
       -newkey rsa:2048 -nodes -keyout domain.key \
       -x509 -out domain.crt

The -x509 option tells req to create a self-signed cerificate. 
All the information for the certificate can be given in command line or
input on CSR information prompt like:

    ---
    Country Name (2 letter code) [AU]:**US**
    State or Province Name (full name) [Some-State]:**North Carolina**
    Locality Name (eg, city) []:**RTP**
    Organization Name (eg, company) []:**Cisco**
    Organizational Unit Name (eg, section) []:**CCS**
    Common Name (e.g. server FQDN or YOUR name) []:**servicelab**
    Email Address []:**servicelab@cisco.com**


                             **Testing the Generated Key**
                             **-------------------------**
Run python encryption to test the key and the cerificate as follows a string 
"alpha" is encrypted and then the encrypted stringis decrypted to get the 
original string back. Below is the sample:
    **(env)-bash-4.2$ python encrypt_utils.py**
    ENCRYPT['alpha']=MIICAwYJKoZIhvcNAQcDoIIB9DCCAfACAQAxggGrMIIBpwIBADCBjjCBgDE
    LMAkGA1UEBhMCVVMxCzAJBgNVBAgMAk5DMQwwCgYDVQQHDANSVFAxDjAMBgNVBAoMBUNpc2NvMQw
    wCgYDVQQLDANDQ1MxEzARBgNVBAMMCnNlcnZpY2VsYWIxIzAhBgkqhkiG9w0BCQEWFHNlcnZpY2V
    sYWJAY2lzY28uY29tAgkAv17VBCRZrfEwDQYJKoZIhvcNAQEBBQAEggEAgyfmnVT/+gRhswy7GDl
    Ouhk8qgmB7zBJ/ST5kks9tjaob/jG0ga7nEUSisvKMdKoO9xlYsifZgwvC1+zQtnNb7j7iIPqCeU
    JC5zwBnJEThTHLbKM5oTEvED1zQ6jRNLxppHDBN8cWKthmE+s/1Ui+6QBtC+xcFTboBHcXTaPctu
    YVK7Bzvv9LMtyiJhMW+tsZqsrWLXHeBFKY/eWrSejE6amREr6jP4dfQoA/GLHy+nwKivWs3F0tEC
    BBF3ZCqUlzJqVZbxtjDxm9p14VTHbqZDNHGgyDm3Z9I8cF7VwpftDDA8Hfgaw4JGHFjXABiAtoRY
    9dcFhOGj5hUd2usDpIzA8BgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBDr1ZpPR25S3uKbBPOzBsf
    TgBDTXOy+/ifvAfvr/f6cW4Zf
    DECRYPT[MIICAwYJKoZIhvcNAQcDoIIB9DCCAfACAQAxggGrMIIBpwIBADCBjjCBgDELMAkGA1UE
    BhMCVVMxCzAJBgNVBAgMAk5DMQwwCgYDVQQHDANSVFAxDjAMBgNVBAoMBUNpc2NvMQwwCgYDVQQL
    DANDQ1MxEzARBgNVBAMMCnNlcnZpY2VsYWIxIzAhBgkqhkiG9w0BCQEWFHNlcnZpY2VsYWJAY2lz
    Y28uY29tAgkAv17VBCRZrfEwDQYJKoZIhvcNAQEBBQAEggEAgyfmnVT/+gRhswy7GDlOuhk8qgmB
    7zBJ/ST5kks9tjaob/jG0ga7nEUSisvKMdKoO9xlYsifZgwvC1+zQtnNb7j7iIPqCeUJC5zwBnJE
    ThTHLbKM5oTEvED1zQ6jRNLxppHDBN8cWKthmE+s/1Ui+6QBtC+xcFTboBHcXTaPctuYVK7Bzvv9
    LMtyiJhMW+tsZqsrWLXHeBFKY/eWrSejE6amREr6jP4dfQoA/GLHy+nwKivWs3F0tECBBF3ZCqUl
    zJqVZbxtjDxm9p14VTHbqZDNHGgyDm3Z9I8cF7VwpftDDA8Hfgaw4JGHFjXABiAtoRY9dcFhOGj5
    hUd2usDpIzA8BgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBDr1ZpPR25S3uKbBPOzBsfTgBDTXOy+
    /ifvAfvr/f6cW4Zf]=alpha

