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
This rpr_routes.py file is the blueprint of the Web RelyingParty Registration service.
"""

import ast
import base64
import binascii
from collections import defaultdict
from datetime import datetime, timedelta
import io
import json
import os
import re
import time
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
    send_file,
    send_from_directory,
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
from pycose.algorithms import EdDSA, Es256
from pycose.keys.curves import Ed25519
from pycose.keys.keyparam import KpKty, OKPKpD, OKPKpX, KpKeyOps, OKPKpCurve
from pycose.keys.keytype import KtyOKP
from pycose.keys.keyops import SignOp, VerifyOp
import base64
from binascii import unhexlify
from pycose.messages import Sign1Message
import cbor2
from pycose.keys import EC2Key, CoseKey
from cryptojwt.jws.jws import JWS
from cryptojwt.jwk.ec import ECKey
from cryptojwt.jwk.ec import import_private_ec_key_from_file

import urllib3
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.x509 import GeneralName, GeneralNames
from cryptography.x509 import SubjectAlternativeName
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives.serialization import pkcs12
from app.EJBCA_and_DB_func import func_get_user_id_by_hash_pid, generateCertificateRequest, get_certificate_data, getCertificateAuthorityName, getJsonBody, getTrustManagerOfCACertificate, http_post_requests_with_custom_ssl_context, update_status, user_relying_party_db
from requests_pkcs12 import Pkcs12Adapter
import urllib.parse

from app.validate_vp_token import validate_vp_token, cbor2elems
from app_config.config import ConfService as cfgserv

from app_config.EJBCA_config import EJBCA_Config as ejbca
from app_config.Crypto_Info import Crypto_Info as crypto
import models as db
import user as get_hash_user_pid
from app.data_management import oid4vp_requests,p12_temp, certificate_data_List

from app import logger

rpr = Blueprint("RPR", __name__, url_prefix="/")

rpr.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template/')


@rpr.route('/', methods=['GET','POST'])
def initial_page():

    return render_template('initial_page.html', redirect_url= cfgserv.service_url, pid_auth = cfgserv.service_url + "authentication")


@rpr.route("/authentication", methods=["GET"])
def authentication():
    """
Start Authentication Flow
---
tags:
  - Authentication
consumes:
  - application/json
produces:
  - application/json

responses:
  200:
    description: Authentication initiated successfully
    schema:
      type: object
      properties:
        QR_code_url:
          type: string
          description: URL to generate/display the QR code for authentication
          example: https://example.com/qr/123456
        presentation_id:
          type: string
          description: Transaction identifier for the authentication session
          example: 550e8400-e29b-41d4-a716-446655440000
"""

    url = "https://" + cfgserv.url_verifier +"/ui/presentations"
    payload ={
        "type": "vp_token",
        "nonce": "hiCV7lZi5qAeCy7NFzUWSR4iCfSmRb99HfIvCkPaCLc=",
        "dcql_query": {
            "credentials": [
            {
                "id": "query_0",
                "format": "mso_mdoc",
                "meta": {
                "doctype_value": "eu.europa.ec.eudi.pid.1"
                },
                "claims": [
                {
                    "path": [
                    "eu.europa.ec.eudi.pid.1",
                    "family_name"
                    ],
                    "intent_to_retain": False
                },
                {
                    "path": [
                    "eu.europa.ec.eudi.pid.1",
                    "given_name"
                    ],
                    "intent_to_retain": False
                },
                {
                    "path": [
                    "eu.europa.ec.eudi.pid.1",
                    "birth_date"
                    ],
                    "intent_to_retain": False
                },
                {
                    "path": [
                    "eu.europa.ec.eudi.pid.1",
                    "issuing_authority"
                    ],
                    "intent_to_retain": False
                },
                {
                    "path": [
                    "eu.europa.ec.eudi.pid.1",
                    "issuing_country"
                    ],
                    "intent_to_retain": False
                }
                ]
            }
            ]
        }
    }


    headers = {
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=json.dumps(payload)).json()
    

    QR_code_url = (
        "eudi-openid4vp://" + cfgserv.url_verifier + "?client_id="
        + response["client_id"]
        + "&request_uri="
        + response["request_uri"]
    )

    
    session["session_id"]=str(uuid.uuid4())
    session["certificate_List"]=False

    qrcode = segno.make(QR_code_url)
    out = io.BytesIO()
    qrcode.save(out, kind='png', scale=3)

    """ qrcode.to_artistic(
        background=cfgtest.qr_png,
        target=out,
        kind="png",
        scale=4,
    ) """

    qr_img_base64 = "data:image/png;base64," + base64.b64encode(out.getvalue()).decode(
        "utf-8"
    )

    return_json = {
        "QR_code_url": QR_code_url,
        "presentation_id": response["transaction_id"]
    }

    return (return_json)

@rpr.route("/pid_authorization")
def pid_authorization_get():
    """
PID Authorization
---
tags:
  - Authentication
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: query
    name: presentation_id
    required: true
    type: string
    description: Transaction identifier received from the authentication step
    example: 550e8400-e29b-41d4-a716-446655440000

responses:
  200:
    description: Authorization successful
    schema:
      type: object
      properties:
        message:
          type: object
          properties:
            message:
              type: string
              example: Sucess

  500:
    description: Error during authorization request
    schema:
      type: object
      properties:
        error:
          type: string
          example: "500"
"""

    presentation_id= request.args.get("presentation_id")

    url = "https://" + cfgserv.url_verifier+ "/ui/presentations/" + presentation_id + "?nonce=hiCV7lZi5qAeCy7NFzUWSR4iCfSmRb99HfIvCkPaCLc="
    headers = {
    'Content-Type': 'application/json',
    }

    response = requests.request("GET", url, headers=headers)
    if response.status_code != 200:
        error_msg= str(response.status_code)
        return jsonify({"error": error_msg}),500
    else:
        data = {"message": "Sucess"}
        return jsonify({"message": data}),200
            
    
@rpr.route("/getpidoid4vp", methods=["GET", "POST"])
def getpidoid4vp():
    """
Get PID (OID4VP)
---
tags:
  - Authentication
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: query
    name: presentation_id
    required: true
    type: string
    description: Transaction identifier received from the authentication step
    example: 550e8400-e29b-41d4-a716-446655440000

