# Relying Party registration service

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

:heavy_exclamation_mark: **Important!** Before you proceed, please read
the [EUDI Wallet Reference Implementation project description](https://github.com/eu-digital-identity-wallet/.github/blob/main/profile/reference-implementation.md)


## Overview

As per the [European Digital Identity Wallet Architecture and Reference Framework Trust Model](https://github.com/eu-digital-identity-wallet/eudi-doc-architecture-and-reference-framework/blob/main/docs/arf.md#6-trust-model),

+ Relying Parties are registered by a Relying Party Registrar in their Member State.
+ As a result of the registration, a Relying Party receives an access certificate from a Relying Party Access CA.

+ The RP access certificate is used by the Wallet Instance to authenticate the Relying Party Instance.

+ Relying Party authentication is a process whereby a Relying Party proves its identity to a Wallet Instance, in the context of a transaction in which the Relying Party requests the Wallet Instance to release some attributes.
+ Relying Party authentication is included in the protocol used (both in ISO/IEC 18013-5 and OpenID4VP) by a Wallet Instance and a Relying Party Instance to communicate. 



The Relying Party Registration Service provides two main functionalities:

+ Register a new Relying Party, issuing the Relying Party Instance certificate and keypair in pkcs#12 (P12) format.
+ List the certificates issued and enable their revocation.

For registering a new Relying Party, the relying party is asked to provide the following information:

+ Country in which the relying party is established
+ Name of the relying party as stated in an official record 
+ Common Name of the Relying Party, in a format suitable for presenting to an end-user
+ Registration number as stated in an official record together with identification data of that official record;
+ Contact details (address, e-mail and phone number) of the relying party 
+ Intended use of European Digital Identity Wallets, including an indication of the data to be requested by the relying party from users. (max of 500 chars)
+ Password to secure the private key

After the register information is provided, the Relying Party Access CA issues automatically the Relying Party instance certificate, and the user downloads the Relying Party Instance certificate and keypair in P12 format.


You can use the Relying Party registration service at https://registry.serviceproviders.eudiw.dev/, or install it locally.


## :heavy_exclamation_mark: Disclaimer

The released software is a initial development release version:

-   The initial development release is an early endeavor reflecting the efforts of a short timeboxed
    period, and by no means can be considered as the final product.
-   The initial development release may be changed substantially over time, might introduce new
    features but also may change or remove existing ones, potentially breaking compatibility with your
    existing code.
-   The initial development release is limited in functional scope.
-   The initial development release may contain errors or design flaws and other problems that could
    cause system or other failures and data loss.
-   The initial development release has reduced security, privacy, availability, and reliability
    standards relative to future releases. This could make the software slower, less reliable, or more
    vulnerable to attacks than mature software.
-   The initial development release is not yet comprehensively documented.
-   Users of the software must perform sufficient engineering and additional testing in order to
    properly evaluate their application and determine whether any of the open-sourced components is
    suitable for use in that application.
-   We strongly recommend not putting this version of the software into production use.
-   Only the latest version of the software will be supported



## Installation

Pre-requisites:

  + Python v. 3.9 or 3.10
  + Flask v. 2.3 or higher

Steps: 

1. Enter the project folder

  ```shell
  cd eudi-srv-web-relyingparty-registration-py
  ```

2. Create .venv to install flask and other libraries

  Windows:
  
  ```shell
  python -m venv .venv 
  ```
  
  Linux:

  ```shell
  python3 -m venv .venv
  ```

3. Activate the environment

  windows:
    
  ```shell
  . .venv\Scripts\Activate
  ```
    
  Linux:
  
  ```shell
  . .venv/bin/activate
  ```
    
4. Install the necessary libraries to run the code

  ```shell
  pip install -r app/requirements.txt
  ```

5. Run the Project
  ```shell
  flask --app app run
  ```

## Run

### 1. Database
     
To create the database use the app/relying_party_reg.sql file. It has been tested with MariaDB version 11.5.
  
The file app/app_config/database.py is used to configure the data needed to connect to the database.

### 2. EJBCA
  
The service needs a connection to an EJBCA (<https://www.ejbca.org/>) instance, in order to issue the certificates.
The configuration file for defining access credentials and the location of the admin's PKCS#12 Keystore file and its corresponding password can be found at app/app_config/EJBCA_config.py.

### 3. Initial Page

The initial Page of the Relying Party Registration Service (<http://127.0.0.1:5000/> or <http://localhost:5000/>) presents one options:

+ Guide: <http://localhost:5000/guide>
    
#### 3.1. (optional) Integrate with EUDI Verifier Endpoint
  
To integrate with the [EUDI Verifier Endpoint to mount an external keystore to be used with Authorization Request signing in](https://github.com/eu-digital-identity-wallet/eudi-srv-web-verifier-endpoint-23220-4-kt?tab=readme-ov-file#mount-external-keystore-to-be-used-with-authorization-request-signing), please use the following command line to convert the downloaded pkcs#12 file to a JKS file:

```shell
keytool -importkeystore -srckeystore [FileIn.p12] -srcstoretype pkcs12 -destkeystore [FileOUT.jks] -deststoretype jks -deststorepass [passwordJKS] 
```

+ FileIn.p12 - .p12 file generated in Relying Party Registration
+ FileOUT.jks - Path to the keystore
+ passwordJKS - password for .jks file (minimum 6 characters)

## Run docker

To start Web Relying Party Registration service a docker compose file, [docker-compose.yml](docker/docker-compose.yml), has been implemented that can be found in `docker` directory.

To start the docker compose environment

```
# From project root directory 
cd docker
docker-compose up -d
```

To stop the docker compose environment

```
# From project root directory 
cd docker
docker-compose down
````

## Configuration

The Web Relying Party Registration application can be configured using the following environment variables:

Variable: `SERVICE_URL`<br>
Description: Application service url

Variable: `TRUSTED_CAS_PATH`<br>
Description: Container path where CA certificates are located for validate vp_token when doing PID login

Variable: `VERIFIER`<br>
Description: Verifier URL

Variable: `LOG_PATH`<br>
Description: Path where log files are saved

Variable: `CERT`<br>
Description: Container path where the XML signing certificate is stored

Variable: `PRIV_KEY`<br>
Description: Container path where the private key of the XML signing certificate is stored

Variable: `DB_HOST`<br>
Description: Database URL

Variable: `DB_PORT`<br>
Description: Port where Database is running

Variable: `DB_USER`<br>
Description: Username of Database user

Variable: `DB_PASSWORD`<br>
Description: Password of Database user

Variable: `DB_NAME`<br>
Description: Name of Database

Variable: `ca_host`<br>
Description: EJBCA URL

Variable: `clienteP12ArchiveFilepath`<br>
Description: Client P12 file to acess EJBCA

Variable: `managementCA`<br>
Description: EJBCA Management CA

Variable: `clienteP12ArchivePassword`<br>
Description: Cliente P12 password to acess EJBCA

Variable: `EJBCA_username`<br>
Description: Username of EJBCA user

Variable: `EJBCA_password`<br>
Description: Password of EJBCA user

Variable: `certificateProfileName`<br>
Description: Name of the profile defined in the EJBCA application

Variable: `endEntityProfileName`<br>
Description: Name of the End Entity Profile defined in the EJBCA application


# User Interface (HTTP Requests)

This project also provides a simple HTTP-based interface, allowing the service to be accessed through direct HTTP requests instead of a graphical user interface.

To simplify interaction with the available endpoints, the project includes Swagger API documentation, which can be accessed through the following route:

```code
/apidocs
```

The Swagger interface provides detailed information about all available endpoints, including:

  * Endpoint descriptions
  * Required parameters
  * Request body structures
  * Example requests and responses

This allows developers and users to easily explore and test the API.

Additionally, a usage guide is available at the following route:

``` code
/guide
```

This page contains explanations on how to correctly use the different endpoints, including recommended request formats and practical examples.

# Authentication Flow

The API uses an authentication flow based on OID4VP and PID verification.

The authentication process works as follows:

1. Start the authentication flow and obtain a QR Code and `presentation_id`
2. Wait for PID authorization validation
3. Retrieve the authenticated user's `hash_pid`
4. Use the `hash_pid` in authenticated endpoints

---

## Authentication Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/authentication` | Start authentication flow and generate QR Code |
| GET | `/pid_authorization` | Validate PID authorization status |
| GET / POST | `/getpidoid4vp` | Retrieve PID data and obtain `hash_pid` |

---

## Authentication Flow Description

### 1. `/authentication`

Starts the authentication process.

Returns:
- QR Code for wallet authentication
- `presentation_id`

The QR Code must be scanned by the user's wallet application.

---

### 2. `/pid_authorization`

Checks whether the PID authorization was completed successfully.
This endpoint waits for the authentication result and validates the received PID authorization.

---

### 3. `/getpidoid4vp`

Retrieves the PID data obtained through the OID4VP flow.

Returns:
- User PID information
- Generated `hash_pid`

The returned `hash_pid` must be used in authenticated API requests.

---

## Example Authenticated Request

```json
{
  "hash_pid": "abc123hash"
}
```

# Endpoint Overview
---

## Identifier Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/identifier/create` | Create identifiers |
| POST | `/identifier/list` | Retrieve identifiers |

---

## Law Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/law/create` | Create laws |
| POST | `/law/list` | Retrieve laws |

---

## Natural Person Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/natural_person/create` | Create natural persons |
| POST | `/natural_person/list` | Retrieve natural persons |

---

## Legal Person Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/legal_person/create` | Create legal persons |
| POST | `/legal_person/list` | Retrieve legal persons |
| POST | `/legal_person/update_law` | Associate laws with legal persons |
| POST | `/legal_person/remove_law` | Remove laws from legal persons |

---

## Legal Entity Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/legal_entity/create` | Create legal entities |
| POST | `/legal_entity/list` | Retrieve legal entities |
| POST | `/legal_entity/update_identifier` | Associate identifiers |
| POST | `/legal_entity/remove_identifier` | Remove identifiers |

---

## Policy Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/policy/create` | Create policies |
| POST | `/policy/list` | Retrieve policies |

---

## Provider Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/provider/create` | Create providers |
| POST | `/provider/list` | Retrieve providers |
| POST | `/provider/update_policy` | Associate policies with providers |
| POST | `/provider/remove_policy` | Remove policies from providers |

---

## Credential Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/credential/create` | Create credentials |
| POST | `/credential/list` | Retrieve credentials |
| POST | `/list_claim` | Retrieve claims |

---

## Intended Use Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/intended_use/create` | Create intended uses |
| POST | `/intended_use/list` | Retrieve intended uses |
| POST | `/intended_use/update_credential` | Associate credentials |
| POST | `/intended_use/update_policy` | Associate policies |
| POST | `/intended_use/remove_credential` | Remove credentials |
| POST | `/intended_use/remove_policy` | Remove policies |

---

## Provided Attestation Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/provided_attestation/create` | Create provided attestations |
| POST | `/provided_attestation/list` | Retrieve provided attestations |

---

## Supervisory Authority Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/supervisory_authority/create` | Create supervisory authorities |
| POST | `/supervisory_authority/list` | Retrieve supervisory authorities |

---

## Wallet Relying Party Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/wallet_rp/create` | Create Wallet Relying Parties |
| POST | `/wallet_rp/list` | Retrieve Wallet Relying Parties |
| POST | `/wallet_rp/update_intended_use` | Associate intended uses |
| POST | `/wallet_rp/update_provided_attestation` | Associate provided attestations |
| POST | `/wallet_rp/update_uses_intermediary` | Associate intermediary WRPs |
| POST | `/wallet_rp/remove_intended_use` | Remove intended uses |
| POST | `/wallet_rp/remove_provided_attestation` | Remove provided attestations |
| POST | `/wallet_rp/remove_uses_intermediary` | Remove intermediary WRPs |

---

## Public Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/wrp` | Search Wallet Relying Parties |
| GET | `/wrp/<identifier>` | Retrieve Wallet Relying Party by identifier |
| GET | `/wrp/check-intended-use` | Validate intended use compatibility |

---

## Utility Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/list_full_info` | Retrieve complete hierarchical user information |

## Certificates

| Method | Endpoint | Description |
|---|---|---|
| POST | `/intended_use/certificate` | Generate Intended Use Registration Certificate |
| POST | `/wallet_rp/certificate` | Generate Wallet Relying Party Access Certificate |





## How to contribute

We welcome contributions to this project. To ensure that the process is smooth for everyone
involved, follow the guidelines found in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

### License details

Copyright (c) 2024 European Commission

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
