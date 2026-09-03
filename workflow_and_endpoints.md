# Workflow and Endpoints


Step-by-step guide for authentication, entity creation, management and certificate generation.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Recommended Workflow](#recommended-workflow)
- [Examples](#examples)
- [Certificates](#certificates)
- [Swagger](#swagger)

---

## Overview

The WRP Registry API allows users to authenticate using PID/OID4VP, manage legal entities and wallet relying parties, and generate certificates.

The implementation of the WRP Registrar service and the database it uses complies with the following standards:

+ [CIR 2025/848](https://eur-lex.europa.eu/eli/reg_impl/2025/848/oj),
+ [TS5](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/main/docs/technical-specifications/ts5-common-formats-and-api-for-rp-registration-information.md)
+ [TS6](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/main/docs/technical-specifications/ts6-common-set-of-rp-information-to-be-registered.md)


The RP access certificate format complies with [ETSI TS 119 411-8](https://www.etsi.org/deliver/etsi_ts/119400_119499/11941108/01.01.01_60/ts_11941108v010101p.pdf).

The RP registration certificate format complies with [ETSI TS 119 475](https://www.etsi.org/deliver/etsi_ts/119400_119499/119475/01.02.01_60/ts_119475v010201p.pdf).

## Explanation of how to register a WRP with the Registrar Service

Authentication via the European Digital Identity Wallet (EUDIW), using the PID document, is currently being implemented as part of a trial phase.

Following authentication, the user must register the Natural Person or Legal Person responsible for the Legal Entity associated with the WRP.

Once the Person has been registered, the user can then register at least one Legal Entity. Next, they must register at least one Provider and, finally, at least one WRP.

They must also register at least one intended use and one credential to specify the required information when a Wallet-Relying Party with the role of a Service Provider is requesting data from a Wallet Unit

Once the WRP has been registered, an access certificate can be issued for the WRP and a registration certificate for each intended use.

To summarise the order of the process:

> **Natural Person/Legal Person → Legal Entity → Provider → Wallet Relying Party → Intended Use → Credential**

---
## Authentication flow

```mermaid
sequenceDiagram
title Authentication Flow

actor U as UserAgent
participant EW as EUDI Wallet    
participant WRP as Registrar Aplication
participant OIDV as OID4VP Verifier

U->>+WRP: Authorization Request (GET /authentication)
WRP->>+OIDV: Authorization Request (POST {verifier}/ui/presentations)
OIDV-->>-WRP: Authorization Request returns
WRP->>+WRP: Generate link to Wallet
WRP-->>-U: Return link
EW->>+OIDV: Share requested information
U->>+WRP: Request hash_pid (GET /getpidoid4vp)
WRP->>+OIDV: Request VP Token
OIDV-->>-WRP: Get and validate VP Token 
WRP->>+WRP: Generate hash_pid 
WRP->>+U: Return hash_pid

```

## Workflow

```mermaid

sequenceDiagram
title WorkFlow - Legal Person Example

actor U as UserAgent
participant WRP as Registrar Aplication
participant EJBCA as EJBCA
participant STATUS as Status List Service
participant WRPRC as RegCertIssuer


U->>+WRP: Create law (POST /law/create)
WRP->>+U: Return law id
U->>+WRP: Create legal person (POST /legal_person/create)
WRP->>+U: Return person id
U->>+WRP: Create identifier (POST /identifier/create)
WRP->>+U: Return identifier id
U->>+WRP: Create legal entity (POST /legal_entity/create)
WRP->>+U: Return legal identity id
U->>+WRP: Create policy (POST /policy/create)
WRP->>+U: Return policy id
U->>+WRP: Create provider (POST /provider/create)
WRP->>+U: Return provider id
U->>+WRP: Create credential (POST /credential/create)
WRP->>+U: Return credential id
U->>+WRP: Create intended_use (POST /intended_use/create)
WRP->>+U: Return intended_use id
U->>+WRP: Create provided_attestation (POST /provided_attestation/create)
WRP->>+U: Return provided_attestation id
U->>+WRP: Create supervisory_authority (POST /supervisory_authority/create)
WRP->>+U: Return supervisory_authority id
U->>+WRP: Create provided_attestation (POST /provided_attestation/create)
WRP->>+U: Return provided_attestation id
U->>+WRP: Create wallet_rp (POST /wallet_rp/create)
WRP->>+U: Return wallet_rp id
U->>+WRP: Create wallet_rp (POST /wallet_rp/certificate)
WRP->>+WRP: Generate certificate request
WRP->>+EJBCA: Enroll certificate with certificate request (POST /certificate/pkcs10enroll)
EJBCA->>+WRP: Return access certificate
WRP->>+WRP: Generate .p12 file 
WRP->>+U: Return .p12 file
U->>+WRP: Create wallet_rp (POST /intended_use/certificate)
WRP->>+STATUS: Generates a new entry in the attestation status list (POST /token_status_list/take)
STATUS->>+WRP: Return status idx and uri claims
WRP->>+WRPRC: Send data needed for WRPRC 
WRPRC->>+WRPRC: Generate certificate
WRPRC->>+WRP: Return certificate in JWT and CBOR format
WRP->>+U: Return registration certificate

```

### `GET` /authentication

Starts the authentication flow and returns a QR Code together with a presentation ID.

```
GET /authentication
```

### `GET` /pid_authorization

Verifies whether the PID authentication flow has been completed.

### `POST` /getpidoid4vp

Retrieves PID information and returns the user `hash_pid`.

---

## Recommended Workflow

1. Authenticate using the PID/OID4VP flow.
2. Create Law.
3. Create Natural Person/Legal Person.
4. Create Identifiers.
5. Create Natural Person or Legal Person.
6. Create a Legal Entity.
7. Create Policies (wrp).
8. Create a Provider.
9. Create Credential.
10. Create Policies (intended_use).
11. Create Intended Uses.
12. Create Provided Attestations.
13. Create Supervisory Authorities.
14. Create Wallet Relying Parties.
15. Generate certificates.

---

## Examples

### `POST` /law/create
Required dependencies:
+ hash_pid
+ law
  + legislativeIdentifier

```json
{
  "hash_pid": "abc123hash",
  "law": [
    {
      "legalBasis": [
        "consent",
        "contract"
      ],
      "legislativeIdentifier": "GDPR-ART-6"
    }
  ]
}
```

### `POST` /legal_person/create

Required dependencies:
  + hash_pid
  + legalPerson
    + legalName

```json
{
  "hash_pid": "abc123hash",
  "legalPerson": [
    {
      "law": [1],
      "legalName": [
        "Company A",
        "Company B"
      ]
    }
  ]
}
```

### `POST` /identifier/create

Required dependencies:
  + hash_pid
  + identifier
    + identifier
    + type

```json
{
  "hash_pid": "abc123hash",
  "identifier": [
    {
      "identifier": "PT123456789",
      "type": "http://data.europa.eu/eudi/id/EORI-No",
    }
  ]
}
```

### `POST` /legal_entity/create

Required dependencies:
  + hash_pid
  + legal_entity
    + identifiers
    + country
    + legal_person_id / natural_person_id

```json
{
  "hash_pid": "abc123hash",
  "legal_entity": [
    {
      "country": "PT",
      "email": [
        "test@email.com"
      ],
      "identifiers": [
        1
      ],
      "infoURI": [
        "https://example.com"
      ],
      "legal_person_id": 1,
      "phone": [
        "+351912345678"
      ],
      "postalAddress": [
        "Rua A, Porto"
      ]
    }
  ]
}
```

### `POST` /policy/create *(intention: wrp)*

Required dependencies:
  + hash_pid
  + policy
    + intention
    + policyURI
    + type

```json
{
  "hash_pid": "{{hash_pid}}",
  "policy": [
    {
      "intention": "wrp",
      "policyURI": "policy",
      "type": "http://data.europa.eu/eudi/policy/trust-service-practice-statement"
    }
  ]
}
```

### `POST` /provider/create

Required dependencies:
  + hash_pid
  + provider
    + legalEntityId
    + policy_id
    + providerType

```json
{
  "hash_pid": "abc123hash",
  "provider": [
    {
      "legalEntityId": 1,
      "policy_id": [
        1
      ],
      "providerType": "WALLET_PROVIDER",
      "x5c": [
        "MIIC...base64cert1",
        "MIIC...base64cert2"
      ]
    }
  ]
}
```

### `POST` /credential/create

Required dependencies:
  + hash_pid
  + credentials
    + format
    + meta
      + "values"
    + claims
      + path
    

```json
{
    "hash_pid": "abc123hash",
    "credentials": [
        {
            "format": "sd-jwt",
            "meta": {
                "vct_values": [
                    "urn:eudi:pid:1",
                    "urn:eu.europa.ec.eudi:learning:credential:1"
                ]
            },
            "claims": [
                { 
                    "path": [
                        "pid"
                    ]
                }
            ]
        }
    ]
}
```

### `POST` /policy/create *(intention: intended_use)*

Required dependencies:
  + hash_pid
  + policy
    + intention
    + policyURI
    + type

```json
{
  "hash_pid": "{{hash_pid}}",
  "policy": [
    {
      "intention": "intended_use",
      "policyURI": "policy",
      "type": "http://data.europa.eu/eudi/policy/trust-service-practice-statement"
    }
  ]
}
```

### `POST` /intended_use/create

Required dependencies:
  + hash_pid
  + intended_uses
    + purpose
      + content
      + lang
    + privacyPolicy_id
    + intendedUseIdentifier 
    + createdAt
    + revokedAt
    + credential_ids

```json
{
  "hash_pid": "abc123hash",
  "intended_uses": [
    {
      "createdAt": "2026-01-01T10:00:00Z",
      "credential_ids": [
        1
      ],
      "intendedUseIdentifier": "USE-001",
      "privacyPolicy_id": [
        2
      ],
      "purpose": [
        {
          "content": "Identity verification",
          "lang": "en"
        }
      ],
      "revokedAt": "2027-01-01T10:00:00Z"
    }
  ]
}
```

### `POST` /provided_attestation/create

Required dependencies:
  + hash_pid
  + providesAttestations
    + format
    + meta
      + "values"

```json
{
  "hash_pid": "abc123hash",
  "providesAttestations": [
    {
      "format": "dc+sd-jwt",
      "meta": {
        "vct_values": [
          "urn:eudi:pid:1",
          "urn:eu.europa.ec.eudi:learning:credential:1"
        ]
      }
    }
  ]
}
```

### `POST` /supervisory_authority/create

Required dependencies:
  + hash_pid
  + supervisoryAuthority
    + country
    + email / formURI / phone
    + name

```json
{
  "hash_pid": "abc123hash",
  "supervisoryAuthority": [
    {
      "country": "PT",
      "email": [
        "geral@cnpd.pt"
      ],
      "formURI": [
        "https://www.cnpd.pt/contactos"
      ],
      "name": "CNPD",
      "phone": [
        "+351213928400"
      ]
    }
  ]
}
```

### `POST` /wallet_rp/create

Required dependencies:
  + hash_pid
  + WalletRelyingParty
    + supportURI
    + srvDescription
      + content
      + lang
    + intendedUse_ids
    + entitlements
    + supervisoryAuthority
    + registryURI

```json
{
  "WalletRelyingParty": [
    {
      "entitlements": [
        "https://uri.etsi.org/19475/Entitlement/Service_Provider"
      ],
      "intendedUse_ids": [
        1
      ],
      "isPSB": true,
      "provider_id": 1,
      "providesAttestations_id": [
        1
      ],
      "registryURI": "https://registry.example.com",
      "srvDescription": [
        {
          "content": "Wallet authentication service",
          "lang": "en"
        }
      ],
      "supervisoryAuthority": 1,
      "supportURI": [
        "https://support.example.com"
      ],
      "tradeName": "My Wallet Service"
    }
  ],
  "hash_pid": "abc123hash"
}
```

---

## Certificates

### `POST` /intended_use/certificate

```json
{
  "hash_pid": "abc123hash",
  "intended_use_id": 1
}
```

Generates a signed Intended Use Registration Certificate using JAdES and COSE.

### `POST` /wallet_rp/certificate

```json
{
  "hash_pid": "abc123hash",
  "password": "StrongPassword123!",
  "wrp_id": 1
}
```

Generates a Wallet Relying Party certificate in PKCS#12 format.

---

## Swagger

Full API documentation is available through Swagger UI.

```
/swagger/
```

---

*WRP Registry API Guide*
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

# Endpoints
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

---
## API Documentation

All available endpoints, request parameters, request body schemas, response formats, and example requests can be consulted through the Swagger API documentation.

The Swagger interface provides an interactive environment where users can explore and test every available endpoint.

| Environment | URL                                                    |
| ----------- | ------------------------------------------------------ |
| Local       | `http://localhost:5000/swagger/`                       |
| Online      | `https://registry.serviceproviders.eudiw.dev/swagger/` |

The Swagger documentation should be considered the primary reference for the API specification, as it is kept up to date with the latest endpoint definitions and supported request/response formats.

--- 
## End-to-End Example
The following example demonstrates a complete registration workflow using the REST API.

The commands below illustrate the typical sequence of requests required to:

* authenticate the user and obtain a hash_pid.
* register all required resources.
* generate a Registration Certificate.
* generate an Access Certificate.

The example uses curl commands and sample values that comply with the referenced technical specifications. Replace identifiers returned by each step (e.g. law_id, provider_id, wrp_id) with the values obtained from your own deployment.

| Step | Endpoint                 | Purpose                           |
| ---- | ------------------------ | --------------------------------- |
| 1    | Authentication           | Obtain `hash_pid`                 |
| 2    | Law                      | Register legal basis              |
| 3    | Legal Person             | Create legal person               |
| 4    | Identifier               | Create organization identifier    |
| 5    | Legal Entity             | Create legal entity               |
| 6    | Policy                   | Create policy                     |
| 7    | Provider                 | Create provider                   |
| 8    | Credential               | Create credential                 |
| 9    | Intended Use             | Create intended use               |
| 10   | Provided Attestation     | Register attestation              |
| 11   | Supervisory Authority    | Register supervisory authority    |
| 12   | Wallet RP                | Create Wallet RP                  |
| 13   | Registration Certificate | Generate registration certificate |
| 14   | Access Certificate       | Generate access certificate       |

### Step 1 - Create Law
#### POST /law/create

``` code
curl --location 'https://registry.serviceproviders.eudiw.dev/law/create' \
--header 'Content-Type: application/json' \
--data '{
    "hash_pid": "<hash_pid>",
    "law": [
        {
            "legislativeIdentifier": "LAW123",
            "legalBasis": ["basis1", "basis2"]
        }
    ]
}'
```

### Step 2 - Create Legal Person
#### POST /legal_person/create

```code
curl --location 'https://registry.serviceproviders.eudiw.dev/legal_person/create' \
--header 'Content-Type: application/json' \
--data '{
    "hash_pid": "<hash_pid>",
    "legalPerson": [
        {
          "law": [
            <law_id>
          ],
          "legalName": [
            "Company A",
            "Company B"
          ]
        }
    ]
}'
```

### Step 3 - Create Identifier
#### POST /identifier/create

``` code
curl --location 'https://registry.serviceproviders.eudiw.dev/identifier/create' \
--header 'Content-Type: application/json' \
--data '{
    "hash_pid": "<hash_pid>",
    "identifier": [
        {
            "identifier": "PT123456789",
            "type": "http://data.europa.eu/eudi/id/EORI-No"
        }
    ]
}'
```

### Step 4 - Create Legal Entity
#### POST /legal_entity/create

``` code
curl --location 'https://registry.serviceproviders.eudiw.dev/legal_entity/create' \
--data-raw '{
    "hash_pid": "<hash_pid>",

    "legal_entity": [
        {
            "postalAddress": [
                "Rua A, Porto",
                "Av B, Lisboa"
            ],

            "country": "FR",

            "email": [
                "contact@empresa.pt",
                "support@empresa.pt"
            ],

            "phone": [
                "+351912345678",
                "+351212345678"
            ],

            "infoURI": [
                "https://empresa.pt/info",
                "https://empresa.pt/about"
            ],

            "identifiers": [<identifiers_ids>],

            "legal_person_id": <legal_person_id>
        }
    ]
}'
```

### Step 5 - Create Policy
#### POST /policy/create (Wallet RP)

``` code
curl --location 'https://registry.serviceproviders.eudiw.dev/policy/create' \
--header 'Content-Type: application/json' \
--data '{
    "hash_pid": "<hash_pid>",
    "policy": [
        {  
            "intention": "wrp",
            "policyURI": "policy",
            "type": "http://data.europa.eu/eudi/policy/trust-service-practice-statement"
        }
    ]
}'
```

### Step 6 - Create Provider
#### POST /provider/create

``` code
curl --location 'https://registry.serviceproviders.eudiw.dev/provider/create' \
--header 'Content-Type: application/json' \
--data '{
    "hash_pid": "<hash_pid>",

    "provider": [
        {
            "legalEntityId": <legal_Entity_Id>,

            "providerType": "EAA_PROVIDER",

            "x5c": [
                "cert1_base64",
                "cert2_base64"
            ],

            "policy_id": [<policy_id>]
        }
    ]
}'
```

### Step 7 - Create Credential
#### POST /credential/create

``` code
curl --location 'https://registry.serviceproviders.eudiw.dev/credential/create' \
--header 'Content-Type: application/json' \
--data '{
    "hash_pid": "<hash_pid>",
    "credentials": [
        {
            "format": "sd-jwt",
            "meta": {
                "vct_values": [
                    "urn:eudi:pid:1",
                    "urn:eu.europa.ec.eudi:learning:credential:1"
                ]
            },
            "claims": [
                { 
                    "path": [
                        "pid",
                        "address",
                        0,
                        "street"
                    ]
                }
            ]
        }
    ]
}'
```

### Step 8 - Create Policy (Intended Use)
#### POST /policy/create 

``` code
curl --location 'https://registry.serviceproviders.eudiw.dev/policy/create' \
--header 'Content-Type: application/json' \
--data '{
    "hash_pid": "<hash_pid>",
    "policy": [
        {
            "intention": "intended_use",
            "policyURI": "https://empresa.pt/terms",
            "type": "http://data.europa.eu/eudi/policy/trust-service-practice-statement"
        }
    ]
}'
```

### Step 9 - Create Intended Use
#### POST /intended_use/create

``` code
curl --location 'https://registry.serviceproviders.eudiw.dev/intended_use/create' \
--header 'Content-Type: application/json' \
--data '{
    "hash_pid": "<hash_pid>",
    "intended_uses": [
        {
            "intendedUseIdentifier": "iu_1",
            "createdAt": "2026-04-17",
            "revokedAt": "2026-04-17",

            "purpose": [
                {
                    "lang": "en",
                    "content": "Access banking services"
                },
                {
                    "lang": "pt",
                    "content": "Aceder a serviços bancários"
                }
            ],

            "privacyPolicy_id": [<privacyPolicy_id>],
            "credential_ids": [<credential_ids>]
        }
    ]
}'
```

### Step 10 - Provided Attestation
#### POST /provided_attestation/create

``` code
curl --location 'https://registry.serviceproviders.eudiw.dev/provided_attestation/create' \
--header 'Content-Type: application/json' \
--data '{
    "hash_pid": "<hash_pid>",
    "providesAttestations": [
        {
        "format": "dc+sd-jwt",
        "meta": {
            "vct_values": [
            "urn:eudi:pid:1",
            "urn:eu.europa.ec.eudi:learning:credential:1"
            ]
        }
        }
    ]
}'
```

### Step 11 - Create Supervisory Authority
#### POST /supervisory_authority/create

``` code
curl --location 'https://registry.serviceproviders.eudiw.dev/supervisory_authority/create' \
--header 'Content-Type: application/json' \
--data-raw '{
    "hash_pid": "<hash_pid>",

    "supervisoryAuthority": [
        {
            "name": "ACME Authority",
            "country": "PT",
            "email": [
                "authority@acme.com"
            ],
            "phone": [
                "+351912345678"
            ],
            "formURI": [
                "https://acme.com/form"
            ]
        }
    ]
}'
```

### Step 12 - Create Wallet Relying Party
#### POST /wallet_rp/create

``` code
curl --location 'https://registry.serviceproviders.eudiw.dev/wallet_rp/create' \
--header 'Content-Type: application/json' \
--data '{
    "hash_pid": "<hash_pid>",

    "WalletRelyingParty": [
        {
            "tradeName": "PY Issuer Dev",

            "supportURI": [
                "https://acme.com/support",
                "https://help.acme.com"
            ],

            "srvDescription": [
                {
                    "lang": "en",
                    "content": "Provides authentication services for ACME users."
                },
                {
                    "lang": "pt",
                    "content": "Fornece serviços de autenticação para utilizadores ACME."
                }
            ],

            "isPSB": false,

            "entitlements": [
                "asadsasd"
            ],

            "usesIntermediary": [],

            "providesAttestations_id": [<provides_Attestations_id>],

            "registryURI": "https://registry.acme.com",

            "supervisoryAuthority": <supervisory_Authority>,

            "provider_id": <provider_id>,

            "intendedUse_ids": [<intended_Use_ids>]
        }
    ]
}'
```

### Step 13 - Generate Registration Certificate
#### POST /intended_use/certificate

``` code
curl --location 'https://registry.serviceproviders.eudiw.dev/wallet_rp/certificate' \
--header 'Content-Type: application/json' \
--data '{
    "hash_pid": "<hash_pid>",
    "wrp_id": 1,
    "password": "<password>"
}'
```

### Step 14 - Generate Access Certificate
#### POST /wallet_rp/certificate

``` code
curl --location 'https://registry.serviceproviders.eudiw.dev/intended_use/certificate' \
--data '{
    "hash_pid": "<hash_pid>",
    "intended_use_id": <intended_use_id>
}'
``` 

## Swagger Documentation

The complete API documentation, including all available endpoints, request parameters, request/response examples, and schemas, is available through Swagger UI.

### Local instance

When running the project locally, the Swagger documentation is available at:

```
http://localhost:5000/swagger
```

*(Adjust the host and port if your local deployment uses different values.)*

### Online instance

The latest online Swagger documentation is available at:

```
https://registry.serviceproviders.eudiw.dev/swagger
```