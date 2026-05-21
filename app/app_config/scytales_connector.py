# coding: latin-1
###############################################################################
# Copyright (c) 2026 European Commission
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
This scytales_connector.py contains configuration data for the scytales oauth service. 

NOTE: You should only change it if you understand what you're doing.
"""


from app_config.config import ConfService as cfgserv

class scytales:
    
    name='scytales',
    client_id='WALLET_CONNECTOR_CLIENT_ID'
    client_secret='WALLET_CONNECTOR_CLIENT_SECRET'
    server_metadata_url='https://idp.connector.scytales.dev/.well-known/openid-configuration'
    client_kwargs={
        'scope': 'openid scope:pid_mandatory',  # Request PID / Mobile Driver's License
        'code_challenge_method': 'S256'  # Enable PKCE
    }
    callback = cfgserv.service_url + 'callback'