# coding: latin-1
###############################################################################
# Copyright (c) 2023 European Commission
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###############################################################################
"""
This EJBCA_and_DB.py file contains functions related to generation of the Certificate Request Info and add data to DB.
"""

import base64
import binascii
import io
import json
import os
from uuid import uuid4
import uuid
import cbor2
from flask import (
    Blueprint,
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
    jsonify,
)
import segno
import requests
from requests.auth import HTTPBasicAuth
import cbor2
import ssl

# from . import oidc_metadata
from pycose.messages import Sign1Message
from pycose.keys import CoseKey
from pycose.headers import Algorithm, KID
from pycose.algorithms import EdDSA
from pycose.keys.curves import Ed25519
from pycose.keys.keyparam import KpKty, OKPKpD, OKPKpX, KpKeyOps, OKPKpCurve
from pycose.keys.keytype import KtyOKP
from pycose.keys.keyops import SignOp, VerifyOp
import base64
from binascii import unhexlify
from pycose.messages import Sign1Message
import cbor2
from pycose.keys import EC2Key, CoseKey

import urllib3

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.x509 import GeneralName, GeneralNames
from cryptography.x509 import SubjectAlternativeName
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from requests_pkcs12 import Pkcs12Adapter

from app.validate_vp_token import validate_vp_token, cbor2elems
from app_config.config import ConfService as cfgserv

from app_config.EJBCA_config import EJBCA_Config as ejbca
from app_config.Crypto_Info import Crypto_Info as crypto
import models as db
import user as get_hash_user_pid

from app import logger

def getCertificateAuthorityName( countryCode):

    countries=ejbca.countries
    return countries.get(countryCode, "PID Issuer CA - EU 02")

def getJsonBody(certificateRequest, certificateAuthorityName, countryName):

    if(countryName == "AV"):
        payload = {
            "certificate_request": certificateRequest,
            "certificate_profile_name": ejbca.avCertificateProfile,
            "end_entity_profile_name":ejbca.avEndEntityProfile,
            "certificate_authority_name": certificateAuthorityName,
            "username":ejbca.username,
            "password":ejbca.password,
            "include_chain": ejbca.includeChain
        }
    else:
        payload = {
            "certificate_request": certificateRequest,
            "certificate_profile_name": ejbca.certificateProfileName,
            "end_entity_profile_name":ejbca.endEntityProfileName,
            "certificate_authority_name": certificateAuthorityName,
            "username":ejbca.username,
            "password":ejbca.password,
            "include_chain": ejbca.includeChain
        }
    return payload

def getTrustManagerOfCACertificate(ManagementCA):

    try:         
        with open(ManagementCA) as pem_file:

            pem_data = pem_file.read()

            pem_data=pem_data.encode()

            certificate = x509.load_pem_x509_certificate(pem_data, default_backend())

    except FileNotFoundError as e:
        extra = {'code':'-'} 
        logger.error(f"TrustedCA Error: file not found.\n {e}", extra=extra)
        print(f"TrustedCA Error: file not found.\n {e}")
    except json.JSONDecodeError as e:
        extra = {'code':'-'} 
        logger.error(f"TrustedCA Error: Metadata Unable to decode JSON.\n {e}", extra=extra)
        print(f"TrustedCA Error: Metadata Unable to decode JSON.\n {e}")
    except Exception as e:
        extra = {'code':'-'} 
        logger.error(f"TTrustedCA Error: An unexpected error occurred.\n {e}rustedCA Error: file not found.\n {e}", extra=extra)
        print(f"TrustedCA Error: An unexpected error occurred.\n {e}")

    return certificate

def http_post_requests_with_custom_ssl_context(trust_manager, key_manager_filepath, key_manager_password, url, json_body, headers):

    # ssl_context = ssl.SSLContext()
    # ssl_context.load_verify_locations(trust_manager)
    # ssl_context.verify_mode=ssl.CERT_REQUIRED

    # http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ssl_context=ssl_context)

    # # Set up the requests session
    session = requests.Session()
    session.mount('https://', Pkcs12Adapter(pkcs12_filename=key_manager_filepath, pkcs12_password=key_manager_password))

    # Perform the POST request
    response = session.post(url, json=json_body, headers=headers, verify=False)

    return response


