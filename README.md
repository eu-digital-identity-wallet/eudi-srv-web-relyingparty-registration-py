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


## How to contribute

We welcome contributions to this project. To ensure that the process is smooth for everyone
involved, follow the guidelines found in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

### License details

Copyright (c) 2023 European Commission

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.