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
from flask import send_from_directory

rpr = Blueprint("RPR", __name__, url_prefix="/")

rpr.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template/')

def validate_required_fields(data, required_fields):
    missing = []

    for field in required_fields:
        if field not in data:
            missing.append(field)
            continue

        value = data[field]

        if value is None:
            missing.append(field)
            continue

        # empty strings
        if isinstance(value, str) and value.strip() == "":
            missing.append(field)
            continue

        # lists ou empty dicts
        if isinstance(value, (list, dict)) and len(value) == 0:
            missing.append(field)
            continue

    return missing

def error_response(message, missing_fields=None, code=400):
    return {
        "status": "error",
        "code": code,
        "message": message,
        "data": {
            "missing_fields": missing_fields or []
        }
    }, code

def error_invalid(message, code=400):
    return {
        "status": "error",
        "code": code,
        "message": message
    }, code

def update_response(message, len, code=201):
    return {
        "status": "success",
        "code": code,
        "message": message,
        "updated_count": len
    }, code

def create_response(message, data=None, result=None, code=201):
    return {
        "status": "success",
        "code": code,
        "message": message,
        "data": {
            data: result or []
        }
    }, code

def list_response(message, result, name, code=200):
    return {
        "status": "success",
        "code": code,
        "message": message,
        "data": {
            name: result
        }
    }, code

@rpr.route("/swagger/api.yaml")
def swagger_yaml():
    return send_from_directory("swagger", "api.yaml")

def serialize_json(value):
    return json.dumps(value) if value is not None else None

def deserialize_json(value):
    return json.loads(value) if value else None

def validate_date_field(value, field_name):
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except (ValueError, TypeError):
        return error_response(
            f"Invalid '{field_name}'. Expected format: YYYY-MM-DD."
        )
    return None

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

    url = "https://" + cfgserv.url_verifier +"/ui/presentations"
    
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

## -law
@rpr.route('/law/create', methods=['POST'])
def create_law():

    data = request.get_json(silent=True)

    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "law"])
    if missing:
        return error_response("Missing required fields.", missing)

    hash_pid = data.get("hash_pid")
    laws = data.get("law", [])

    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    result = []

    for law in laws: 
        missing = validate_required_fields(law, ["legislativeIdentifier"])
        if missing:
            return error_response("Missing required fields.", missing)
    
    for law in laws:
        legislativeIdentifier = law.get("legislativeIdentifier")
        legalBasis = law.get("legalBasis", [])

        law_id = db.insert_law(legislativeIdentifier, user_id)
        result.append(law_id)

        for aux in legalBasis:
            if aux:
                db.insert_law_legal_basis(law_id, aux)

    return create_response("Law created successfully", "Law new ids:", result)

@rpr.route('/law/list', methods=['POST'])
def list_law():

    data = request.get_json(silent=True)
    
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid", missing)

    result = db.get_law(user_id)

    return list_response("Law retrieved successfully.", result, "law")

## -legal person 
@rpr.route('/legal_person/create', methods=['POST'])
def create_legal_person():

    data = request.get_json(silent=True)

    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "legalPerson"])
    if missing:
        return error_response("Missing required fields.", missing)

    hash_pid = data.get("hash_pid")
    legalPersons = data.get("legalPerson", [])

    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    result = []

    #verification
    for legalPerson in legalPersons:
        missing = validate_required_fields(legalPerson, ["legalName"])
        if missing:
            return error_response("Missing required fields.", missing)
        
        laws = legalPerson.get("law", [])
        for law in laws:
            if law:
                if user_id != db.check_law(law):
                    return error_invalid(f"law id {law} doesn't belong to this user")
    
    #inserts data base
    for legalPerson in legalPersons:
        legalNames = legalPerson.get("legalName", [])
        laws = legalPerson.get("law", [])

        legal_person_id = db.insert_legal_person(user_id)
        result.append(legal_person_id)
        
        for legalName in legalNames:
            db.insert_legal_person_name(legal_person_id, legalName)
        
        for law in laws:
            if law:
                db.associate_legal_person_law(legal_person_id, law)

    return create_response("Legal Person created successfully", "Legal person new ids:", result)

@rpr.route('/legal_person/list', methods=['POST'])
def list_legal_person():

    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")

    result = db.get_legal_person(user_id)

    return list_response("Legal Persons retrieved successfully.", result, "legal_person")

@rpr.route('/legal_person/update_law', methods=['POST'])
def update_legal_person_law():

    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "legal_person_id", "law_ids"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    legal_person_id = data.get("legal_person_id")
    law_ids = data.get("law_ids", [])
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    #verification
    if user_id != db.check_legal_person(legal_person_id):
        return error_invalid(f"Legal Person id {legal_person_id} doesn't belong to this user")
    
    for law_id in law_ids:
        if user_id != db.check_law(law_id):
            return error_invalid(f"law id {law_id} doesn't belong to this user")
        
    #insert data base
    for law_id in law_ids:
        db.insert_legal_person_law(legal_person_id, law_id)

    return update_response("Legal person law associations updated successfully", len(law_ids))

@rpr.route('/legal_person/remove_law', methods=['POST'])
def remove_legal_person_law():

    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "legal_person_id", "law_ids"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    legal_person_id = data.get("legal_person_id")
    law_ids = data.get("law_ids", [])
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    # verification
    if user_id != db.check_legal_person(legal_person_id):
        return error_invalid(f"Legal Person id {legal_person_id} doesn't belong to this user")
    
    for law_id in law_ids:
        if user_id != db.check_law(law_id):
            return error_invalid(f"law id {law_id} doesn't belong to this user")
        
    deleted_count = db.delete_legal_person_laws(legal_person_id, law_ids)

    return update_response(
        "Legal person law associations removed successfully",
        deleted_count
    )

## -natural person
@rpr.route('/natural_person/create', methods=['POST'])
def create_natural_person():

    data = request.get_json(silent=True)

    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "naturalPerson"])
    if missing:
        return error_response("Missing required fields.", missing)

    hash_pid = data.get("hash_pid")
    naturalPersons = data.get("naturalPerson", [])

    user_id = db.check_user(hash_pid)
    result = []

    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    #verification
    for naturalPerson in naturalPersons:
        missing = validate_required_fields(naturalPerson, ["familyName", "givenName"])
        if missing:
            return error_response("Missing required fields.", missing)
        
    #insert data base    
    for naturalPerson in naturalPersons:
        family_name = naturalPerson.get("familyName")
        given_name = naturalPerson.get("givenName")
        date_of_birth = naturalPerson.get("dateOfBirth")
        place_of_birth = naturalPerson.get("placeOfBirth")

        natural_person_id = db.insert_natural_person(family_name, given_name, date_of_birth, place_of_birth, user_id)
        result.append(natural_person_id)

    return create_response("Natural Person created successfully", "Natural person new ids", result)

@rpr.route('/natural_person/list', methods=['POST'])
def get_natural_person():

    data = request.get_json(silent=True)
    
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")

    result = db.get_natural_person(user_id)

    return list_response("Natural Persons retrieved successfully.", result, "natural_person")