def generateCertificateRequest(priv_key, commonName, countryName, uniformResourceIdentifier, organizationIdentifier=None, organizationName=None, organizationalUnit=None, email=None, phone=None, givenName=None,surname=None, serialNumber=None ):

    #PHONE_OID = ObjectIdentifier("2.5.4.20")
    #encoded_phone = phone.encode('utf-8')

    subject =[
       x509.NameAttribute(NameOID.COMMON_NAME, commonName),
       x509.NameAttribute(NameOID.COUNTRY_NAME, countryName),
    ]

    alt_name_extension = x509.SubjectAlternativeName([])

    optional_subject=[
       (NameOID.GIVEN_NAME, givenName),
       (NameOID.SURNAME, surname),
       (NameOID.ORGANIZATION_NAME, organizationName),
        #x509.NameAttribute(NameOID.ORGANIZATION_IDENTIFIER, organizationIdentifier),
       (NameOID.SERIAL_NUMBER, serialNumber),
       (NameOID.ORGANIZATION_IDENTIFIER, organizationIdentifier),
       #(ObjectIdentifier("2.5.4.20"), phone),
       (NameOID.ORGANIZATIONAL_UNIT_NAME, organizationalUnit)
    ]

    for subjects_oid, value in optional_subject:

        if value is not None:
            subject.append(x509.NameAttribute(subjects_oid,value))
    
    final_SubjectAlternativename=[]
    
    if email:
        final_SubjectAlternativename.append(x509.RFC822Name(email))

    final_SubjectAlternativename.append(x509.UniformResourceIdentifier(uniformResourceIdentifier))
    
    final_subject=x509.Name(subject)
    alt_name_extension = x509.SubjectAlternativeName(final_SubjectAlternativename)
    cri = x509.CertificateSigningRequestBuilder().add_extension(alt_name_extension, critical=False).subject_name(final_subject).sign(priv_key,hashes.SHA256())

    cri_der = cri.public_bytes(serialization.Encoding.DER)

    return cri_der

def user_relying_party_db(user,relying_party, serial_number, certificate , certificateString, log_id):

    givenName=user["given_name"]
    surname=user["family_name"]
    birth_date=user["birth_date"]
    issuing_country=user["issuing_country"]
    issuance_authority=user["issuing_authority"]

    commonName=relying_party.get("Common Name")
    countryName=relying_party.get("Country")
    organizationName=relying_party.get("Name")
    registration_number=relying_party.get("Registration Number")
    intended_use=relying_party.get("Intended use of European Digital Identity Wallets")
    dns_Name=relying_party.get("DNS Name")
    RP_serial_number=relying_party.get("Registration Number")
    
    email=relying_party.get("email")
    address=relying_party.get("address")
    phone_number=relying_party.get("phone_number")
    contact=email +", "+ address + ", " + str(phone_number)

    certificate_issuer=certificate.issuer.rfc4514_string()
    certificate_distinguished_name= certificate.subject.rfc4514_string()
    validity_from=certificate.not_valid_before_utc
    validity_to=certificate.not_valid_after_utc
    serial_number=serial_number
    status= "active"

    try:

        new_user = get_hash_user_pid.User(surname, givenName, birth_date, issuing_country, issuance_authority)
        hash_pid = new_user.hash

        aux = db.check_user(hash_pid, log_id)

        if(aux == None):
            user_id = db.insert_user(hash_pid, log_id) 
        
            if not user_id:
                extra = {'code': log_id} 
                logger.info(f"Error creating user.", extra=extra)

                return "Error creating user.", 500
        else:
            user_id = aux
        
        RP_id=db.insert_relying_party(countryName, organizationName, registration_number, commonName, contact, user_id, log_id)

        db.insert_access_certificate(intended_use, certificateString, certificate_issuer, certificate_distinguished_name, 
                              validity_from, validity_to, serial_number, status, dns_Name, user_id, RP_id, log_id)
        return None
    
    except Exception as e:
        
        extra = {'code': log_id} 
        logger.error(f"Error processing the form: {e}", extra=extra)

        print(f"Error processing the form: {e}")
        return "Error processing the form.", 500
    
def func_get_user_id_by_hash_pid(hash_pid, log_id):

    try:
        user_id =db.get_user_id_by_hash_pid(hash_pid, log_id)
    except Exception as e:
        extra = {'code': log_id} 
        logger.error(f"User doesn't exist!", extra=extra)
        print("User doesn't exist!")

    return user_id

def get_certificate_data(user_id, log_id):

    certificate_dict={

    }

    try:
        relying_parties=db.get_relying_party_names_by_user_id(user_id, log_id)

        for rel in relying_parties:
            certificates=db.get_access_certificate_by_user_id_by_relying_party_id(user_id, rel['relyingParty_id'], log_id)
            for acc in certificates:
                acc["Relying Party Name"]=rel['name']
                certificate_dict.update({str(uuid.uuid4()):acc})

    except Exception as e:
        extra = {'code': log_id} 
        logger.error(f"Error: {e}", extra=extra)
        print(f"Error: {e}")
        
    return certificate_dict

def update_status(id_certificate, log_id):

    try:
        db.update_access_certificate_status(id_certificate, "revoke", log_id)
        
    except Exception as e:
        extra = {'code': log_id} 
        logger.error(f"Error: {e}", extra=extra)
        print(f"Error: {e}")
    