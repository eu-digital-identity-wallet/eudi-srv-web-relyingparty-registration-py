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
from cryptography.hazmat.primitives.asymmetric import ec
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


@rpr.route("/authentication", methods=["GET","POST"])
def authentication():

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

    # payload_sameDevice=payload

    # payload_sameDevice.update({"wallet_response_redirect_uri_template":cfgserv.service_url +
    #                                                    "getpidoid4vp?response_code={RESPONSE_CODE}&session_id=" + session["session_id"]})

    # response_same_device= requests.request("POST", url, headers=headers, data=json.dumps(payload_sameDevice)).json()

    # deeplink_url = (
    #     "eudi-openid4vp://" + cfgserv.url_verifier + "?client_id="
    #     + response_same_device["client_id"]
    #     + "&request_uri="
    #     + response_same_device["request_uri"]
    # )

    # oid4vp_requests.update({session["session_id"]:{"response": response_same_device, "expires":datetime.now() + timedelta(minutes=cfgserv.deffered_expiry), "certificate_List":False}})


    # Generate QR code
    # img = qrcode.make("uri")
    # QRCode.print_ascii()

    qrcode = segno.make(QR_code_url)
    out = io.BytesIO()
    qrcode.save(out, kind='png', scale=3)

    """ qrcode.to_artistic(
        background=cfgtest.qr_png,
        target=out,
        kind="png",
        scale=4,
    ) """
    # qrcode.terminal()
    # qr_img_base64 = qrcode.png_data_uri(scale=4)

    qr_img_base64 = "data:image/png;base64," + base64.b64encode(out.getvalue()).decode(
        "utf-8"
    )

    return render_template(
        "pid_login_qr_code.html",
        url_data="deeplink_url",
        qrcode=qr_img_base64,
        presentation_id=response["transaction_id"],
        redirect_url= cfgserv.service_url
    )

@rpr.route("/pid_authorization")
def pid_authorization_get():

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

    if "response_code" in request.args and "session_id" in request.args:

        response_code = request.args.get("response_code")
        presentation_id = oid4vp_requests[request.args.get("session_id")]["response"]["transaction_id"]
        session["session_id"]=request.args.get("session_id")

        if oid4vp_requests[request.args.get("session_id")]["certificate_List"]:
            if oid4vp_requests[request.args.get("session_id")]["certificate_List"] == True:
                session["certificate_List"]=True
        url = (
            "https://" + cfgserv.url_verifier +"/ui/presentations/"
            + presentation_id
            + "?nonce=hiCV7lZi5qAeCy7NFzUWSR4iCfSmRb99HfIvCkPaCLc="
            + "&response_code=" + response_code
        )

    elif "presentation_id" in request.args:
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

    temp_user_id=str(uuid.uuid4())
    session[temp_user_id]= attributesForm
    session["temp_user_id"] =temp_user_id

    user=session[temp_user_id]

    givenName=user["given_name"]
    surname=user["family_name"]
    birth_date=user["birth_date"]
    issuing_country=user["issuing_country"]
    issuance_authority=user["issuing_authority"]

    new_user = get_hash_user_pid.User(surname, givenName, birth_date, issuing_country, issuance_authority)
    hash_pid = new_user.hash

    check_user = db.check_user(hash_pid, session["session_id"])
    
    if(check_user == None):
        db.insert_user(hash_pid, session["session_id"])
        return redirect(url_for('RPR.menu_RP_user'))
    else:
        return redirect(url_for('RPR.menu_RP_user'))
    

@rpr.route("/user_auth", methods=["GET", "POST"])
def user_auth():
    
    temp_user_id = session['temp_user_id']

    #user data
    user_data_pid = session[temp_user_id]

    # address = request.form.get('address')
    # email = request.form.get('email')
    # phone_number = request.form.get('phone_number')
    # country = request.form.get('Country')
    # identifier= request.form.get("Identifier")
    # info_uri = request.form.get("Information URI")

    #introduzir os dados na BD legal entity
    #check = func.user_db_info(role, operator_name, PostalAddress, electronicAddress, user['id'], session["session_id"])

    return redirect(url_for('RPR.menu_RP_user'))
    
@rpr.route('/menu', methods=['GET','POST'])
def menu_RP_user():
    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]
    
    return render_template("rp_user_menu.html", user = user['given_name'], temp_user_id = temp_user_id)