## -identifier
@rpr.route('/identifier/create', methods=['POST'])
def create_identifier():

    data = request.get_json(silent=True)

    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "identifier"])
    if missing:
        return error_response("Missing required fields.", missing)

    hash_pid = data.get("hash_pid")
    identifiers = data.get("identifier", [])

    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    result = []

    #verification
    for identifier in identifiers:
        missing = validate_required_fields(identifier, ["identifier", "type"])
        if missing:
            return error_response("Missing required fields.", missing)
        
        type = identifier.get("type")
        if type not in cfgserv.legal_entity_type_identifier["Type of Identifier"]:
            return error_invalid(f"Invalid type_of_identifier. Must be one of: {', '.join(cfgserv.legal_entity_type_identifier['Type of Identifier'])}")

    #insert data base
    for identifier in identifiers:
        identifier_value = identifier.get("identifier")
        type = identifier.get("type")

        identifier_id = db.insert_identifier(identifier_value, type, user_id)
        result.append(identifier_id)

    return create_response("Identifier created successfully", "Identifiers new ids", result)

@rpr.route('/identifier/list', methods=['POST'])
def list_identifier():

    data = request.get_json(silent=True)

    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")

    result = db.get_identifier(user_id)

    return list_response("Identifiers retrieved successfully.", result, "identifier")

## -legal entity
@rpr.route('/legal_entity/create', methods=['POST'])
def create_legal_entity():

    data = request.get_json(silent=True)

    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "legal_entity"])
    if missing:
        return error_response("Missing required fields.", missing)

    hash_pid = data.get("hash_pid")
    legal_entity = data.get("legal_entity")

    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    result = []

    #verification
    for aux in legal_entity:
        missing = validate_required_fields(aux, ["identifiers", "country"])
        if missing:
            return error_response("Missing required fields.", missing)

        legal_person_id = aux.get("legal_person_id")
        natural_person_id = aux.get("natural_person_id")
        identifier_ids = aux.get("identifiers", [])
        country = aux.get("country")

        if legal_person_id and natural_person_id:
            return error_response("There can't be two different types of people", "legal_person_id or natural_person_id")
        if not legal_person_id and not natural_person_id:
            return error_response("Missing required fields.", "legal_person_id or natural_person_id")

        if country not in cfgserv.eu_countries:
                return error_invalid(f"Invalid Country. Must be one of: {', '.join(cfgserv.eu_countries)}")

        if natural_person_id:
            if user_id != db.check_natural_person(natural_person_id):
                return error_invalid(f"The natural person ID {natural_person_id} does not belong to this user")

        if legal_person_id: 
            if user_id != db.check_legal_person(legal_person_id):
                return error_invalid(f"The legal person ID {legal_person_id} does not belong to this user")
        
        for identifier_id in identifier_ids:
            if user_id != db.check_identifier(identifier_id):
                return error_invalid(f"The identifier ID {identifier_id} does not belong to this user")

    #insert data base
    for aux in legal_entity:
        identifier_ids = aux.get("identifiers", [])
        postalAddress = aux.get("postalAddress", [])
        country = aux.get("country")
        emails = aux.get("email", [])
        phones = aux.get("phone", [])
        infoURIs = aux.get("infoURI", [])
        legal_person_id = aux.get("legal_person_id")
        natural_person_id = aux.get("natural_person_id")

        legal_entity_id = db.insert_legal_entity(legal_person_id, natural_person_id, country, user_id)
        result.append(legal_entity_id)

        for identifier_id in identifier_ids:
            db.insert_legal_entity_identifier(legal_entity_id, identifier_id)

        if postalAddress:
            for aux in postalAddress:
                db.insert_legal_entity_postal_address(legal_entity_id, aux)
        
        if emails:
            for email in emails:
                db.insert_legal_entity_email(legal_entity_id, email)
        
        if phones:
            for phone in phones:
                db.insert_legal_entity_phone(legal_entity_id, phone)

        if  infoURIs:
            for infoURI in infoURIs:
                db.insert_legal_entity_info_uri(legal_entity_id, infoURI)

    return create_response("Legal Entity created successfully.", "legal Entity id:", result)

@rpr.route('/legal_entity/list', methods=['POST'])
def list_legal_entity():

    data = request.get_json(silent=True)
    
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")

    result = db.get_legal_entity(user_id)

    return list_response("Legal Entity retrieved successfully.", result, "legal_entity")

@rpr.route('/legal_entity/update_identifier', methods=['POST'])
def update_legal_entity_identifier():

    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "legal_entity_id", "identifier_ids"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    legal_entity_id = data.get("legal_entity_id")
    identifier_ids = data.get("identifier_ids", [])
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    #verification
    if user_id != db.check_legal_entity(legal_entity_id):
        return error_invalid(f"Legal Entity id {legal_entity_id} doesn't belong to this user")
    
    for identifier_id in identifier_ids:
        if user_id != db.check_identifier(identifier_id):
            return error_invalid(f"Identifier id {identifier_id} doesn't belong to this user")
        
    #insert data base
    for identifier_id in identifier_ids:
        db.insert_legal_entity_identifier(legal_entity_id, identifier_id)

    return update_response("Legal Entity Identifier associations updated successfully", len(identifier_ids))

@rpr.route('/legal_entity/remove_identifier', methods=['POST'])
def remove_legal_entity_remove_identifier():

    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "legal_entity_id", "identifier_ids"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    legal_entity_id = data.get("legal_entity_id")
    identifier_ids = data.get("identifier_ids", [])

    #verification
    if not isinstance(identifier_ids, list) or not identifier_ids:
        return error_invalid("identifier_ids must be a non-empty list")

    identifier_ids = list(set(identifier_ids))
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    if user_id != db.check_legal_entity(legal_entity_id):
        return error_invalid(f"Legal Entity id {legal_entity_id} doesn't belong to this user")
     
    for identifier_id in identifier_ids:
        if user_id != db.check_identifier(identifier_id):
            return error_invalid(f"Identifier {identifier_id} doesn't belong to this user")

    current_identifiers = db.get_identifiers_legal_entity(legal_entity_id)

    current_ids = {row[0] for row in current_identifiers}

    if not current_ids:
        return error_invalid("Legal Entity has no identifiers (invalid state)")

    valid_identifiers_to_remove = [
        i for i in identifier_ids if i in current_ids
    ]

    if not valid_identifiers_to_remove:
        return error_invalid("None of the provided identifiers are associated with this Legal Entity")

    if len(current_ids) - len(valid_identifiers_to_remove) < 1:
        return error_invalid("A Legal Entity must have at least one identifier")

    #delete
    deleted_count = db.delete_legal_entity_identifier(
        legal_entity_id,
        valid_identifiers_to_remove
    )

    return update_response(
        "Legal Entity Identifier associations removed successfully",
        deleted_count
    )