responses:
  200:
    description: PID retrieved successfully
    schema:
      type: string
      example: abc123hashpid

  400:
    description: Missing presentation_id
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing presentation_id
"""
    if "presentation_id" not in request.args:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing presentation_id"
        }, 400
    else:
        presentation_id = request.args.get("presentation_id")
        url = "https://" + cfgserv.url_verifier +"/ui/presentations/" + presentation_id + "?nonce=hiCV7lZi5qAeCy7NFzUWSR4iCfSmRb99HfIvCkPaCLc="
    
    headers = {
    'Content-Type': 'application/json',
    }

    response = requests.request("GET", url, headers=headers)
    if response.status_code != 200:
        error_msg= str(response.status_code)
        return jsonify({"error": error_msg}),400
    
    error, error_msg= validate_vp_token(response.json())

    if error == True:
        return error_msg
    
    mdoc_json = cbor2elems(response.json()["vp_token"]["query_0"][0] + "==")

    attributesForm={}

    for doctype in mdoc_json:
        for attribute, value in mdoc_json[doctype]:
            attributesForm.update({attribute:value})

    user = attributesForm

    givenName=user["given_name"]
    surname=user["family_name"]
    birth_date=user["birth_date"]
    issuing_country=user["issuing_country"]
    issuance_authority=user["issuing_authority"]

    new_user = get_hash_user_pid.User(surname, givenName, birth_date, issuing_country, issuance_authority)
    hash_pid = new_user.hash

    check_user = db.check_user(hash_pid)
    
    if(check_user == None):
        db.insert_user(hash_pid)
        return (hash_pid)
    else:
        return (hash_pid)
    

@rpr.route('/insert_wrp', methods=['POST'])
def insert_wrp():

    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")
    
    legalEntity = data.get("LegalEntity")

    entity_type = legalEntity.get("type")
    
    if entity_type == "natural": 
        naturalPerson = legalEntity.get("NaturalPerson")

        familyName = naturalPerson.get("familyName")
        givenName = naturalPerson.get("givenName")
        dateOfBirth = naturalPerson.get("dateOfBirth")
        placeOfBirth = naturalPerson.get("placeOfBirth")
    
    if entity_type == "legal": 
        legalPerson = legalEntity.get("LegalPerson")
        
        legalName = legalPerson.get("legalName", [])
        law = legalPerson.get("Law", [])

    else:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid Entity Type (type), should be 'legal' or 'natural'."
        }, 400

    identifier = legalEntity.get("Identifier", [])

    postalAddress = legalEntity.get("postalAddress", [])
    country_le = legalEntity.get("country")
    emails = legalEntity.get("email", [])
    phone = legalEntity.get("phone", [])
    infoURI = legalEntity.get("infoURI", [])


    provider = data.get("provider")

    providerType = provider.get("providerType")
    x5c = provider.get("x5c", [])
    policy_provider = provider.get("policy", [])


    wrp = data.get("wrp")
    tradeName = wrp.get("tradeName")
    supportURI = wrp.get("supportURI", [])
    srvDescription = wrp.get("srvDescription", [])
    IntendedUse = wrp.get("IntendedUse", [])
    isPSB = wrp.get("isPSB")
    entitlements = wrp.get("entitlements", [])
    providesAttestations = wrp.get("providesAttestations", [])
    supervisoryAuthority = wrp.get("SupervisoryAuthority")
    registryURI = wrp.get("registryURI")
    usesIntermediary = wrp.get("usesIntermediary", [])
    isIntermediary = wrp.get("isIntermediary")

    required_fields = {
        "hash_pid": hash_pid
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    user_id = db.check_user(hash_pid)

    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    legal_person_id = None
    natural_person_id = None

    if entity_type == "legal": 
        legal_person_id = db.insert_legal_person(user_id)
        
        for aux in legalName :
            db.insert_legal_person_name(legal_person_id, aux)
        
        for aux in law:
            legislativeIdentifier = aux.get("legislativeIdentifier")
            legalBasis = aux.get("legalBasis", [])

            law_id = db.insert_law(legislativeIdentifier)

            db.insert_legal_person_law(legal_entity_id, law_id)

            for aux in legalBasis:
                db.insert_law_legal_basis(law_id, aux)

    if entity_type == "natural": 
        natural_person_id = db.insert_natural_person(familyName, givenName, dateOfBirth, placeOfBirth, user_id)
    
    legal_entity_id = db.insert_legal_entity(legal_person_id, natural_person_id, country_le, user_id)


    for aux in identifier:
        identifier = aux.get("identifier")
        type = aux.get("type")

        identifier_id = db.insert_identifier(identifier, type, user_id)

        db.insert_legal_entity_identifier(legal_entity_id, identifier_id)

    for aux in postalAddress:
        db.insert_legal_entity_postal_address(legal_entity_id, aux)

    for aux in infoURI:
        db.insert_legal_entity_info_uri(legal_entity_id, aux)

    for aux in emails:
        db.insert_legal_entity_email(legal_entity_id, aux)

    for aux in phone:
        db.insert_legal_entity_phone(legal_entity_id, aux)


    provider_id = db.insert_provider(legal_entity_id, providerType, user_id)

    for aux in x5c:
        db.insert_provider_x5c(provider_id, aux)

    for aux in policy_provider:
        policyURI = aux.get("policyURI")
        type = aux.get("type")

        policy_id_provider = db.insert_policy(policyURI, type, user_id)

        db.insert_provider_policy(provider_id, policy_id_provider)

    
    supervisoryAuthority_id = db.insert_supervisory_authority(supervisoryAuthority.get("name"), supervisoryAuthority.get("country"), user_id)

    for aux in supervisoryAuthority.get("phone"):
        db.insert_supervisory_authority_phone(supervisoryAuthority_id, aux)
    
    for aux in supervisoryAuthority.get("formURI"):
        db.insert_supervisory_authority_formuri(supervisoryAuthority_id, aux)
    
    for aux in supervisoryAuthority.get("email"):
        db.insert_supervisory_authority_email(supervisoryAuthority_id, aux)
    
    
    wrp_id = db.insert_wrp(provider_id, tradeName, isPSB, registryURI, isIntermediary, supervisoryAuthority_id, user_id)

    for aux in srvDescription:
        lang = aux.get("lang")
        content = aux.get("content")

        multilang_id = db.insert_multilanguage_string(lang, content, user_id)

        db.insert_wrp_srv_description(wrp_id, multilang_id)

    for aux in entitlements:
        db.insert_wrp_entitlement(wrp_id, aux)

    for aux in usesIntermediary:
        db.insert_wrp_intermediary(wrp_id, aux)

    for aux in supportURI:
        db.insert_wrp_support_uri(wrp_id, aux)

    for aux in providesAttestations:
        format = aux.get("format")
        meta = aux.get("meta") 

        db.insert_provided_attestation(wrp_id, format, meta, user_id)

    
    for aux in IntendedUse:
        intended_use_id = db.insert_intended_use(wrp_id, aux.get("intendedUseIdentifier"), aux.get("createdAt"), 
                                                 aux.get("revokedAt"), user_id)

        purpose = aux.get("purpose")
        for x in purpose:
            lang = x.get("lang")
            content = x.get("content")

            multilang_id = db.insert_multilanguage_string(lang, content, user_id)

            db.insert_intended_use_purpose(intended_use_id, multilang_id)

        privacyPolicy = aux.get("privacyPolicy")
        for x in privacyPolicy:
            policyURI = x.get("policyURI")
            type = x.get("type")

            policy_id = db.insert_policy(policyURI, type, user_id)

            db.insert_intended_use_policy(intended_use_id, policy_id)

        for x in aux.get("credentials"):
            format = x.get("format")
            meta = x.get("meta")

            credential_id = db.insert_credential(intended_use_id, format, meta, user_id)

            claims = x.get("claims")
            for y in claims:
                db.insert_claim(credential_id, y.get("path"))
                


    return {
        "status": "success",
        "code": 201,
        "message": "Wallet Relying Party successfully created."
    }, 201

## -law
@rpr.route('/create_law', methods=['POST'])
def create_law():

    data = request.get_json(silent=True)

    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400

    hash_pid = data.get("hash_pid")
    
    laws = data.get("law", [])

    required_fields = {
        "hash_pid": hash_pid
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    user_id = db.check_user(hash_pid)

    for law in laws:
        legislativeIdentifier = law.get("legislativeIdentifier")
        legalBasis = law.get("legalBasis", [])

        law_id = db.insert_law(legislativeIdentifier, user_id)

        for aux in legalBasis:
            db.insert_law_legal_basis(law_id, aux)

    return {
        "status": "success",
        "code": 201,
        "message": "Lawcreated successfully"
    }, 201

@rpr.route('/list_law', methods=['POST'])
def list_law():

    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    if not hash_pid:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": ["hash_pid"]
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    result = db.get_law(user_id)

    return {
        "status": "success",
        "code": 200,
        "message": "Law retrieved successfully.",
        "data": {
            "law": result
        }
    }, 200

## -legal person 
@rpr.route('/create_legal_person', methods=['POST'])
def create_legal_person():

    data = request.get_json(silent=True)

    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400

    hash_pid = data.get("hash_pid")
    
    legalNames = data.get("legalName", [])
    laws = data.get("law", [])

    required_fields = {
        "hash_pid": hash_pid,
        "laws": laws
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    user_id = db.check_user(hash_pid)

    legal_person_id = db.insert_legal_person(user_id)

    for legalName in legalNames:
        db.insert_legal_person_name(legal_person_id, legalName)

    for law in laws:
        db.associate_legal_person_law(legal_person_id, law)

    return {
        "status": "success",
        "code": 201,
        "message": "Legal Person created successfully"
    }, 201

@rpr.route('/list_legal_person', methods=['POST'])
def list_legal_person():

    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    if not hash_pid:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": ["hash_pid"]
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    result = db.get_legal_person(user_id)

    return {
        "status": "success",
        "code": 200,
        "message": "Legal Persons retrieved successfully.",
        "data": {
            "legal_person": result
        }
    }, 200

## -natural person
@rpr.route('/create_natural_person', methods=['POST'])
def create_natural_person():

    data = request.get_json(silent=True)

    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400

    hash_pid = data.get("hash_pid")
    family_name = data.get("familyName")
    given_name = data.get("givenName")
    date_of_birth = data.get("dateOfBirth")
    place_of_birth = data.get("placeOfBirth")

    required_fields = {
        "hash_pid": hash_pid
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    user_id = db.check_user(hash_pid)

    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    if not family_name or not given_name:
        return {
            "status": "error",
            "code": 400,
            "message": "familyName and givenName are required"
        }, 400

    result = db.insert_natural_person(
        family_name,
        given_name,
        date_of_birth,
        place_of_birth,
        user_id
    )

    if not result:
        return {
            "status": "error",
            "code": 500,
            "message": "Failed to create natural person"
        }, 500

    return {
        "status": "success",
        "code": 201,
        "message": "Natural Person created successfully"
    }, 201

@rpr.route('/list_natural_person', methods=['POST'])
def get_natural_person():

    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    if not hash_pid:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": ["hash_pid"]
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    result = db.get_natural_person(user_id)

    return {
        "status": "success",
        "code": 200,
        "message": "Natural Persons retrieved successfully.",
        "data": {
            "natural_person": result
        }
    }, 200

## -identifier
@rpr.route('/create_identifier', methods=['POST'])
def create_identifier():

    data = request.get_json(silent=True)

    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400

    hash_pid = data.get("hash_pid")
    identifiers = data.get("identifier", [])

    required_fields = {
        "hash_pid": hash_pid
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    user_id = db.check_user(hash_pid)

    for identifier in identifiers:
        identifier_value = identifier.get("identifier")
        type = identifier.get("type")

        result = db.insert_identifier(identifier_value, type, user_id)

    if not result:
        return {
            "status": "error",
            "code": 500,
            "message": "Failed to create Identifier"
        }, 500

    return {
        "status": "success",
        "code": 201,
        "message": "Identifier created successfully"
    }, 201

@rpr.route('/list_identifier', methods=['POST'])
def list_identifier():

    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    if not hash_pid:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": ["hash_pid"]
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    result = db.get_identifier(user_id)

    return {
        "status": "success",
        "code": 200,
        "message": "Identifiers retrieved successfully.",
        "data": {
            "identifier": result
        }
    }, 200

## -legal entity
@rpr.route('/create_legal_entity', methods=['POST'])
def create_legal_entity():

    data = request.get_json(silent=True)

    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400

    hash_pid = data.get("hash_pid")
    identifier_ids = data.get("identifiers", [])
    postalAddress = data.get("postalAddress", [])
    country = data.get("country")
    emails = data.get("email", [])
    phones = data.get("phone", [])
    infoURIs = data.get("infoURI", [])
    legal_person_id = data.get("legal_person_id")
    natural_person_id = data.get("natural_person_id")

    required_fields = {
        "hash_pid": hash_pid
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    user_id = db.check_user(hash_pid)

    legal_entity_id = db.insert_legal_entity(legal_person_id, natural_person_id, country, user_id)
    
    for identifier_id in identifier_ids:
        db.insert_legal_entity_identifier(legal_entity_id, identifier_id)

    for aux in postalAddress:
        db.insert_legal_entity_postal_address(legal_entity_id, aux)
        
    for email in emails:
        db.insert_legal_entity_email(legal_entity_id, email)
        
    for phone in phones:
        db.insert_legal_entity_phone(legal_entity_id, phone)
        
    for infoURI in infoURIs:
        result = db.insert_legal_entity_info_uri(legal_entity_id, infoURI)

    if not result:
        return {
            "status": "error",
            "code": 500,
            "message": "Failed to create Lgal Entity"
        }, 500

    return {
        "status": "success",
        "code": 201,
        "message": "Legal Entity created successfully"
    }, 201

@rpr.route('/list_legal_entity', methods=['POST'])
def list_legal_entity():

    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    if not hash_pid:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": ["hash_pid"]
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    result = db.get_legal_entity(user_id)

    return {
        "status": "success",
        "code": 200,
        "message": "Legal Entity retrieved successfully.",
        "data": {
            "legal_entity": result
        }
    }, 200

## -provider
@rpr.route('/create_provider', methods=['POST'])
def create_provider():

    data = request.get_json(silent=True)

    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400

    hash_pid = data.get("hash_pid")
    legalEntityId = data.get("legalEntityId")
    providerType = data.get("providerType")
    x5c = data.get("x5c", [])
    policy_ids = data.get("policy_id", [])

    required_fields = {
        "hash_pid": hash_pid
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    user_id = db.check_user(hash_pid)

    provider_id = db.insert_provider(legalEntityId, providerType, user_id)
    
    for policy_id in policy_ids:
        db.insert_provider_policy(provider_id, policy_id)

    for cert in x5c:
        db.insert_provider_x5c(provider_id, cert)

    return {
        "status": "success",
        "code": 201,
        "message": "Provider created successfully"
    }, 201

@rpr.route('/list_provider', methods=['POST'])
def list_provider():
    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    if not hash_pid:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": ["hash_pid"]
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    result = db.get_provider(user_id)

    return {
        "status": "success",
        "code": 200,
        "message": "Legal Entity retrieved successfully.",
        "data": {
            "provider": result
        }
    }, 200

## -policy
@rpr.route('/create_policy', methods=['POST'])
def create_policy():

    data = request.get_json(silent=True)

    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400

    hash_pid = data.get("hash_pid")
    policies = data.get("policy", [])

    required_fields = {
        "hash_pid": hash_pid
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    user_id = db.check_user(hash_pid)

    for policy in policies:
        policyURI = policy.get("policyURI")
        type = policy.get("type")

        db.insert_policy(policyURI, type, user_id)

    return {
        "status": "success",
        "code": 201,
        "message": "Policy created successfully"
    }, 201

@rpr.route('/list_policy', methods=['POST'])
def list_policy():

    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    if not hash_pid:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": ["hash_pid"]
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    result = db.get_policy(user_id)

    return {
        "status": "success",
        "code": 200,
        "message": "Policies retrieved successfully.",
        "data": {
            "policy": result
        }
    }, 200

## -credential
@rpr.route('/create_credential', methods=['POST'])
def create_credential():

    data = request.get_json(silent=True)

    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400

    hash_pid = data.get("hash_pid")
    credentials = data.get("credentials", [])

    required_fields = {
        "hash_pid": hash_pid
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    user_id = db.check_user(hash_pid)

    for credential in credentials:
        format = credential.get("format")
        meta = credential.get("meta")
        claims = credential.get("claims", [])

        credential_id = db.insert_credential(format, meta, user_id)

        for claim in claims:
            path = claim.get("path")

            db.insert_claim(credential_id, path)
    
    return {
        "status": "success",
        "code": 201,
        "message": "Credential created successfully"
    }, 201

@rpr.route('/list_credential', methods=['POST'])
def list_credential():
    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    if not hash_pid:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": ["hash_pid"]
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    result = db.get_credentials(user_id)

    return {
        "status": "success",
        "code": 200,
        "message": "Credentials retrieved successfully.",
        "data": {
            "credential": result
        }
    }, 200

## -intended use
@rpr.route('/create_intended_use', methods=['POST'])
def create_intended_use():

    data = request.get_json(silent=True)

    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400

    hash_pid = data.get("hash_pid")
    intended_uses = data.get("intended_uses", [])

    required_fields = {
        "hash_pid": hash_pid
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    user_id = db.check_user(hash_pid)

    for intended_use in intended_uses:
        intendedUseIdentifier = intended_use.get("intendedUseIdentifier")
        createdAt = intended_use.get("createdAt")
        revokedAt = intended_use.get("revokedAt")
        purposes = intended_use.get("purpose", [])
        privacyPolicy_ids = intended_use.get("privacyPolicy_id", [])
        credential_ids = intended_use.get("credential_ids", [])

        intended_use_id = db.insert_intended_use(intendedUseIdentifier, createdAt, revokedAt, user_id)

        for purpose in purposes:
            lang = purpose.get("lang")
            content = purpose.get("content")

            mls_id = db.insert_multilanguage_string(lang, content, user_id)
            db.insert_intended_use_purpose(intended_use_id, mls_id)
        
        for privacyPolicy_id in privacyPolicy_ids:
            db.insert_intended_use_policy(intended_use_id, privacyPolicy_id)

        for credential_id in credential_ids:
            db.insert_intended_use_credential(intended_use_id, credential_id)
    
    return {
        "status": "success",
        "code": 201,
        "message": "Credential created successfully"
    }, 201

@rpr.route('/list_intended_use', methods=['POST'])
def list_intended_use():
    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    if not hash_pid:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": ["hash_pid"]
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    result = db.get_intended_use(user_id)

    return {
        "status": "success",
        "code": 200,
        "message": "Intended Use retrieved successfully.",
        "data": {
            "intended_use": result
        }
    }, 200

## -provided attestation
@rpr.route('/create_provided_attestation', methods=['POST'])
def create_provided_attestation():

    data = request.get_json(silent=True)

    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400

    hash_pid = data.get("hash_pid")
    providesAttestations = data.get("providesAttestations", [])

    required_fields = {
        "hash_pid": hash_pid
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    user_id = db.check_user(hash_pid)

    for providesAttestation in providesAttestations:
        format = providesAttestation.get("format")
        meta = providesAttestation.get("meta")

        db.insert_provided_attestation(format, meta, user_id)

    return {
        "status": "success",
        "code": 201,
        "message": "Provided Attestation created successfully"
    }, 201

@rpr.route('/list_provided_attestation', methods=['POST'])
def list_provided_attestation():
    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    if not hash_pid:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": ["hash_pid"]
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    result = db.get_provided_attestation(user_id)

    return {
        "status": "success",
        "code": 200,
        "message": "Provided attestation retrieved successfully.",
        "data": {
            "provided_attestation": result
        }
    }, 200

## -wrp
@rpr.route('/create_wrp', methods=['POST'])
def create_wrp():

    data = request.get_json(silent=True)

    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400

    hash_pid = data.get("hash_pid")
    wrps = data.get("WalletRelyingParty", [])

    required_fields = {
        "hash_pid": hash_pid
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    user_id = db.check_user(hash_pid)
    
    for wrp in wrps:
        tradeName = wrp.get("tradeName")
        supportURIs = wrp.get("supportURI", [])
        srvDescriptions = wrp.get("srvDescription", [])
        isPSB = wrp.get("isPSB")
        isIntermediary = wrp.get("isIntermediary")
        entitlements = wrp.get("entitlements", [])
        usesIntermediarys = wrp.get("usesIntermediary", [])
        providesAttestations_ids = wrp.get("providesAttestations_id", [])
        registryURI = wrp.get("registryURI")
        supervisoryAuthority = wrp.get("supervisoryAuthority")
        provider_id = wrp.get("provider_id")
        intendedUse_ids = wrp.get("intendedUse_ids", [])

        supervisoryAuthority_name = supervisoryAuthority.get("name")
        supervisoryAuthority_country = supervisoryAuthority.get("country")
        supervisoryAuthority_emails = supervisoryAuthority.get("email", [])
        supervisoryAuthority_formuris = supervisoryAuthority.get("formURI", [])
        supervisoryAuthority_phones = supervisoryAuthority.get("phone", [])

        supervisory_authority_id = db.insert_supervisory_authority(supervisoryAuthority_name, supervisoryAuthority_country, user_id)

        for email in supervisoryAuthority_emails:
            db.insert_supervisory_authority_email(supervisory_authority_id, email)

        for formUri in supervisoryAuthority_formuris:
            db.insert_supervisory_authority_formuri(supervisory_authority_id, formUri)

        for phone in supervisoryAuthority_phones:
            db.insert_supervisory_authority_phone(supervisory_authority_id, phone)

        wrp_id = db.insert_wrp(provider_id, tradeName, isPSB, registryURI, isIntermediary, supervisory_authority_id, user_id)

        for entitlement in entitlements:
            db.insert_wrp_entitlement(wrp_id, entitlement)

        for usesIntermediary in usesIntermediarys:
            db.insert_wrp_intermediary(wrp_id, usesIntermediary)
        
        for supportURI in supportURIs:
            db.insert_wrp_support_uri(wrp_id, supportURI)

        for srvDescription in srvDescriptions:
            lang = srvDescription.get("lang")
            content = srvDescription.get("content")

            mls_id = db.insert_multilanguage_string(lang, content, user_id)

            db.insert_wrp_srv_description(wrp_id, mls_id)

        for providesAttestations_id in providesAttestations_ids:
            db.insert_wrp_provided_attestation(wrp_id, providesAttestations_id)

        for intendedUse_id in intendedUse_ids:
            db.insert_wrp_intended_use(wrp_id, intendedUse_id)

    return {
        "status": "success",
        "code": 201,
        "message": "Provided Attestation created successfully"
    }, 201

@rpr.route('/list_wrp', methods=['POST'])
def list_wrp():
    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    if not hash_pid:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": ["hash_pid"]
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    result = db.get_wrp(user_id)

    return {
        "status": "success",
        "code": 200,
        "message": "Wallet Relying Party retrieved successfully.",
        "data": {
            "wrp": result
        }
    }, 200

@rpr.route('/list_supervisory_authority', methods=['POST'])
def list_supervisory_authority():
    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    if not hash_pid:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": ["hash_pid"]
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    result = db.get_supervisory_authority(user_id)

    return {
        "status": "success",
        "code": 200,
        "message": "Legal Entity retrieved successfully.",
        "data": {
            "supervisory_authority": result
        }
    }, 200

@rpr.route('/list_claim', methods=['POST'])
def list_claim():
    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    if not hash_pid:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": ["hash_pid"]
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400


    result = db.get_claim(user_id)

    return {
        "status": "success",
        "code": 200,
        "message": "Claims retrieved successfully.",
        "data": {
            "claim": result
        }
    }, 200
@rpr.route('/list_full_info', methods=['POST'])
def list_full_info():
    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    if not hash_pid:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": ["hash_pid"]
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    legal_entities = db.get_legal_entity(user_id)
    providers = db.get_provider(user_id)
    wrps = db.get_wrp(user_id)
    intended_uses = db.get_intended_use(user_id)

    result = []

    provider_by_le = {}
    for p in providers:
        provider_by_le.setdefault(p["legal_entity_id"], []).append(p)

    wrp_by_provider = {}
    for w in wrps:
        wrp_by_provider.setdefault(w["provider_id"], []).append(w)

    iu_by_id = {iu["intended_use_id"]: iu for iu in intended_uses}

    for le in legal_entities:

        le_id = le["legal_entity_id"]

        le_obj = le.copy()
        le_obj["providers"] = []

        for p in provider_by_le.get(le_id, []):

            p_id = p["provider_id"]

            p_obj = p.copy()
            p_obj["wrp"] = []

            for w in wrp_by_provider.get(p_id, []):

                w_obj = w.copy()

                full_iu = []

                for iu_ref in w.get("intendedUses", []):
                    iu_id = iu_ref["id"]

                    if iu_id in iu_by_id:
                        full_iu.append(iu_by_id[iu_id])

                w_obj["intended_use"] = full_iu

                p_obj["wrp"].append(w_obj)

            le_obj["providers"].append(p_obj)

        result.append(le_obj)

    return {
        "status": "success",
        "code": 200,
        "data": result
    }, 200

@rpr.route('/wrp', methods=['GET'])
def search_wrp_public():

    identifier = request.args.get("identifier")
    legalname = request.args.get("legalname")
    #tradename = request.args.get("tradename")
    policy = request.args.get("policy")
    entitlement = request.args.get("entitlement")
    providesattestation = request.args.get("providesattestation")
    intendeduseidentifier = request.args.get("intendeduseidentifier")
    isintermediary = request.args.get("isintermediary")
    #usesintermediary = request.args.get("usesintermediary")

    if isintermediary is not None:
        if isintermediary.lower() == "true":
            isintermediary = 1
        elif isintermediary.lower() == "false":
            isintermediary = 0
        else:
            isintermediary = None 

    result = db.search_wrp_public(
        identifier=identifier,
        legalname=legalname,
        #tradename=tradename,
        policy=policy,
        entitlement=entitlement,
        #providesattestation=providesattestation,
        #intendeduseidentifier=intendeduseidentifier,
        isintermediary=isintermediary,
        #usesintermediary=usesintermediary
    )
    
    final_result= json.dumps(result)

    key = import_private_ec_key_from_file(cfgserv.wrprc_privateKey)
    ec_key = ECKey(priv_key=key)

    jws = JWS(final_result, alg="ES256")

    signed_jws = jws.sign_json([ec_key])

    return signed_jws


@rpr.route('/wrp/<identifier>', methods=['GET'])
def get_wrp_by_identifier(identifier):

    wrp = db.get_wrp_by_identifier(identifier)

    if not wrp:
        return {
            "status": "error",
            "code": 404,
            "message": "WRP not found"
        }, 404

    key = import_private_ec_key_from_file(cfgserv.wrprc_privateKey)
    ec_key = ECKey(priv_key=key)

    jws = JWS(json.dumps(wrp), alg="ES256")

    signed_jws = jws.sign_json([ec_key])

    return signed_jws

@rpr.route('/wrp/check-intended-use', methods=['GET'])
def check_intended_use():

    identifier = request.args.get("identifier")
    claim_path = request.args.get("claim_path")
    credential_format = request.args.get("credential_format")
    credential_meta = request.args.get("credential_meta")
    intended_use_identifier = request.args.get("intended_use_identifier")

    if not identifier:
        return {
            "status": "error",
            "code": 400,
            "message": "identifier is required"
        }, 400

    exists = db.check_intended_use(
        identifier,
        claim_path,
        credential_format,
        credential_meta,
        intended_use_identifier
    )
    
    key = import_private_ec_key_from_file(cfgserv.wrprc_privateKey)
    ec_key = ECKey(priv_key=key)

    jws = JWS(json.dumps(exists), alg="ES256")

    signed_jws = jws.sign_json([ec_key])

    return signed_jws



































    
@rpr.route('/natural_person/add_natural_person_db', methods=['POST'])
def add_natural_person_db():
    """
    Create a new Natural Person
    ---
    tags:
      - Natural Person
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - hash_pid
            - given_name
            - family_name
            - birthdate
            - birthplace
          properties:
            hash_pid:
              type: string
              description: User identifier (from wallet login)
              example: "abc123hashpid"
            given_name:
              type: string
              example: "John"
            family_name:
              type: string
              example: "Doe"
            birthdate:
              type: string
              format: date
              example: "1990-01-01"
            birthplace:
              type: string
              example: "Lisbon"
    responses:
      201:
        description: Natural Person successfully created
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            code:
              type: integer
              example: 201
            message:
              type: string
              example: Natural Person successfully created.
            data:
              type: object
              properties:
                Natural Person id:
                  type: integer
                  example: 42

      400:
        description: Missing or invalid fields
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            code:
              type: integer
              example: 400
            message:
              type: string
              example: Missing required fields
            data:
              type: object
              properties:
                missing_fields:
                  type: array
                  items:
                    type: string
    """

    data = request.get_json(silent=True)

    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")
    given_name= data.get("given_name")
    family_name=data.get("family_name")
    birthdate=data.get("birthdate")
    birthplace=data.get("birthplace")

    required_fields = {
        "hash_pid": hash_pid,
        "given_name": given_name,
        "family_name": family_name,
        "birthdate": birthdate,
        "birthplace": birthplace
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    user_id = db.check_user(hash_pid)

    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    id = db.insert_user_naturalPerson(given_name, family_name, birthdate, birthplace, user_id) 

    return {
        "status": "success",
        "code": 201,
        "message": "Natural Person successfully created.",
        "data": {
            "Natural Person id": id
        }
    }, 201


@rpr.route('/natural_person/ui_update_legal_entities', methods=["POST"])
def ui_update_legal_entities():
    """
    Update associations between a Natural Person and Legal Entities
    ---
    tags:
      - Natural Person
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - hash_pid
            - natural_person
            - legal_entities_ids
          properties:
            hash_pid:
              type: string
              example: "abc123hashpid"
            natural_person:
              type: string
              example: "15"
            legal_entities_ids:
              type: array
              items:
                type: integer
              example: [1, 2, 3]
    responses:
      200:
        description: Associations updated successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Associations updated successfully
            updated_count:
              type: integer
              example: 3

      400:
        description: Invalid request or validation error
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            code:
              type: integer
              example: 400
            message:
              type: string
              example: Missing required fields
    """

    data = request.get_json(silent=True)

    if not data:
        return {
                "status": "error",
                "code": 400,
                "message": "Invalid or missing JSON body"
            }, 400

    hash_pid = data.get("hash_pid")
    natural_person = data.get("natural_person")
    legal_entities_ids = data.get("legal_entities_ids")

    required_fields = {
        "hash_pid": hash_pid,
        "natural_person": natural_person,
        "legal_entities_ids": legal_entities_ids
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    if not isinstance(legal_entities_ids, list):
        return {
                "status": "error",
                "code": 400,
                "message": "Legal Entities ids must be a list"
            }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    all_natural_person = db.get_natural_person_info(user_id)
    valid_natural_person_ids = {str(p["naturalperson_id"]) for p in all_natural_person}

    if str(natural_person) not in valid_natural_person_ids:
        return {
                "status": "error",
                "code": 400,
                "message": "Natural person does not exist or does not belong to this user"
            }, 400
    
    all_legal_entities = db.get_legal_entity_info(user_id)
    valid_ids = {int(e["legalentity_id"]) for e in all_legal_entities}

    invalid_ids = [
        le_id for le_id in legal_entities_ids
        if int(le_id) not in valid_ids
    ]
        
    if invalid_ids:
        return {
            "status": "error",
            "code": 400,
            "message": "Some legal entities do not exist or do not belong to this user",
            "invalid_legal_entities_ids": invalid_ids
        }, 400

    for elem_id in legal_entities_ids:
        db.update_naturalPerson_legal_entity(natural_person, elem_id)

    return {
        "status": "success",
        "message": "Associations updated successfully",
        "updated_count": len(legal_entities_ids)
    }, 200

def list_naturalPerson(user_id):

    person_dict = db.get_natural_person_info(user_id)
    
    header_table=[ "Given Name", "Family Name", "Date of Birth", "Place of Birth"]
    
    if(person_dict == "err" or person_dict == None):
        data={}
    else:
        data={}

        for person in person_dict:
            data_temp={
                person["naturalperson_id"]:{
                    "Given Name":person["givenName"],
                    "Family Name":person["familyName"],
                    "Date of Birth":person["dateOfBirth"],
                    "Place of Birth":person["placeOfBirth"]
                }
            }
            data.update(data_temp)
    
    legal_entity_dict = db.get_legal_entity_info(user_id)
    
    list = []
    if(data != {}):
        if(legal_entity_dict != "err" and legal_entity_dict != None):

            for item in legal_entity_dict:
                name = item["identifier"]

                if(item["naturalperson_id"] != None):
                    person_name = db.get_natural_person_info_le(item["naturalperson_id"])

                    new_item = {
                        "id": item["legalentity_id"],
                        "name": name,
                        "associated_id": item["naturalperson_id"],
                        "ass_name": person_name
                    }
                else:
                    new_item = {
                        "id": item["legalentity_id"],
                        "name": name,
                        "associated_id": item["naturalperson_id"],
                        "ass_name": ""
                    }
                
                list.append(new_item)
    
    menu= cfgserv.service_url + "menu"

    return menu, data, header_table, list 

@rpr.route('/natural_person/list', methods=['GET', 'POST'])
def natural_person_list():
    """