@rpr.route('/natural_person/create_person', methods=['GET','POST'])
def create_natural_person():

    attributesForm={}

    form_items={
        "Given Name":"string",
        "Family Name":"string",
        "Date of Birth": "full-date",
        "Place of Birth": "string",
    }
    descriptions = {
        "Given Name":"First name(s) of the natural person including middle name(s) where applicable",
        "Family Name":"Last name(s) or surnames of the natural person",
        "Date of Birth": "Date of birth of the natural person",
        "Place of Birth": "Place of birth of the natural person",
    }
    attributesForm.update(form_items)

    return render_template("dynamic-form.html",title="Create Natural Person",title_description="Please enter your Natural Person data.", desc = descriptions, countries = cfgserv.eu_countries ,attributes=attributesForm, redirect_url= cfgserv.service_url + "natural_person/add_natural_person_db")

@rpr.route('/natural_person/add_natural_person_db', methods=['GET','POST'])
def add_natural_person_db():

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]

    given_name= request.form.get("Given Name")
    family_name=request.form.get("Family Name")
    birthdate=request.form.get("Date of Birth")
    birthplace=request.form.get( "Place of Birth")

    new_user = get_hash_user_pid.User(user["family_name"], user["given_name"], user["birth_date"], user["issuing_country"], user["issuing_authority"])
    hash_pid = new_user.hash
    user_id = db.check_user(hash_pid, session["session_id"])

    db.insert_user_naturalPerson(given_name, family_name, birthdate, birthplace, user_id, session["session_id"]) 
   
    return redirect('/natural_person/list')

@rpr.route('/natural_person/update_legal_entities', methods=["GET", "POST"])
def update_legal_entities():
    
    natural_person_id = request.args.get("id")
    legal_entities = ast.literal_eval(request.args.get("checks"))
    check_legal_entities = db.get_check_legal_entity_info(natural_person_id, session["session_id"])

    temp_user_id = session['temp_user_id']

    check_legal_entities = db.get_check_legal_entity_info(natural_person_id, session["session_id"]) or []

    previous = { x["naturalperson_id"] for x in check_legal_entities }
    current = { int(x) for x in legal_entities }
    to_remove = previous - current
        
    for elem in to_remove:
        db.remove_naturalPerson_legal_entity(elem, session["session_id"])
    
    for elem in legal_entities:
        legal_entity_id = int(elem)

        check = db.update_naturalPerson_legal_entity(natural_person_id, legal_entity_id, session["session_id"])
        
        if check is None:
            return ("erro")

    return redirect('/natural_person/list')

def list_naturalPerson():
    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]
    
    new_user = get_hash_user_pid.User(user["family_name"], user["given_name"], user["birth_date"], user["issuing_country"], user["issuing_authority"])
    hash_pid = new_user.hash
    user_id = db.check_user(hash_pid, session["session_id"])

    person_dict = db.get_natural_person_info(user_id, session["session_id"])
    
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
    
    legal_entity_dict = db.get_legal_entity_info(user_id, session["session_id"])
    
    list = []
    if(data != {}):
        if(legal_entity_dict != "err" and legal_entity_dict != None):

            for item in legal_entity_dict:
                name = item["identifier"]

                if(item["naturalperson_id"] != None):
                    person_name = db.get_natural_person_info_le(item["naturalperson_id"], session["session_id"])

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

@rpr.route('/natural_person/list')
def natural_person_list():

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]
        
    menu, data, header_table, list = list_naturalPerson()
        
    return render_template("CertificateList.html", h1 = "Natural Person List", menu = menu, data=data, title="Natural Persons", list= list, header_table=header_table, url=cfgserv.service_url +"natural_person", temp_user_id = temp_user_id)

@rpr.route('/legal_person/create_person', methods=['GET','POST'])
def create_legal_person():

    attributesForm={}

    form_items={
        "Legal Name":"string",
        "Established By Law":"multi_string",
    }
    descriptions = {
        "Legal Name": " Legal name of the legal person",
        "Established By Law": " Legal basis on which the legal person is established",
    }
    attributesForm.update(form_items)

    return render_template("dynamic-form.html",title="Create Legal Person",title_description="Please enter your Legal Person data.", desc = descriptions, countries = cfgserv.eu_countries, lang=cfgserv.eu_languages ,attributes=attributesForm, redirect_url= cfgserv.service_url + "legal_person/add_legal_person_db")