## -policy
@rpr.route('/policy/create', methods=['POST'])
def create_policy():

    data = request.get_json(silent=True)

    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "policy"])
    if missing:
        return error_response("Missing required fields.", missing)

    hash_pid = data.get("hash_pid")
    policies = data.get("policy", [])

    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    result = []

    #verification
    for policy in policies:
        missing = validate_required_fields(policy, ["policyURI", "type", "intention"])
        if missing:
            return error_response("Missing required fields.", missing)

        type = policy.get("type")
        intention = policy.get("intention")

        if intention != "intended_use" and intention != "wrp":
            return error_invalid("Invalid intention. 'wrp' or 'intended_use'.")

        if intention == "wrp":
            if type not in cfgserv.relying_party["Type of Policy"]:
                return error_invalid(f"Invalid 'wrp' Type of Policy. Must be one of: {', '.join(cfgserv.relying_party['Type of Policy'])}")

        if intention == "intended_use":
            if type not in cfgserv.intended_use["Type of Privacy Policy"]:
                return error_invalid(f"Invalid 'intended_use' type_policy. Must be one of: {', '.join(cfgserv.intended_use['Type of Privacy Policy'])}")

    #insert data base
    for policy in policies:
        policyURI = policy.get("policyURI")
        type = policy.get("type")

        policy_id = db.insert_policy(policyURI, type, user_id)
        result.append(policy_id)

    return create_response("Policy created successfully", "Policies IDs:", result)

@rpr.route('/policy/list', methods=['POST'])
def list_policy():

    data = request.get_json(silent=True)
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")

    result = db.get_policy(user_id)

    return create_response("Policies retrieved successfully.", "policy", result)

## -provider
@rpr.route('/provider/create', methods=['POST'])
def create_provider():

    data = request.get_json(silent=True)

    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "provider"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    providers = data.get("provider", [])

    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    result = []

    #validation
    for provider in providers:
        missing = validate_required_fields(provider, ["policy_id", "providerType"])
        if missing:
            return error_response("Missing required fields.", missing)

        policy_ids = provider.get("policy_id", [])
        for policy_id in policy_ids:
            row = db.check_policy(policy_id)

            if not row:
                return error_invalid(f"Policy {policy_id} not found")
            if user_id[0] != row[0]:
                return error_invalid(f"The Policy ID {policy_id} does not belong to this user")
            
            if row[1] not in cfgserv.relying_party["Type of Policy"]:
                return error_invalid(f"The policy has an incorrect type; it must be a policy with a type for 'Wallet Relying Party'(intention: wrp). Must be one of: {', '.join(cfgserv.relying_party['Type of Policy'])}")

        legalEntityId = provider.get("legalEntityId")
        if user_id != db.check_legal_entity(legalEntityId):
            return error_invalid(f"The Legal Entity ID {legalEntityId} does not belong to this user")
            
    #insert data base
    for provider in providers:
        legalEntityId = provider.get("legalEntityId")
        providerType = provider.get("providerType")
        x5c = provider.get("x5c", [])
        policy_ids = provider.get("policy_id", [])

        provider_id = db.insert_provider(legalEntityId, providerType, user_id)
        result.append(provider_id)

        for policy_id in policy_ids:
            db.insert_provider_policy(provider_id, policy_id)

        for cert in x5c:
            if cert:
                db.insert_provider_x5c(provider_id, cert)

    return create_response("Provider created successfully", "Provider id", result)


@rpr.route('/provider/list', methods=['POST'])
def list_provider():
    data = request.get_json(silent=True)
    
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")

    result = db.get_provider(user_id)

    return list_response("Legal Entity retrieved successfully.", result, "provider")

@rpr.route('/provider/update_policy', methods=['POST'])
def update_provider_policy():
    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "provider_id", "policy_ids"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    provider_id = data.get("provider_id")
    policy_ids = data.get("policy_ids", [])
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    #verification
    if user_id != db.check_provider(provider_id):
        return error_invalid(f"Provider id {provider_id} doesn't belong to this user")
    
    for policy_id in policy_ids:
        row = db.check_policy(policy_id)
        
        if user_id[0] != row[0]:
            return error_invalid(f"The Policy ID {policy_id} does not belong to this user")
        if row[1] not in cfgserv.relying_party["Type of Policy"]:
            return error_invalid(f"The policy has an incorrect type; it must be a policy with a type for 'Wallet Relying Party'(intention: wrp). Must be one of: {', '.join(cfgserv.relying_party['Type of Policy'])}")

    #insert data base
    for policy_id in policy_ids:
        db.insert_provider_policy(provider_id, policy_id)

    return update_response("Provider Policy associations updated successfully", len(policy_ids))

@rpr.route('/provider/remove_policy', methods=['POST'])
def remove_provider_policy():

    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "provider_id", "policy_ids"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    provider_id = data.get("provider_id")
    policy_ids = data.get("policy_ids", [])

    if not isinstance(policy_ids, list) or not policy_ids:
        return error_invalid("policy_ids must be a non-empty list")

    policy_ids = list(set(policy_ids))
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    if user_id != db.check_provider(provider_id):
        return error_invalid(f"Provider id {provider_id} doesn't belong to this user")
    
    for policy_id in policy_ids:
        row = db.check_policy(policy_id)
        if not row[0] or user_id[0] != row[0]:
            return error_invalid(f"Policy {policy_id} doesn't belong to this user")

    current_policies = db.get_provider_policy(provider_id)

    current_policy_ids = {row[0] for row in current_policies}

    if not current_policy_ids:
        return error_invalid("Provider has no policies (invalid state)")

    valid_policies_to_remove = [
        p for p in policy_ids if p in current_policy_ids
    ]

    if not valid_policies_to_remove:
        return error_invalid("None of the provided policies are associated with this provider")

    if len(current_policy_ids) - len(valid_policies_to_remove) < 1:
        return error_invalid("A Provider must have at least one policy")

    deleted_count = db.delete_provider_policy(
        provider_id,
        valid_policies_to_remove
    )

    return update_response(
        "Provider Policy associations removed successfully",
        deleted_count
    )

## -credential
@rpr.route('/credential/create', methods=['POST'])
def create_credential():

    data = request.get_json(silent=True)
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "credentials"])
    if missing:
        return error_response("Missing required fields.", missing)

    hash_pid = data.get("hash_pid")
    credentials = data.get("credentials", [])

    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    result = []

    #verification
    for credential in credentials:
        missing = validate_required_fields(credential, ["format", "meta", "claims"])
        if missing:
            return error_response("Missing required fields.", missing)
        
        if not isinstance(credential["meta"], dict):
            return error_response(
                "Field 'meta' must be an object."
            )
        
        claims = credential.get("claims", [])
        for claim in claims:
            missing = validate_required_fields(claim, ["path"])
            if missing:
                return error_response("Missing required fields.", missing)

            if not isinstance(claim["path"], list):
                return error_response(
                    "Field 'path' must be an array."
                )

            if len(claim["path"]) == 0:
                return error_response(
                    "Field 'path' cannot be empty."
                )

    #insert data base
    for credential in credentials:
        format = credential.get("format")
        meta = serialize_json(credential["meta"])
        claims = credential.get("claims", [])
        
        credential_id = db.insert_credential(format, meta, user_id)
        result.append(credential_id)

        for claim in claims:
            path = serialize_json(claim["path"])

            db.insert_claim(credential_id, path)
    
    return create_response("Credential created successfully", "Credentials ids", result)