List Legal Entities and Natural Persons
---
tags:
  - Natural Person
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: "abc123hashpid"

responses:
  200:
    description: Legal entities and natural persons retrieved successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        code:
          type: integer
          example: 200
        message:
          type: string
          example: Legal entities and natural persons retrieved successfully.
        data:
          type: object
          properties:
            legal_entities:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 10
                  name:
                    type: string
                    example: "ACME Corporation"
                  associated:
                    type: boolean
                    example: true
                  natural_person:
                    type: object
                    nullable: true
                    properties:
                      id:
                        type: integer
                        example: 5
                      given_name:
                        type: string
                        example: "John"
                      family_name:
                        type: string
                        example: "Doe"
                      date_of_birth:
                        type: string
                        example: "1990-05-10"
                      place_of_birth:
                        type: string
                        example: "Lisbon"

            natural_persons:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 5
                  given_name:
                    type: string
                    example: "John"
                  family_name:
                    type: string
                    example: "Doe"
                  date_of_birth:
                    type: string
                    example: "1990-05-10"
                  place_of_birth:
                    type: string
                    example: "Lisbon"

  400:
    description: Invalid hash_pid
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Invalid hash_pid
        data:
          type: object
          properties:
            hash_pid:
              type: string
              example: "abc123hashpid"
"""

    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    required_fields = {
        "hash_pid": hash_pid
    }
    
    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    menu, data, header_table, list = list_naturalPerson(user_id)

    used_ids = {
        str(item["associated_id"])
        for item in list
        if item["associated_id"] is not None
    }

    natural_persons = []
    available = []

    for pid, person in data.items():
        p = {
            "id": int(pid),
            "given_name": person["Given Name"],
            "family_name": person["Family Name"],
            "date_of_birth": person["Date of Birth"],
            "place_of_birth": person["Place of Birth"]
        }
        natural_persons.append(p)

        if pid not in used_ids:
            available.append({
                "id": int(pid),
                "given_name": person["Given Name"],
                "family_name": person["Family Name"]
            })

    legal_entities = []
    
    for le in list:
        assoc_id = le["associated_id"]
        legal_entities.append({
            "id": le["id"],
            "name": le["name"],
            "associated": assoc_id is not None,
            "natural_person": (
                {
                    "id": assoc_id,
                    "given_name": data[assoc_id]["Given Name"],
                    "family_name": data[assoc_id]["Family Name"],
                    "date_of_birth": data[assoc_id]["Date of Birth"],
                    "place_of_birth": data[assoc_id]["Place of Birth"]
                } if assoc_id and assoc_id in data else None
            )
        })
        
    return {
        "status": "success",
        "code": 200,
        "message": "Legal entities and natural persons retrieved successfully.",
        "data": {
            "legal_entities": legal_entities,
            "natural_persons": natural_persons
        }
    }, 200

@rpr.route('/legal_person/add_legal_person_db', methods=['POST'])
def add_legal_person_db():

    """
Create a new Legal Person
---
tags:
  - Legal Person
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
        - legal_name
        - established_by_law
        - lang
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: "abc123hashpid"
        legal_name:
          type: string
          description: Legal name of the Legal Person
          example: "ACME Corporation"
        established_by_law:
          type: string
          description: Legal basis or law establishing the entity
          example: "Commercial Law Article 10"
        lang:
          type: string
          description: Language of the legal basis
          example: "EU"
responses:
  201:
    description: Legal Person successfully created
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        code:
          type: integer
          example: 201
        message:
          type: string
          example: Legal Person successfully created.
        data:
          type: object
          properties:
            legal_person_id:
              type: integer
              example: 12

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example:
                - lang
"""

    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400

    hash_pid = data.get("hash_pid")
    legal_name= data.get("legal_name")
    established_by_law=data.get("established_by_law")
    lang=data.get("lang")

    required_fields = {
        "hash_pid": hash_pid,
        "legal_name": legal_name,
        "established_by_law": established_by_law,
        "lang": lang
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400
    
    if lang not in cfgserv.eu_countries:
        return {
            "status": "error",
            "code": 400,
            "message": f"Invalid lang. Must be one of: {', '.join(cfgserv.eu_countries)}",
            "provided": lang
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    legalBasis = '[{"lang":"' + lang + '", "legalBasis":"' + established_by_law + '"}]'

    id = db.insert_user_legalPerson(legal_name, legalBasis, user_id)

    return {
        "status": "success",
        "code": 201,
        "message": "Legal Person successfully created.",
        "data": {
            "legal_person_id": id
        }
    }, 201

@rpr.route('/legal_person/ui_update_legal_entities', methods=["POST"])
def ui_update_legal_person_entities():
    """
Update Legal Person associations with Legal Entities
---
tags:
  - Legal Person
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
        - legal_person
        - legal_entities_ids
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: abc123hashpid

        legal_person:
          type: integer
          description: ID of the Legal Person to associate Legal Entities with
          example: 8

        legal_entities_ids:
          type: array
          description: List of Legal Entity IDs to associate with the Legal Person
          items:
            type: integer
          example: [3, 5, 12]

responses:
  200:
    description: Associations updated successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        message:
          type: string
          example: Associations updated successfully
        updated_count:
          type: integer
          example: 3

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example: [legal_entities_ids]

  401:
    description: Invalid hash_pid
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Invalid hash_pid
        data:
          type: object
          properties:
            hash_pid:
              type: string
              example: abc123hashpid

  422:
    description: Some Legal Entities are invalid or do not belong to the user
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Some legal entities do not exist or do not belong to this user
        invalid_legal_entities_ids:
          type: array
          items:
            type: integer
          example: [99, 120]
"""

    data = request.get_json(silent=True)

    if not data:
        return {
                "status": "error",
                "code": 400,
                "message": "Invalid or missing JSON body"
            }, 400

    hash_pid = data.get("hash_pid")
    legal_person = data.get("legal_person")
    legal_entities_ids = data.get("legal_entities_ids")

    required_fields = {
        "hash_pid": hash_pid,
        "legal_person": legal_person,
        "legal_entities_ids": legal_entities_ids
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    if not isinstance(legal_entities_ids, list):
        return {
                "status": "error",
                "code": 400,
                "message": "Legal Entities ids must be a list"
            }, 400
    
    user_id = db.check_user(hash_pid)
    
    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    all_legal_person = db.get_legal_person_info(user_id)
    valid_legal_person_ids = {str(p["legalperson_id"]) for p in all_legal_person}

    if str(legal_person) not in valid_legal_person_ids:
        return {
                "status": "error",
                "code": 400,
                "message": "Legal person does not exist or does not belong to this user"
            }, 400
    
    all_legal_entities = db.get_legal_entity_info(user_id)
    valid_ids = {int(e["legalentity_id"]) for e in all_legal_entities}

    invalid_ids = [
        le_id for le_id in legal_entities_ids
        if int(le_id) not in valid_ids
    ]
        
    if invalid_ids:
        return {
            "status": "error",
            "code": 400,
            "message": "Some legal entities do not exist or do not belong to this user",
            "invalid_legal_entities_ids": invalid_ids
        }, 400

    for elem_id in legal_entities_ids:
        db.update_legalPerson_legal_entity(legal_person, elem_id)

    return {
        "status": "success",
        "message": "Associations updated successfully",
        "updated_count": len(legal_entities_ids)
    }, 200

def list_legalPerson(user_id):

    person_dict = db.get_legal_person_info(user_id)

    header_table=[ "Legal Name", "Established By Law"]
    if(person_dict == None):
        data={}
    else:
        data={}

        for person in person_dict:
            data_temp={
                person["legalperson_id"]:{
                    "Legal Name":person["legalName"],
                    "Established By Law":person["legalBasis"]
                }
            }
            data.update(data_temp)

    legal_entity_dict = db.get_legal_entity_info(user_id)
    
    list = []
    if(data != {}):
        if(legal_entity_dict != "err" and legal_entity_dict != None):

            for item in legal_entity_dict:
                name = item["identifier"]
                
                if(item["legalperson_id"] != None):
                    person_name = db.get_legal_person_info_le(item["legalperson_id"])
                    
                    new_item = {
                        "id": item["legalentity_id"],
                        "name": name,
                        "associated_id": item["legalperson_id"],
                        "ass_name": person_name
                    }
                else:
                    new_item = {
                        "id": item["legalentity_id"],
                        "name": name,
                        "associated_id": item["legalperson_id"],
                        "ass_name": ""
                    }
                
                list.append(new_item)
    
    menu= cfgserv.service_url + "menu"

    return menu, data, header_table, list

@rpr.route('/legal_person/list', methods=['GET', 'POST'])
def legal_person_list():
    """