@rpr.route('/legal_person/add_legal_person_db', methods=['GET','POST'])
def add_legal_person_db():

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]

    legal_name = request.form.get("Legal Name")
    established_by_law = request.form.get("Established By Law")
    lang = request.form.get("Lang")

    new_user = get_hash_user_pid.User(user["family_name"], user["given_name"], user["birth_date"], user["issuing_country"], user["issuing_authority"])
    hash_pid = new_user.hash
    user_id = db.check_user(hash_pid, session["session_id"])

    legalBasis = '[{"lang":"' + lang + '", "legalBasis":"' + established_by_law + '"}]'

    db.insert_user_legalPerson(legal_name, legalBasis, user_id, session["session_id"])

    return redirect('/legal_person/list')

@rpr.route('/legal_person/update_legal_entities', methods=["GET", "POST"])
def update_legal_person_entities():
    legal_person_id = request.args.get("id")
    legal_entities = ast.literal_eval(request.args.get("checks"))

    temp_user_id = session['temp_user_id']

    check_legal_entities = db.get_check_legal_entity_info(legal_person_id, session["session_id"]) or []

    previous = { x["legalentity"] for x in check_legal_entities }
    current = { int(x) for x in legal_entities }
    to_remove = previous - current
        
    for elem in to_remove:
        db.remove_legalPerson_legal_entity(elem, session["session_id"])
    
    for elem in legal_entities:
        legal_entity_id = int(elem)

        check = db.update_legalPerson_legal_entity(legal_person_id, legal_entity_id, session["session_id"])
        
        if check is None:
            return ("erro")
    
    return redirect('/legal_person/list')

def list_legalPerson():
    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]

    new_user = get_hash_user_pid.User(user["family_name"], user["given_name"], user["birth_date"], user["issuing_country"], user["issuing_authority"])
    hash_pid = new_user.hash
    user_id = db.check_user(hash_pid, session["session_id"])
    
    person_dict = db.get_legal_person_info(user_id, session["session_id"])

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

    legal_entity_dict = db.get_legal_entity_info(user_id, session["session_id"])
    
    list = []
    if(data != {}):
        if(legal_entity_dict != "err" and legal_entity_dict != None):

            for item in legal_entity_dict:
                name = item["identifier"]
                
                if(item["legalperson_id"] != None):
                    person_name = db.get_legal_person_info_le(item["legalperson_id"], session["session_id"])
                    
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

@rpr.route('/legal_person/list')
def legal_person_list():

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]
        
    menu, data, header_table, list = list_legalPerson()

    return render_template("CertificateList.html", h1 = "Legal Person List", list = list, menu = menu, data=data, title="Legal Persons", header_table=header_table, url=cfgserv.service_url +"legal_person", temp_user_id = temp_user_id)

@rpr.route('/legal_entity/create_person', methods=['GET','POST'])
def create_legal_entity():                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         

    attributesForm={}

    form_items={
        "Type of Identifier":"select",
        "Identifier":"string",
        "Country": "select",
        "Contact": "contact",
        "Information URI":"string",
    }
    descriptions = {
        "Country": "Country in which the Legal Entity is established.",
        "Type of Identifier":"Type of the identifier specified by a URI according to RFC3986",
        "Identifier": "Identifier wich identifies the legal entity.",
        "Contact": "Contact details (address, e-mail and phone number) of the legal entity.",
        "Information URI": "Information and support URI from the legal entity.",
    }
    attributesForm.update(form_items)

    select_dict={
        "Country":list(cfgserv.eu_countries),
        "Type of Identifier":["http://data.europa.eu/eudi/id/EORI-No",
                            "http://data.europa.eu/eudi/id/LEI" ,
                            "http://data.europa.eu/eudi/id/EUID" ,
                            "http://data.europa.eu/eudi/id/VATIN"  ,
                            "http://data.europa.eu/eudi/id/TIN" ,
                            "http://data.europa.eu/eudi/id/Excise"]
    }

    return render_template("dynamic-form.html", title="Create Legal Entity",title_description="Please enter your Legal Entity data.", desc = descriptions, countries = cfgserv.eu_countries ,attributes=attributesForm, select_dict=select_dict, redirect_url= cfgserv.service_url + "legal_entity/add_legal_entity_db")