@rpr.route('/credential/list', methods=['POST'])
def list_credential():
    data = request.get_json(silent=True)
    
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid"])
    if missing:
        return error_response("Missing required fields.", missing)

    hash_pid = data.get("hash_pid")
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    result = db.get_credentials(user_id)

    return list_response("Credentials retrieved successfully.", result, "credential")

## -intended use
@rpr.route('/intended_use/create', methods=['POST'])
def create_intended_use():

    data = request.get_json(silent=True)

    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "intended_uses"])
    if missing:
        return error_response("Missing required fields.", missing)

    hash_pid = data.get("hash_pid")
    intended_uses = data.get("intended_uses", [])

    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    result = []

    #validation
    for intended_use in intended_uses:
        missing = validate_required_fields(intended_use, ["intendedUseIdentifier", "createdAt", "revokedAt", "purpose", "privacyPolicy_id", "credential_ids"])
        if missing:
            return error_response("Missing required fields.", missing)
        
        purposes = intended_use.get("purpose", [])
        for purpose in purposes:
            missing = validate_required_fields(purpose, ["lang", "content"])
            if missing:
                return error_response("Missing required fields.", missing)
            
            lang = purpose.get("lang")
            
            if lang not in cfgserv.eu_languages:
                return error_invalid(f"Invalid purpose_lang. Must be one of: {', '.join(cfgserv.eu_languages)}")
        
        privacyPolicy_ids = intended_use.get("privacyPolicy_id", [])
        for privacyPolicy_id in privacyPolicy_ids:
            row = db.check_policy(privacyPolicy_id)
            
            if user_id[0] != row[0]:
                return error_invalid(f"The Policy ID {privacyPolicy_id} does not belong to this user")
            
            if row[1] not in cfgserv.intended_use["Type of Privacy Policy"]:
                return error_invalid( f"The policy has an incorrect type; it must be a policy with a type for 'Wallet Relying Party'(intention: wrp). Must be one of: {', '.join(cfgserv.relying_party['Type of Policy'])}")

        credential_ids = intended_use.get("credential_ids", [])
        for credential_id in credential_ids:
            if user_id != db.check_credentials(credential_id):
                return error_invalid(f"The Credential ID {credential_id} does not belong to this user.")
            
    #insert data base
    for intended_use in intended_uses:
        intendedUseIdentifier = intended_use.get("intendedUseIdentifier")
        purposes = intended_use.get("purpose", [])
        privacyPolicy_ids = intended_use.get("privacyPolicy_id", [])
        credential_ids = intended_use.get("credential_ids", [])

        createdAt = intended_use.get("createdAt")
        revokedAt = intended_use.get("revokedAt")

        error = validate_date_field(createdAt, "createdAt")
        if error:
            return error

        error = validate_date_field(revokedAt, "revokedAt")
        if error:
            return error

        intended_use_id = db.insert_intended_use(intendedUseIdentifier, createdAt, revokedAt, user_id)
        result.append(intended_use_id)

        for purpose in purposes:
            lang = purpose.get("lang")
            content = purpose.get("content")

            mls_id = db.insert_multilanguage_string(lang, content, user_id)
            db.insert_intended_use_purpose(intended_use_id, mls_id)
        
        for privacyPolicy_id in privacyPolicy_ids:
            db.insert_intended_use_policy(intended_use_id, privacyPolicy_id)

        for credential_id in credential_ids:
            db.insert_intended_use_credential(intended_use_id, credential_id)
    
    return create_response("Intended Use created successfully", "Credentials ids", result)

@rpr.route('/intended_use/list', methods=['POST'])
def list_intended_use():
    data = request.get_json(silent=True)
    
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")

    result = db.get_intended_use(user_id)

    return list_response("Intended Use retrieved successfully.", result, "intended_use")

@rpr.route('/intended_use/update_credential', methods=['POST'])
def update_intended_use_credential():
    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "intended_use_id", "credential_ids"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    intended_use_id = data.get("intended_use_id")
    credential_ids = data.get("credential_ids", [])
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    #verification
    if user_id != db.check_intendedUse(intended_use_id):
        return error_invalid(f"Intended Use id {intended_use_id} doesn't belong to this user")
    
    for credential_id in credential_ids:
        if user_id != db.check_credentials(credential_id):
            return error_invalid(f"Credential id {credential_id} doesn't belong to this user")
        
    #insert data base
    for credential_id in credential_ids:
        db.insert_intended_use_credential(intended_use_id, credential_id)

    return update_response("Intended Use Credential associations updated successfully", len(credential_ids))

@rpr.route('/intended_use/update_policy', methods=['POST'])
def update_intended_use_policy():
    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "intended_use_id", "policy_ids"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    intended_use_id = data.get("intended_use_id")
    policy_ids = data.get("policy_ids", [])
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    #verification
    if user_id != db.check_intendedUse(intended_use_id):
        return error_invalid(f"Intended Use id {intended_use_id} doesn't belong to this user")
    
    for policy_id in policy_ids:
        row = db.check_policy(policy_id)
        
        if user_id[0] != row[0]:
            return error_invalid(f"The Policy ID {policy_id} does not belong to this user")
        if row[1] not in cfgserv.intended_use["Type of Privacy Policy"]:
            return error_invalid(f"The policy has an incorrect type; it must be a policy with a type for 'Intended Use'(intention: intended_use). Must be one of: {', '.join(cfgserv.relying_party['Type of Policy'])}")

    #insert data base
    for policy_id in policy_ids:
        db.insert_intended_use_policy(intended_use_id, policy_id)

    return update_response("Intended Use Policy associations updated successfully", len(policy_ids))

@rpr.route('/intended_use/remove_credential', methods=['POST'])
def remove_intended_use_credential():
    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "intended_use_id", "credential_ids"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    intended_use_id = data.get("intended_use_id")
    credential_ids = data.get("credential_ids", [])
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    #verification
    if user_id != db.check_intendedUse(intended_use_id):
        return error_invalid(f"Intended Use id {intended_use_id} doesn't belong to this user")
    
    for credential_id in credential_ids:
        if user_id != db.check_credentials(credential_id):
            return error_invalid(f"Credential id {credential_id} doesn't belong to this user")

    current_credentials = db.get_intended_use_credential(intended_use_id)

    current_credential_ids = {row[0] for row in current_credentials}

    if not current_credential_ids:
        return error_invalid("Provider has no credentials (invalid state)")

    valid_credentials_to_remove = [
        p for p in credential_ids if p in current_credential_ids
    ]

    if not valid_credentials_to_remove:
        return error_invalid("None of the provided credentials are associated with this Intended Use")

    if len(current_credential_ids) - len(valid_credentials_to_remove) < 1:
        return error_invalid("A Intended Use must have at least one Credential")
        
    #insert data base
    deleted_count = db.delete_intended_use_credential(intended_use_id, credential_ids)

    return update_response(
        "Intended Use Credential associations removed successfully",
        deleted_count
    )

