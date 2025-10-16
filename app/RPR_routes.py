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

import base64
import binascii
from datetime import datetime, timedelta
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

    payload_sameDevice=payload
    session["session_id"]=str(uuid.uuid4())

    payload_sameDevice.update({"wallet_response_redirect_uri_template":cfgserv.service_url +
                                                       "getpidoid4vp?response_code={RESPONSE_CODE}&session_id=" + session["session_id"]})

    response_same_device= requests.request("POST", url, headers=headers, data=json.dumps(payload_sameDevice)).json()

    deeplink_url = (
        "eudi-openid4vp://" + cfgserv.url_verifier + "?client_id="
        + response_same_device["client_id"]
        + "&request_uri="
        + response_same_device["request_uri"]
    )

    oid4vp_requests.update({session["session_id"]:{"response": response_same_device, "expires":datetime.now() + timedelta(minutes=cfgserv.deffered_expiry), "certificate_List":False}})


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
        url_data=deeplink_url,
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

    #check user~
    #user exitir menu
    return redirect(url_for('RPR.menu_RP_user'))
    #user nao existe, criar user
    

@rpr.route("/user_auth", methods=["GET", "POST"])
def user_auth():
    
    temp_user_id = session['temp_user_id']

    #user data
    user_data_pid = session[temp_user_id]

    address = request.form.get('address')
    email = request.form.get('email')
    phone_number = request.form.get('phone_number')
    country = request.form.get('Country')
    identifier= request.form.get("Identifier")
    info_uri = request.form.get("Information URI")

    #introduzir os dados na BD legal entity
    #check = func.user_db_info(role, operator_name, PostalAddress, electronicAddress, user['id'], session["session_id"])

    

    return redirect(url_for('RPR.menu_RP_user'))
    
@rpr.route('/menu_RP_user', methods=['GET','POST'])
def menu_lotl():
    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]
    
    return render_template("rp_user_menu.html", user = user['given_name'], temp_user_id = temp_user_id)

@rpr.route('/create_legal_entity', methods=['GET','POST'])
def legal_entity_add_edit():

    attributesForm={}

    form_items={
        "Identifer":"string",
        "Country": "select",
        "Contact": "contact",
        "Information URI":"string",
    }
    descriptions = {
        "Country": "Country in which the Legal Entity is established.",
        "Identifier": "Identifier wick identifies the legal entity.",
        "Contact": "Contact details (address, e-mail and phone number) of the relying party.",
        "Information URI": "Information and support URI from the legal entity.",
    }
    attributesForm.update(form_items)

    return render_template("dynamic-form.html", desc = descriptions, countries = ejbca.countries ,attributes=attributesForm, redirect_url= cfgserv.service_url + "user_auth")

@rpr.route('/RP_create', methods=['GET','POST'])
def RP_create():

    attributesForm={}

    form_items={
        "Trade Name": "string",
        "Support URI": "string",
        "Services Description": "string",
        "Entitlement": "select",
        "Type of Policy": "select",
        "Policy":"string",
        "Password":"password"
    }
    descriptions = {
        "Trade Name": "Trade name (common name, service name) of the Wallet-Relying Party.",
        "Support URI": "Information and support URI from the legal entity.",
        "Services Description": "Descriptions of the services provided by the Wallet-Relying Party.",
        "Entitlement": "Set of entitlements of the Wallet-Relying Party. ",
        "Type of Policy":"Type of the policy.",
        "Policy URI": "URI where the policy is published.",
        "Password":"Password required for P12 file. "
    }

    attributesForm.update(form_items)
    
    return render_template("dynamic-form.html", desc = descriptions, countries = ejbca.countries ,attributes=attributesForm, redirect_url= cfgserv.service_url + "relying_party_registration_request")

@rpr.route('/RP_list', methods=['GET','POST'])
def RP_list():

    temp_user_id = session['temp_user_id']
    user = session[temp_user_id]
    
    tsl_dict = func.get_tsl_info(user["id"], session["session_id"])
    
    header_table=[ "Version","Sequence Number","TSL Type","Scheme Name","Scheme Territory","Issue Date","Next Update"]
    if(tsl_dict == "err"):
        data={}
    else:

        data={}

        for tsl in tsl_dict:
            data_temp={
                tsl["tsl_id"]:{
                    "Version":tsl["Version"],
                    "Sequence Number":tsl["SequenceNumber"],
                    "TSL Type":tsl["TSLType"],
                    "Scheme Name":tsl["SchemeName_lang"],
                    "Scheme Territory":tsl["schemeTerritory"],
                    "Issue Date":tsl["issue_date"],
                    "Next Update":tsl["next_update"]
                }
            }
            data.update(data_temp)
    
    tsp_dict = func.get_tsp_update(user["id"], session["session_id"])
    
    list = []
    if(data != {}):
        if(tsp_dict != "err"):

            for item in tsp_dict:
                name = json.loads(item["name"])
                
                name_txt = name[0]["text"] if name else "No Name"
                if(item["tsl_id"] != None):
                    tsl_name = func.get_tsl_name(item["tsl_id"], session["session_id"])
                    aux_name = json.loads(tsl_name["SchemeName_lang"])
                    tsl_name = aux_name[0]["text"] if aux_name else "No Name"
                    
                    new_item = {
                        "id": item["tsp_id"],
                        "name": name_txt,
                        "associated_id": item["tsl_id"],
                        "ass_name": tsl_name
                    }
                else:
                    new_item = {
                        "id": item["tsp_id"],
                        "name": name_txt,
                        "associated_id": item["tsl_id"],
                        "ass_name": ""
                    }
                
                list.append(new_item)
    

    menu= cfgserv.service_url + "menu"
    return render_template("CertificateList.html", h1 = "Trusted Service Lists", menu = menu, data=data, title="Trusted Lists", list= list, header_table=header_table, url=cfgserv.service_url +"tsl", temp_user_id = temp_user_id)



@rpr.route("/relying_party_registration_request", methods=["GET", "POST"])
def relying_party_registration():

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