@rpr.route('/legal_entity/add_legal_entity_db', methods=['GET','POST'])
def add_legal_entity_db():

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]
    
    type_of_identifier= request.form.get("Type of Identifier")
    identifier= request.form.get("Identifier")
    address=request.form.get("address")
    email=request.form.get("email")
    phone_number=request.form.get("phone_number")
    information_URI=request.form.get("Information URI")
    country=request.form.get("Country")

    new_user = get_hash_user_pid.User(user["family_name"], user["given_name"], user["birth_date"], user["issuing_country"], user["issuing_authority"])
    hash_pid = new_user.hash
    user_id = db.check_user(hash_pid, session["session_id"])

    db.insert_legal_entity(address, country, email, phone_number, information_URI, identifier, type_of_identifier, user_id, session["session_id"]) 
    
    return redirect('/legal_entity/list')

@rpr.route('/legal_entity/edit', methods=["GET", "POST"])
def legal_entity_edit():
    
    if not request.args.get("id"):
        return ""
    
    legal_entity_id = request.args.get("id")

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]

    db_data = db.get_legal_entity_info_edit(legal_entity_id, session["session_id"])

    select_dict = {
        "identifierType": [
            "http://data.europa.eu/eudi/id/EORI-No",
            "http://data.europa.eu/eudi/id/LEI" ,
            "http://data.europa.eu/eudi/id/EUID" ,
            "http://data.europa.eu/eudi/id/VATIN"  ,
            "http://data.europa.eu/eudi/id/TIN" ,
            "http://data.europa.eu/eudi/id/Excise"
        ]
    }

    return render_template("dynamic-form_edit_add.html", h3 = "Legal Entity Information", id = legal_entity_id, select_dict = select_dict, lang = cfgserv.eu_languages, data_edit = db_data, Langs=cfgserv.eu_languages,Countries=cfgserv.eu_countries, temp_user_id=temp_user_id, redirect_url= cfgserv.service_url + "legal_entity/edit_db")

@rpr.route('/legal_entity/edit_db', methods=["GET", "POST"])
def legal_entity_edit_db():

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]

    legal_entity_id = request.form.get("id")

    form = dict(request.form)
    form.pop("proceed")
    grouped = defaultdict(list)

    for key, value in form.items():
        grouped[key] = value

    check = db.update_legal_entity_edit(
        grouped, 
        legal_entity_id, 
        session["session_id"]
    )

    if check is None:
        return ("erro")
    else:
        return redirect('/legal_entity/list')
    
@rpr.route('/legal_entity/update_RPs', methods=["GET", "POST"])
def update_RPs():
    
    legal_entity_id = request.args.get("id")
    RPs = ast.literal_eval(request.args.get("checks"))
    
    temp_user_id = session['temp_user_id']

    check_rp = db.get_check_cred_info(legal_entity_id, session["session_id"]) or []

    previous = { x["wrp_id"] for x in check_rp }
    current = { int(x) for x in RPs }
    to_remove = previous - current

    for elem in to_remove:
        db.remove_legal_entity_wrp(elem, session["session_id"])
    
    for elem in RPs:
        RP_id = int(elem)
        
        check = db.update_wrp_legal_entity(legal_entity_id, RP_id, session["session_id"])
        
        if check is None:
            return ("err")

    return redirect('/legal_entity/list')
    
def list_legalEntity():
    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]
    
    new_user = get_hash_user_pid.User(user["family_name"], user["given_name"], user["birth_date"], user["issuing_country"], user["issuing_authority"])
    hash_pid = new_user.hash
    user_id = db.check_user(hash_pid, session["session_id"])
    
    legal_entity_dict = db.get_legal_entity_info(user_id, session["session_id"])
    
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
    
    RP_dict = db.get_rp_info(user_id, session["session_id"])
    
    list = []
    if(data != {}):
        if(RP_dict != "err" and RP_dict != None):

            for item in RP_dict:
                name_txt = item["tradeName"]

                if(item["supervisorAuthority"] != None):    
                    legal_entity_name = db.get_legal_entity_info_rp(item["supervisorAuthority"], session["session_id"])
                    
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

@rpr.route('/legal_entity/list')
def legal_entity_list():

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]

    menu, data, header_table, list = list_legalEntity()
            
    return render_template("CertificateList.html", h1 = "Legal Entity List", menu = menu, data=data, title="Legal Entities", list= list, header_table=header_table, url=cfgserv.service_url +"legal_entity", temp_user_id = temp_user_id)