@rpr.route('/intended_use/remove_policy', methods=['POST'])
def remove_intended_use_policy():
    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "intended_use_id", "policy_ids"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    intended_use_id = data.get("intended_use_id")
    policy_ids = data.get("policy_ids", [])
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    #verification
    if user_id != db.check_intendedUse(intended_use_id):
        return error_invalid(f"Intended Use id {intended_use_id} doesn't belong to this user")
    
    for policy_id in policy_ids:
        row = db.check_policy(policy_id)
        
        if user_id[0] != row[0]:
            return error_invalid(f"The Policy ID {policy_id} does not belong to this user")
        
    current_policies = db.get_intended_use_policy(intended_use_id)

    current_policy_ids = {row[0] for row in current_policies}

    if not current_policy_ids:
        return error_invalid("Intended Use has no policies (invalid state)")

    valid_policies_to_remove = [
        p for p in policy_ids if p in current_policy_ids
    ]

    if not valid_policies_to_remove:
        return error_invalid("None of the provided policies are associated with this Intended Use")

    if len(current_policy_ids) - len(valid_policies_to_remove) < 1:
        return error_invalid("A Intended Use must have at least one policy")
        
    #insert data base  
    deleted_count = db.delete_intended_use_policy(intended_use_id, policy_ids)

    return update_response(
        "Intended Use Policy associations removed successfully",
        deleted_count
    )

## -provided attestation
@rpr.route('/provided_attestation/create', methods=['POST'])
def create_provided_attestation():

    data = request.get_json(silent=True)

    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "providesAttestations"])
    if missing:
        return error_response("Missing required fields.", missing)

    hash_pid = data.get("hash_pid")
    providesAttestations = data.get("providesAttestations", [])

    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    result = []
    
    #validation
    for providesAttestation in providesAttestations:
        missing = validate_required_fields(providesAttestation, ["format", "meta"])
        if missing:
            return error_response("Missing required fields.", missing)
        
        if not isinstance(providesAttestation["meta"], dict):
            return error_response(
                "Field 'meta' must be an object."
            )
    
    #insert data base
    for providesAttestation in providesAttestations:
        format = providesAttestation.get("format")
        meta = serialize_json(providesAttestation["meta"])
        
        provided_attestation_id = db.insert_provided_attestation(format, meta, user_id)
        result.append(provided_attestation_id)

    return create_response("Provided Attestation created successfully.", "Provided Attestation ids", result)

@rpr.route('/provided_attestation/list', methods=['POST'])
def list_provided_attestation():
    data = request.get_json(silent=True)

    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")

    result = db.get_provided_attestation(user_id)

    return list_response("Provided attestation retrieved successfully.", result, "provided_attestation")

## -supervisoryAuthority
@rpr.route('/supervisory_authority/create', methods=['POST'])
def create_supervisory_authority():

    data = request.get_json(silent=True)

    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "supervisoryAuthority"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    supervisoryAuthority = data.get("supervisoryAuthority", [])
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")

    result = []

    #validation
    for aux in supervisoryAuthority:
        missing = validate_required_fields(aux, ["name", "country"])
        if missing:
            return error_response("Missing required fields.", missing)
        
        emails = aux.get("email", [])
        formuris = aux.get("formURI", [])
        phones = aux.get("phone", [])
        country = aux.get("country")

        if country not in cfgserv.eu_countries:
            return error_invalid(f"Invalid country. Must be one of: {', '.join(cfgserv.eu_countries)}")

        if not emails and not formuris and not phones:
            return error_response("At least one of the following fields is required.", "email, formURI or phone")
        
    #insert data base
    for aux in supervisoryAuthority:

        name = aux.get("name")
        country = aux.get("country")
        emails = aux.get("email", [])
        formuris = aux.get("formURI", [])
        phones = aux.get("phone", [])
        
        supervisory_authority_id = db.insert_supervisory_authority(name, country, user_id)
        result.append(supervisory_authority_id)

        if emails:
            for email in emails:
                db.insert_supervisory_authority_email(supervisory_authority_id, email)

        if formuris:
            for formUri in formuris:
                db.insert_supervisory_authority_formuri(supervisory_authority_id, formUri)

        if phones:
            for phone in phones:
                db.insert_supervisory_authority_phone(supervisory_authority_id, phone)

    return create_response("Supervisory Authority created successfully", "Supervisory Authority ids", result)

@rpr.route('/supervisory_authority/list', methods=['POST'])
def list_supervisory_authority():
    data = request.get_json(silent=True)
    
    if not data:
        return error_response("Invalid or missing JSON body")
    
    missing = validate_required_fields(data, ["hash_pid"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")

    result = db.get_supervisory_authority(user_id)

    return list_response("Supervisory Authority retrieved successfully.", result, "supervisory_authority")

## -wrp
@rpr.route('/wallet_rp/create', methods=['POST'])
def create_wrp():

    data = request.get_json(silent=True)

    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "WalletRelyingParty"])
    if missing:
        return error_response("Missing required fields.", missing)

    hash_pid = data.get("hash_pid")
    wrps = data.get("WalletRelyingParty", [])

    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")

    result = []

    #validation
    for wrp in wrps:
        missing = validate_required_fields(wrp, ["supportURI", "provider_id", "srvDescription", 
                                                 "isPSB", "entitlements", 
                                                 "supervisoryAuthority", "registryURI"])
        if missing:
            return error_response("Missing required fields.", missing)
        
        supervisoryAuthority = wrp.get("supervisoryAuthority")
        usesIntermediarys = wrp.get("usesIntermediary", [])
        providesAttestations_ids = wrp.get("providesAttestations_id", [])
        provider_id = wrp.get("provider_id")
        intendedUse_ids = wrp.get("intendedUse_ids", [])
        entitlements = wrp.get("entitlements", [])
        srvDescriptions = wrp.get("srvDescription", [])
        
        if user_id != db.check_supervisory_authority(supervisoryAuthority):
            return error_invalid(f"The supervisoryAuthority ID {supervisoryAuthority} does not belong to this user")
        
        if usesIntermediarys:
            for usesIntermediary in usesIntermediarys:
                if user_id != db.check_wrp(usesIntermediary):
                    return error_invalid(f"The usesIntermediary ID {usesIntermediary} does not belong to this user")
                
                if db.check_wrp_intermediary(usesIntermediary) != []:
                    return error_invalid(f"The usesIntermediary ID {usesIntermediary} already is a Intermediary")

        if providesAttestations_ids:
            for providesAttestations_id in providesAttestations_ids:
                if user_id != db.check_provided_attestation(providesAttestations_id):
                    return error_invalid(f"The providesAttestations ID {providesAttestations_id} does not belong to this user")
        
        if user_id != db.check_provider(provider_id):
                return error_invalid(f"The Provider ID {provider_id} does not belong to this user")
        
        if intendedUse_ids:
            for intendedUse_id in intendedUse_ids:
                if user_id != db.check_intendedUse(intendedUse_id):
                    return error_invalid(f"The intendedUse ID {intendedUse_id} does not belong to this user")

            if db.check_wrp_intendedUse(intendedUse_id) != []:
                return error_invalid(f"Intended Use id {intendedUse_id} already belongs to other wallet relying party")
        
        for entitlement in entitlements:
            if entitlement not in cfgserv.relying_party["Entitlement"]:
                return error_invalid(f"Invalid entitlement. Must be one of: {', '.join(cfgserv.relying_party['Entitlement'])}")

        for srvDescription in srvDescriptions:
            missing = validate_required_fields(srvDescription, ["lang"])
            if missing:
                return error_response("Missing required fields.", missing)
            
            lang = srvDescription.get("lang")
            if lang not in cfgserv.eu_languages:
                return error_invalid(f"Invalid srvDescription_lang. Must be one of: {', '.join(cfgserv.eu_languages)}")

    #insert data base
    for wrp in wrps:
        tradeName = wrp.get("tradeName")
        supportURIs = wrp.get("supportURI", [])
        srvDescriptions = wrp.get("srvDescription", [])
        isPSB = wrp.get("isPSB")
        isIntermediary = True
        entitlements = wrp.get("entitlements", [])
        usesIntermediarys = wrp.get("usesIntermediary", [])
        providesAttestations_ids = wrp.get("providesAttestations_id", [])
        registryURI = wrp.get("registryURI")
        supervisoryAuthority = wrp.get("supervisoryAuthority")
        provider_id = wrp.get("provider_id")
        intendedUse_ids = wrp.get("intendedUse_ids", [])

        if usesIntermediarys:
            isIntermediary = False

        wrp_id = db.insert_wrp(provider_id, tradeName, isPSB, registryURI, isIntermediary, supervisoryAuthority, user_id)
        result.append(wrp_id)

        for entitlement in entitlements:
            db.insert_wrp_entitlement(wrp_id, entitlement)

        if usesIntermediarys:
            for usesIntermediary in usesIntermediarys:
                db.insert_wrp_intermediary(wrp_id, usesIntermediary)
        
        for supportURI in supportURIs:
            db.insert_wrp_support_uri(wrp_id, supportURI)

        for srvDescription in srvDescriptions:
            lang = srvDescription.get("lang")
            content = srvDescription.get("content")

            mls_id = db.insert_multilanguage_string(lang, content, user_id)

            db.insert_wrp_srv_description(wrp_id, mls_id)

        if providesAttestations_ids:
            for providesAttestations_id in providesAttestations_ids:
                db.insert_wrp_provided_attestation(wrp_id, providesAttestations_id)

        for intendedUse_id in intendedUse_ids:
            db.insert_wrp_intended_use(wrp_id, intendedUse_id)

    return create_response("Wallet Relying Party created successfully", "wrp ids", result)