List Legal Entities and Legal Persons
---
tags:
  - Legal Person
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: "abc123hashpid"

responses:
  200:
    description: Legal entities and legal persons retrieved successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        code:
          type: integer
          example: 200
        message:
          type: string
          example: Legal entities and legal persons retrieved successfully.
        data:
          type: object
          properties:
            legal_entities:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 10
                  name:
                    type: string
                    example: "ACME Corporation"
                  associated:
                    type: boolean
                    example: true
                  legal_person:
                    type: object
                    nullable: true
                    properties:
                      id:
                        type: integer
                        example: 3
                      legal_name:
                        type: string
                        example: "ACME Corporation"
                      established_by_law:
                        type: object
                        example: {"law": "Commercial Law Article 10", "lang": "EN"}

            legal_persons:
              type: object
              additionalProperties:
                type: object
                properties:
                  legal_name:
                    type: string
                    example: "ACME Corporation"
                  established_by_law:
                    type: object
                    example: {"law": "Commercial Law Article 10", "lang": "EN"}

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example:
                - hash_pid
"""

    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")
    
    required_fields = {
        "hash_pid": hash_pid
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    menu, data, header_table, list = list_legalPerson(user_id)
    
    legal_persons = {}

    for lp_id, lp_data in data.items():
        legal_persons[int(lp_id)] = {
            "legal_name": lp_data["Legal Name"],
            "established_by_law": json.loads(lp_data["Established By Law"])
        }

    legal_entities = []

    for entity in list:
        associated_id = entity["associated_id"]

        legal_entities.append({
            "id": entity["id"],
            "name": entity["name"],
            "associated": associated_id is not None,
            "legal_person": (
                {
                    "id": associated_id,
                    **legal_persons.get(associated_id, {})
                }
                if associated_id in legal_persons else None
            )
        })

    return {
        "status": "success",
        "code": 200,
        "message": "Legal entities and legal persons retrieved successfully.",
        "data": {
            "legal_entities": legal_entities,
            "legal_persons": legal_persons
        }
    }, 200

@rpr.route('/legal_entity/add_legal_entity_db', methods=['POST'])
def add_legal_entity_db():
    """
Create a new Legal Entity
---
tags:
  - Legal Entity
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
        - type_of_identifier
        - identifier
        - address
        - email
        - phone_number
        - information_URI
        - country
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: "abc123hashpid"
        type_of_identifier:
          type: string
          description: Type of identifier
          example: "http://data.europa.eu/eudi/id/EORI-No"
        identifier:
          type: string
          description: Identifier value of the legal entity
          example: "123456789"
        address:
          type: string
          description: Legal address of the entity
          example: "123 Main Street, City, Country"
        email:
          type: string
          description: Contact email of the legal entity
          example: "contact@acme.com"
        phone_number:
          type: string
          description: Contact phone number
          example: "+123456789"
        information_URI:
          type: string
          description: URL for more information about the legal entity
          example: "https://acme.com/info"
        country:
          type: string
          description: Country of registration
          example: "EU"
responses:
  201:
    description: Legal Entity successfully created
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        code:
          type: integer
          example: 201
        message:
          type: string
          example: Legal Entity successfully created.
        data:
          type: object
          properties:
            legal_entity_id:
              type: integer
              example: 15

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example:
                - email
                - country
"""

    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")
    type_of_identifier = data.get("type_of_identifier")
    identifier = data.get("identifier")
    address = data.get("address")
    email = data.get("email")
    phone_number = data.get("phone_number")
    information_URI = data.get("information_URI")
    country = data.get("country")

    required_fields = {
        "hash_pid": hash_pid,
        "type_of_identifier": type_of_identifier,
        "identifier": identifier,
        "address": address,
        "email": email,
        "phone_number": type_of_identifier,
        "information_URI": identifier,
        "country": address
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400
    
    if type_of_identifier not in cfgserv.legal_entity_type_identifier["Type of Identifier"]:
        return {
            "status": "error",
            "code": 400,
            "message": f"Invalid type_of_identifier. Must be one of: {', '.join(cfgserv.legal_entity_type_identifier['Type of Identifier'])}",
            "provided": type_of_identifier
        }, 400
    
    if country not in cfgserv.eu_countries:
        return {
            "status": "error",
            "code": 400,
            "message": f"Invalid Country. Must be one of: {', '.join(cfgserv.eu_countries)}",
            "provided": country
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    id = db.insert_legal_entity(address, country, email, phone_number, information_URI, identifier, type_of_identifier, user_id) 
    
    return {
        "status": "success",
        "code": 201,
        "message": "Legal Entity successfully created.",
        "data": {
            "Legal Entity id": id
        }
    }, 201

@rpr.route('/legal_entity/ui_update_RPs', methods=["POST"])
def ui_update_RPs():
    """
Update Legal Entity associations with Relying Parties
---
tags:
  - Legal Entity
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
        - legal_entity
        - relying_parties
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: abc123hashpid

        legal_entity:
          type: integer
          description: ID of the Legal Entity to associate Relying Parties with
          example: 10

        relying_parties:
          type: array
          description: List of Relying Party IDs to associate with the Legal Entity
          items:
            type: integer
          example: [3, 5, 9]

responses:
  200:
    description: Associations updated successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        message:
          type: string
          example: Associations updated successfully
        updated_count:
          type: integer
          example: 3

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example: [relying_parties]

  401:
    description: Invalid hash_pid
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Invalid hash_pid
        data:
          type: object
          properties:
            hash_pid:
              type: string
              example: abc123hashpid

  422:
    description: Some relying parties are invalid or do not belong to the user
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Some legal entities do not exist or do not belong to this user
        invalid_relying_parties:
          type: array
          items:
            type: integer
          example: [99, 120]
"""

    data = request.get_json(silent=True)

    if not data:
        return {
                "status": "error",
                "code": 400,
                "message": "Invalid or missing JSON body"
            }, 400

    hash_pid = data.get("hash_pid")
    legal_entity = data.get("legal_entity")
    relying_parties = data.get("relying_parties")

    required_fields = {
        "hash_pid": hash_pid,
        "legal_entity": legal_entity,
        "relying_parties": relying_parties
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    if not isinstance(relying_parties, list):
        return {
                "status": "error",
                "code": 400,
                "message": "Legal Entities ids must be a list"
            }, 400

    user_id = db.check_user(hash_pid)
    
    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
  
    all_legal_entities = db.get_legal_entity_info(user_id)
    valid_legal_person_ids = {str(p["legalentity_id"]) for p in all_legal_entities}

    if str(legal_entity) not in valid_legal_person_ids:
        return {
                "status": "error",
                "code": 400,
                "message": "Legal Entity does not exist or does not belong to this user"
            }, 400
    
    all_wrp = db.get_rp_info(user_id)
    valid_ids = {int(e["wrp_id"]) for e in all_wrp}

    invalid_ids = [
        le_id for le_id in relying_parties
        if int(le_id) not in valid_ids
    ]
        
    if invalid_ids:
        return {
            "status": "error",
            "code": 400,
            "message": "Some legal entities do not exist or do not belong to this user",
            "invalid_relying_parties": invalid_ids
        }, 400

    for elem_id in relying_parties:
        db.update_wrp_legal_entity(legal_entity, elem_id)

    return {
        "status": "success",
        "message": "Associations updated successfully",
        "updated_count": len(relying_parties)
    }, 200

  
@rpr.route('/legal_entity/ui_remove_update_natural_person', methods=["POST"])
def ui_remove_update_natural_person():
    """
Remove Natural Person associations from Legal Entities
---
tags:
  - Legal Entity
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
        - legal_entity
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: abc123hashpid

        legal_entity:
          type: array
          description: List of Legal Entity IDs to remove the Natural Person association from
          items:
            type: integer
          example: [3, 7, 12]

responses:
  200:
    description: Associations removed successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        message:
          type: string
          example: Associations updated successfully
        updated_count:
          type: integer
          example: 3

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example: [legal_entity]

  401:
    description: Invalid hash_pid
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Invalid hash_pid
        data:
          type: object
          properties:
            hash_pid:
              type: string
              example: abc123hashpid

  422:
    description: Some Legal Entities are invalid or do not belong to the user
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Some legal entities do not exist or do not belong to this user
        invalid_legal_entities:
          type: array
          items:
            type: integer
          example: [99, 120]
"""

    data = request.get_json(silent=True)

    if not data:
        return {
                "status": "error",
                "code": 400,
                "message": "Invalid or missing JSON body"
            }, 400

    hash_pid = data.get("hash_pid")
    legal_entity = data.get("legal_entity")

    required_fields = {
        "hash_pid": hash_pid,
        "legal_entity": legal_entity,
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    if not isinstance(legal_entity, list):
        return {
                "status": "error",
                "code": 400,
                "message": "Legal Entities ids must be a list"
            }, 400

    user_id = db.check_user(hash_pid)
    
    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    all_legal_entities = db.get_legal_entity_info(user_id)
    valid_legal_person_ids = {p["legalentity_id"] for p in all_legal_entities}

    invalid_ids = [
        le_id for le_id in legal_entity
        if int(le_id) not in valid_legal_person_ids
    ]
        
    if invalid_ids:
        return {
            "status": "error",
            "code": 400,
            "message": "Some legal entities do not exist or do not belong to this user",
            "invalid_legal_entities": invalid_ids
        }, 400

    for elem_id in legal_entity:
        db.update_naturalPerson_legal_entity(None, elem_id)

    return {
        "status": "success",
        "message": "Associations removed successfully",
        "updated_count": len(legal_entity)
    }, 200
  

@rpr.route('/legal_entity/ui_remove_update_legal_person', methods=["POST"])
def ui_remove_update_legal_person():
    """
Remove Legal Person associations from Legal Entities
---
tags:
  - Legal Entity
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
        - legal_entity
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: abc123hashpid

        legal_entity:
          type: array
          description: List of Legal Entity IDs to remove the Legal Person association from
          items:
            type: integer
          example: [3, 7, 12]

responses:
  200:
    description: Associations removed successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        message:
          type: string
          example: Associations updated successfully
        updated_count:
          type: integer
          example: 3

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example: [legal_entity]

  401:
    description: Invalid hash_pid
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Invalid hash_pid
        data:
          type: object
          properties:
            hash_pid:
              type: string
              example: abc123hashpid

  422:
    description: Some Legal Entities are invalid or do not belong to the user
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Some legal entities do not exist or do not belong to this user
        invalid_legal_entities:
          type: array
          items:
            type: integer
          example: [99, 120]
"""

    data = request.get_json(silent=True)

    if not data:
        return {
                "status": "error",
                "code": 400,
                "message": "Invalid or missing JSON body"
            }, 400

    hash_pid = data.get("hash_pid")
    legal_entity = data.get("legal_entity")

    required_fields = {
        "hash_pid": hash_pid,
        "legal_entity": legal_entity,
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    if not isinstance(legal_entity, list):
        return {
                "status": "error",
                "code": 400,
                "message": "Legal Entities ids must be a list"
            }, 400
    
    user_id = db.check_user(hash_pid)
    
    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    all_legal_entities = db.get_legal_entity_info(user_id)
    valid_legal_person_ids = {p["legalentity_id"] for p in all_legal_entities}

    invalid_ids = [
        le_id for le_id in legal_entity
        if int(le_id) not in valid_legal_person_ids
    ]
        
    if invalid_ids:
        return {
            "status": "error",
            "code": 400,
            "message": "Some legal entities do not exist or do not belong to this user",
            "invalid_legal_entities": invalid_ids
        }, 400

    for elem_id in legal_entity:
        db.update_legalPerson_legal_entity(None, elem_id)

    return {
        "status": "success",
        "message": "Associations updated successfully",
        "updated_count": len(legal_entity)
    }, 200
  
def list_legalEntity(user_id):

    legal_entity_dict = db.get_legal_entity_info(user_id)
    
    header_table=[ "Identifier","Postal Address","Country","E-mail","Phone","Information URI"]
    
    if(legal_entity_dict == "err" or legal_entity_dict == None):
        data={}
    else:
        data={}

        for legal_entity in legal_entity_dict:
            data_temp={
                legal_entity["legalentity_id"]:{
                    "Identifier":legal_entity["identifier"],
                    "Postal Address":legal_entity["postalAddress"],
                    "Country":legal_entity["country"],
                    "E-mail":legal_entity["email"],
                    "Phone":legal_entity["phone"],
                    "Information URI":legal_entity["infoURI"]
                }
            }
            data.update(data_temp)
    
    RP_dict = db.get_rp_info(user_id)
    
    list = []
    if(data != {}):
        if(RP_dict != "err" and RP_dict != None):

            for item in RP_dict:
                name_txt = item["tradeName"]

                if(item["supervisorAuthority"] != None):    
                    legal_entity_name = db.get_legal_entity_info_rp(item["supervisorAuthority"])
                    
                    new_item = {
                        "id": item["wrp_id"],
                        "name": name_txt,
                        "associated_id": item["supervisorAuthority"],
                        "ass_name": legal_entity_name
                    }
                else:
                    new_item = {
                        "id": item["wrp_id"],
                        "name": name_txt,
                        "associated_id": item["supervisorAuthority"],
                        "ass_name": ""
                    }
                
                list.append(new_item)
    
    menu= cfgserv.service_url + "menu"

    return menu, data, header_table, list

@rpr.route('/legal_entity/list', methods=['GET', 'POST'])
def legal_entity_list():
    """
List Relying Parties and Legal Entities
---
tags:
  - Legal Entity
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: "abc123hashpid"

responses:
  200:
    description: Relying Parties and Legal Entities retrieved successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        code:
          type: integer
          example: 200
        message:
          type: string
          example: Relying Parties and Legal Entities retrieved successfully.
        data:
          type: object
          properties:
            relying_parties:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 7
                  name:
                    type: string
                    example: "ACME RP Services"
                  associated:
                    type: boolean
                    example: true
                  associated_rp:
                    type: object
                    nullable: true
                    properties:
                      id:
                        type: integer
                        example: 3
                      name:
                        type: string
                        example: "Main Relying Party"

            legal_entities:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 2
                  country:
                    type: string
                    example: "PT"
                  email:
                    type: string
                    example: "contact@acme.com"
                  identifier:
                    type: string
                    example: "123456789"
                  info_uri:
                    type: string
                    example: "https://acme.com/info"
                  phone:
                    type: string
                    example: "+351900000000"
                  postal_address:
                    type: string
                    example: "Rua Central 123, Porto, Portugal"

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example:
                - hash_pid
"""
    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    required_fields = {
        "hash_pid": hash_pid
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    menu, data, header_table, list = list_legalEntity(user_id)
    
    legal_entities = []
    for rp_id, rp in data.items():
        legal_entities.append({
            "id": int(rp_id),
            "country": rp["Country"],
            "email": rp["E-mail"],
            "identifier": rp["Identifier"],
            "info_uri": rp["Information URI"],
            "phone": rp["Phone"],
            "postal_address": rp["Postal Address"]
        })

    relying_parties = []
    for le in list:
        relying_parties.append({
            "id": le["id"],
            "name": le["name"],
            "associated": le["associated_id"] is not None,
            "associated_rp": (
                {
                    "id": le["associated_id"],
                    "name": le["ass_name"][0] if le["ass_name"] else None
                }
                if le["associated_id"] else None
            )
        })

    return {
        "status": "success",
        "code": 200,
        "message": "Relying Parties and Legal Entities retrieved successfully.",
        "data": {
            "relying_parties": relying_parties,
            "legal_entities": legal_entities
        }
    }, 200

@rpr.route('/RP/add_RP_db', methods=['POST'])
def add_RP_db():
    """