@rpr.route('/RP/create_person', methods=['GET','POST'])
def RP_create():

    attributesForm={}

    form_items={
        "Trade Name": "string",
        "Support URI": "string",
        "Services Description": "multi_string",
        "Entitlement": "select",
        "Registry URI":"string",
        "Type of Policy": "select",
        "Policy URI":"string",
        "x5c":"string"
    }
    descriptions = {
        "Trade Name": "Trade name (common name, service name) of the Wallet-Relying Party.",
        "Support URI": "Information and support URI from the legal entity.",
        "Services Description": "Descriptions of the services provided by the Wallet-Relying Party.",
        "Entitlement": "Set of entitlements of the Wallet-Relying Party. ",
        "Registry URI":"URI for the national registry API of the registered Wallet-Relying Party",
        "Type of Policy":"Type of the policy.",
        "Policy URI": "URI where the policy is published.",
        "x5c":"X.509 certificate chains" 
    }

    attributesForm.update(form_items)

    select_dict={
        "Entitlement":["http://data.europa.eu/eudi/entitlement/Service_Provider",
                    "http://data.europa.eu/eudi/entitlement/QEAA_Provider",
                    "http://data.europa.eu/eudi/entitlement/Non_Q_EAA_Provider",
                    "http://data.europa.eu/eudi/entitlement/PUB_EAA_Provider",
                    "http://data.europa.eu/eudi/entitlement/PID_Provider",
                    "http://data.europa.eu/eudi/entitlement/QCert_for_ESeal_Provider",
                    "http://data.europa.eu/eudi/entitlement/QCert_for_ESig_Provider",
                    "http://data.europa.eu/eudi/entitlement/rQSealCDs_Provider",
                    "http://data.europa.eu/eudi/entitlement/rQSigCDs_Provider",
                    "http://data.europa.eu/eudi/entitlement/ESig_ESeal_Creation_Provider"],

        "Type of Policy":["http://data.europa.eu/eudi/policy/trust-service-practice-statement ",
                        "http://data.europa.eu/eudi/policy/terms-and-conditions",
                        "http://data.europa.eu/eudi/policy/privacy-statement",
                        "http://data.europa.eu/eudi/policy/privacy-policy",
                        "http://data.europa.eu/eudi/policy/registration-policy"]

    }
    
    return render_template("dynamic-form.html",title="Create Relying Party",title_description="Please enter your Relying Party data.", desc = descriptions, countries = cfgserv.eu_countries, lang=cfgserv.eu_languages, attributes=attributesForm, select_dict=select_dict, redirect_url= cfgserv.service_url + "RP/add_RP_db")

@rpr.route('/RP/add_RP_db', methods=['GET','POST'])
def add_RP_db():

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]

    trade_name= request.form.get("Trade Name")
    support_URI= request.form.get("Support URI")
    srvDescription_lang=request.form.get("Lang")
    srvDescription=request.form.get("Services Description")
    entitlement= request.form.get("Entitlement")
    registry_uri=request.form.get("Registry URI")
    type_of_policy=request.form.get("Type of Policy")
    policy_uri=request.form.get("Policy URI")
    x5c=request.form.get("x5c")
    
    srvDescription = '[{"lang":"' + srvDescription_lang + '", "srvDescription":"' + srvDescription + '"}]'
    
    new_user = get_hash_user_pid.User(user["family_name"], user["given_name"], user["birth_date"], user["issuing_country"], user["issuing_authority"])
    hash_pid = new_user.hash
    user_id = db.check_user(hash_pid, session["session_id"])

    db.insert_RP(trade_name, support_URI, srvDescription, entitlement, registry_uri, type_of_policy, policy_uri, x5c, user_id, session["session_id"])

    return redirect('/RP/list')

@rpr.route('/RP/edit', methods=["GET", "POST"])
def RP_edit():
    
    if not request.args.get("id"):
        return ""
    
    RP_id = request.args.get("id")

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]

    db_data = db.get_rp_info_edit(RP_id, session["session_id"])

    select_dict = {
        "typePolicy":[
            "http://data.europa.eu/eudi/policy/trust-service-practice-statement ",
            "http://data.europa.eu/eudi/policy/terms-and-conditions",
            "http://data.europa.eu/eudi/policy/privacy-statement",
            "http://data.europa.eu/eudi/policy/privacy-policy",
            "http://data.europa.eu/eudi/policy/registration-policy"
        ]
    }

    return render_template("dynamic-form_edit_add.html", h3 = "Relying Party Information", id = RP_id, select_dict = select_dict, lang = cfgserv.eu_languages, data_edit = db_data, Langs=cfgserv.eu_languages,Countries=cfgserv.eu_countries, temp_user_id=temp_user_id, redirect_url= cfgserv.service_url + "RP/edit_db")

