# Security policy

## Supported versions

Traxy is currently pre-1.0. Security fixes are applied to the latest release.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting feature for this repository.
Do not open a public issue containing exploit details, credentials, private URLs,
or sensitive response data.

Include the affected version, reproduction steps, impact, and any suggested
mitigation. You should receive an acknowledgement within seven days.

## Scope and safe use

Traxy performs user-requested HTTP GET operations. Only check endpoints you are
authorized to access. Configuration files should not contain secrets. Use a CI
secret manager for any surrounding authentication or private deployment data.