Create a new Relying Party (RP)
---
tags:
  - Relying Party
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
        - trade_name
        - support_URI
        - srvDescription_lang
        - srvDescription
        - entitlement
        - registry_uri
        - type_of_policy
        - policy_uri
        - x5c
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: "abc123hashpid"
        trade_name:
          type: string
          description: Trade name of the Relying Party
          example: "ACME RP Services"
        support_URI:
          type: string
          description: URI for support or help
          example: "https://acme.com/support"
        srvDescription_lang:
          type: string
          description: Language of the service description
          example: "EU"
        srvDescription:
          type: string
          description: Service description of the RP
          example: "Provides authentication services for ACME users."
        entitlement:
          type: string
          description: Entitlement or permissions required
          example: "http://data.europa.eu/eudi/entitlement/Service_Provider"
        registry_uri:
          type: string
          description: Registry URI for the RP
          example: "https://registry.acme.com"
        type_of_policy:
          type: string
          description: Type of policy applicable
          example: "http://data.europa.eu/eudi/policy/trust-service-practice-statement"
        policy_uri:
          type: string
          description: URI to the policy document
          example: "https://acme.com/policy"
        x5c:
          type: string
          description: Certificate chain (x5c) for the RP
          example: "MIID...AB"
responses:
  201:
    description: Relying Party successfully created
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        code:
          type: integer
          example: 201
        message:
          type: string
          example: Relying Party successfully created.
        data:
          type: object
          properties:
            relying_party_id:
              type: integer
              example: 27

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example:
                - trade_name
                - x5c
"""
    
    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")
    trade_name = data.get("trade_name")
    support_URI = data.get("support_URI")
    srvDescription_lang = data.get("srvDescription_lang")
    srvDescription = data.get("srvDescription")
    entitlement = data.get("entitlement")
    registry_uri = data.get("registry_uri")
    type_of_policy = data.get("type_of_policy")
    policy_uri = data.get("policy_uri")
    x5c = data.get("x5c")

    required_fields = {
        "hash_pid": hash_pid,
        "trade_name": trade_name,
        "support_URI": support_URI,
        "srvDescription_lang": srvDescription_lang,
        "srvDescription": srvDescription,
        "entitlement": entitlement,
        "registry_uri": registry_uri,
        "type_of_policy": type_of_policy,
        "policy_uri": policy_uri,
        "x5c": x5c
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400
    
    if entitlement not in cfgserv.relying_party["Entitlement"]:
        return {
            "status": "error",
            "code": 400,
            "message": f"Invalid entitlement. Must be one of: {', '.join(cfgserv.relying_party['Entitlement'])}",
            "provided": entitlement
        }, 400
    
    if type_of_policy not in cfgserv.relying_party["Type of Policy"]:
        return {
            "status": "error",
            "code": 400,
            "message": f"Invalid Type of Policy. Must be one of: {', '.join(cfgserv.relying_party['Type of Policy'])}",
            "provided": type_of_policy
        }, 400
    
    if srvDescription_lang not in cfgserv.eu_countries:
        return {
            "status": "error",
            "code": 400,
            "message": f"Invalid srvDescription_lang. Must be one of: {', '.join(cfgserv.eu_countries)}",
            "provided": srvDescription_lang
        }, 400
    
    user_id = db.check_user(hash_pid)
    
    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400

    srvDescription = '[{"lang":"' + srvDescription_lang + '", "srvDescription":"' + srvDescription + '"}]'

    id = db.insert_RP(trade_name, support_URI, srvDescription, entitlement, registry_uri, type_of_policy, policy_uri, x5c, user_id)

    return {
        "status": "success",
        "code": 201,
        "message": "Relying Party successfully created.",
        "data": {
            "Relying Party id": id
        }
    }, 201

@rpr.route("/RP/certificate", methods=["GET"])
def relying_party_access_certificate():
    """
Retrieve Relying Party Certificate
---
tags:
  - Relying Party
consumes:
  - application/json
produces:
  - application/octet-stream
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
        - relying_party
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: abc123hashpid

        relying_party:
          type: integer
          description: ID of the Relying Party whose certificate will be retrieved
          example: 2

        password:
            type: string
            format: password
            description: Password required
            example: example-password

responses:
  200:
    description: Certificate file successfully retrieved
    schema:
      type: string
      format: binary

  400_missing_fields:
    description: Missing required fields
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example:
                - relying_party

  400_invalid_hash_pid:
    description: Invalid hash_pid
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Invalid hash_pid
        data:
          type: object
          properties:
            hash_pid:
              type: string
              example: abc123hashpid

  400_rp_not_exist:
    description: Relying Party does not exist
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Relying Parties do not Exist
        data:
          type: object
          properties:
            relying_party:
              type: integer
              example: 2

  400_rp_not_user:
    description: Relying Party does not belong to the authenticated user
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Relying Parties do not belong to this User.
        data:
          type: object
          properties:
            relying_party:
              type: integer
              example: 2
"""
    
    data = request.get_json(silent=True)

    if not data:
        return {
                "status": "error",
                "code": 400,
                "message": "Invalid or missing JSON body"
            }, 400

    hash_pid = data.get("hash_pid")
    relying_party = data.get("relying_party")
    password = data.get("password")

    required_fields = {
        "hash_pid": hash_pid,
        "relying_party": relying_party,
        "password": password
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400
    
    user_id = db.check_user(hash_pid)
    
    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    RP=db.get_rp_certificate(relying_party)

    if RP is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Relying Parties do not Exist",
            "data": {
                "relying_party": relying_party
            }
        }, 400
    
    if RP[0]["user_id"] is not user_id:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Relying Parties do not belong to this User.",
            "data": {
                "relying_party": relying_party
            }
        }, 400

    modulus=crypto.key_size
    exponent=crypto.exponent
    priv_key = ec.generate_private_key(ec.SECP256R1(), default_backend() )

    #dados da RP
    TypeIdentifier={
        "http://data.europa.eu/eudi/id/EORI-No":"EOR",
        "http://data.europa.eu/eudi/id/LEI":"LEI" ,
        "http://data.europa.eu/eudi/id/EUID":"NTR" ,
        "http://data.europa.eu/eudi/id/VATIN":"VAT"  ,
        "http://data.europa.eu/eudi/id/TIN":"TIN",
        "http://data.europa.eu/eudi/id/Excise":"EXC"
    }
    #commonName
    tradeName=RP[0]["tradeName"]
    #uniformResourceIdentifier
    supportURI=RP[0]["supportURI"]
    legal_entity = db.get_legal_entity(RP[0]["supervisorAuthority"])

    if legal_entity is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Relying Parties do not have associated Legal Entity."
        }, 400

    #dados da legalEntity
    #caso for natural person é serialNumber no caso de uma legal person organizationIdentifier
    identifier=legal_entity[0]["identifier"]
    country= legal_entity[0]["country"]
    email= legal_entity[0]["email"]
    phone= legal_entity[0]["phone"]

    
    if legal_entity[0]["legalperson_id"] is None:
        natural_person = db.get_natural_person(legal_entity[0]["naturalperson_id"])
        #se user for natural person
        givenName=natural_person[0]["givenName"]
        #surname
        surname=natural_person[0]["familyName"]
        serial_number=TypeIdentifier[legal_entity[0]["identifierType"]] + identifier
        
    else:
        legal_person = db.get_legal_person(legal_entity[0]["legalperson_id"])
        #se user for legal person
        #dados da legal person
        #organizationName
        legalName=legal_person[0]["legalName"]
        organizationIdentifier= TypeIdentifier[legal_entity[0]["identifierType"]] + identifier

    #como as TSLs, ex: lang en, description=test  
    servicesDescription=RP[0]["srvDescription"]#como as TSLs, ex: lang en, description=test  
    entitlement=RP[0]["entitlement"]
    # verificar legal entity se é pertence ao sector público, se sim True, se não False
    isPSB= False
#### ------
    # password=request.form.get("Password")

    certificateRequest= generateCertificateRequest(priv_key, tradeName, country, supportURI)

    certificateRequestString = "-----BEGIN CERTIFICATE REQUEST-----\n"+ base64.b64encode(certificateRequest).decode("utf-8") + "\n"+ "-----END CERTIFICATE REQUEST-----"
    certificateAuthorityName = getCertificateAuthorityName(country)
    certificateRequestBody = getJsonBody(certificateRequestString, certificateAuthorityName, country)
    postUrl = "https://" + ejbca.cahost + "/ejbca/ejbca-rest-api/v1" + ejbca.endpoint

    headers ={
        "Content-Type": "application/json",
        'Authorization': 'Bearer test',
    }

    clientP12ArchiveFilepath = ejbca.clientP12ArchiveFilepath
    clientP12ArchivePassword = ejbca.clientP12ArchivePassword
    ManagementCA = ejbca.managementCA

    trustCA= getTrustManagerOfCACertificate(ManagementCA)

    response = http_post_requests_with_custom_ssl_context(ManagementCA, clientP12ArchiveFilepath, clientP12ArchivePassword, postUrl,certificateRequestBody, headers)

    response = response.json()
    
    certificate_bytes=base64.b64decode(response["certificate"])

    certificate = x509.load_der_x509_certificate(certificate_bytes, default_backend())

    serial_number=response["serial_number"]

    p12=pkcs12.serialize_key_and_certificates(
        name=tradeName.encode("utf-8"),key=priv_key,cert=certificate, cas=list().append(trustCA),
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode("utf-8"))
    )

    tag = uuid.uuid4()

    file_name = tradeName + "_" + str(tag)

    p12_temp.update({file_name:{"response": p12, "expires":datetime.now() + timedelta(minutes=cfgserv.deffered_expiry)}})

    cert = certificate.subject.rfc4514_string().split(",")
    dic = {parte.split("=")[0]: parte for parte in cert}
    order = [dic.get("C"),
            #dic.get("O"),
            dic.get("CN")]
    aux = [v for k, v in dic.items() if k not in ["C", "O", "CN"]]

    cert_subject_rfc4514_string = ",".join(order + aux)

    certificate_presentation={
        "certificate_issuer":certificate.issuer.rfc4514_string(),
        "certificate_distinguished_name":cert_subject_rfc4514_string,
        "validity_from":certificate.not_valid_before_utc,
        "validity_to":certificate.not_valid_after_utc,
    }

    file_base64 = base64.b64encode(p12).decode()

    return jsonify({
        "status": "success",
        "code": 200,
        "data": {
            "filename": "document_with_signature.json",
            "file_base64": file_base64
        }
    })

def wallet_rp_list(user_id):

    RP_dict = db.get_rp_info(user_id)
    
    header_table=[ "Trade Name","Support URIs","Description","Entitlement","Provides Attestations","Supervisory Authority","Registry URI"]
    
    if(RP_dict == "err" or RP_dict == None):
        data={}
    else:
        data={}

        for RP in RP_dict:
            data_temp={
                RP["wrp_id"]:{
                    "Trade Name":RP["tradeName"],
                    "Support URIs":RP["supportURI"],
                    "Description":RP["srvDescription"],
                    "Entitlement":RP["entitlement"],
                    "Provides Attestations":RP["providesAttestations"],
                    "Supervisory Authority":RP["supervisorAuthority"],
                    "Registry URI":RP["registryURI"]
                }
            }
            data.update(data_temp)
    
    iu_dict = db.get_intended_use_info(user_id)

    list = []
    if(data != {}):
        if(iu_dict != "err" and iu_dict != None):

            for item in iu_dict:
                name_txt = item["intendedUseIdentifier"]
                
                if(item["wrp"] != None):
                    wrp_name = db.get_iu_info_rp(item["wrp"])
                    
                    new_item = {
                        "id": item["intendeduse_id"],
                        "name": name_txt,
                        "associated_id": item["wrp"],
                        "ass_name": wrp_name
                    }
                else:
                    new_item = {
                        "id": item["intendeduse_id"],
                        "name": name_txt,
                        "associated_id": item["wrp"],
                        "ass_name": ""
                    }
                
                list.append(new_item)
    
    
    menu= cfgserv.service_url + "menu"
    
    return menu, data, header_table, list

@rpr.route('/RP/list', methods=['GET', 'POST'])
def RP_list():
    """
List Wallet Relying Parties and Intended Uses
---
tags:
  - Relying Party
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: "abc123hashpid"

responses:
  200:
    description: Wallet Relying Parties and Intended Uses retrieved successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        code:
          type: integer
          example: 200
        message:
          type: string
          example: Wallet Relying Party and Intended Use retrieved successfully.
        data:
          type: object
          properties:
            relying_parties:
              type: object
              additionalProperties:
                type: object
                properties:
                  entitlement:
                    type: string
                    example: "full_access"
                  description:
                    type: object
                    example:
                      EN: "Provides authentication services"
                  provides_attestations:
                    type: boolean
                    example: true
                  registry_URI:
                    type: string
                    example: "https://registry.example.com"
                  supervisory_authority:
                    type: string
                    example: "National Authority"
                  support_URIs:
                    type: array
                    items:
                      type: string
                    example:
                      - "https://example.com/support"
                  trade_name:
                    type: string
                    example: "ACME Wallet RP"

            intended_uses:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 12
                  name:
                    type: string
                    example: "Login Authentication"
                  associated:
                    type: boolean
                    example: true
                  wallet_relying_party:
                    type: object
                    nullable: true
                    properties:
                      id:
                        type: integer
                        example: 3
                      entitlement:
                        type: string
                        example: "full_access"
                      description:
                        type: object
                        example:
                          EN: "Authentication and identity verification"
                      provides_attestations:
                        type: boolean
                        example: true
                      registry_URI:
                        type: string
                        example: "https://registry.example.com"
                      supervisory_authority:
                        type: string
                        example: "National Authority"
                      support_URIs:
                        type: array
                        items:
                          type: string
                        example:
                          - "https://example.com/support"
                      trade_name:
                        type: string
                        example: "ACME Wallet RP"

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example:
                - hash_pid
"""

    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")

    required_fields = {
        "hash_pid": hash_pid
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400
    
    user_id = db.check_user(hash_pid)
    
    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    menu, data, header_table, list = wallet_rp_list(user_id)

    wrp = {}

    for lp_id, lp_data in data.items():
        wrp[int(lp_id)] = {
            "entitlement": lp_data["Entitlement"],
            "description": json.loads(lp_data["Description"]),
            "provides_attestations": lp_data["Provides Attestations"],
            "registry_URI": lp_data["Registry URI"],
            "supervisory_authority": lp_data["Supervisory Authority"],
            "support_URIs": lp_data["Support URIs"],
            "trade_name": lp_data["Trade Name"]
        }
    
    intended_use = []

    for entity in list:
        associated_id = entity["associated_id"]

        intended_use.append({
            "id": entity["id"],
            "name": entity["name"],
            "associated": associated_id is not None,
            "wallet_relying_party": (
                {
                    "id": associated_id,
                    **wrp.get(associated_id, {})
                }
                if associated_id in wrp else None
            )
        })

    return {
        "status": "success",
        "code": 200,
        "message": "Wallet Relying Party and Intended Use retrieved successfully.",
        "data": {
            "relying_parties": wrp,
            "intended_uses": intended_use
        }
    }, 200

@rpr.route('/RP/ui_update_intended_use', methods=["POST"])
def ui_update_intended_use():
    """
Update Relying Party associations with Intended Uses
---
tags:
  - Relying Party
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
        - relying_party
        - intended_uses
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: abc123hashpid

        relying_party:
          type: integer
          description: ID of the Relying Party to associate Intended Uses with
          example: 5

        intended_uses:
          type: array
          description: List of Intended Use IDs to associate with the Relying Party
          items:
            type: integer
          example: [2, 4, 7]

responses:
  200:
    description: Associations updated successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        message:
          type: string
          example: Associations updated successfully
        updated_count:
          type: integer
          example: 3

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example: [intended_uses]

  401:
    description: Invalid hash_pid
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Invalid hash_pid
        data:
          type: object
          properties:
            hash_pid:
              type: string
              example: abc123hashpid

  422:
    description: Some Intended Uses are invalid or do not belong to the user
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Some Intended Uses do not exist or do not belong to this user
        invalid_intended_uses:
          type: array
          items:
            type: integer
          example: [99, 120]