@rpr.route('/wallet_rp/list', methods=['POST'])
def list_wrp():
    data = request.get_json(silent=True)
    
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")

    result = db.get_wrp(user_id)

    return list_response("Wallet Relying Party retrieved successfully.", result, "wrp")

@rpr.route('/wallet_rp/update_intended_use', methods=['POST'])
def update_wrp_intended_use():
    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "wrp_id", "intended_use_ids"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    wrp_id = data.get("wrp_id")
    intended_use_ids = data.get("intended_use_ids", [])
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    #verification
    if user_id != db.check_wrp(wrp_id):
        return error_invalid(f"Wallet Relying Party id {wrp_id} doesn't belong to this user")
    
    for intended_use_id in intended_use_ids:
        if user_id != db.check_intendedUse(intended_use_id):
            return error_invalid(f"Intended Use id {intended_use_id} doesn't belong to this user")

        if db.check_wrp_intendedUse(intended_use_id) != []:
            return error_invalid(f"Intended Use id {intended_use_id} already belongs to other wallet relying party")

    #insert data base
    for intended_use_id in intended_use_ids:
        db.insert_wrp_intended_use(wrp_id, intended_use_id)

    return update_response("Wallet Relying Party Intended Use associations updated successfully", len(intended_use_ids))

@rpr.route('/wallet_rp/update_provided_attestation', methods=['POST'])
def update_wrp_provided_attestion():
    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "wrp_id", "provided_attestation_ids"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    wrp_id = data.get("wrp_id")
    provided_attestation_ids = data.get("provided_attestation_ids", [])
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    #verification
    if user_id != db.check_wrp(wrp_id):
        return error_invalid(f"Wallet Relying Party id {wrp_id} doesn't belong to this user")
    
    for provided_attestation_id in provided_attestation_ids:
        if user_id != db.check_provided_attestation(provided_attestation_id):
            return error_invalid(f"Provided Attestation id {provided_attestation_id} doesn't belong to this user")
        
    #insert data base
    for provided_attestation_id in provided_attestation_ids:
        db.insert_wrp_provided_attestation(wrp_id, provided_attestation_id)

    return update_response("Wallet Relying Party Provided Attestation associations updated successfully", len(provided_attestation_ids))

@rpr.route('/wallet_rp/update_uses_intermediary', methods=['POST'])
def update_wrp_uses_intermediary():
    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "wrp_id", "uses_intermediary_ids"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    wrp_id = data.get("wrp_id")
    uses_intermediary_ids = data.get("uses_intermediary_ids", [])
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    #verification
    if user_id != db.check_wrp(wrp_id):
        return error_invalid(f"Wallet Relying Party id {wrp_id} doesn't belong to this user")
    
    for uses_intermediary_id in uses_intermediary_ids:
        if user_id != db.check_wrp(uses_intermediary_id):
            return error_invalid(f"Wallet Relying Party id {uses_intermediary_id} doesn't belong to this user")
        
        if db.check_wrp_intermediary(uses_intermediary_id) != []:
            return error_invalid(f"The usesIntermediary ID {uses_intermediary_id} already is a Intermediary")
        
    #insert data base
    for uses_intermediary_id in uses_intermediary_ids:
        db.insert_wrp_intermediary(wrp_id, uses_intermediary_id)

    return update_response("Wallet Relying Party uses Intermediary associations updated successfully", len(uses_intermediary_ids))

@rpr.route('/wallet_rp/remove_intended_use', methods=['POST'])
def remove_wrp_intended_use():
    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "wrp_id", "intended_use_ids"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    wrp_id = data.get("wrp_id")
    intended_use_ids = data.get("intended_use_ids", [])
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    #verification
    if user_id != db.check_wrp(wrp_id):
        return error_invalid(f"Wallet Relying Party id {wrp_id} doesn't belong to this user")
    
    for intended_use_id in intended_use_ids:
        if user_id != db.check_intendedUse(intended_use_id):
            return error_invalid(f"Intended Use id {intended_use_id} doesn't belong to this user")
        
    current_intended_use = db.get_wrp_intendedUse(wrp_id)

    current_intended_use_ids = {row[0] for row in current_intended_use}

    if not current_intended_use_ids:
        return error_invalid("Wallet Relying Party has no intended use (invalid state)")

    valid_intended_use_to_remove = [
        p for p in intended_use_ids if p in current_intended_use_ids
    ]

    if not valid_intended_use_to_remove:
        return error_invalid("None of the provided Intended Uses are associated with this Wallet Relying Party")

    if len(current_intended_use_ids) - len(valid_intended_use_to_remove) < 1:
        return error_invalid("A Wallet Relying Party must have at least one Intended Use")
        
    #insert data base  
    deleted_count = db.delete_wrp_intended_use(wrp_id, intended_use_ids)

    return update_response(
        "Wallet Relying Party Intended Use associations removed successfully",
        deleted_count
    )

