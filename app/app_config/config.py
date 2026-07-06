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
This config.py contains configuration data for the age-over-poc Web service. 

NOTE: You should only change it if you understand what you're doing.
"""

import logging
from logging.handlers import TimedRotatingFileHandler
import os
import random
from flask import  session
import logging
from logging.handlers import TimedRotatingFileHandler


class ConfService:

    secret_key = os.urandom(32).hex()

    #service_url = "http://127.0.0.1:5000/"
    service_url = os.getenv("SERVICE_URL","https://registry.serviceproviders.eudiw.dev/")

    #trusted_CAs_path = "app\certs"
    trusted_CAs_path = os.getenv("TRUSTED_CAS_PATH","/etc/eudiw/pid-issuer/cert/")

    deffered_expiry = 100

    log_dir = "app\logs"
    #log_dir = os.getenv("LOG_PATH", "app/logs")

    url_verifier=os.getenv("VERIFIER","verifier-backend.eudiw.dev")

    eu_languages = [
        "bg", "cs", "da", "de", "el", "en", "es", "et", "fi", "fr",
        "ga", "hr", "hu", "it", "lt", "lv", "mt", "nl", "pl", "pt",
        "ro", "sk", "sl", "sv"]

    eu_countries = [
        "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
        "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
        "PL", "PT", "RO", "SK", "SI", "ES", "SE","UT", "EU"]
    
    legal_entity_type_identifier={
        "Country":list(eu_countries),
        "Type of Identifier":["http://data.europa.eu/eudi/id/EORI-No",
                            "http://data.europa.eu/eudi/id/LEI" ,
                            "http://data.europa.eu/eudi/id/EUID" ,
                            "http://data.europa.eu/eudi/id/VATIN"  ,
                            "http://data.europa.eu/eudi/id/TIN" ,
                            "http://data.europa.eu/eudi/id/Excise"]
    }

    relying_party={
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

        "Type of Policy":["http://data.europa.eu/eudi/policy/trust-service-practice-statement",
                        "http://data.europa.eu/eudi/policy/terms-and-conditions",
                        "http://data.europa.eu/eudi/policy/privacy-statement",
                        "http://data.europa.eu/eudi/policy/privacy-policy",
                        "http://data.europa.eu/eudi/policy/registration-policy"]
    }

    intended_use={
        "Type of Privacy Policy":["http://data.europa.eu/eudi/policy/trust-service-practice-statement",
                        "http://data.europa.eu/eudi/policy/terms-and-conditions",
                        "http://data.europa.eu/eudi/policy/privacy-statement",
                        "http://data.europa.eu/eudi/policy/privacy-policy",
                        "http://data.europa.eu/eudi/policy/registration-policy"]
    }

    sca_signer_url= os.getenv("SCA_SIGNER_URL", "http://localhost:8086")

    url_statuslist= os.getenv("URL_STATUSLIST", "tthps://dev.issuer.eudiw.dev/token_status_list/take")

    wrprc_privateKey = os.getenv("WRPRC_PRIVATEkEY", "app/EJBCA/ecdsa_key.pem")

    wrprc_certificate = os.getenv("WRPRC_CERTIFICATE", "app/EJBCA/ecdsa_cert.pem")
    

    # log_dir = "/tmp/log"
    # #log_dir = "../../log"
    # log_file_info = "logs.log"

    # backup_count = 7

    # log_handler_info = TimedRotatingFileHandler(
    #     filename=f"{log_dir}/{log_file_info}",
    #     when="midnight",  # Rotation midnight
    #     interval=1,  # new file each day
    #     backupCount=backup_count,
    # )

    # log_handler_info.setFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")

    # logger_info = logging.getLogger("info")
    # logger_info.addHandler(log_handler_info)
    # logger_info.setLevel(logging.INFO)