"""

    data = request.get_json(silent=True)

    if not data:
        return {
                "status": "error",
                "code": 400,
                "message": "Invalid or missing JSON body"
            }, 400

    hash_pid = data.get("hash_pid")
    relying_party = data.get("relying_party")
    intended_uses = data.get("intended_uses")

    required_fields = {
        "hash_pid": hash_pid,
        "relying_party": relying_party,
        "intended_uses": intended_uses
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    if not isinstance(intended_uses, list):
        return {
                "status": "error",
                "code": 400,
                "message": "Relying Party ids must be a list"
            }, 400
    
    user_id = db.check_user(hash_pid)
    
    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    all_relying_party = db.get_rp_info(user_id)
    valid_relying_party_ids = {str(p["wrp_id"]) for p in all_relying_party}

    if str(relying_party) not in valid_relying_party_ids:
        return {
                "status": "error",
                "code": 400,
                "message": "Relying Party does not exist or does not belong to this user"
            }, 400
    
    all_iu = db.get_intended_use_info(user_id)
    valid_ids = {int(e["intendeduse_id"]) for e in all_iu}

    invalid_ids = [
        le_id for le_id in intended_uses
        if int(le_id) not in valid_ids
    ]
        
    if invalid_ids:
        return {
            "status": "error",
            "code": 400,
            "message": "Some Intended Uses do not exist or do not belong to this user",
            "invalid_intended_uses": invalid_ids
        }, 400

    for elem_id in intended_uses:
        db.update_iu_wrp(relying_party, elem_id)

    return {
        "status": "success",
        "message": "Associations updated successfully",
        "updated_count": len(intended_uses)
    }, 200

@rpr.route('/RP/ui_remove_update_legal_entity', methods=["POST"])
def ui_remove_update_legal_entity():
    """
Remove Legal Entity associations from Relying Parties
---
tags:
  - Relying Party
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
        - relying_party
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: abc123hashpid

        relying_party:
          type: array
          description: List of Relying Party IDs to remove the Legal Entity association from
          items:
            type: integer
          example: [2, 5, 9]

responses:
  200:
    description: Associations removed successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        message:
          type: string
          example: Associations updated successfully
        updated_count:
          type: integer
          example: 3

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example: [relying_party]

  401:
    description: Invalid hash_pid
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Invalid hash_pid
        data:
          type: object
          properties:
            hash_pid:
              type: string
              example: abc123hashpid

  422:
    description: Some Relying Parties are invalid or do not belong to the user
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Some Relying Parties do not exist or do not belong to this user
        invalid_legal_entities:
          type: array
          items:
            type: integer
          example: [99, 120]
"""

    data = request.get_json(silent=True)

    if not data:
        return {
                "status": "error",
                "code": 400,
                "message": "Invalid or missing JSON body"
            }, 400

    hash_pid = data.get("hash_pid")
    relying_party = data.get("relying_party")

    required_fields = {
        "hash_pid": hash_pid,
        "relying_party": relying_party,
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    if not isinstance(relying_party, list):
        return {
                "status": "error",
                "code": 400,
                "message": "Relying Parties ids must be a list"
            }, 400
    
    user_id = db.check_user(hash_pid)
    
    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    all_relying_party = db.get_rp_info(user_id)
    valid_relying_party_ids = {p["wrp_id"] for p in all_relying_party}

    invalid_ids = [
        le_id for le_id in relying_party
        if int(le_id) not in valid_relying_party_ids
    ]
        
    if invalid_ids:
        return {
            "status": "error",
            "code": 400,
            "message": "Some Relying Parties do not exist or do not belong to this user",
            "invalid_legal_entities": invalid_ids
        }, 400

    for elem_id in relying_party:
        db.update_wrp_legal_entity(None, elem_id)

    return {
        "status": "success",
        "message": "Associations updated successfully",
        "updated_count": len(relying_party)
    }, 200

@rpr.route('/intended_use/add_intended_use_db', methods=['POST'])
def add_intended_use_db():
    """
Create a new Intended Use
---
tags:
  - Intended Use
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
        - purpose
        - purpose_lang
        - type_policy
        - policy_uri
        - createAt
        - revokeAt
        - intendedUseIdentifier
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: "abc123hashpid"
        purpose:
          type: string
          description: Purpose of the intended use
          example: "Data processing for analytics"
        purpose_lang:
          type: string
          description: Language of the purpose description
          example: "EU"
        type_policy:
          type: string
          description: Type of policy governing the intended use
          example: "http://data.europa.eu/eudi/policy/trust-service-practice-statement"
        policy_uri:
          type: string
          description: URI to the policy document
          example: "https://acme.com/privacy-policy"
        createAt:
          type: string
          format: date-time
          description: Timestamp when the intended use was created
          example: "2026-02-09 12:00:00"
        revokeAt:
          type: string
          format: date-time
          description: Timestamp when the intended use will be revoked
          example: "2026-12-31 23:59:59"
        intendedUseIdentifier:
          type: string
          description: Unique identifier for the intended use
          example: "intended_use_001"
responses:
  201:
    description: Intended Use successfully created
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        code:
          type: integer
          example: 201
        message:
          type: string
          example: Intended Use successfully created.
        data:
          type: object
          properties:
            intended_use_id:
              type: integer
              example: 42

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example:
                - purpose
                - policy_uri
"""

    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")
    purpose = data.get("purpose")
    purpose_lang = data.get("purpose_lang")
    type_policy = data.get("type_policy")
    policy_uri = data.get("policy_uri")
    createAt = data.get("createAt")
    revokeAt = data.get("revokeAt")
    intendedUseIdentifier = data.get("intendedUseIdentifier")

    required_fields = {
        "hash_pid": hash_pid,
        "purpose": purpose,
        "purpose_lang": purpose_lang,
        "type_policy": type_policy,
        "policy_uri": policy_uri,
        "createAt": createAt,
        "revokeAt": revokeAt,
        "intendedUseIdentifier": intendedUseIdentifier
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400
    
    if purpose_lang not in cfgserv.eu_countries:
        return {
            "status": "error",
            "code": 400,
            "message": f"Invalid purpose_lang. Must be one of: {', '.join(cfgserv.eu_countries)}",
            "provided": purpose_lang
        }, 400
    
    if type_policy not in cfgserv.intended_use["Type of Privacy Policy"]:
        return {
            "status": "error",
            "code": 400,
            "message": f"Invalid type_policy. Must be one of: {', '.join(cfgserv.intended_use['Type of Privacy Policy'])}",
            "provided": type_policy
        }, 400

    user_id = db.check_user(hash_pid)

    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    purpose = '[{"lang":"' + purpose_lang + '", "srvDescription":"' + purpose + '"}]'
    
    id = db.insert_intended_use(createAt, revokeAt, intendedUseIdentifier, type_policy, policy_uri, purpose, user_id)

    if id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Something went wrong"
        }, 400

    return {
        "status": "success",
        "code": 201,
        "message": "Intended Use successfully created.",
        "data": {
            "Intended Use id": id
        }
    }, 201
   
@rpr.route("/intended_use/certificate", methods=["GET"])
def intended_use_registration_certificate():
    """
Retrieve Intended Use Certificate
---
tags:
  - Intended Use
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
        - intended_use
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: abc123hashpid

        intended_use:
          type: integer
          description: ID of the Intended Use whose certificate will be retrieved
          example: 3

responses:
  200:
    description: Intended Use certificate retrieved successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        code:
          type: integer
          example: 200
        data:
          type: object
          properties:
            filename:
              type: string
              example: document_with_signature.json
            file_base64:
              type: string
              description: Base64 encoded file containing the generated document
              example: ewoJImRhdGEiOiAiZXhhbX...
            cose_base64:
              type: string
              description: Base64 encoded COSE signature of the document
              example: eyJhbGciOiAiRVMyNTYifQ...

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example:
                - intended_use

  400_invalid_hash_pid:
    description: Invalid hash_pid
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Invalid hash_pid
        data:
          type: object
          properties:
            hash_pid:
              type: string
              example: abc123hashpid

  400_invalid_intended_use:
    description: Intended Use does not exist
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Intended Use do not Exist
        data:
          type: object
          properties:
            intended_use:
              type: integer
              example: 3

  400_not_user:
    description: Intended Use does not belong to the authenticated user
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Intended Use do not belong to this User.
        data:
          type: object
          properties:
            intended_use:
              type: integer
              example: 3
"""

    data = request.get_json(silent=True)

    if not data:
        return {
                "status": "error",
                "code": 400,
                "message": "Invalid or missing JSON body"
            }, 400

    hash_pid = data.get("hash_pid")
    intended_use = data.get("intended_use")

    required_fields = {
        "hash_pid": hash_pid,
        "intended_use": intended_use,
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400
    
    user_id = db.check_user(hash_pid)
    
    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    intended_use_data=db.get_intended_use(intended_use)

    if intended_use_data is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Intended Use do not Exist",
            "data": {
                "intended_use": intended_use
            }
        }, 400
    
    if intended_use_data[0]["user_id"] is not user_id:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Intended Use do not belong to this User.",
            "data": {
                "intended_use": intended_use
            }
        }, 400

    RP_data = db.get_rp_certificate(intended_use_data[0]["wrp"])
    if RP_data is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Intended Use do not have associated Relying Party."
        }, 400

    legal_entity_data = db.get_legal_entity(RP_data[0]["supervisorAuthority"])
    if legal_entity_data is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Relying Parties do not have associated Legal Entity."
        }, 400

    credentials_data = db.get_credential(intended_use_data[0]["intendeduse_id"])
    if credentials_data is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Intended Use do not have associated Credential."
        }, 400


# #if legal person
# legal_person_data=get_legal_person_data()

# #if natural person
# natural_person_data= get_natural_person_data()

# #if legal_person
# legal_name=legal_person_data["legal_name"]

# #if natural_person
# given_name=natural_person_data["given_name"]
# family_name=natural_person_data["family_name"]


    if legal_entity_data[0]["legalperson_id"] is None:
        natural_person = db.get_natural_person(legal_entity_data[0]["naturalperson_id"])
        #se user for natural person
        legalName=natural_person[0]["givenName"]
        #surname
        surname=natural_person[0]["familyName"]
        certificate_policy = "itu-t(0) identified-organization(4) etsi(0) eudiwrp(194118) policy-identifiers(1) ncp-natural (1)"

        
    else:
        legal_person = db.get_legal_person(legal_entity_data[0]["legalperson_id"])
        #se user for legal person
        #dados da legal person
        #organizationName
        legalName=legal_person[0]["legalName"]
        certificate_policy = "itu-t(0) identified-organization(4) etsi(0) eudiwrp(194118) policy-identifiers(1) ncp-legal (2)"

    iat= int(time.time())

# name=RP_data["tradeName"]
# purpose=intended_use_data["purpose"]
# info_uri=legal_entity_data["info_uri"]
# country=legal_entity_data["country"]

    name=RP_data[0]["tradeName"]
    purpose=intended_use_data[0]["purpose"]
    info_uri=legal_entity_data[0]["infoURI"]
    country=legal_entity_data[0]["country"]

# id=legal_entity_data["identifier"]
# privacy_policy=intended_use_data["privacyPolicy"]

    id=legal_entity_data[0]["identifier"]
    privacy_policy=intended_use_data[0]["type_policy"]

# # definir de acordo com os dados do certificado
# # policy_id=certificate_policy_id
# # certificate_policy=certificate_URI

# entitlement=RP_data["entitlement"]
# providesAttestations=RP_data["providesAttestations"]
# public_body=RP_data["isPSB"]
# service=RP_data["srvDescription"]

    entitlement=RP_data[0]["entitlement"]
    providesAttestations=RP_data[0]["providesAttestations"]
    public_body=RP_data[0]["isPSB"]
    service=RP_data[0]["srvDescription"]

# #A URI to a status list presenting information about validity of the WRPRC. 
# #status=

# #se utiliza intermediário
# #act            

    TypeIdentifier={
        "http://data.europa.eu/eudi/id/EORI-No":"EOR",
        "http://data.europa.eu/eudi/id/LEI":"LEI" ,
        "http://data.europa.eu/eudi/id/EUID":"NTR" ,
        "http://data.europa.eu/eudi/id/VATIN":"VAT"  ,
        "http://data.europa.eu/eudi/id/TIN":"TIN",
        "http://data.europa.eu/eudi/id/Excise":"EXC"
    }

    sub_id = TypeIdentifier[legal_entity_data[0]["identifierType"]] + '-' + id

    json_header = { "typ": "rc-wrp+jwt",
                "alg": "ES256", 
                "b64": "true", 
                "cty": ["b64"], "x5c": [],}

    headers={
        "accept": "application/json",
        "X-API-Key": "test" ,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data={
        "country":"FC",
        "doctype":"wrprc",
        "expiry_date":"2030-11-11"
    }

    response = requests.post(cfgserv.url_statuslist, headers=headers, data=data)

    status=response.json()

    status_idx=status["status_list"]["idx"]
    status_uri=status["status_list"]["uri"]

    if RP_data[0]["usesIntermediary"] != None:
        rp_intermediary = db.get_rp_certificate(RP_data[0]["usesIntermediary"])
        legalentity_intermediary = db.get_legal_entity_info_edit(rp_intermediary[0]["supervisorAuthority"])
        aux = TypeIdentifier[legalentity_intermediary[0]['identifierType']] + '-' + legalentity_intermediary[0]['identifier']
        json_payload = { 
                        "name": name,
                        "purpose": purpose, 
                        "info_uri": info_uri,
                        "country": country,
                        "sub": { 
                                "legal_name": legalName,
                                "id": sub_id
                        },
                        "privacy_policy": privacy_policy, 
                        "policy_id": [ "{ itu-t(0) identified-organization(4) etsi(0) eudiwrpa(19475) policy-identifiers(3) wrprc (1)}" ], 
                        "certificate_policy": certificate_policy, 
                        "iat": iat, 
                        "credentials": credentials_data,
                        "entitlements": entitlement,
                        "provided_attestations": [ { 
                                                    "format": credentials_data[0]["format"], "meta": { "vct_values": [ credentials_data[0]["meta"] ] } 
                        } ],
                        "public_body": False,
                        "service": service,
                        "status": { 
                            "status_list": { 
                                            "idx": status_idx, "uri": status_uri
                            } 
                        }, 
                        "act": { 
                            "sub":{ 
                                "id": aux
                            } 
                        }
        }
    else: 
        json_payload = { 
                        "name": name,
                        "purpose": purpose, 
                        "info_uri": info_uri,
                        "country": country,
                        "sub": { 
                                "legal_name": legalName,
                                "id": sub_id
                        },
                        "privacy_policy": privacy_policy, 
                        "policy_id": [ "{ itu-t(0) identified-organization(4) etsi(0) eudiwrpa(19475) policy-identifiers(3) wrprc (1)}" ], 
                        "certificate_policy": certificate_policy, 
                        "iat": iat, 
                        "credentials": credentials_data,
                        "entitlements": entitlement,
                        "provided_attestations": [ { 
                                                    "format": credentials_data[0]["format"], "meta": { "vct_values": [ credentials_data[0]["meta"] ] } 
                        } ],
                        "public_body": False,
                        "service": service,
                        "status": { 
                            "status_list": { 
                                            "idx": status_idx, "uri": status_uri
                            } 
                        }
        }
    
    with open(cfgserv.wrprc_certificate, "rb") as f:
        cert = x509.load_der_x509_certificate(f.read(), default_backend())

    base64_cert = base64.b64encode(cert.public_bytes(serialization.Encoding.PEM)).decode("utf-8")
    
    #Jades with b-b profile

    # base64_header=base64.b64encode(json.dumps(json_header).encode()).decode("utf-8")

    # with open("naoAssinado.json", "w", encoding="utf-8") as f:
    #     json.dump(
    #         json_payload,
    #         f,
    # )

    file_bytes = json.dumps(json_payload).encode()
    
    # digest = hashes.Hash(hashes.SHA256())
    # digest.update(file_bytes)
    # hash_value = digest.finalize()

    base64_payload=base64.b64encode(file_bytes).decode("utf-8")

    #print(document)
    payload=json.dumps({

            "documents":[{

                "document": base64_payload,
                "signature_format": "J",
                "conformance_level":"Ades-B-B",
                "signed_envelope_property": "ENVELOPING",
                "container": "No"

            } ],
        "endEntityCertificate": base64_cert,
        "certificateChain": [
        ],
        "hashAlgorithmOID": "2.16.840.1.101.3.4.2.1"

    })

    headers={
        'Content-Type': 'application/json'
    }

    calculate_hash=requests.post(url=cfgserv.sca_signer_url+"/signatures/calculate_hash",headers=headers, data=payload)

    #print(calculate_hash.json())
    #print(calculate_hash.json()["hashes"])

    hashes1 = calculate_hash.json()["hashes"]

    #print(hashes1[0])

    base64_string = urllib.parse.unquote(hashes1[0])

    data_to_be_signed = base64.b64decode(base64_string)

    #print(data_to_be_signed)

    #print(data_to_be_signed)
    # hash = base64.urlsafe_b64decode(hashes[0]).
    # base64.b64decode

    signature_date = calculate_hash.json()["signature_date"]

    with open(cfgserv.wrprc_privateKey, "rb") as f:
        private_key = serialization.load_pem_private_key(
        f.read(),
        password=None,
        backend=default_backend()
    )

    # key=ECC.import_key(private_key)

    # signature = DSS.new(key).sign(data_to_be_signed)
    signature = private_key.sign(
        data_to_be_signed,
        ec.ECDSA(utils.Prehashed(hashes.SHA256()))
    )

    base64_signature= base64.b64encode(signature).decode()
    #print(base64_signature)

    payload = json.dumps({
        "documents": [
            {
                "document": base64_payload,
                "signature_format": "J",
                "conformance_level":"Ades-B-B",
                "signed_envelope_property": "ENVELOPING",
                "container": "No"
            }
        ],
        "hashAlgorithmOID": "2.16.840.1.101.3.4.2.1",
        "returnValidationInfo": False,
        "endEntityCertificate": base64_cert,
        "certificateChain": [
        ],
        "signatures":[base64_signature],
        "date": signature_date
    }).encode()

    obtain_signed_document=requests.post(url=cfgserv.sca_signer_url+"/signatures/obtain_signed_doc",headers=headers, data=payload)
    
    document_with_signature=obtain_signed_document.json()["documentWithSignature"][0]

    # data=json.loads(base64.b64decode(document_with_signature).decode("utf-8"))

    # jwt_payload=data["payload"]
    # jwt_header=data["signatures"][0]["protected"]
    # jwt_signature=data["signatures"][0]["signature"]

    # jwt = jwt_header + "." + jwt_payload + "." + jwt_signature
    #cbor

    cbor_data= cbor2.dumps(json_payload)

    msg = Sign1Message(phdr={Algorithm: Es256},uhdr={KID: b"key1"},payload=cbor_data)

    with open(cfgserv.wrprc_privateKey, "rb") as f:
        pem_bytes = f.read()

    cose_key = CoseKey.from_pem_private_key(pem_bytes.decode())
    msg.key = cose_key
    cose_bytes = msg.encode()

    file_data = base64.b64decode(document_with_signature)

    file_base64 = base64.b64encode(file_data).decode()
    cose_base64 = base64.urlsafe_b64encode(cose_bytes).decode()

    return jsonify({
        "status": "success",
        "code": 200,
        "data": {
            "filename": "document_with_signature.json",
            "file_base64": file_base64,
            "cose_base64": cose_base64
        }
    })

    return send_file(
        io.BytesIO(file_data),
        download_name="document_with_signature.json",
        as_attachment=True,
        mimetype='application/json'
    )

    cose_base64 = base64.urlsafe_b64encode(cose_bytes).decode()
    return cose_base64
    
def list_intended_use(user_id):

    intended_use_dict = db.get_intended_use_info(user_id)
    
    header_table=[ "Identifier","Purpose","Created At","Revoked At","Type of Policy", "Policy URI"]

    if(intended_use_dict == "err" or intended_use_dict == None):
        data={}
    else:
        data={}
        for intended_use in intended_use_dict:
            data_temp={
                intended_use["intendeduse_id"]:{
                    "Identifier":intended_use["intendedUseIdentifier"],
                    "Purpose":intended_use["purpose"],
                    "Created At":intended_use["createdAt"],
                    "Revoked At":intended_use["revokedAt"],
                    "Type of Policy":intended_use["type_policy"],
                    "Policy URI":intended_use["policy_uri"]
                }
            }
            data.update(data_temp)

        cred_dict = db.get_credential_info(user_id)
        
        list = []
        if(data != {}):
            if(cred_dict != "err" and cred_dict != None):

                for item in cred_dict:
                    name_txt = item["name"]
                    
                    if(item["intendedUse_id"] != None):
                        iu_name = db.get_iu_info_cred(item["intendedUse_id"])
                        
                        new_item = {
                            "id": item["credential_id"],
                            "name": name_txt,
                            "associated_id": item["intendedUse_id"],
                            "ass_name": iu_name
                        }
                    else:
                        new_item = {
                            "id": item["intendedUse_id"],
                            "name": name_txt,
                            "associated_id": item["intendedUse_id"],
                            "ass_name": ""
                        }
                    
                    list.append(new_item)

    menu= cfgserv.service_url + "menu"

    return menu, data, header_table, list

@rpr.route('/intended_use/list', methods=['GET','POST'])
def intended_use_list():
    """
