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
This EJBCA_config.py contains configuration data for the EJBCA service. 

NOTE: You should only change it if you understand what you're doing.
"""

import logging
from logging.handlers import TimedRotatingFileHandler
import os
from flask import  session

from .config import ConfService as cfgserv

class EJBCA_Config:

    cahost=os.getenv("cahost")
    clientP12ArchiveFilepath=os.getenv("clientP12ArchiveFilepath")
    clientP12ArchivePassword=os.getenv("clientP12ArchivePassword")
    managementCA=os.getenv("managementCA")

    # Endpoint:
    endpoint= "/certificate/pkcs10enroll"
    # Values required by the endpoint "/pkcs10enroll":
    certificateProfileName= os.getenv("certificateProfileName")
    endEntityProfileName= os.getenv("endEntityProfileName")

    avCertificateProfile="mDL_Reader_Auth_AgeV_ISO_18013-7"
    avEndEntityProfile="IACA_AgeV-mdocReader_ISO-18013-7"


    username=os.getenv("EJBCA_username")
    password=os.getenv("EJBCA_password")
    includeChain= True

    countries={
      "CZ":"PID Issuer CA - CZ 02",
      "EE":"PID Issuer CA - EE 02",
      "EU":"PID Issuer CA - EU 02",
      "LU":"PID Issuer CA - LU 02",
      "NL":"PID Issuer CA - NL 02",
      "PT":"PID Issuer CA - PT 02",
      "UT":"PID Issuer CA - UT 02",
      "AV":"Age Verification Issuer CA 01"
    }