@rpr.route('/wallet_rp/remove_provided_attestation', methods=['POST'])
def remove_wrp_provided_attestion():
    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "wrp_id", "provided_attestation_ids"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    wrp_id = data.get("wrp_id")
    provided_attestation_ids = data.get("provided_attestation_ids", [])
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    #verification
    if user_id != db.check_wrp(wrp_id):
        return error_invalid(f"Wallet Relying Party id {wrp_id} doesn't belong to this user")
    
    for provided_attestation_id in provided_attestation_ids:
        if user_id != db.check_provided_attestation(provided_attestation_id):
            return error_invalid(f"Provided Attestation id {provided_attestation_id} doesn't belong to this user")
        
    #insert data base
    deleted_count = db.delete_wrp_provided_attestion(wrp_id, provided_attestation_ids)

    return update_response(
        "Wallet Relying Party Provided Attestation associations removed successfully",
        deleted_count
    )

@rpr.route('/wallet_rp/remove_uses_intermediary', methods=['POST'])
def remove_wrp_uses_intermediary():
    data = request.get_json(silent=True)
   
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "wrp_id", "uses_intermediary_ids"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    wrp_id = data.get("wrp_id")
    uses_intermediary_ids = data.get("uses_intermediary_ids", [])
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    #verification
    if user_id != db.check_wrp(wrp_id):
        return error_invalid(f"Wallet Relying Party id {wrp_id} doesn't belong to this user")
    
    for uses_intermediary_id in uses_intermediary_ids:
        if user_id != db.check_wrp(uses_intermediary_id):
            return error_invalid(f"Wallet Relying Party id {uses_intermediary_id} doesn't belong to this user")
        
    #insert data base
    deleted_count = db.delete_wrp_intermediary(wrp_id, uses_intermediary_ids)

    return update_response(
        "Wallet Relying Party uses Intermediary associations removed successfully",
        deleted_count
    )

@rpr.route('/list_claim', methods=['POST'])
def list_claim():
    data = request.get_json(silent=True)
        
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")

    result = db.get_claim(user_id)

    return list_response("Claims retrieved successfully.", result, "claim")

@rpr.route('/list_full_info', methods=['POST'])
def list_full_info():
    data = request.get_json(silent=True)
    
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    
    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")

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

    return list_response("Info retrieved successfully.", result, "data")

@rpr.route('/wrp', methods=['GET'])
def search_wrp_public():

    identifier = request.args.get("identifier")
    legalname = request.args.get("legalname")
    tradename = request.args.get("tradename")
    policy = request.args.get("policy")
    entitlement = request.args.get("entitlement")
    providesattestation = request.args.get("providesattestation")
    intendeduseidentifier = request.args.get("intendeduseidentifier")
    isintermediary = request.args.get("isintermediary")
    usesintermediary = request.args.get("usesintermediary")

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
        tradename=tradename,
        policy=policy,
        entitlement=entitlement,
        providesattestation=providesattestation,
        intendeduseidentifier=intendeduseidentifier,
        isintermediary=isintermediary,
        usesintermediary=usesintermediary
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
        return error_invalid("Wallet Relying Party not found")

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
        return error_response("Missing required fields.", "identifier")

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

# @rpr.route("/static/swagger.json")
# def swagger_static():
#     return send_from_directory("static", "swagger.json")

@rpr.route("/guide")
def guide():
    return render_template("guide.html")

@rpr.route("/wallet_rp/certificate", methods=["POST"])
def wrp_access_certificate():
    
    data = request.get_json(silent=True)
        
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "wrp_id", "password"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    wrp_id = data.get("wrp_id")
    password = data.get("password")

    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    if user_id != db.check_wrp(wrp_id):
        return error_invalid(f"Wallet Relying Party id {wrp_id} doesn't belong to this user")

    wrp = db.get_wrp_id(wrp_id)

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
    tradeName = wrp[0]["trade_name"]

    #uniformResourceIdentifier
    supportURI = wrp[0]["supportURI"][0]

    legal_entity = db.get_legal_entity_id(wrp[0]["provider_id"])
    
    #dados da legalEntity
    #caso for natural person é serialNumber no caso de uma legal person organizationIdentifier
    identifier = legal_entity[0]["identifier"]
    country = legal_entity[0]["country"]

    email = None
    if email:
        email = legal_entity[0]["email"][0]
    phone = None
    if phone:
        phone = legal_entity[0]["phone"][0]

    if legal_entity[0]["LegalPerson"] is None:
        #se user for natural person
        givenName=legal_entity[0]["NaturalPerson"]["givenName"]
        #surname
        surname=legal_entity[0]["NaturalPerson"]["familyName"]

        first = legal_entity[0]["identifier"][0]
        country_code = "XG" if TypeIdentifier[first['type']] == "LEI" else country

        serial_number = (
            f"{TypeIdentifier[first['type']]}"
            f"{country_code}-"
            f"{first['identifier']}"
        )

        certificateRequest= generateCertificateRequest(priv_key=priv_key, commonName=tradeName, countryName=country, uniformResourceIdentifier=supportURI, 
                                                       givenName=givenName, surname=surname, serialNumber=serial_number, email=email)
        
    else:
        #se user for legal person
        #dados da legal person
        #organizationName
        legalName = legal_entity[0]["LegalPerson"]["legalName"][0]

        first = legal_entity[0]["identifier"][0]
        country_code = "XG" if TypeIdentifier[first['type']] == "LEI" else country

        organizationIdentifier = (
            f"{TypeIdentifier[first['type']]}"
            f"{country_code}-"
            f"{first['identifier']}"
        )
        
        certificateRequest = generateCertificateRequest(priv_key=priv_key, commonName=tradeName, countryName=country, uniformResourceIdentifier=supportURI, 
                                                       organizationName=legalName, organizationIdentifier=organizationIdentifier, email=None)

    #como as TSLs, ex: lang en, description=test  
    #servicesDescription=RP[0]["srvDescription"]#como as TSLs, ex: lang en, description=test  
    #entitlement=RP[0]["entitlement"]
    # verificar legal entity se é pertence ao sector público, se sim True, se não False
    isPSB= False
#### ------
    # password=request.form.get("Password")


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

@rpr.route("/intended_use/certificate", methods=["POST"])
def intended_use_registration_certificate():

    data = request.get_json(silent=True)
        
    if not data:
        return error_response("Invalid or missing JSON body")

    missing = validate_required_fields(data, ["hash_pid", "intended_use_id"])
    if missing:
        return error_response("Missing required fields.", missing)
    
    hash_pid = data.get("hash_pid")
    intended_use_id = data.get("intended_use_id")

    user_id = db.check_user(hash_pid)
    if user_id is None:
        return error_invalid("Invalid hash_pid")
    
    if user_id != db.check_intendedUse(intended_use_id):
        return error_invalid(f"Intended Use id {intended_use_id} doesn't belong to this user")
    
    intended_use = db.get_intended_use_id(intended_use_id)

    wrp = db.get_wrp_intended_id(intended_use_id)
    if wrp == []:
        return error_invalid(f"Intended Use id {intended_use_id} doesn't have a Wallet Relying Party associated.")

    legal_entity = db.get_legal_entity_id(wrp[0]["provider_id"])