List Intended Uses
---
tags:
  - Intended Use
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: "abc123hashpid"

responses:
  200:
    description: Intended Uses and Credential associations retrieved successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        code:
          type: integer
          example: 200
        message:
          type: string
          example: Intended Use retrieved successfully.
        data:
          type: object
          properties:

            credential:
              type: array
              description: List of credentials and their Intended Use associations
              items:
                type: object
                properties:
                  id:
                    type: integer
                    nullable: true
                    example: 4
                  name:
                    type: string
                    example: Employee ID
                  associated:
                    type: boolean
                    description: Indicates whether the credential is associated with an Intended Use
                    example: true
                  Intended_Use:
                    type: object
                    nullable: true
                    properties:
                      id:
                        type: integer
                        example: 12
                      created_at:
                        type: string
                        format: date-time
                        example: "2026-02-09T12:00:00Z"
                      identifier:
                        type: string
                        example: intended_use_001
                      policy_URI:
                        type: string
                        example: https://acme.com/privacy-policy
                      purpose:
                        type: array
                        items:
                          type: object
                          properties:
                            lang:
                              type: string
                              example: EN
                            srvDescription:
                              type: string
                              example: Data processing for analytics
                      revoked_at:
                        type: string
                        format: date-time
                        nullable: true
                        example: "2026-12-31T23:59:59Z"
                      type_of_policy:
                        type: string
                        example: http://data.europa.eu/eudi/policy/trust-service-practice-statement

            intended_use:
              type: object
              description: Dictionary of all Intended Uses indexed by ID
              additionalProperties:
                type: object
                properties:
                  created_at:
                    type: string
                    format: date-time
                    example: "2026-02-09T12:00:00Z"
                  identifier:
                    type: string
                    example: intended_use_001
                  policy_URI:
                    type: string
                    example: https://acme.com/privacy-policy
                  purpose:
                    type: array
                    items:
                      type: object
                      properties:
                        lang:
                          type: string
                          example: EN
                        srvDescription:
                          type: string
                          example: Data processing for analytics
                  revoked_at:
                    type: string
                    format: date-time
                    nullable: true
                    example: "2026-12-31T23:59:59Z"
                  type_of_policy:
                    type: string
                    example: Privacy Policy

    examples:
      application/json:
        status: success
        code: 200
        message: Intended Use retrieved successfully.
        data:
          credential:
            - id: 4
              name: Employee ID
              associated: true
              Intended_Use:
                id: 12
                created_at: "2026-02-09T12:00:00Z"
                identifier: intended_use_001
                policy_URI: https://acme.com/privacy-policy
                purpose:
                  - lang: EN
                    srvDescription: Data processing for analytics
                revoked_at: "2026-12-31T23:59:59Z"
                type_of_policy: http://data.europa.eu/eudi/policy/trust-service-practice-statement

            - id: 7
              name: Access Credential
              associated: false
              Intended_Use: null

          intended_use:
            "12":
              created_at: "2026-02-09T12:00:00Z"
              identifier: intended_use_001
              policy_URI: https://acme.com/privacy-policy
              purpose:
                - lang: EN
                  srvDescription: Data processing for analytics
              revoked_at: "2026-12-31T23:59:59Z"
              type_of_policy: Privacy Policy

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example:
                - hash_pid
"""

    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")
    
    required_fields = {
        "hash_pid": hash_pid
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400
    
    user_id = db.check_user(hash_pid)
    
    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
            
    menu, data, header_table, list = list_intended_use(user_id)

    intended_use = {}

    for lp_id, lp_data in data.items():
        intended_use[int(lp_id)] = {
            "created_at	": lp_data["Created At"],
            "identifier": lp_data["Identifier"],
            "policy_URI": lp_data["Policy URI"],
            "purpose": json.loads(lp_data["Purpose"]),
            "revoked_at": lp_data["Revoked At"],
            "type_of_policy": lp_data["Type of Policy"]
        }
        
    cred = []
    
    for entity in list:
        associated_id = entity["associated_id"]

        cred.append({
            "id": entity["id"],
            "name": entity["name"],
            "associated": associated_id is not None,
            "Intended_Use": (
                {
                    "id": associated_id,
                    **intended_use.get(associated_id, {})
                }
                if associated_id in intended_use else None
            )
        })
        
    return {
        "status": "success",
        "code": 200,
        "message": "Intended Use retrieved successfully.",
        "data": {
            "intended_use": intended_use,
            "credential": cred
        }
    }, 200

@rpr.route('/intended_use/ui_remove_update_relying_party', methods=["POST"])
def ui_remove_update_relying_party():
    """
Remove Relying Party associations from Intended Uses
---
tags:
  - Intended Use
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
        - intended_use
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: abc123hashpid

        intended_use:
          type: array
          description: List of Intended Use IDs to remove the Relying Party association from
          items:
            type: integer
          example: [2, 5, 9]

responses:
  200:
    description: Associations removed successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        message:
          type: string
          example: Associations updated successfully
        updated_count:
          type: integer
          example: 3

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example: [intended_use]

  401:
    description: Invalid hash_pid
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Invalid hash_pid
        data:
          type: object
          properties:
            hash_pid:
              type: string
              example: abc123hashpid

  422:
    description: Some Intended Uses are invalid or do not belong to the user
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Some Intended Use do not exist or do not belong to this user
        invalid_legal_entities:
          type: array
          items:
            type: integer
          example: [99, 120]
"""

    data = request.get_json(silent=True)

    if not data:
        return {
                "status": "error",
                "code": 400,
                "message": "Invalid or missing JSON body"
            }, 400

    hash_pid = data.get("hash_pid")
    intended_use = data.get("intended_use")

    required_fields = {
        "hash_pid": hash_pid,
        "intended_use": intended_use,
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    if not isinstance(intended_use, list):
        return {
                "status": "error",
                "code": 400,
                "message": "Intended Use ids must be a list"
            }, 400
    
    user_id = db.check_user(hash_pid)
    
    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    all_intended_use = db.get_intended_use_info(user_id)
    valid_intended_use_ids = {p["intendeduse_id"] for p in all_intended_use}

    invalid_ids = [
        le_id for le_id in intended_use
        if int(le_id) not in valid_intended_use_ids
    ]
        
    if invalid_ids:
        return {
            "status": "error",
            "code": 400,
            "message": "Some Intended Use do not exist or do not belong to this user",
            "invalid_legal_entities": invalid_ids
        }, 400

    for elem_id in intended_use:
        db.update_iu_wrp(None, elem_id)

    return {
        "status": "success",
        "message": "Associations updated successfully",
        "updated_count": len(intended_use)
    }, 200

@rpr.route('/credential/ui_remove_update_credential', methods=["POST"])
def ui_remove_update_credential():
    """
Remove Credential associations from Intended Uses
---
tags:
  - Credential
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
        - credentials
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: abc123hashpid

        credentials:
          type: array
          description: List of Credential IDs to remove their Intended Use associations
          items:
            type: integer
          example: [4, 5, 6, 7]

responses:
  200:
    description: Associations removed successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        code:
          type: integer
          example: 200
        message:
          type: string
          example: Associations removed successfully
        updated_count:
          type: integer
          description: Number of Credentials updated
          example: 4

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example: [credentials]

  401:
    description: Invalid hash_pid
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 401
        message:
          type: string
          example: Invalid hash_pid
        data:
          type: object
          properties:
            hash_pid:
              type: string
              example: abc123hashpid

  422:
    description: Some Credentials are invalid or do not belong to the user
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 422
        message:
          type: string
          example: Some Credentials do not exist or do not belong to this user
        invalid_credentials:
          type: array
          items:
            type: integer
          example: [99, 120]
"""

    data = request.get_json(silent=True)

    if not data:
        return {
                "status": "error",
                "code": 400,
                "message": "Invalid or missing JSON body"
            }, 400

    hash_pid = data.get("hash_pid")
    credentials = data.get("credentials")

    required_fields = {
        "hash_pid": hash_pid,
        "credentials": credentials,
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    if not isinstance(credentials, list):
        return {
                "status": "error",
                "code": 400,
                "message": "Credentials ids must be a list"
            }, 400
    
    user_id = db.check_user(hash_pid)
    
    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    all_cred = db.get_credential_info(user_id)
    valid_cred_ids = {p["credential_id"] for p in all_cred}

    invalid_ids = [
        le_id for le_id in credentials
        if int(le_id) not in valid_cred_ids
    ]
        
    if invalid_ids:
        return {
            "status": "error",
            "code": 400,
            "message": "Some Credentials do not exist or do not belong to this user",
            "invalid_legal_entities": invalid_ids
        }, 400

    for elem_id in credentials:
        db.update_iu_cred(None, elem_id)

    return {
        "status": "success",
        "message": "Associations updated successfully",
        "updated_count": len(credentials)
    }, 200

@rpr.route('/credential/add_credential_db', methods=['POST'])
def add_credential_db():
    """
Create a new Credential
---
tags:
  - Credential
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
        - name
        - format
        - meta
        - path
        - credentialValues
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: "abc123hashpid"
        name:
          type: string
          description: Name of the credential
          example: "Credential name"
        format:
          type: string
          description: Format type of the credential
          example: "JSON"
        meta:
          type: string
          description: Metadata associated with the credential
          example: "meta"
        path:
          type: string
          description: Path or location where the credential is stored
          example: "/credentials/cred.json"
        credentialValues:
          type: string
          description: Values contained within the credential
          example: "credentialValues"
responses:
  201:
    description: Credential successfully created
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        code:
          type: integer
          example: 201
        message:
          type: string
          example: Credential successfully created.
        data:
          type: object
          properties:
            credential_id:
              type: integer
              example: 101

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example:
                - name
                - credentialValues
"""

    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")
    name= data.get("name")
    format=data.get("format")
    meta=data.get("meta")
    path=data.get("path")
    credentialValues=data.get("credentialValues")

    required_fields = {
        "hash_pid": hash_pid,
        "name": name,
        "format": format,
        "meta": meta,
        "path": path,
        "credentialValues": credentialValues
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    id = db.insert_credential(name, format, meta, path, credentialValues, user_id)

    if id is None:
        return {
            "status": "error",
            "code": 400,
            "message": "Something went wrong"
        }, 400
    
    return {
        "status": "success",
        "code": 201,
        "message": "Credential successfully created.",
        "data": {
            "Credential id": id
        }
    }, 201


def cred_list(user_id):

    credential_dict = db.get_credential_info(user_id)
    
    header_table=[ "Name","Format", "Meta", "Path", "Credential Values"]

    if(credential_dict == "err" or credential_dict == None):
        data={}
    else:

        data={}

        for credential in credential_dict:
            data_temp={
                credential["credential_id"]:{
                    "Name":credential["name"],
                    "Format":credential["format"],
                    "Meta":credential["meta"],
                    "Path":credential["path"],
                    "Values":credential["credentialValues"],
                }
            }
            data.update(data_temp)
    
    menu= cfgserv.service_url + "menu"

    return menu, data, header_table

@rpr.route('/credential/list', methods=['GET','POST'])
def credential_list():
    """