@rpr.route('/RP/edit_db', methods=["GET", "POST"])
def RP_edit_db():

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]

    RP_id = request.form.get("id")

    form = dict(request.form)
    form.pop("proceed")
    grouped = defaultdict(list)

    for key, value in form.items():
        grouped[key] = value

    check = db.update_RP_edit(
        grouped, 
        RP_id, 
        session["session_id"]
    )

    if check is None:
        return ("erro")
    else:
        return redirect('/RP/list')

def wallet_rp_list():
    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]

    new_user = get_hash_user_pid.User(user["family_name"], user["given_name"], user["birth_date"], user["issuing_country"], user["issuing_authority"])
    hash_pid = new_user.hash
    user_id = db.check_user(hash_pid, session["session_id"])
    
    RP_dict = db.get_rp_info(user_id, session["session_id"])
    
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
    
    menu= cfgserv.service_url + "menu"
    
    return menu, data, header_table

@rpr.route('/RP/list', methods=['GET','POST'])
def RP_list():
    
    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]

    menu, data, header_table = wallet_rp_list()
    return render_template("CertificateList.html", h1 = "Relying Party List", menu = menu, data=data, title="Relying Parties", header_table=header_table, url=cfgserv.service_url +"RP", temp_user_id = temp_user_id)

@rpr.route('/intended_use/create_person', methods=['GET','POST'])
def intended_use_create():

    attributesForm={}

    form_items={
        "Purpose": "multi_string",
        "Type of Privacy Policy": "select",
        "Privacy Policy URI": "string",
        "Created at": "full-date",
        "Revoked at": "full-date",
        "Intended Use Identifier": "string"

        
    }
    descriptions = {
        "Purpose": "Purpose of the intended data processing",
        "Type of Policy":"Type of the policy.",
        "Privacy Policy URI": "URI where the policy is published.",
        "Created at": "full-date",
        "Revoked at": "full-date",
        "Intended Use Identifier": "string"
    }

    attributesForm.update(form_items)

    select_dict={
        "Type of Privacy Policy":["http://data.europa.eu/eudi/policy/trust-service-practice-statement ",
                        "http://data.europa.eu/eudi/policy/terms-and-conditions",
                        "http://data.europa.eu/eudi/policy/privacy-statement",
                        "http://data.europa.eu/eudi/policy/privacy-policy",
                        "http://data.europa.eu/eudi/policy/registration-policy"]

    }
    
    return render_template("dynamic-form.html",title="Create Intended Use",title_description="Please enter your Intended Use data.", desc = descriptions, countries = cfgserv.eu_countries ,attributes=attributesForm, select_dict=select_dict, redirect_url= cfgserv.service_url + "/intended_use/add_intended_use_db")

@rpr.route('/intended_use/add_intended_use_db', methods=['GET','POST'])
def add_intended_use_db():

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]
 
    purpose=request.form.get("Purpose")
    purpose_lang=request.form.get("Lang")
    type_policy=request.form.get("Type of Privacy Policy")
    policy_uri=request.form.get("Privacy Policy URI")
    createAt=request.form.get("Created at")
    revokeAt=request.form.get("Revoked at")
    intendedUseIdentifier=request.form.get("Intended Use Identifier")
    
    purpose = '[{"lang":"' + purpose_lang + '", "srvDescription":"' + purpose + '"}]'
    
    new_user = get_hash_user_pid.User(user["family_name"], user["given_name"], user["birth_date"], user["issuing_country"], user["issuing_authority"])
    hash_pid = new_user.hash
    user_id = db.check_user(hash_pid, session["session_id"])

    db.insert_intended_use(createAt, revokeAt, intendedUseIdentifier, type_policy, policy_uri, purpose, user_id, session["session_id"])

    return redirect('/intended_use/list')

