# Changelog

## [0.2.2]

21 Jul 2026

### Fixed
- Fix for the error when entering dates in the “Intended Uses” field.

### Changed
- Changes to the database to support changes to the meta format in the provided attestations and credentials.
- The “meta” field is now an object instead of a string in the “provided attestation”.
- The “meta” field is now an object instead of a string in the “Credential.

---

## [0.2.1]

06 Jul 2026

### Fixed
- Fixed Certificate Authority fallback selection in the EJBCA integration when the country code is not configured.
- Fixed the `credential/create` section in the Guide documentation.

### Changed
- Updated Docker configuration and environment variables.
- Improved API error handling and validation messages.
- Minor improvements to the authentication flow documentation.

---

## [0.2.0]

03 Jun 2026

### Added
- Full implementation aligned with **EU Technical Specification 5** (Common formats and API for Relying Party Registration Information).
- Full implementation aligned with **EU Technical Specification 6** (Common Set of Relying Party Information to be Registered).
- Support for Wallet Relying Party registration.
- Registration certificate generation.
- Wallet access certificate generation.
- Public WRP search endpoints.
- Swagger API documentation.
- HTML User Guide.
- Complete REST API for:
  - Authentication
  - Legal Persons
  - Natural Persons
  - Legal Entities
  - Providers
  - Wallet Relying Parties
  - Intended Uses
  - Credentials
  - Policies
  - Laws
  - Identifiers
  - Supervisory Authorities
  - Provided Attestations

### Changed
- Refactored the registration workflow to comply with ETSI TS 119 475.
- Updated API responses to provide a consistent structure across endpoints.
- Improved certificate generation workflow.
- Improved validation and ownership checks for protected resources.