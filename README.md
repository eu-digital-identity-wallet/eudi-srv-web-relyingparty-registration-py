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

The initial Page of the Relying Party Registration Service (<http://127.0.0.1:5000/> or <http://localhost:5000/>) presents two options:

+ Register Relying Party : <http://localhost:5000/authentication>
+ User's Certificate List:  <http://localhost:5000/authentication_List>

#### 3.1. Register Relying Party

+ First step is authentication with the PID
+ After authentication, the user must enter the Relying Party details.
+ Once the Relying Party is registered, the user downloads a pkcs#12 (.p12) file containing the private key and the certificate for the Relying Party, encrypted with the password set when entering the Relying Party details.
    
#### 3.1.1. (optional) Integrate with EUDI Verifier Endpoint
  
To integrate with the [EUDI Verifier Endpoint to mount an external keystore to be used with Authorization Request signing in](https://github.com/eu-digital-identity-wallet/eudi-srv-web-verifier-endpoint-23220-4-kt?tab=readme-ov-file#mount-external-keystore-to-be-used-with-authorization-request-signing), please use the following command line to convert the downloaded pkcs#12 file to a JKS file:

```shell
keytool -importkeystore -srckeystore [FileIn.p12] -srcstoretype pkcs12 -destkeystore [FileOUT.jks] -deststoretype jks -deststorepass [passwordJKS] 
```

+ FileIn.p12 - .p12 file generated in Relying Party Registration
+ FileOUT.jks - Path to the keystore
+ passwordJKS - password for .jks file (minimum 6 characters)

#### 3.2. Certificate List

+ First step is authentication with the PID 
+ After authentication, the user has access to all their certificates and has the option to revoke any certificate they hold by clicking the "Revoke" button.

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

This project also provides a simple HTTP-based user interface, allowing the service to be used through direct requests instead of a graphical user interface.

To facilitate the interaction with the available endpoints, the project includes Swagger API documentation, which can be accessed through the following route:

``` code
/apidocs/
```

The Swagger interface provides detailed information about all available endpoints, including:
  * Endpoint descriptions
  * Required parameters
  * Request body structure
  * Example requests and responses

This allows developers and users to easily explore and test the API.

Additionally, a usage guide will be available at the following route:

``` code
/guide
```

This page will contain an explanation on how to correctly use the different endpoints, including recommended request formats and practical examples.

## Create a Natural Person

This route is responsible for creating and storing a new Natural Person in the system.

### Endpoint
``` code
/natural_person/add_natural_person_db
```

### Arguments
| Name          | Type   | Description                         |
| ------------- | ------ | ----------------------------------- |
| `hash_pid`    | string | User identifier (from wallet login) |
| `given_name`  | string | Given name of the natural person    |
| `family_name` | string | Family name of the natural person   |
| `birthdate`   | string | Date of birth (YYYY-MM-DD)          |
| `birthplace`  | string | Place of birth                      |



### Example
``` code
{
  "hash_pid": "<hash_pid>",
  "given_name": "John",
  "family_name": "Doe",
  "birthdate": "1990-05-12",
  "birthplace": "Lisbon"
}

```

### Success Response
``` code
{
  "status": "success",
  "code": 201,
  "message": "Natural Person successfully created.",
  "data": {
    "Natural Person id": 5
  }
}
```

### Missing required fields
``` code
{
  "status": "error",
  "code": 400,
  "message": "Missing required fields.",
  "data": {
    "missing_fields": ["birthplace"]
  }
}
```

### Invalid or missing JSON body
``` code
{
  "status": "error",
  "code": 400,
  "message": "Invalid or missing JSON body"
}
```

### Notes
  * The hash_pid parameter is mandatory.
  * All fields must be provided in the JSON body.
  * The Natural Person is created only if the hash_pid belongs to a valid user.
  * This endpoint uses POST and modifies persistent data.
  * Query parameters are not supported for this endpoint.

## Create a Legal Person

This route is responsible for creating and storing a new Legal Person in the system.

### Endpoint
``` code
/legal_person/add_legal_person_db
```

### Arguments
| Name                 | Description                                |
| -------------------- | ------------------------------------------ |
| `hash_pid`           | User identifier (from wallet login)        |
| `legal_name`         | Legal name of the entity                   |
| `established_by_law` | Legal basis or law establishing the entity |
| `lang`               | Language of the legal basis                |

### Example Request
``` code
{
  "hash_pid": "<hash_pid>",
  "legal_name": "ACME Corporation",
  "established_by_law": "Commercial Law Article 10",
  "lang": "EN"
}
```

### Success Response
``` code
{
  "status": "success",
  "code": 201,
  "message": "Legal Person successfully created.",
  "data": {
    "legal_person_id": 12
  }
}
```

### Error Responses
#### Missing required fields
``` code
{
  "status": "error",
  "code": 400,
  "message": "Missing required fields.",
  "data": {
    "missing_fields": ["lang"]
  }
}
```

#### Invalid hash_pid
``` code
{
  "status": "error",
  "code": 400,
  "message": "Invalid hash_pid"
}
```

### Notes
  * hash_pid is mandatory when calling via API.
  * All fields must be sent in the JSON body.
  * The Legal Person will only be created if the hash_pid belongs to a valid user.
  * The legal basis is internally stored as JSON array:


## Create a Legal Entity

This route is responsible for creating and storing a new Legal Entity in the system.

### Endpoint
``` code
/legal_entity/add_legal_entity_db
```

### Arguments
| Name                 | Description                         |
| -------------------- | ----------------------------------- |
| `hash_pid`           | User identifier (from wallet login) |
| `type_of_identifier` | Type of legal entity identifier     |
| `identifier`         | Identifier value                    |
| `address`            | Postal address                      |
| `email`              | Contact email                       |
| `phone_number`       | Contact phone number                |
| `information_URI`    | Information URI                     |
| `country`            | Country code                        |

### Example Request
``` code
{
  "hash_pid": "<hash_pid>",
  "type_of_identifier": "VAT",
  "identifier": "123456789",
  "address": "123 Main Street, City, Country",
  "email": "contact@acme.com",
  "phone_number": "+123456789",
  "information_URI": "https://acme.com/info",
  "country": "US"
}
```

### Success Response
``` code
{
  "status": "success",
  "code": 201,
  "message": "Legal Entity successfully created.",
  "data": {
    "legal_entity_id": 15
  }
}
```

### Error Responses
#### Missing required fields
``` code
{
  "status": "error",
  "code": 400,
  "message": "Missing required fields.",
  "data": {
    "missing_fields": ["email", "country"]
  }
}
```

#### Invalid hash_pid
``` code
{
  "status": "error",
  "code": 400,
  "message": "Invalid hash_pid",
  "data": {
    "hash_pid": "<hash_pid>"
  }
}
```

### Notes
  * hash_pid is mandatory when calling via API.
  * All fields must be sent in the JSON body.
  * The Legal Entity will only be created if the hash_pid belongs to a valid user.


## Create a Relying Party

This route is responsible for creating and storing a new Relying Party.

### Endpoint
``` code
/RP/add_RP_db
```

### Arguments
| Name                  | Description                         |
| --------------------- | ----------------------------------- |
| `hash_pid`            | User identifier (from wallet login) |
| `trade_name`          | Trade name of the relying party     |
| `support_URI`         | Support URI                         |
| `srvDescription_lang` | Language of the service description |
| `srvDescription`      | Service description                 |
| `entitlement`         | Entitlement URI                     |
| `registry_uri`        | Registry URI                        |
| `type_of_policy`      | Type of policy                      |
| `policy_uri`          | Policy URI                          |
| `x5c`                 | Certificate chain (x5c)             |


### Example Request
``` code
{
  "hash_pid": "<hash_pid>",
  "trade_name": "ACME RP Services",
  "support_URI": "https://acme.com/support",
  "srvDescription_lang": "EN",
  "srvDescription": "Provides authentication services for ACME users.",
  "entitlement": "full_access",
  "registry_uri": "https://registry.acme.com",
  "type_of_policy": "Privacy Policy",
  "policy_uri": "https://acme.com/policy",
  "x5c": "MIID...AB"
}
```

### Success Response
``` code
{
  "status": "success",
  "code": 201,
  "message": "Relying Party successfully created.",
  "data": {
    "relying_party_id": 27
  }
}
```

### Error Responses
#### Missing required fields
``` code
{
  "status": "error",
  "code": 400,
  "message": "Missing required fields.",
  "data": {
    "missing_fields": ["trade_name", "x5c"]
  }
}
```

#### Invalid hash_pid
``` code
{
  "status": "error",
  "code": 400,
  "message": "Invalid hash_pid",
  "data": {
    "hash_pid": "<hash_pid>"
  }
}
```

### Notes
  * hash_pid is mandatory when calling via API.
  * All fields must be sent in the JSON body.
  * The Relying Party will only be created if the hash_pid belongs to a valid user.

## Create an Intended Use

This route is responsible for creating and storing a new Intended Use.

### Endpoint
```code
/intended_use/add_intended_use_db
```

### Arguments
| Name                    | Description                                     |
| ----------------------- | ----------------------------------------------- |
| `hash_pid`              | User identifier (from wallet login)             |
| `purpose`               | Purpose of the intended use                     |
| `purpose_lang`          | Language of the purpose description             |
| `type_policy`           | Type of policy governing the intended use       |
| `policy_uri`            | URI to the policy document                      |
| `createAt`              | Timestamp when the intended use was created     |
| `revokeAt`              | Timestamp when the intended use will be revoked |
| `intendedUseIdentifier` | Unique identifier for the intended use          |

### Example Request
```code
{
  "hash_pid": "<hash_pid>",
  "purpose": "Data processing for analytics",
  "purpose_lang": "EN",
  "type_policy": "Privacy Policy",
  "policy_uri": "https://acme.com/privacy-policy",
  "createAt": "2026-02-09T12:00:00Z",
  "revokeAt": "2026-12-31T23:59:59Z",
  "intendedUseIdentifier": "intended_use_001"
}
```

### Success Response
```code
{
  "status": "success",
  "code": 201,
  "message": "Intended Use successfully created.",
  "data": {
    "intended_use_id": 42
  }
}
```

### Error Responses
#### Missing required fields
```code
{
  "status": "error",
  "code": 400,
  "message": "Missing required fields.",
  "data": {
    "missing_fields": ["purpose", "policy_uri"]
  }
}
```

#### Invalid hash_pid
```code
{
  "status": "error",
  "code": 400,
  "message": "Invalid hash_pid",
  "data": {
    "hash_pid": "<hash_pid>"
  }
}
```

### Notes
  * hash_pid is mandatory when calling via API.
  * All fields must be sent in the JSON body.
  * The Intended Use will only be created if the hash_pid belongs to a valid user.

## Create a Credential

This route is responsible for creating and storing a new Credential.

### Endpoint
``` code
/credential/add_credential_db
```

### Arguments
| Name               | Description                                     |
| ------------------ | ----------------------------------------------- |
| `hash_pid`         | User identifier (from wallet login)             |
| `name`             | Name of the credential                          |
| `format`           | Format type of the credential                   |
| `meta`             | Metadata associated with the credential         |
| `path`             | Path or location where the credential is stored |
| `credentialValues` | Values contained within the credential          |

### Example Request
``` code
{
  "hash_pid": "<hash_pid>",
  "name": "Credential name",
  "format": "JSON",
  "meta": "meta",
  "path": "/credentials/cred.json",
  "credentialValues": "credentialValues"
}
```

### Success Response
``` code
{
  "status": "success",
  "code": 201,
  "message": "Credential successfully created.",
  "data": {
    "credential_id": 101
  }
}
```

### Error Responses
#### Missing required fields
``` code
{
  "status": "error",
  "code": 400,
  "message": "Missing required fields.",
  "data": {
    "missing_fields": ["name", "credentialValues"]
  }
}
```

#### Invalid hash_pid
``` code
{
  "status": "error",
  "code": 400,
  "message": "Invalid hash_pid",
  "data": {
    "hash_pid": "<hash_pid>"
  }
}
```

#### General failure
``` code
{
  "status": "error",
  "code": 400,
  "message": "Something went wrong"
}
```

### Notes
  * hash_pid is mandatory when calling via API.
  * All fields must be sent in the JSON body.
  * The Credential will only be created if the hash_pid belongs to a valid user.

## Natural Person – List
This endpoint retrieves all Natural Persons created by the authenticated user, as well as the Legal Entities associated with each Natural Person.

It is intended to be used to:
  * List all Natural Persons owned by the user
  * Identify which Legal Entities are associated with each Natural Person


### Endpoint
``` code
/natural_person/list
```

### Arguments

| Name               | Description                         |
| ------------------ | ----------------------------------- |
| `hash_pid`         | User identifier (from wallet login) |

### Example Request
```code
{
  "hash_pid": "<hash_pid>"
}
```

### Response Fields
#### natural_persons

List of all Natural Persons created by the user.

| Field            | Description               |
| ---------------- | ------------------------- |
| `id`             | Natural Person identifier |
| `given_name`     | Given name                |
| `family_name`    | Family name               |
| `date_of_birth`  | Date of birth             |
| `place_of_birth` | Place of birth            |

#### legal_entities

List of Legal Entities linked to Natural Persons.

| Field            | Description                                                 |
| ---------------- | ----------------------------------------------------------- |
| `id`             | Legal Entity identifier                                     |
| `name`           | Legal Entity name                                           |
| `associated`     | Indicates if the entity is associated with a Natural Person |
| `natural_person` | Natural Person associated with the entity                   |

### Notes

  * The hash_pid parameter is mandatory.

  * Only data owned by the authenticated user is returned.

  * This endpoint does not modify data, it is read-only.


## Legal Person – List

This endpoint retrieves all Legal Persons created by the authenticated user, as well as the Legal Entities associated with each Legal Person.

It is intended to be used to:
  * List all Legal Persons owned by the user
  * Identify which Legal Entities are associated with each Legal Person

## Endpoint
``` code
/legal_person/list
```

## Arguments
| Name       | Description                         |
| ---------- | ----------------------------------- |
| `hash_pid` | User identifier (from wallet login) |

## Example Request
``` code
{
  "hash_pid": "<hash_pid>"
}
```
### Response Fields
#### legal_persons

List of all Legal Persons created by the user.
| Field                | Description                               |
| -------------------- | ----------------------------------------- |
| `legal_name`         | Legal name of the Legal Person            |
| `established_by_law` | Legal basis information (language + text) |

`established_by_law` is an array of objects with the following structure:
| Field        | Description             |
| ------------ | ----------------------- |
| `lang`       | Language code           |
| `legalBasis` | Legal basis description |

#### legal_entities

List of Legal Entities linked to Legal Persons.
| Field          | Description                                               |
| -------------- | --------------------------------------------------------- |
| `id`           | Legal Entity identifier                                   |
| `name`         | Legal Entity name                                         |
| `associated`   | Indicates if the entity is associated with a Legal Person |
| `legal_person` | Legal Person associated with the entity                   |

The `legal_person` object contains:
| Field                | Description             |
| -------------------- | ----------------------- |
| `id`                 | Legal Person identifier |
| `legal_name`         | Legal Person name       |
| `established_by_law` | Legal basis information |

### Notes

  * The hash_pid parameter is mandatory.
  * Only data owned by the authenticated user is returned.
  * This endpoint does not modify data; it is read-only.

## Legal Entity – List

This endpoint retrieves all Legal Entities created by the authenticated user, as well as the Relying Parties associated with each Legal Entity.

It is intended to be used to:
  * List all Legal Entities owned by the user
  * Identify which Relying Parties are associated with each Legal Entity

### Endpoint
``` code
/legal_entity/list
```

### Arguments
| Name       | Description                         |
| ---------- | ----------------------------------- |
| `hash_pid` | User identifier (from wallet login) |

### Example Request
``` code
{
  "hash_pid": "<hash_pid>"
}
```

### Response Fields
#### legal_entities
List of all Legal Entities created by the user.

| Field            | Description             |
| ---------------- | ----------------------- |
| `id`             | Legal Entity identifier |
| `identifier`     | Legal identifier        |
| `postal_address` | Postal address          |
| `email`          | Contact email           |
| `phone`          | Contact phone number    |
| `info_uri`       | Information URI         |
| `country`        | Country code            |

#### relying_parties
List of Relying Parties linked to Legal Entities.

| Field           | Description                                           |
| --------------- | ----------------------------------------------------- |
| `id`            | Relying Party identifier                              |
| `name`          | Relying Party name                                    |
| `associated`    | Indicates if the RP is associated with a Legal Entity |
| `associated_rp` | Associated Wallet Relying Party information           |

The `associated_rp` object contains:
| Field  | Description               |
| ------ | ------------------------- |
| `id`   | Wallet Relying Party ID   |
| `name` | Wallet Relying Party name |

### Notes
  * The hash_pid parameter is mandatory.
  * Only data owned by the authenticated user is returned.
  * This endpoint is read-only and does not modify data.

## Relying Party – List

This endpoint retrieves all Wallet Relying Parties created by the authenticated user, as well as the Intended Uses associated with each Relying Party.

It is intended to be used to:
  * List all Relying Parties owned by the user
  * Identify which Intended Uses are linked to each Relying Party

### Endpoint
``` code
/RP/list
```

### Arguments
| Name       | Description                         |
| ---------- | ----------------------------------- |
| `hash_pid` | User identifier (from wallet login) |

### Example Request
``` code
{
  "hash_pid": "<hash_pid>"
}
```

### Response Fields
#### relying_parties

List of all Wallet Relying Parties created by the user.

| Field                   | Description                            |
| ----------------------- | -------------------------------------- |
| `trade_name`            | Trade name                             |
| `description`           | Service description (language-based)   |
| `entitlement`           | Entitlement URI                        |
| `registry_URI`          | Registry reference URI                 |
| `support_URIs`          | Support contact URIs                   |
| `supervisory_authority` | Supervisory authority identifier       |
| `provides_attestations` | Indicates if attestations are provided |

The `description` field is an array with the following structure:
| Field            | Description              |
| ---------------- | ------------------------ |
| `lang`           | Language code            |
| `srvDescription` | Service description text |

#### intended_uses

List of Intended Uses linked to Relying Parties.
| Field                  | Description                                        |
| ---------------------- | -------------------------------------------------- |
| `id`                   | Intended Use identifier                            |
| `name`                 | Intended Use name                                  |
| `associated`           | Indicates if it is associated with a Relying Party |
| `wallet_relying_party` | Relying Party associated with the Intended Use     |

The `wallet_relying_party` object contains the same structure as described in `relying_parties`.

### Notes
  * The hash_pid parameter is mandatory.
  * Only data owned by the authenticated user is returned.
  * This endpoint is read-only and does not modify data.

## Intended Use – List

This endpoint retrieves all Intended Uses created by the authenticated user.

It is intended to be used to:
* List all Intended Uses owned by the user

### Endpoint
```  code
/intended_use/list
```

### Arguments
| Name       | Description                         |
| ---------- | ----------------------------------- |
| `hash_pid` | User identifier (from wallet login) |

### Example Request
``` code
{
  "hash_pid": "<hash_pid>"
}
```

### Response Fields
#### intended_use

List of all Intended Uses created by the user.
| Field            | Description                          |
| ---------------- | ------------------------------------ |
| `identifier`     | Intended Use identifier              |
| `policy_URI`     | Policy reference URI                 |
| `type_of_policy` | Type of policy URI                   |
| `created_at`     | Creation timestamp                   |
| `revoked_at`     | Revocation timestamp                 |
| `purpose`        | Purpose description (language-based) |

The `purpose` field is an array with the following structure:
| Field            | Description              |
| ---------------- | ------------------------ |
| `lang`           | Language code            |
| `srvDescription` | Purpose description text |

### Notes
  * The hash_pid parameter is mandatory.
  * Only data owned by the authenticated user is returned.
  * This endpoint is read-only and does not modify data.

## Credential – List

This endpoint retrieves all Credentials created by the authenticated user, as well as the Intended Uses associated with each Credential.

It is intended to be used to:
  * List all Credentials owned by the user
  * Identify which Intended Uses are associated with each Credential

### Endpoint
``` code 
/credential/list
```

### Arguments
| Name       | Description                         |
| ---------- | ----------------------------------- |
| `hash_pid` | User identifier (from wallet login) |

### Example Request
``` code
{
  "hash_pid": "<hash_pid>"
}
```

### Response Fields
#### credential

List of all Credentials created by the user.
| Field    | Description                    |
| -------- | ------------------------------ |
| `name`   | Credential name                |
| `format` | Credential format              |
| `path`   | Credential path                |
| `values` | Credential values              |
| `neta`   | Additional credential metadata |

#### intended_uses

List of Intended Uses and their association with Credentials.
| Field        | Description                                             |
| ------------ | ------------------------------------------------------- |
| `id`         | Intended Use identifier                                 |
| `name`       | Intended Use name                                       |
| `associated` | Indicates if the Intended Use is linked to a Credential |
| `Credential` | Credential associated with the Intended Use (if any)    |

The `Credential` object contains:
| Field    | Description           |
| -------- | --------------------- |
| `id`     | Credential identifier |
| `name`   | Credential name       |
| `format` | Credential format     |
| `path`   | Credential path       |
| `values` | Credential values     |
| `neta`   | Additional metadata   |

If no Credential is associated, this field is returned as null.

### Notes
  * The hash_pid parameter is mandatory.  
  * Only data owned by the authenticated user is returned.
  * This endpoint is read-only and does not modify data.

## Natural Person – Update Legal Entities

This endpoint updates the association between a Natural Person and one or more Legal Entities.

It is intended to be used to:
  * Associate a Natural Person with multiple Legal Entities
  * Update existing associations owned by the authenticated user

### Endpoint
``` code
/natural_person/ui_update_legal_entities
```

### Arguments (JSON Body)
| Name                 | Description                                    |
| -------------------- | ---------------------------------------------- |
| `hash_pid`           | User identifier (from wallet login)            |
| `natural_person`     | Natural Person identifier                      |
| `legal_entities_ids` | Array of Legal Entity identifiers to associate |

### Example Request
``` code
{
  "hash_pid": <hash_pid>,
  "natural_person": 7,
  "legal_entities_ids": [3, 4, 5]
}
```

### Notes
  * The hash_pid parameter is mandatory.
  * The natural_person field must contain a single Natural Person ID.
  * The legal_entities_ids field must always be an array, even if it contains only one element.
  * All provided identifiers must belong to the authenticated user (hash_pid).
  * If the Natural Person or any Legal Entity does not belong to the user, the request will fail.
  * This endpoint updates data by modifying associations.

## Legal Person – Update Legal Entities

This endpoint updates the association between a Legal Person and one or more Legal Entities.

It is intended to be used to:
  * Associate a Legal Person with multiple Legal Entities
  * Update existing associations owned by the authenticated user

### Endpoint
``` code
/legal_person/ui_update_legal_entities
```

### Arguments (JSON Body)
| Name                 | Description                                    |
| -------------------- | ---------------------------------------------- |
| `hash_pid`           | User identifier (from wallet login)            |
| `legal_person`       | Legal Person identifier                        |
| `legal_entities_ids` | Array of Legal Entity identifiers to associate |

### Example Request
``` code
{
  "hash_pid": <hash_pid>,
  "legal_person": 7,
  "legal_entities_ids": [3, 4, 5]
}
```

### Notes
  * The hash_pid parameter is mandatory.
  * The legal_person field must contain a single Legal Person ID.
  * The legal_entities_ids field must always be an array, even if it contains only one element.
  * All provided identifiers must belong to the authenticated user (hash_pid).
  * If the Legal Person or any Legal Entity does not belong to the user, the request will fail.
  * This endpoint updates data by modifying associations.

## Legal Entity – Update Relying Parties

This endpoint updates the association between a Legal Entity and one or more Relying Parties.

It is intended to be used to:
  * Associate a Legal Entity with multiple Relying Parties
  * Update existing associations owned by the authenticated user

### Endpoint
``` code
/legal_entity/ui_update_RPs
```

### Arguments (JSON Body)
| Name              | Description                                     |
| ----------------- | ----------------------------------------------- |
| `hash_pid`        | User identifier (from wallet login)             |
| `legal_entity`    | Legal Entity identifier                         |
| `relying_parties` | Array of Relying Party identifiers to associate |

### Example Request
``` code
{
  "hash_pid": <hash_pid>,
  "legal_entity": 3,
  "relying_parties": [9, 11, 13]
}
```

### Notes
  * The hash_pid parameter is mandatory.
  * The legal_entity field must contain a single Legal Entity ID.
  * The relying_parties field must always be an array, even if it contains only one element.
  * All provided identifiers must belong to the authenticated user (hash_pid).
  * If the Legal Entity or any Relying Party does not belong to the user, the request will fail.
  * This endpoint updates data by modifying associations.

## Relying Party – Update Intended Uses

This endpoint updates the association between a Relying Party and one or more Intended Uses.

It is intended to be used to:
  * Associate a Relying Party with multiple Intended Uses
  * Update existing associations owned by the authenticated user

### Endpoint
``` code
/RP/ui_update_intended_use
```

### Arguments (JSON Body)
| Name            | Description                                    |
| --------------- | ---------------------------------------------- |
| `hash_pid`      | User identifier (from wallet login)            |
| `relying_party` | Relying Party identifier                       |
| `intended_uses` | Array of Intended Use identifiers to associate |

### Notes
  * The hash_pid parameter is mandatory.
  * The relying_party field must contain a single Relying Party ID.
  * The intended_uses field must always be an array, even if it contains only one element.
  * All provided identifiers must belong to the authenticated user (hash_pid).
  * If the Relying Party or any Intended Use does not belong to the user, the request will fail.
  * This endpoint updates data by modifying associations.

## Credential – Update Intended Uses

This endpoint updates the association between a Credential and one or more Intended Uses.

It is intended to be used to:
  * Associate a Credential with multiple Intended Uses
  * Update existing associations owned by the authenticated user

### Endpoint
``` code
/credential/ui_update_intended_uses
```

### Arguments (JSON Body)
| Name            | Description                                    |
| --------------- | ---------------------------------------------- |
| `hash_pid`      | User identifier (from wallet login)            |
| `credential`    | Credential identifier                          |
| `intended_uses` | Array of Intended Use identifiers to associate |

### Example Request
``` code
{
  "hash_pid": <hash_pid>,
  "credential": 2,
  "intended_uses": [1, 2, 3]
}
```

### Notes
  * The hash_pid parameter is mandatory.
  * The credential field must contain a single Credential ID.
  * The intended_uses field must always be an array, even if it contains only one element.
  * All provided identifiers must belong to the authenticated user (hash_pid).
  * If the Credential or any Intended Use does not belong to the user, the request will fail.
  * This endpoint updates data by modifying associations.

## Legal Entity – Remove / Update Natural Person

This endpoint removes the association between one or more Legal Entities and their associated Natural Person.

It is intended to be used to:
  * Disassociate a Natural Person from one or more Legal Entities
  * Set the natural_person field to NULL for the given Legal Entity IDs

### Endpoint
``` code
/legal_entity/ui_remove_update_natural_person
```

### Arguments (JSON Body)
| Name           | Description                                 |
| -------------- | ------------------------------------------- |
| `hash_pid`     | User identifier (from wallet login)         |
| `legal_entity` | Array of Legal Entity identifiers to update |

### Example Request
{
  "hash_pid": "<hash_pid>",
  "legal_entity": [1, 2, 3]
}

### Notes
  * The hash_pid parameter is mandatory.
  * The legal_entity field must always be an array, even if it contains only one element.
  * All provided Legal Entity identifiers must belong to the authenticated user (hash_pid).
  * If any Legal Entity does not belong to the user, the request will fail.
  * This endpoint updates data by setting the associated Natural Person to NULL.

## Legal Entity – Remove / Update Legal Person

This endpoint removes the association between one or more Legal Entities and their associated Legal Person.

It is intended to be used to:
  * Disassociate a Legal Person from one or more Legal Entities
  * Set the legal_person field to NULL for the given Legal Entity IDs

### Endpoint
``` code
/legal_entity/ui_remove_update_legal_person
``` 

### Arguments (JSON Body)
| Name           | Description                                 |
| -------------- | ------------------------------------------- |
| `hash_pid`     | User identifier (from wallet login)         |
| `legal_entity` | Array of Legal Entity identifiers to update |

### Example Request
``` code
{
  "hash_pid": "<hash_pid>",
  "legal_entity": [4, 5]
}
```

### Notes
  * The hash_pid parameter is mandatory.
  * The legal_entity field must always be an array, even if it contains only one element.
  * All provided Legal Entity identifiers must belong to the authenticated user (hash_pid).
  * If any Legal Entity does not belong to the user, the request will fail.
  * This endpoint updates data by setting the associated Legal Person to NULL.

## Relying Party – Remove / Update Legal Entity

This endpoint removes the association between one or more Relying Parties and their associated Legal Entity.

It is intended to be used to:
  * Disassociate a Legal Entity from one or more Relying Parties
  * Set the legal_entity reference to NULL for the given Relying Party IDs

### Endpoint
``` code
/RP/ui_remove_update_legal_entity
```

### Arguments (JSON Body)
| Name            | Description                                  |
| --------------- | -------------------------------------------- |
| `hash_pid`      | User identifier (from wallet login)          |
| `relying_party` | Array of Relying Party identifiers to update |

### Example Request
``` code
{
  "hash_pid": "<hash_pid>",
  "relying_party": [1, 3]
}
```

### Notes
  * The hash_pid parameter is mandatory.
  * The relying_party field must always be an array, even if it contains only one element.
  * All provided Relying Party identifiers must belong to the authenticated user (hash_pid).
  * If any Relying Party does not belong to the user, the request will fail.
  * This endpoint updates data by removing the association with the Legal Entity.

## Intended Use – Remove / Update Relying Party

This endpoint removes the association between one or more Intended Uses and their associated Relying Party.

It is intended to be used to:
  * Disassociate a Relying Party from one or more Intended Uses
  * Set the relying_party reference to NULL for the given Intended Use IDs

### Endpoint
``` code
/intended_use/ui_remove_update_relying_party
```

### Arguments (JSON Body)
| Name           | Description                                 |
| -------------- | ------------------------------------------- |
| `hash_pid`     | User identifier (from wallet login)         |
| `intended_use` | Array of Intended Use identifiers to update |

### Example Request
``` code
{
  "hash_pid": "<hash_pid>",
  "intended_use": [2, 4]
}
```

### Notes
  * The hash_pid parameter is mandatory.
  * The intended_use field must always be an array, even if it contains only one element.
  * All provided Intended Use identifiers must belong to the authenticated user (hash_pid).
  * If any Intended Use does not belong to the user, the request will fail.
  * This endpoint updates data by removing the association with the Relying Party.

## Intended Use – Remove / Update Credential

This endpoint removes the association between one or more Intended Uses and their associated Credential.

It is intended to be used to:
  * Disassociate a Credential from one or more Intended Uses
  * Remove the Credential association for the given Intended Use IDs

### Endpoint
``` code
/intended_use/ui_remove_update_credential
```

### Arguments (JSON Body)
| Name           | Description                                 |
| -------------- | ------------------------------------------- |
| `hash_pid`     | User identifier (from wallet login)         |
| `intended_use` | Array of Intended Use identifiers to update |

### Example Request
``` code
{
  "hash_pid": "<hash_pid>",
  "intended_use": [1, 2, 3]
}
```

### Notes
  * The hash_pid parameter is mandatory.
  * The intended_use field must always be an array, even if it contains only one element.
  * All provided Intended Use identifiers must belong to the authenticated user (hash_pid).
  * If any Intended Use does not belong to the user, the request will fail.
  * This endpoint updates data by removing the association with the Credential.



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