List Credentials
---
tags:
  - Credential
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: "abc123hashpid"

responses:
  200:
    description: Credential and Intended Use retrieved successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        code:
          type: integer
          example: 200
        message:
          type: string
          example: Credential and Intended Use retrieved successfully.
        data:
          type: object
          properties:
            credential:
              type: object
              additionalProperties:
                type: object
                properties:
                  format:
                    type: string
                    example: "jwt_vc"
                  meta:
                    type: string
                    description: Metadata JSON stored as string
                    example: '{"issuer":"example"}'
                  name:
                    type: string
                    example: "UserCredential"
                  path:
                    type: string
                    example: "/credentials/user"
                  values:
                    type: string
                    example: '{"given_name":"John","family_name":"Doe"}'

            intended_uses:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 10
                  name:
                    type: string
                    example: "Login Intended Use"
                  associated:
                    type: boolean
                    example: true
                  Credential:
                    type: object
                    nullable: true
                    properties:
                      id:
                        type: integer
                        example: 3
                      format:
                        type: string
                        example: "jwt_vc"
                      meta:
                        type: string
                        example: '{"issuer":"example"}'
                      name:
                        type: string
                        example: "UserCredential"
                      path:
                        type: string
                        example: "/credentials/user"
                      values:
                        type: string
                        example: '{"given_name":"John","family_name":"Doe"}'

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example:
                - hash_pid
"""

    data = request.get_json(silent=True)
    
    if not data:
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid or missing JSON body"
        }, 400
    
    hash_pid = data.get("hash_pid")
    
    required_fields = {
        "hash_pid": hash_pid
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    menu, data, header_table = cred_list(user_id)

    credential = {}

    for lp_id, lp_data in data.items():
        credential[int(lp_id)] = {
            "format": lp_data["Format"],
            "neta": lp_data["Meta"],
            "name": lp_data["Name"],
            "path": lp_data["Path"],
            "values": lp_data["Values"]
        }

    return {
        "status": "success",
        "code": 200,
        "message": "Credential retrieved successfully.",
        "data": {
            "credential": credential
        }
    }, 200

@rpr.route('/intended_use/ui_update_intended_uses', methods=["POST"])
def ui_update_intended_uses():
    """
Update Intended Use associations with Credentials
---
tags:
  - Intended Use
consumes:
  - application/json
produces:
  - application/json
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - hash_pid
        - intended_use
        - credentials
      properties:
        hash_pid:
          type: string
          description: User identifier obtained from wallet login
          example: "abc123hashpid"

        intended_use:
          type: integer
          description: ID of the Intended Use to associate Credentials with
          example: 12

        credentials:
          type: array
          description: List of Credential IDs to associate with the Intended Use
          items:
            type: integer
          example:
            - 5
            - 6
            - 9

responses:
  200:
    description: Associations updated successfully
    schema:
      type: object
      properties:
        status:
          type: string
          example: success
        code:
          type: integer
          example: 200
        message:
          type: string
          example: Associations updated successfully
        updated_count:
          type: integer
          description: Number of Credentials successfully associated
          example: 3

  400:
    description: Invalid request or validation error
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Missing required fields.
        data:
          type: object
          properties:
            missing_fields:
              type: array
              items:
                type: string
              example:
                - credentials

  400_invalid_hash_pid:
    description: Invalid hash_pid
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Invalid hash_pid
        data:
          type: object
          properties:
            hash_pid:
              type: string
              example: abc123hashpid

  400_invalid_ids:
    description: Some Credentials are invalid or do not belong to the user
    schema:
      type: object
      properties:
        status:
          type: string
          example: error
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Some Credentials do not exist or do not belong to this user
        invalid_credentials:
          type: array
          items:
            type: integer
          example:
            - 99
            - 120
"""

    data = request.get_json(silent=True)

    if not data:
        return {
                "status": "error",
                "code": 400,
                "message": "Invalid or missing JSON body"
            }, 400

    hash_pid = data.get("hash_pid")
    credentials = data.get("credentials")
    intended_use = data.get("intended_use")

    required_fields = {
        "hash_pid": hash_pid,
        "credentials": credentials,
        "intended_use": intended_use
    }

    missing_fields = [name for name, value in required_fields.items() if not value]

    if missing_fields:
        return {
            "status": "error",
            "code": 400,
            "message": "Missing required fields.",
            "data": {
                "missing_fields": missing_fields
            }
        }, 400

    if not isinstance(credentials, list):
        return {
                "status": "error",
                "code": 400,
                "message": "Intended Use ids must be a list"
            }, 400
    
    user_id = db.check_user(hash_pid)

    if user_id is None:
        
        return {
            "status": "error",
            "code": 400,
            "message": "Invalid hash_pid",
            "data": {
                "hash_pid": hash_pid
            }
        }, 400
    
    all_intended_use = db.get_intended_use_info(user_id)
    valid_intended_use_ids = {str(p["intendeduse_id"]) for p in all_intended_use}

    if str(intended_use) not in valid_intended_use_ids:
        return {
                "status": "error",
                "code": 400,
                "message": "Intended Use does not exist or does not belong to this user"
            }, 400
    
    all_cred = db.get_credential_info(user_id)
    valid_ids = {int(e["credential_id"]) for e in all_cred}

    invalid_ids = [
        le_id for le_id in credentials
        if int(le_id) not in valid_ids
    ]
        
    if invalid_ids:
        return {
            "status": "error",
            "code": 400,
            "message": "Some Crendentials do not exist or do not belong to this user",
            "invalid_intended_uses": invalid_ids
        }, 400

    for elem_id in credentials:
        db.update_iu_cred(intended_use, elem_id)

    return {
        "status": "success",
        "message": "Associations updated successfully",
        "updated_count": len(credentials)
    }, 200

    
@rpr.route("/relying_party_registration_request", methods=["GET", "POST"])
def relying_party_registration():
    
    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]

    modulus=crypto.key_size
    exponent=crypto.exponent
    priv_key = ec.generate_private_key(ec.SECP256R1(), default_backend() )

    temp_user_id=request.form.get("temp_user_id")

    user=session[temp_user_id]
    givenName=user["given_name"]
    surname=user["family_name"]

    tradeName=request.form.get("Trade Name")
    supportURI=request.form.get("Support URI")
    #como as TSLs, ex: lang en, description=test  
    servicesDescription=request.form.get("Services Description")#como as TSLs, ex: lang en, description=test  
    entitlement=request.form.get("Entitlement")
    # verificar legal entity se é pertence ao sector público, se sim True, se não False
    isPSB= False
    password=request.form.get("Password")


    certificateRequest= generateCertificateRequest(priv_key, commonName, countryName, organizationName, registration_number, email,dns_Name)
    
    certificateRequestString = "-----BEGIN CERTIFICATE REQUEST-----\n"+ base64.b64encode(certificateRequest).decode("utf-8") + "\n"+ "-----END CERTIFICATE REQUEST-----"
    certificateAuthorityName = getCertificateAuthorityName(countryName)
    certificateRequestBody = getJsonBody(certificateRequestString, certificateAuthorityName, countryName)
    postUrl = "https://" + ejbca.cahost + "/ejbca/ejbca-rest-api/v1" + ejbca.endpoint

    headers ={
        "Content-Type": "application/json",
        'Authorization': 'Bearer test',
    }

    clientP12ArchiveFilepath = ejbca.clientP12ArchiveFilepath
    clientP12ArchivePassword = ejbca.clientP12ArchivePassword
    ManagementCA = ejbca.managementCA

    trustCA= getTrustManagerOfCACertificate(ManagementCA)

    response = http_post_requests_with_custom_ssl_context(ManagementCA, clientP12ArchiveFilepath, clientP12ArchivePassword, postUrl,certificateRequestBody, headers)

    response = response.json()
    
    certificate_bytes=base64.b64decode(response["certificate"])

    certificate = x509.load_der_x509_certificate(certificate_bytes, default_backend())

    serial_number=response["serial_number"]

    user_relying_party_db(user,request.form, serial_number, certificate,response["certificate"], session["session_id"])

    p12=pkcs12.serialize_key_and_certificates(
        name=commonName.encode("utf-8"),key=priv_key,cert=certificate, cas=list().append(trustCA),
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode("utf-8"))
    )

    tag = uuid.uuid4()

    file_name = commonName + "_" + str(tag)

    p12_temp.update({file_name:{"response": p12, "expires":datetime.now() + timedelta(minutes=cfgserv.deffered_expiry)}})

    cert = certificate.subject.rfc4514_string().split(",")
    dic = {parte.split("=")[0]: parte for parte in cert}
    order = [dic.get("C"), dic.get("O"), dic.get("CN")]
    aux = [v for k, v in dic.items() if k not in ["C", "O", "CN"]]

    cert_subject_rfc4514_string = ",".join(order + aux)

    certificate_presentation={
        "certificate_issuer":certificate.issuer.rfc4514_string(),
        "certificate_distinguished_name":cert_subject_rfc4514_string,
        "validity_from":certificate.not_valid_before_utc,
        "validity_to":certificate.not_valid_after_utc,
    }

    final_name = file_name.split("_")[0] + ".p12"
    return send_file(io.BytesIO(p12),download_name=final_name,as_attachment=True)

    return render_template('downloadPage.html', attributes=certificate_presentation, download_url= "/Download/"+ file_name)

@rpr.route("/Download/<name>", methods=["GET", "POST"])
def download(name):

    p12_file_bytes=p12_temp[name]["response"]

    final_name = name.split("_")[0] + ".p12"
    
    extra = {'code': session["session_id"]} 
    logger.info(f"Download p12.", extra=extra)

    return send_file(io.BytesIO(p12_file_bytes),download_name=final_name,as_attachment=True)

@rpr.route("/Revoke", methods=["GET", "POST"])
def Revoke_Certificate():

    certificate= request.args.get("id")

    user_id=request.args.get("user_id")

    log_id = request.args.get("log_id")

    certificate_data=certificate_data_List[user_id]["certificate_data"]

    cn_issuer=certificate_data[certificate]["certificate_issuer"]

    serial_number=certificate_data[certificate]["serial_number"]


    revocation_status_Url = "https://" + ejbca.cahost + "/ejbca/ejbca-rest-api/v1/certificate/"+ urllib.parse.quote(cn_issuer) +"/" + serial_number + "/revocationstatus"

    revocation_Url = "https://" + ejbca.cahost + "/ejbca/ejbca-rest-api/v1/certificate/"+ urllib.parse.quote(cn_issuer) +"/" + serial_number + "/revoke?reason=KEY_COMPROMISE"

    headers ={
        "Content-Type": "application/json",
        'Authorization': 'Bearer test',
    }

    clientP12ArchiveFilepath = ejbca.clientP12ArchiveFilepath
    clientP12ArchivePassword = ejbca.clientP12ArchivePassword

    session = requests.Session()
    session.mount('https://', Pkcs12Adapter(pkcs12_filename=clientP12ArchiveFilepath, pkcs12_password=clientP12ArchivePassword))

    response_status = session.get(revocation_status_Url, headers=headers, verify=False)

    response_s=response_status.json()

    if response_status.status_code !=200:
        #response_s["error_message"]

        return jsonify({"error": "Error Revoking"}),500

    if response_s["revoked"]==True:

        update_status(certificate_data[certificate]["accessCertificate_id"], log_id)

        data = {"message": "Sucess"}
        return jsonify({"message": data}),200

    else:

        response_revoke = session.put(revocation_Url, headers=headers, verify=False)

        response_r=response_revoke.json()
        
        if response_revoke.status_code !=200:
            return jsonify({"error":"Error Revoking"}),500
        
        if response_r["revoked"]==True:

            try:

                update_status(certificate_data[certificate]["accessCertificate_id"], log_id)
                data = {"message": "Sucess"}

                return jsonify({"message": data}),200
            
            except:
                extra = {'code':log_id} 
                logger.error(f"Error Revoking", extra=extra)
                return jsonify({"error": "Error Revoking"}),500
        else:
            extra = {'code':log_id} 
            logger.error(f"Error Revoking", extra=extra)
            return jsonify({"error": "Error Revoking"}),500

@rpr.route("/Logout", methods=["GET", "POST"])
def Logout():

    extra = {'code':session["session_id"]} 
    logger.info(f"Logout", extra=extra)
    session.clear()

    return render_template('initial_page.html', redirect_url= cfgserv.service_url, pid_auth = cfgserv.service_url + "authentication", certificateList=cfgserv.service_url + "authentication_List")

@rpr.route("/request_RP_data", methods=["GET"])
def request_RP_data():

    #ter dados em memória ou ficheiro para não fazer chamadas á BD. Atualizar de x em x tempo 

    registration_number= request.args.get("registration_number")
    name=request.args.get("name")
    privacy_policy_url=request.args.get("privacy_policy_url")
    entitlement=request.args.get("entitlement")
    intermediary_association=request.args.get("intermediary_association")
    acting_on_behalf_of=request.args.get("acting_on_behalf_of")
    limit=request.args.get("limit", default=20, type=int)

    # data = request.get_json(silent=True)

    # if not data:
    #     return {
    #             "status": "error",
    #             "code": 400,
    #             "message": "Invalid or missing JSON body"
    #         }, 400

    # registration_number = data.get("registration_number")
    # name = data.get("name")
    # privacy_policy_url = data.get("privacy_policy_url")
    # entitlement = data.get("entitlement")
    # intermediary_association = data.get("intermediary_association")
    # acting_on_behalf_of = data.get("acting_on_behalf_of")
    # limit = data.get("limit")

    # required_fields = {
    #     "registration_number": registration_number,
    #     "name": name,
    #     "privacy_policy_url": privacy_policy_url,
    #     "entitlement": entitlement,
    #     "intermediary_association": intermediary_association,
    #     "acting_on_behalf_of": acting_on_behalf_of,
    #     "limit": limit
    # }

    # missing_fields = [name for name, value in required_fields.items() if not value]

    # if missing_fields:
    #     return {
    #         "status": "error",
    #         "code": 400,
    #         "message": "Missing required fields.",
    #         "data": {
    #             "missing_fields": missing_fields
    #         }
    #     }, 400

    # todas as rps da bd
    results=db.get_all_rp_inf()

    if name:
        name_lower = name.lower()
        results = [
            u for u in results
            if name_lower in u["tradeName"].lower()
        ]
        
    # if registration_number:

    #     results = [
    #         u for u in results
    #         if registration_number in u["registration_number"]
    #     ]
    
    if privacy_policy_url:

        results = [
            u for u in results
            if privacy_policy_url in u["policyURI"]
        ]

    if entitlement:

        results = [
            u for u in results
            if entitlement in u["entitlement"]
        ]

    if intermediary_association:

        intermediary_association_lower = intermediary_association.lower()
        results = [
            u for u in results
            if intermediary_association_lower in u["usesIntermediary"].lower()
        ]

    if acting_on_behalf_of:

        acting_on_behalf_of_lower = acting_on_behalf_of.lower()
        results = [
            u for u in results
            if acting_on_behalf_of_lower in u["isIntermediary"].lower()
        ]

    results = results[:limit]

    # results={
    #     "teste":"test"
    # }

    final_result= json.dumps(results)

    # with open("app/EJBCA/ecdsa_key.pem", "rb") as f:
    #   ec_key = serialization.load_pem_private_key(
    #       f.read(),
    #       password=None,
    #       backend=default_backend()
    #   )
    
    key = import_private_ec_key_from_file(cfgserv.wrprc_privateKey)
    ec_key = ECKey(priv_key=key)

    jws = JWS(final_result, alg="ES256")

    signed_jws = jws.sign_json([ec_key])

    return signed_jws

@rpr.route("/static/swagger.json")
def swagger_static():
    return send_from_directory("static", "swagger.json")

@rpr.route("/guide")
def guide():
    return render_template("guide.html")