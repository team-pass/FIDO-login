'''
This file is mostly adapted from 
https://cryptography.io/en/latest/x509/tutorial/#creating-a-self-signed-certificate.

ONLY USE THIS FILE TO CREATE SELF-SIGNED CERTIFICATES IN DEVELOPMENT!!
'''
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import NameOID
from cryptography import x509
import datetime

# Generate our key
key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)
# Write our key to disk for safe keeping
with open("./key.pem", "wb") as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(), # ONLY SAFE FOR LOCAL DEVELOPMENT
    ))

# Various details about who we are. For a self-signed certificate the
# subject and issuer are always the same.
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Maryland"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, u"College Park"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Team PASS"),
    x509.NameAttribute(NameOID.COMMON_NAME, u"team-pass.github.io"),
])
cert = x509.CertificateBuilder().subject_name(
    subject
).issuer_name(
    issuer
).public_key(
    key.public_key()
).serial_number(
    x509.random_serial_number()
).not_valid_before(
    datetime.datetime.utcnow()
).not_valid_after(
    # Our certificate will be valid for ~6 months
    datetime.datetime.utcnow() + datetime.timedelta(days=180)
).add_extension(
    x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
    critical=False,
# Sign our certificate with our private key
).sign(key, hashes.SHA256())
# Write our certificate out to disk.
with open("./certificate.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))