@rpr.route('/intended_use/edit', methods=["GET", "POST"])
def intended_use_edit():
    
    if not request.args.get("id"):
        return ""
    
    intended_use_id = request.args.get("id")

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]

    db_data = db.get_iu_info_edit(intended_use_id, session["session_id"])

    select_dict = {
        "type_policy": [
            "http://data.europa.eu/eudi/policy/trust-service-practice-statement",
            "http://data.europa.eu/eudi/policy/terms-and-conditions",
            "http://data.europa.eu/eudi/policy/privacy-statement",
            "http://data.europa.eu/eudi/policy/privacy-policy",
            "http://data.europa.eu/eudi/policy/registration-policy"
        ]
    }

    return render_template("dynamic-form_edit_add.html", h3 = "Intended Use Information", id = intended_use_id, select_dict = select_dict, lang = cfgserv.eu_languages, data_edit = db_data, Langs=cfgserv.eu_languages,Countries=cfgserv.eu_countries, temp_user_id=temp_user_id, redirect_url= cfgserv.service_url + "intended_use/edit_db")

@rpr.route('/intended_use/edit_db', methods=["GET", "POST"])
def intended_use_edit_db():

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]

    intended_use_id = request.form.get("id")

    form = dict(request.form)
    form.pop("proceed")
    grouped = defaultdict(list)

    for key, value in form.items():
        grouped[key] = value

    check = db.update_iu_edit(
        grouped, 
        intended_use_id, 
        session["session_id"]
    )

    if check is None:
        return ("erro")
    else:
        return redirect('/intended_use/list')
    
def list_intended_use():

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]
    
    new_user = get_hash_user_pid.User(user["family_name"], user["given_name"], user["birth_date"], user["issuing_country"], user["issuing_authority"])
    hash_pid = new_user.hash
    user_id = db.check_user(hash_pid, session["session_id"])
    
    intended_use_dict = db.get_intended_use_info(user_id, session["session_id"])
    
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
    
    wrp_dict = db.get_rp_info(user_id, session["session_id"])

    list = []
    if(data != {}):
        if(wrp_dict != "err" and wrp_dict != None):

            for item in wrp_dict:
                name_txt = item["tradeName"]
                
                if(item["intended_use"] != None):
                    intended_use_name = db.get_iu_info_rp(item["intended_use"], session["session_id"])
                    
                    new_item = {
                        "id": item["wrp_id"],
                        "name": name_txt,
                        "associated_id": item["intended_use"],
                        "ass_name": intended_use_name
                    }
                else:
                    new_item = {
                        "id": item["wrp_id"],
                        "name": name_txt,
                        "associated_id": item["intended_use"],
                        "ass_name": ""
                    }
                
                list.append(new_item)
    
    menu= cfgserv.service_url + "menu"

    return menu, data, header_table, list

@rpr.route('/intended_use/update_RPs', methods=["GET", "POST"])
def update_RPs_iu():
    
    iu_id = request.args.get("id")
    RPs = ast.literal_eval(request.args.get("checks"))
    
    temp_user_id = session['temp_user_id']

    check_rp = db.get_check_rp_info_iu(iu_id, session["session_id"]) or []

    previous = { x["wrp_id"] for x in check_rp }
    current = { int(x) for x in RPs }
    to_remove = previous - current

    for elem in to_remove:
        db.remove_iu_wrp(elem, session["session_id"])
    
    for elem in RPs:
        RP_id = int(elem)
        
        check = db.update_wrp_iu(iu_id, RP_id, session["session_id"])
        
        if check is None:
            return ("err")
    
    return redirect('/intended_use/list')

@rpr.route('/intended_use/list', methods=['GET','POST'])
def intended_use_list():

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]

    menu, data, header_table, list = list_intended_use()

    return render_template("CertificateList.html", h1 = "Intended Use List", menu = menu, data=data, title="Intended Uses", list= list, header_table=header_table, url=cfgserv.service_url +"intended_use", temp_user_id = temp_user_id)

@rpr.route('/credential/create_person', methods=['GET','POST'])
def credential_create():

    attributesForm={}

    form_items={
        "Name": "string",
        "Format": "string",
        "Meta": "string",
        "Path": "string",
        "Credential Values": "string",
    }
    descriptions = {
        "Name": "string",
        "Format": "Format of the attestation.",
        "Meta":"An object defining additional properties requested by the Verifier (including the credential type) that apply to the metadata and validity data of the Credential",
        "Path": "string",
        "Credential Values": "string"
    }

    attributesForm.update(form_items)

    select_dict={}
    
    return render_template("dynamic-form.html",title="Create Intended Use",title_description="Please enter your Intended Use data.", desc = descriptions, countries = cfgserv.eu_countries ,attributes=attributesForm, select_dict=select_dict, redirect_url= cfgserv.service_url + "/credential/add_credential_db")