# #if legal person
# legal_person_data=get_legal_person_data()

# #if natural person
# natural_person_data= get_natural_person_data()

# #if legal_person
# legal_name=legal_person_data["legal_name"]

# #if natural_person
# given_name=natural_person_data["given_name"]
# family_name=natural_person_data["family_name"]


    iat= int(time.time())

# name=RP_data["tradeName"]
# purpose=intended_use_data["purpose"]
# info_uri=legal_entity_data["info_uri"]
# country=legal_entity_data["country"]

    name = wrp[0]["trade_name"]
    supportURI = wrp[0]["supportURI"][0]
    purpose = intended_use[0]["purpose"]
    if legal_entity[0].get("infoURI") and len(legal_entity[0]["infoURI"]) > 0:
        info_uri = legal_entity[0]["infoURI"][0]
    country = legal_entity[0]["country"]

# id=legal_entity_data["identifier"]
# privacy_policy=intended_use_data["privacyPolicy"]

    id = legal_entity[0]["identifier"][0]["identifier"]

    #id = legal_entity_data[0]["identifier"]
    privacy_policy = intended_use[0]["privacyPolicy"][0]["type"]

# # definir de acordo com os dados do certificado
# # policy_id=certificate_policy_id
# # certificate_policy=certificate_URI

# entitlement=RP_data["entitlement"]
# providesAttestations=RP_data["providesAttestations"]
# public_body=RP_data["isPSB"]
# service=RP_data["srvDescription"]

    entitlement = wrp[0]["entitlements"]
    # if wrp[0]["providesAttestations"]:
    #     providesAttestations = wrp[0]["providesAttestations"]
    public_body = wrp[0]["isPSB"]
    srv_description = wrp[0]["srvDescription"]

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
    
    identifier = legal_entity[0]["identifier"][0]

    country_code = "XG" if TypeIdentifier[identifier['type']] == "LEI" else country

    sub_id = (
        f"{TypeIdentifier[identifier['type']]}"
        f"{country_code}-"
        f"{identifier['identifier']}"
    )

    #sub_id = TypeIdentifier[legal_entity[0]["identifierType"]] + '-' + id

    # json_header = { "typ": "rc-wrp+jwt",
    #             "alg": "ES256", 
    #             "b64": "true", 
    #             "cty": ["b64"], "x5c": [],}

    headers={
        "accept": "application/json",
        "X-API-Key": "test" ,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data={
        "country":"FC",
        "doctype":"wrprc",
        "expiry_date":datetime.utcfromtimestamp(iat).strftime("%Y-%m-%d")
    }

    response = requests.post(cfgserv.url_statuslist, headers=headers, data=data)

    status=response.json()
    
    status_idx=status["status_list"]["idx"]
    status_uri=status["status_list"]["uri"]

    credentials = [
        cred
        for item in intended_use
        for cred in item.get("credentials", [])
    ]

    json_payload = { 
                        "name": name,
                        "purpose": purpose, 
                        "country": country,
                        "sub": sub_id,
                        "registry_uri": cfgserv.service_url,
                        "privacy_policy": privacy_policy, 
                        "policy_id": [
                            "0.4.0.19475.3.1"
                        ],
                        "iat": iat, 
                        "credentials": credentials,
                        "entitlements": entitlement,
                        "public_body": False,
                        "srv_description": srv_description,
                        "support_uri":supportURI,
                        "status": { 
                            "status_list": { 
                                            "idx": status_idx, "uri": status_uri
                            } 
                        }
        }

    if info_uri:
        json_payload["info_uri"] = info_uri
    
    if wrp[0].get("providesAttestations"):
        json_payload["provides_attestations"] = wrp[0]["providesAttestations"]
    
    sa = wrp[0].get("SupervisoryAuthority")
    if sa:
        supervisory_authority = {}

        if sa.get("email"):
            supervisory_authority["email"] = sa["email"][0]

        if sa.get("phone"):
            supervisory_authority["phone"] = sa["phone"][0]

        if sa.get("formURI"):
            supervisory_authority["uri"] = sa["formURI"][0]

        if supervisory_authority:
            json_payload["supervisory_authority"] = supervisory_authority
    
    if legal_entity[0]["LegalPerson"] is None:
        #se user for natural person
        givenName=legal_entity[0]["NaturalPerson"]["givenName"]
        #surname
        surname=legal_entity[0]["NaturalPerson"]["familyName"]

        # givenName=legal_entity[0]["givenName"]
        # #surname
        # surname=natural_person[0]["familyName"]
        certificate_policy = cfgserv.service_url + "certificate_policy"
        json_payload.update({
            "sub_gn": givenName,
            "sub_fn":surname,
            "certificate_policy":certificate_policy
        })

        
    else:
        #se user for legal person
        #dados da legal person
        #organizationName
        
        legalName = legal_entity[0]["LegalPerson"]["legalName"][0]
        #legalName=legal_person[0]["legalName"]
        certificate_policy = cfgserv.service_url + "certificate_policy"
        json_payload.update({
            "sub_ln": legalName,
            "certificate_policy":certificate_policy
        })
        
    if db.get_wrp_intermediary(wrp[0]["wrp_id"]) != []:
        
        rp_intermediary = db.get_wrp_id(db.get_wrp_intermediary(wrp[0]["wrp_id"]))
        legalentity_intermediary = db.get_legal_entity_id(rp_intermediary[0]["provider_id"])

        identifier = legalentity_intermediary[0]["identifier"][0]
        country = legalentity_intermediary[0]["country"]

        country_code = "XG" if TypeIdentifier[identifier['type']] == "LEI" else country

        aux = (
            f"{TypeIdentifier[identifier['type']]}"
            f"{country_code}-"
            f"{identifier['identifier']}"
        )

        json_payload.update({
            "intermediary": {
                "sub": aux,
                "sname": rp_intermediary[0]["trade_name"]
            }
        })
    
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

    data=json.loads(base64.b64decode(document_with_signature).decode("utf-8"))

    jwt_payload=data["payload"]
    jwt_header=data["signatures"][0]["protected"]
    jwt_signature=data["signatures"][0]["signature"]

    jwt = jwt_header + "." + jwt_payload + "." + jwt_signature

    #cbor

    cbor_data= cbor2.dumps(json_payload)

    msg = Sign1Message(phdr={Algorithm: Es256},uhdr={KID: b"key1"},payload=cbor_data)

    with open(cfgserv.wrprc_privateKey, "rb") as f:
        pem_bytes = f.read()

    cose_key = CoseKey.from_pem_private_key(pem_bytes.decode())
    msg.key = cose_key
    cose_bytes = msg.encode()

    #file_data = base64.b64decode(document_with_signature)

    file_base64 = base64.urlsafe_b64encode(jwt.encode()).decode()
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
