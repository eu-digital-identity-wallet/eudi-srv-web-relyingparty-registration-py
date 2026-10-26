# Launchpad 2026 — Get your WRP registration and access certificates — v1.1

**Document version:** 1.1 · **Date:** 2026-10-26

## What this guide is for

This guide explains how to issue Wallet Relying Party (WRP) certificates for Launchpad 2026 tests. It is intended for the technical teams of entities and Member States (MS) that cannot issue these certificates for their own Relying Parties (RPs).

Follow the steps below to obtain a **WRPRC** and a **WRPAC** for your RP. You will provide its identity, role, service details, privacy statement and the data it requests or issues.

You will obtain:

| Certificate                                                      | What it is used for                                                                                                                      |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **WRPRC — Wallet Relying Party Registration Certificate** | Provides registered information about the RP, its role and, as applicable, the data it requests and the attestations it issues.          |
| **WRPAC — Wallet Relying Party Access Certificate**       | Lets a Wallet authenticate the RP Instance. The service returns it with its private key in a password-protected PKCS#12 (`.p12`) file. |

The Registrar is based on the **EUDI Wallet Reference Implementation**:

- [Source code](https://github.com/eu-digital-identity-wallet/eudi-srv-web-relyingparty-registration-py)
- [Launchpad certificate-issuance service](https://itb.registry.serviceproviders.eudiw.dev/)
- [API documentation](https://itb.registry.serviceproviders.eudiw.dev/swagger/)

### Service version and standards

The Launchpad service complies with **[TS5 v1.3](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/af9b1460f02eb1904120c0cb5c020568538378db/docs/technical-specifications/ts5-common-formats-and-api-for-rp-registration-information.md)**, **[TS6 v1.1](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/8a0bc4d3829aa6e86de1c68891695add7c37b9b8/docs/technical-specifications/ts6-common-set-of-rp-information-to-be-registered.md)** and **CIR 2025/848**. The certificate profiles referenced in this guide are **[ETSI TS 119 411-8 V1.1.1](https://www.etsi.org/deliver/etsi_ts/119400_119499/11941108/01.01.01_60/ts_11941108v010101p.pdf)** for WRPAC and **[ETSI TS 119 475 V1.2.1](https://www.etsi.org/deliver/etsi_ts/119400_119499/119475/01.02.01_60/ts_119475v010201p.pdf)** for WRPRC.

**[CIR (EU) 2024/2982](https://eur-lex.europa.eu/eli/reg_impl/2024/2982/2026-08-11)** (consolidated version of 11 August 2026) specifies the protocols and interfaces for Wallet interactions, including how WRP certificates are conveyed in those exchanges.

### Using this guide

This workflow is for an RP that is a **legal person**, operating **without an intermediary**. For setups using intermediaries, follow the [Swagger API documentation](https://itb.registry.serviceproviders.eudiw.dev/swagger/).

**First obtain the WRPAC, then the WRPRC.** Choose the route below according to what your RP does. The preparation steps collect the information for both certificates before you register the RP in step 10. The step numbers refer to the sections below. 

| Role                                                                                                  | Prepare and obtain the WRPAC                                                                                                                    | After obtaining the WRPAC                                      |
| ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `Service_Provider` — requests Wallet data without issuing PID or attestations                      | Steps 1–7, 9 and 10, then step 12. Skip step 8 and use`"providesAttestations_id": []`.                                                       | Run step 11 with the ID saved in step 7 and linked in step 10. |
| `PID_Provider` — issues person identification data                                                 | Steps 1–10, then step 12. Select this role and`Service_Provider` in step 10.                                                                 | Run step 11 with the ID saved in step 7 and linked in step 10. |
| `QEAA_Provider` — issues qualified electronic attestations of attributes                           | Steps 1–10, then step 12. Select this role and`Service_Provider` in step 10.                                                                 | Run step 11 with the ID saved in step 7 and linked in step 10. |
| `Non_Q_EAA_Provider` — issues non-qualified electronic attestations of attributes                  | Steps 1–10, then step 12. Select this role and`Service_Provider` in step 10.                                                                 | Run step 11 with the ID saved in step 7 and linked in step 10. |
| `PUB_EAA_Provider` — issues public-sector electronic attestations of attributes                    | Steps 1–10, then step 12. Select this role and`Service_Provider` in step 10.                                                                 | Run step 11 with the ID saved in step 7 and linked in step 10. |
| `mDL_Provider` — issues mobile driving licences for Launchpad testing                              | Steps 1–10, then step 12. Select this role and `Service_Provider` in step 10.                                                                | Run step 11 with the ID saved in step 7 and linked in step 10. |
| `QCert_for_ESeal_Provider` — issues qualified certificates for electronic seals                    | Steps 1–7, 9 and 10, then step 12. Select this role and`Service_Provider` in step 10. Skip step 8 and use `"providesAttestations_id": []`. | Run step 11 with the ID saved in step 7 and linked in step 10. |
| `QCert_for_ESig_Provider` — issues qualified certificates for electronic signatures                | Steps 1–7, 9 and 10, then step 12. Select this role and`Service_Provider` in step 10. Skip step 8 and use `"providesAttestations_id": []`. | Run step 11 with the ID saved in step 7 and linked in step 10. |
| `rQSealCDs_Provider` — manages remote qualified electronic seal creation devices                   | Steps 1–7, 9 and 10, then step 12. Select this role and`Service_Provider` in step 10. Skip step 8 and use `"providesAttestations_id": []`. | Run step 11 with the ID saved in step 7 and linked in step 10. |
| `rQSigCDs_Provider` — manages remote qualified electronic signature creation devices               | Steps 1–7, 9 and 10, then step 12. Select this role and`Service_Provider` in step 10. Skip step 8 and use `"providesAttestations_id": []`. | Run step 11 with the ID saved in step 7 and linked in step 10. |
| `ESig_ESeal_Creation_Provider` — provides non-qualified remote signature or seal creation services | Steps 1–7, 9 and 10, then step 12. Select this role and`Service_Provider` in step 10. Skip step 8 and use `"providesAttestations_id": []`. | Run step 11 with the ID saved in step 7 and linked in step 10. |

If your RP issues PID or attestations, follow its issuer row, including when it also requests Wallet data. For that combined activity, select both the issuer entitlement and `Service_Provider` in step 10; create the RP record only once. For other combinations of roles, combine the relevant preparation steps. 

The **`entitlements` in the WRPRC identify the roles registered for this RP record**. Select the applicable roles in step 10 using the complete URIs listed there. 

**Launchpad-only test entitlement:** `mDL_Provider` is included solely to test the handling of mDL issuer entitlements during Launchpad 2026. The URI `https://uri.etsi.org/19475/Entitlement/mDL_Provider` is not defined in the applicable ETSI specifications and must not be treated as a normative entitlement outside these tests.

Placeholders such as `<LegalPerson.legalName>` identify the data you must supply, using the specification's field names. The class before the dot identifies which record the field belongs to. Legal-entity, identifier and policy definitions come from [TS2](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/ee91a294c833af5188726fd8c302c641212192aa/docs/technical-specifications/ts2-notification-publication-provider-information.md), referenced by TS5. Uppercase placeholders ending in `_ID` are the numbers returned by earlier API requests. Keep the JSON field names and the fixed values shown in the commands.

## Before you start

Have the following ready:

- A terminal running Bash or a compatible shell, `curl` 7.76 or later, and Python 3 to extract the certificates.
- Your organisation's RP legal name, official identifier, physical address and country code: the details of the legal entity operating the RP for which you are requesting certificates.
- The RP's trade name, service description, entitlement, support URL and policy URLs.
- For the data your RP requests: a reference you choose, the purpose, credential types and attributes, privacy-statement URL, start date and end date. Also identify any attestations the RP issues.
- The Launchpad **`hash_pid`** is `1a2b3c4d5e6f7g8h9i0j`. It is already included in every request below; keep it unchanged.

Set the service address once, in the terminal you will use for all steps:

```bash
BASE_URL='https://itb.registry.serviceproviders.eudiw.dev'
umask 077
```

**How to use the examples:** replace every `<PLACEHOLDER>` before running a command. Keep double quotes around text; replace numeric ID placeholders with the numbers returned by your own requests, without quotes. Escape quotation marks inside JSON text as `"`. The creation requests add records: save the returned IDs and continue from the last successful step instead of restarting the workflow.

Successful creation responses contain `status: "success"` and the new IDs in `data`. Read the response after every step; stop and fix any error before continuing.

## 1. Add the RP's legal name

Create the legal-person record for the RP. `<LegalPerson.legalName>` is the RP legal name as recorded officially, not the name of the team requesting certificates. This is the **Name** information in [TS6 §2](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/8a0bc4d3829aa6e86de1c68891695add7c37b9b8/docs/technical-specifications/ts6-common-set-of-rp-information-to-be-registered.md#2-common-data-set) and `LegalPerson.legalName` in [TS2 §2.8.4](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/ee91a294c833af5188726fd8c302c641212192aa/docs/technical-specifications/ts2-notification-publication-provider-information.md#284-legalperson), inherited through TS5 §2.4.9.

```bash
curl --silent --show-error --fail-with-body \
  "$BASE_URL/legal_person/create" \
  --header 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{
  "hash_pid": "1a2b3c4d5e6f7g8h9i0j",
  "legalPerson": [
    {
      "legalName": [
        "<LegalPerson.legalName>"
      ]
    }
  ]
}
JSON
```

**Save:** `LEGAL_PERSON_ID`.

## 2. Add the RP's official identifier

Create an `Identifier` record: `<Identifier.identifier>` is the actual official identifier and `<Identifier.type>` is its scheme. See [TS6 §2, Identifier](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/8a0bc4d3829aa6e86de1c68891695add7c37b9b8/docs/technical-specifications/ts6-common-set-of-rp-information-to-be-registered.md#2-common-data-set), [TS5 §2.4.2](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/af9b1460f02eb1904120c0cb5c020568538378db/docs/technical-specifications/ts5-common-formats-and-api-for-rp-registration-information.md#242-identifier-external) and [TS2 §2.8.2](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/ee91a294c833af5188726fd8c302c641212192aa/docs/technical-specifications/ts2-notification-publication-provider-information.md#282-identifier).

Use EUID when available in the national business register. TS5 specifies a published national scheme when EUID is unavailable. The API accepts these six exact scheme URIs:

- `http://data.europa.eu/eudi/id/EORI-No`
- `http://data.europa.eu/eudi/id/LEI`
- `http://data.europa.eu/eudi/id/EUID`
- `http://data.europa.eu/eudi/id/VATIN`
- `http://data.europa.eu/eudi/id/TIN`
- `http://data.europa.eu/eudi/id/Excise`

Repeat this step if the RP needs several identifiers; include all returned IDs in step 3.

```bash
curl --silent --show-error --fail-with-body \
  "$BASE_URL/identifier/create" \
  --header 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{
  "hash_pid": "1a2b3c4d5e6f7g8h9i0j",
  "identifier": [
    {
      "identifier": "<Identifier.identifier>",
      "type": "<Identifier.type>"
    }
  ]
}
JSON
```

**Save:** `IDENTIFIER_ID`.

## 3. Create the legal entity

Create the `LegalEntity` record that links the RP legal name and identifier. See [TS5 §2.3](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/af9b1460f02eb1904120c0cb5c020568538378db/docs/technical-specifications/ts5-common-formats-and-api-for-rp-registration-information.md#23-legalentity), [TS2 §2.1](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/ee91a294c833af5188726fd8c302c641212192aa/docs/technical-specifications/ts2-notification-publication-provider-information.md#21-legalentity) and [TS6 §2, Physical Address and Info URI](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/8a0bc4d3829aa6e86de1c68891695add7c37b9b8/docs/technical-specifications/ts6-common-set-of-rp-information-to-be-registered.md#2-common-data-set).

- `<LEGAL_PERSON_ID>` and `<IDENTIFIER_ID>`: returned by steps 1 and 2.
- `<LegalEntity.country>`: country where the RP is established, using its ISO alpha-2 code, such as `PT`. TS2 also defines `EU` for providers operating at European level.
- `<LegalEntity.postalAddress>`: the RP physical address. TS6 includes this information even though TS2 allows the generic field to be optional.
- `<LegalEntity.infoURI>`: an information page belonging to the RP, where applicable. Enter the URL of the RP's website or an information page describing it.

```bash
curl --silent --show-error --fail-with-body \
  "$BASE_URL/legal_entity/create" \
  --header 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{
  "hash_pid": "1a2b3c4d5e6f7g8h9i0j",
  "legal_entity": [
    {
      "country": "<LegalEntity.country>",
      "postalAddress": ["<LegalEntity.postalAddress>"],
      "identifiers": [
        <IDENTIFIER_ID>
      ],
      "legal_person_id": <LEGAL_PERSON_ID>,
      "infoURI": [
        "<LegalEntity.infoURI>"
      ]
    }
  ]
}
JSON
```

**Save:** `LEGAL_ENTITY_ID`.

## 4. Add the RP's policies

Create two policy records: the RP provider policy and the privacy statement for the data processing described in step 7. See [TS2 §2.2](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/ee91a294c833af5188726fd8c302c641212192aa/docs/technical-specifications/ts2-notification-publication-provider-information.md#22-provider), [TS2 §2.8.6](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/ee91a294c833af5188726fd8c302c641212192aa/docs/technical-specifications/ts2-notification-publication-provider-information.md#286-policy) and [TS5 §2.4.3](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/af9b1460f02eb1904120c0cb5c020568538378db/docs/technical-specifications/ts5-common-formats-and-api-for-rp-registration-information.md#243-intendeduse).

`<Policy.policyURI>` is the URL where the corresponding document is published. It appears twice because the documents can differ. For the first record, select `<Policy.type>` from the complete list below. For the second record, **keep `privacy-statement` as shown**: this identifies the privacy statement.

- `http://data.europa.eu/eudi/policy/trust-service-practice-statement`
- `http://data.europa.eu/eudi/policy/terms-and-conditions`
- `http://data.europa.eu/eudi/policy/privacy-statement`
- `http://data.europa.eu/eudi/policy/privacy-policy`
- `http://data.europa.eu/eudi/policy/registration-policy`

Keep both policy objects and the `intention` values as shown. Save both returned IDs for the following steps.

```bash
curl --silent --show-error --fail-with-body \
  "$BASE_URL/policy/create" \
  --header 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{
  "hash_pid": "1a2b3c4d5e6f7g8h9i0j",
  "policy": [
    {
      "intention": "wrp",
      "policyURI": "<Policy.policyURI>",
      "type": "<Policy.type>"
    },
    {
      "intention": "intended_use",
      "policyURI": "<Policy.policyURI>",
      "type": "http://data.europa.eu/eudi/policy/privacy-statement"
    }
  ]
}
JSON
```

**Save:** the first returned ID as `WRP_POLICY_ID`, and the second as `PRIVACY_POLICY_ID`. Repeat the policy request with only the `intended_use` object if another intended use needs a different privacy policy; save its returned ID separately.

## 5. Create the provider

Link the RP's legal entity to its policy. Use `LEGAL_ENTITY_ID` from step 3 and `WRP_POLICY_ID` from step 4.

The command already sets `providerType` to `WalletRelyingParty` because this record is for an RP. Its role, such as PID provider or service provider, is selected separately through `entitlements` in step 10. See [TS5 §2.2](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/af9b1460f02eb1904120c0cb5c020568538378db/docs/technical-specifications/ts5-common-formats-and-api-for-rp-registration-information.md#22-provider) and [TS2 §2.2](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/ee91a294c833af5188726fd8c302c641212192aa/docs/technical-specifications/ts2-notification-publication-provider-information.md#22-provider).

```bash
curl --silent --show-error --fail-with-body \
  "$BASE_URL/provider/create" \
  --header 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{
  "hash_pid": "1a2b3c4d5e6f7g8h9i0j",
  "provider": [
    {
      "legalEntityId": <LEGAL_ENTITY_ID>,
      "providerType": "WalletRelyingParty",
      "policy_id": [
        <WRP_POLICY_ID>
      ]
    }
  ]
}
JSON
```

**Save:** `PROVIDER_ID`.

## 6. Describe the data the RP may request

Describe the attestations and attributes the RP may request for the purpose you will describe in step 7. They do not all have to be requested in every interaction: include planned requests during initial issuance or a later reissuance, as applicable. This step does not issue a credential. See [TS6 §2, Data Requested](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/8a0bc4d3829aa6e86de1c68891695add7c37b9b8/docs/technical-specifications/ts6-common-set-of-rp-information-to-be-registered.md#2-common-data-set), [TS5 §2.4.4 Credential](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/af9b1460f02eb1904120c0cb5c020568538378db/docs/technical-specifications/ts5-common-formats-and-api-for-rp-registration-information.md#244-credential), [§2.4.1 Claim](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/af9b1460f02eb1904120c0cb5c020568538378db/docs/technical-specifications/ts5-common-formats-and-api-for-rp-registration-information.md#241-claim).

Choose `<Credential.format>` and replace `<Credential.meta>` with the **complete JSON object** for that format. Use the format of the credential your RP may request:

| Credential format | Value for`format` | Example`meta` object                         |
| ----------------- | ------------------- | ---------------------------------------------- |
| SD-JWT VC         | `dc+sd-jwt`       | `{"vct_values": ["urn:eudi:pid:1"]}`         |
| ISO mdoc          | `mso_mdoc`        | `{"doctype_value": "org.iso.18013.5.1.mDL"}` |

These two formats and their metadata are described in [OpenID4VP Appendix B](https://openid.net/specs/openid-4-verifiable-presentations-1_0-27.html#appendix-B), referenced by TS5. Choose the format used by your Wallet and RP test configuration.

Replace the example credential type or document type with your own. For SD-JWT, `vct_values` lists the accepted types. For mdoc, `doctype_value` identifies the document type.

Replace `<Claim.path>` with a JSON array locating the requested attribute:

- SD-JWT: `["given_name"]`.
- mdoc: `["org.iso.18013.5.1", "given_name"]` — namespace, then element name.

Use names from your credential schema. Add one `claims` object per requested attribute, and repeat this step for each credential description needed. Changing the format also requires the matching metadata and claim paths.

```bash
curl --silent --show-error --fail-with-body \
  "$BASE_URL/credential/create" \
  --header 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{
  "hash_pid": "1a2b3c4d5e6f7g8h9i0j",
  "credentials": [
    {
      "format": "<Credential.format>",
      "meta": <Credential.meta>,
      "claims": [
        {
          "path": <Claim.path>
        }
      ]
    }
  ]
}
JSON
```

**Save:** `CREDENTIAL_ID`. A nested path is a JSON array such as `["address", "street"]`; an array index is a number, for example `["addresses", 0, "street"]`. These are syntax examples, not a prescribed PID schema.

## 7. Add the purpose and privacy information

Describe why your RP may request the data and link the privacy statement from step 4 to the data descriptions from step 6. If the data is intended for a later reissuance, describe that purpose explicitly; for example, identifying the recipient using specified PID attributes when reissuing the attestation. See [TS6 §2, Purpose and Data Requested](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/8a0bc4d3829aa6e86de1c68891695add7c37b9b8/docs/technical-specifications/ts6-common-set-of-rp-information-to-be-registered.md#2-common-data-set) and [TS5 §2.4.3](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/af9b1460f02eb1904120c0cb5c020568538378db/docs/technical-specifications/ts5-common-formats-and-api-for-rp-registration-information.md#243-intendeduse).

- `<IntendedUse.intendedUseIdentifier>`: an identifier you choose for this intended use, for example `rp1-age-check`. Supply it in the request. It is different from the numeric `INTENDED_USE_ID` returned by the API.
- `<IntendedUse.createdAt>`: validity start date of the intended use, in `YYYY-MM-DD`.
- `<IntendedUse.revokedAt>`: the intended use's end date, in `YYYY-MM-DD`.
- `<MultiLangString.content>`: description of the purpose for requesting the data.
- `<MultiLangString.lang>`: language of that text; see [TS5 §2.4.5](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/af9b1460f02eb1904120c0cb5c020568538378db/docs/technical-specifications/ts5-common-formats-and-api-for-rp-registration-information.md#245-multilangstring). API values: `bg`, `cs`, `da`, `de`, `el`, `en`, `es`, `et`, `fi`, `fr`, `ga`, `hr`, `hu`, `it`, `lt`, `lv`, `mt`, `nl`, `pl`, `pt`, `ro`, `sk`, `sl`, `sv`.
- `<PRIVACY_POLICY_ID>`: ID of the privacy statement from step 4, representing `IntendedUse.privacyPolicy`.
- `<CREDENTIAL_ID>`: ID from step 6, representing an entry in `IntendedUse.credentials`. For several, use your actual IDs as an array, such as `[21, 22]`.

For the Launchpad tests, **one language is sufficient**. Provide one `purpose` entry and the privacy statement in that language. Additional translations are optional; add a separate `purpose` entry for each extra language.

```bash
curl --silent --show-error --fail-with-body \
  "$BASE_URL/intended_use/create" \
  --header 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{
  "hash_pid": "1a2b3c4d5e6f7g8h9i0j",
  "intended_uses": [
    {
      "intendedUseIdentifier": "<IntendedUse.intendedUseIdentifier>",
      "createdAt": "<IntendedUse.createdAt>",
      "revokedAt": "<IntendedUse.revokedAt>",
      "purpose": [
        {
          "lang": "<MultiLangString.lang>",
          "content": "<MultiLangString.content>"
        }
      ],
      "privacyPolicy_id": [
        <PRIVACY_POLICY_ID>
      ],
      "credential_ids": [
        <CREDENTIAL_ID>
      ]
    }
  ]
}
JSON
```

**Save:** `INTENDED_USE_ID`. Repeat this step for every intended use, keeping the IDs separate. In this response, copy the number under `Credentials ids` and save it as `INTENDED_USE_ID` for steps 10 and 11. Despite the response label, do not use the credential ID from step 6.

## 8. Describe attestations the RP issues — if applicable

**Complete this step only if the RP has at least one of these entitlements:**

- `QEAA_Provider`
- `Non_Q_EAA_Provider`
- `PUB_EAA_Provider`
- `PID_Provider`
- `mDL_Provider` — Launchpad testing only

**For all other RPs, skip this step** and use `"providesAttestations_id": []` in step 10.

For the roles above, describe each attestation type the RP issues. Set `<ProvidedAttestation.format>` and replace `<ProvidedAttestation.meta>` with the matching JSON object:

| Issued attestation format | Value for`format` | Example`meta` object                         |
| ------------------------- | ------------------- | ---------------------------------------------- |
| SD-JWT VC                 | `dc+sd-jwt`       | `{"vct_values": ["urn:eudi:pid:1"]}`         |
| ISO mdoc                  | `mso_mdoc`        | `{"doctype_value": "org.iso.18013.5.1.mDL"}` |

Use the format your issuer actually produces and replace the example type values with those of the issued attestation. The format identifiers follow the explanation in step 6. There is no `claims` array here: this step describes what the RP issues, not what it requests. Repeat for each attestation type issued.

References: [TS5 §2.4.7](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/af9b1460f02eb1904120c0cb5c020568538378db/docs/technical-specifications/ts5-common-formats-and-api-for-rp-registration-information.md#247-providedattestation) and [TS6 §2.2](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/8a0bc4d3829aa6e86de1c68891695add7c37b9b8/docs/technical-specifications/ts6-common-set-of-rp-information-to-be-registered.md#22-role-dependent-mandatory-data-to-be-provided-in-registration).

```bash
curl --silent --show-error --fail-with-body \
  "$BASE_URL/provided_attestation/create" \
  --header 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{
  "hash_pid": "1a2b3c4d5e6f7g8h9i0j",
  "providesAttestations": [
    {
      "format": "<ProvidedAttestation.format>",
      "meta": <ProvidedAttestation.meta>
    }
  ]
}
JSON
```

**Save:** `PROVIDED_ATTESTATION_ID`, if created.

## 9. Register the supervisory authority

Create the record for the **competent data protection supervisory authority** supervising the RP and its intended uses. See [TS6 §2, Supervisory Authority](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/8a0bc4d3829aa6e86de1c68891695add7c37b9b8/docs/technical-specifications/ts6-common-set-of-rp-information-to-be-registered.md#2-common-data-set) and [TS5 §2.4.6](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/af9b1460f02eb1904120c0cb5c020568538378db/docs/technical-specifications/ts5-common-formats-and-api-for-rp-registration-information.md#246-supervisoryauthority).

Supply its official `<SupervisoryAuthority.name>`, ISO alpha-2 `<SupervisoryAuthority.country>` and `<SupervisoryAuthority.email>`. Name and country are required. At least one contact is required: `email`, `phone` or `formURI`. This command uses email. To use another contact, replace the email array with `"phone": ["<SupervisoryAuthority.phone>"]` or `"formURI": ["<SupervisoryAuthority.formURI>"]`. Phone numbers start with `+` and the country calling code; `formURI` is the URL of the authority's reporting web form.

```bash
curl --silent --show-error --fail-with-body \
  "$BASE_URL/supervisory_authority/create" \
  --header 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{
  "hash_pid": "1a2b3c4d5e6f7g8h9i0j",
  "supervisoryAuthority": [
    {
      "name": "<SupervisoryAuthority.name>",
      "country": "<SupervisoryAuthority.country>",
      "email": [
        "<SupervisoryAuthority.email>"
      ]
    }
  ]
}
JSON
```

**Save:** `SUPERVISORY_AUTHORITY_ID`.

## 10. Register your Wallet Relying Party

Create the RP record by linking the information and IDs from the previous steps. Choose a name and description that a Wallet user can recognise. See [TS5 §2.1](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/af9b1460f02eb1904120c0cb5c020568538378db/docs/technical-specifications/ts5-common-formats-and-api-for-rp-registration-information.md#21-walletrelyingparty) and [TS6 §2](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/8a0bc4d3829aa6e86de1c68891695add7c37b9b8/docs/technical-specifications/ts6-common-set-of-rp-information-to-be-registered.md#2-common-data-set).

Replace `<WalletRelyingParty.entitlements>` with the complete URI for the RP's role. The ETSI-defined entitlement URIs used by this guide are:

- `https://uri.etsi.org/19475/Entitlement/Service_Provider`
- `https://uri.etsi.org/19475/Entitlement/QEAA_Provider`
- `https://uri.etsi.org/19475/Entitlement/Non_Q_EAA_Provider`
- `https://uri.etsi.org/19475/Entitlement/PUB_EAA_Provider`
- `https://uri.etsi.org/19475/Entitlement/PID_Provider`
- `https://uri.etsi.org/19475/Entitlement/QCert_for_ESeal_Provider`
- `https://uri.etsi.org/19475/Entitlement/QCert_for_ESig_Provider`
- `https://uri.etsi.org/19475/Entitlement/rQSealCDs_Provider`
- `https://uri.etsi.org/19475/Entitlement/rQSigCDs_Provider`
- `https://uri.etsi.org/19475/Entitlement/ESig_ESeal_Creation_Provider`

For the Launchpad mDL entitlement test only, the service also accepts:

- `https://uri.etsi.org/19475/Entitlement/mDL_Provider`

This is a Launchpad test value. It is not an entitlement URI defined in the applicable ETSI specifications.

For example, choose `https://uri.etsi.org/19475/Entitlement/PID_Provider` for a PID provider. If that issuer also acts as a service provider requesting attestations, include `https://uri.etsi.org/19475/Entitlement/Service_Provider` as well. If the RP has several applicable entitlements, include each complete URI as a separate quoted entry in the array.

Complete the remaining fields as follows:

- `<WalletRelyingParty.tradeName>` and `<MultiLangString.content>`: the RP's user-facing name and description.
- `<WalletRelyingParty.supportURI>`: the RP's support page.
- `<MultiLangString.lang>`: language of the service description, from the list in step 7. **One language is sufficient for Launchpad**; additional `srvDescription` entries in other languages are optional.
- `<PROVIDER_ID>` and `<SUPERVISORY_AUTHORITY_ID>`: IDs from steps 5 and 9.
- `intendedUse_ids`: **all** intended-use IDs created for this RP in step 7. For two uses, write `"intendedUse_ids": [31, 32]`, replacing the example IDs with your own.
- `providesAttestations_id`: IDs from step 8, or `[]` if the RP issues no attestations.
- `<WalletRelyingParty.isPSB>`: `true` or `false`, without quotes.

Keep `registryURI` as shown and leave `"usesIntermediary": []`: this guide covers RPs that do not use intermediaries. For a setup with intermediaries, use the [Swagger API documentation](https://itb.registry.serviceproviders.eudiw.dev/swagger/).

```bash
curl --silent --show-error --fail-with-body \
  "$BASE_URL/wallet_rp/create" \
  --header 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{
  "hash_pid": "1a2b3c4d5e6f7g8h9i0j",
  "WalletRelyingParty": [
    {
      "tradeName": "<WalletRelyingParty.tradeName>",
      "provider_id": <PROVIDER_ID>,
      "supervisoryAuthority": <SUPERVISORY_AUTHORITY_ID>,
      "registryURI": "https://itb.registry.serviceproviders.eudiw.dev/",
      "supportURI": [
        "<WalletRelyingParty.supportURI>"
      ],
      "srvDescription": [
        {
          "lang": "<MultiLangString.lang>",
          "content": "<MultiLangString.content>"
        }
      ],
      "intendedUse_ids": [
        <INTENDED_USE_ID>
      ],
      "providesAttestations_id": [
        <PROVIDED_ATTESTATION_ID>
      ],
      "usesIntermediary": [],
      "entitlements": [
        "<WalletRelyingParty.entitlements>"
      ],
      "isPSB": <WalletRelyingParty.isPSB>
    }
  ]
}
JSON
```

**Save:** `WRP_ID`. Use `"providesAttestations_id": []` if you skipped step 8. The empty `usesIntermediary` array is for the non-intermediary scenario covered here.

## 11. Get the registration certificate — WRPRC

Use the numeric `INTENDED_USE_ID` returned in step 7; do not substitute the text reference you supplied.

Request the WRPRC for your RP using the record linked in step 10. If you registered several records in step 7, repeat the request with each corresponding ID. Save each response in a separate directory to avoid overwriting earlier certificates:

```bash
mkdir -p "<LOCAL_RP_DIRECTORY>/<LOCAL_USE_DIRECTORY>"
cd "<LOCAL_RP_DIRECTORY>/<LOCAL_USE_DIRECTORY>"
```

These directory placeholders are local file-management choices. Replace them with short names identifying the RP and intended use, such as `rp1/age-check`. For the next intended use, return to your original working directory and choose a different intended-use directory. Keep the same terminal so that `BASE_URL` remains set.

```bash
curl --silent --show-error --fail-with-body \
  "$BASE_URL/intended_use/certificate" \
  --header 'Content-Type: application/json' \
  --output wrprc-response.json \
  --data-binary @- <<'JSON'
{
  "hash_pid": "1a2b3c4d5e6f7g8h9i0j",
  "intended_use_id": <INTENDED_USE_ID>
}
JSON
```

**Expected:** a successful JSON response with `data.file_base64` (JWT) and `data.cose_base64` (COSE). Extract both files:

```bash
python3 - <<'PYTHON'
import base64, json
from pathlib import Path
r = json.loads(Path("wrprc-response.json").read_text())
if r.get("status") != "success":
    raise SystemExit(r.get("message", "Certificate request failed"))
for field, filename in [("file_base64", "wrprc.jwt"), ("cose_base64", "wrprc.cose")]:
    value = r["data"][field]
    Path(filename).write_bytes(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)))
    print("Saved", filename)
PYTHON
```

## 12. Get the access certificate — WRPAC

Use `WRP_ID` from step 10. Save the output in a directory identifying the RP. Choose `<password>` to protect the PKCS#12 file. Enter it in the request below using valid JSON escaping. Keep the password and resulting private key private.

```bash
curl --silent --show-error --fail-with-body \
  "$BASE_URL/wallet_rp/certificate" \
  --header 'Content-Type: application/json' \
  --output wrpac-response.json \
  --data-binary @- <<'JSON'
{
  "hash_pid": "1a2b3c4d5e6f7g8h9i0j",
  "wrp_id": <WRP_ID>,
  "password": "<password>"
}
JSON
```

**Expected:** a successful JSON response with the PKCS#12 file encoded in `data.file_base64`. Extract it:

```bash
python3 - <<'PYTHON'
import base64, json
from pathlib import Path
r = json.loads(Path("wrpac-response.json").read_text())
if r.get("status") != "success":
    raise SystemExit(r.get("message", "Certificate request failed"))
Path("wrpac.p12").write_bytes(base64.b64decode(r["data"]["file_base64"], validate=True))
print("Saved wrpac.p12")
PYTHON
```

The response's `filename` may say `document_with_signature.json`; use `wrpac.p12` for the decoded access-certificate bundle.

## Generate deliberately invalid certificates for testing

The Launchpad service provides separate error-test routes that generate deliberately invalid WRP certificates. Use them **only to verify that your component detects and rejects invalid certificates**. Do not use the resulting certificates as credentials in a normal Launchpad flow.

Complete the applicable registration steps above before using these routes. Each error-test request uses the same payload as the corresponding normal certificate request, with one additional field: `error_type`. Use the same `hash_pid`, `WRP_ID` or `INTENDED_USE_ID` that you would use for a normal request.

| Certificate under test | Error-test route | Accepted `error_type` | What your component should detect |
| ---------------------- | ---------------- | --------------------- | --------------------------------- |
| WRPAC | `/wallet_rp/certificate_error` | `invalid_signature` | The WRPAC signature is invalid. |
| WRPAC | `/wallet_rp/certificate_error` | `expired` | The WRPAC is outside its validity period. |
| WRPRC | `/intended_use/certificate_error` | `invalid_signature` | The WRPRC signature is invalid. |

### Test an invalid WRPAC signature

```bash
curl --silent --show-error --fail-with-body \
  "$BASE_URL/wallet_rp/certificate_error" \
  --header 'Content-Type: application/json' \
  --output wrpac-invalid-signature-response.json \
  --data-binary @- <<'JSON'
{
  "hash_pid": "1a2b3c4d5e6f7g8h9i0j",
  "wrp_id": <WRP_ID>,
  "password": "<password>",
  "error_type": "invalid_signature"
}
JSON
```

Decode the returned bundle without overwriting the valid WRPAC created in step 12:

```bash
python3 - <<'PYTHON'
import base64, json
from pathlib import Path
r = json.loads(Path("wrpac-invalid-signature-response.json").read_text())
if r.get("status") != "success":
    raise SystemExit(r.get("message", "Certificate request failed"))
Path("wrpac-invalid-signature.p12").write_bytes(
    base64.b64decode(r["data"]["file_base64"], validate=True)
)
print("Saved wrpac-invalid-signature.p12")
PYTHON
```

The test succeeds if your component rejects this WRPAC because its signature is invalid.

### Test an expired WRPAC

```bash
curl --silent --show-error --fail-with-body \
  "$BASE_URL/wallet_rp/certificate_error" \
  --header 'Content-Type: application/json' \
  --output wrpac-expired-response.json \
  --data-binary @- <<'JSON'
{
  "hash_pid": "1a2b3c4d5e6f7g8h9i0j",
  "wrp_id": <WRP_ID>,
  "password": "<password>",
  "error_type": "expired"
}
JSON
```

Decode the returned bundle without overwriting the valid WRPAC:

```bash
python3 - <<'PYTHON'
import base64, json
from pathlib import Path
r = json.loads(Path("wrpac-expired-response.json").read_text())
if r.get("status") != "success":
    raise SystemExit(r.get("message", "Certificate request failed"))
Path("wrpac-expired.p12").write_bytes(
    base64.b64decode(r["data"]["file_base64"], validate=True)
)
print("Saved wrpac-expired.p12")
PYTHON
```

The test succeeds if your component rejects this WRPAC because it has expired.

### Test an invalid WRPRC signature

The WRPRC error-test route supports only `invalid_signature`:

```bash
curl --silent --show-error --fail-with-body \
  "$BASE_URL/intended_use/certificate_error" \
  --header 'Content-Type: application/json' \
  --output wrprc-invalid-signature-response.json \
  --data-binary @- <<'JSON'
{
  "hash_pid": "1a2b3c4d5e6f7g8h9i0j",
  "intended_use_id": <INTENDED_USE_ID>,
  "error_type": "invalid_signature"
}
JSON
```

Extract both returned WRPRC formats without overwriting the valid files created in step 11:

```bash
python3 - <<'PYTHON'
import base64, json
from pathlib import Path
r = json.loads(Path("wrprc-invalid-signature-response.json").read_text())
if r.get("status") != "success":
    raise SystemExit(r.get("message", "Certificate request failed"))
for field, filename in [
    ("file_base64", "wrprc-invalid-signature.jwt"),
    ("cose_base64", "wrprc-invalid-signature.cose"),
]:
    value = r["data"][field]
    Path(filename).write_bytes(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)))
    print("Saved", filename)
PYTHON
```

The test succeeds if your component rejects the WRPRC because its signature is invalid. A successful response from the Registrar means that the test certificate was generated; it does not mean that the certificate should pass validation.

## Ready for integration

For each RP, check that you have `wrpac.p12` and the `wrprc.jwt` and `wrprc.cose` files saved in step 11. If you made several registration-certificate requests, keep each result in its own directory. The JWT and COSE files are two formats of the same WRPRC. Use the WRPRC format expected by your test component and import the PKCS#12 bundle using the password chosen in step 12.

If OpenSSL is available, check that the bundle opens and inspect its contents without exporting the private key:

```bash
openssl pkcs12 -in wrpac.p12 -info -noout
```

Successful decoding does not establish trust or interoperability. Configure the trust material required by your test setup and check that your component can use the certificates before the session.

## If a request fails

| Response or symptom                 | What to check                                                                                            |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `Invalid hash_pid`                | Use`1a2b3c4d5e6f7g8h9i0j` with the Launchpad service address above.                                    |
| Missing fields / invalid JSON       | Replace all placeholders, keep text quoted, and use numbers for IDs.                                     |
| Record does not belong to this user | Use IDs created with the same`hash_pid` in the same environment.                                       |
| Invalid date                        | Use`YYYY-MM-DD`; set `revokedAt` to the WRPRC validity end date.                                     |
| Intended use has no WRP associated  | Complete step 10 before requesting the WRPRC.                                                            |
| Invalid entitlement or policy type  | Copy an exact supported URI, including its case.                                                         |
| Certificate request fails           | Keep the HTTP error and response message for the Registrar team. Do not share passwords or private keys. |

*Field descriptions are adapted and summarised from European Union TS5, TS6 and TS2 (© European Union, 2025–2026), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*

## Changes from version 1.0

- Updated the document version and date to 1.1 and 2026-10-26.
- Added the Launchpad-only `mDL_Provider` test entitlement to the role-selection table and to the instructions for describing issued attestations and registering the Wallet Relying Party.
- Clarified that `https://uri.etsi.org/19475/Entitlement/mDL_Provider` is a Launchpad 2026 test value and is not an entitlement URI defined in the applicable ETSI specifications.
- Added the Launchpad-only error-test routes for generating WRPACs with an invalid signature or expired validity and WRPRCs with an invalid signature.