@rpr.route('/credential/add_credential_db', methods=['GET','POST'])
def add_credential_db():

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]

    name=request.form.get("Name")
    format=request.form.get("Format")
    meta=request.form.get("Meta")
    path=request.form.get("Path")
    credentialValues=request.form.get("Credential Values")
    
    new_user = get_hash_user_pid.User(user["family_name"], user["given_name"], user["birth_date"], user["issuing_country"], user["issuing_authority"])
    hash_pid = new_user.hash
    user_id = db.check_user(hash_pid, session["session_id"])

    db.insert_credential(name, format, meta, path, credentialValues, user_id, session["session_id"])

    return redirect('/credential/list')

def cred_list():

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]
    
    new_user = get_hash_user_pid.User(user["family_name"], user["given_name"], user["birth_date"], user["issuing_country"], user["issuing_authority"])
    hash_pid = new_user.hash
    user_id = db.check_user(hash_pid, session["session_id"])
    
    credential_dict = db.get_credential_info(user_id, session["session_id"])
    
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
    
    ie_dict = db.get_intended_use_info(user_id, session["session_id"])

    list = []
    if(data != {}):
        if(ie_dict != "err" and ie_dict != None):

            for item in ie_dict:
                name_txt = item["intendedUseIdentifier"]
                
                if(item["credential_id"] != None):
                    credential_name = db.get_iu_info_cred(item["credential_id"], session["session_id"])
                    
                    new_item = {
                        "id": item["intendeduse_id"],
                        "name": name_txt,
                        "associated_id": item["credential_id"],
                        "ass_name": credential_name
                    }
                else:
                    new_item = {
                        "id": item["intendeduse_id"],
                        "name": name_txt,
                        "associated_id": item["credential_id"],
                        "ass_name": ""
                    }
                
                list.append(new_item)
   
    menu= cfgserv.service_url + "menu"

    return menu, data, header_table, list

@rpr.route('/credential/list', methods=['GET','POST'])
def credential_list():
    temp_user_id = session['temp_user_id']

    menu, data, header_table, list = cred_list()

    return render_template("CertificateList.html", h1 = "Credential List", menu = menu, data=data, title="Credentials", list= list, header_table=header_table, url=cfgserv.service_url +"credential", temp_user_id = temp_user_id)

@rpr.route('/credential/update_intended_uses', methods=["GET", "POST"])
def update_intended_uses():
    
    cred_id = request.args.get("id")
    iu = ast.literal_eval(request.args.get("checks"))
    
    temp_user_id = session['temp_user_id']

    check_iu = db.get_check_iu_info(cred_id, session["session_id"]) or []

    previous = { x["intendeduse_id"] for x in check_iu }
    current = { int(x) for x in iu }
    to_remove = previous - current

    for elem in to_remove:
        db.remove_cred_iu(elem, session["session_id"])
    
    for elem in iu:
        RP_id = int(elem)
        
        check = db.update_iu_cred(cred_id, RP_id, session["session_id"])
        
        if check is None:
            return ("err")

    return redirect('/credential/list')
    

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

    return render_template('downloadPage.html', attributes=certificate_presentation, download_url= "/Download/"+ file_name)

@rpr.route("/Download/<name>", methods=["GET", "POST"])
def download(name):

    p12_file_bytes=p12_temp[name]["response"]

    final_name = name.split("_")[0] + ".p12"
    
    extra = {'code': session["session_id"]} 
    logger.info(f"Download p12.", extra=extra)

    return send_file(io.BytesIO(p12_file_bytes),download_name=final_name,as_attachment=True)

def certificate_List(temp_user_id):

    user=session[temp_user_id]

    givenName=user["given_name"]
    surname=user["family_name"]
    birth_date=user["birth_date"]
    issuing_country=user["issuing_country"]
    issuance_authority=user["issuing_authority"]

    new_user = get_hash_user_pid.User(surname, givenName, birth_date, issuing_country, issuance_authority)
    hash_pid = new_user.hash

    user_id=func_get_user_id_by_hash_pid(hash_pid, session["session_id"])

    certificate_data= get_certificate_data(user_id, session["session_id"])

    certificate_data_List.update({temp_user_id:{"certificate_data": certificate_data, "expires":datetime.now() + timedelta(minutes=cfgserv.deffered_expiry)}})

    return render_template('CertificateList.html', certificates=certificate_data, log_id = session["session_id"], redirect_url= cfgserv.service_url, user_id=temp_user_id)


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
