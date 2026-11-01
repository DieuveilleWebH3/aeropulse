# Security Policy

AeroPulse is an engineering demonstrator for aircraft predictive-maintenance
and fleet-health software. Security reports are welcome and should follow
coordinated disclosure.

## Supported versions

AeroPulse does not yet publish stable production releases.

| Version | Security support |
| --- | --- |
| `main` | Supported |
| Older branches, commits, and superseded development snapshots | Not supported |

This policy will be updated when versioned releases are introduced.

## Reporting a vulnerability

**Do not open a public issue containing vulnerability details, exploit code,
credentials, secrets, or proof-of-concept material.**

Preferred path:

1. Open the repository's **Security** area on GitHub.
2. Choose **Report a vulnerability** when private vulnerability reporting is enabled.
3. Include the affected component, impact, reproduction conditions, and a minimal
   proof of concept when appropriate.

If private vulnerability reporting is not enabled, open a minimal public issue
requesting a private security contact channel. Do not include sensitive technical
details in that issue.

Useful information in a private report includes:

- affected commit/version;
- affected API, worker, CI/CD, container, dependency, or infrastructure component;
- vulnerability class or CWE when known;
- realistic impact;
- reproduction steps;
- proof of concept;
- suggested mitigation, if available;
- whether the issue is already public or known elsewhere.

## Response targets

These are best-effort targets for this portfolio/open-source project:

- acknowledgement within 3 business days;
- initial triage within 7 business days;
- remediation timeline based on severity, exploitability, and scope;
- coordinated public disclosure after a fix or mitigation is available.

Complex issues may require additional time.

## Scope

Examples of issues in scope:

- authentication or authorization bypass;
- injection vulnerabilities;
- remote code execution;
- server-side request forgery;
- unsafe deserialization;
- privilege escalation;
- exposure of credentials, secrets, or sensitive operational data;
- dependency vulnerabilities with realistic AeroPulse impact;
- CI/CD or supply-chain compromise paths;
- container or cloud configuration weaknesses introduced by this repository;
- denial-of-service issues with credible impact.

Generally out of scope unless they create a software-security impact:

- PHM model quality or prediction accuracy;
- aviation certification or regulatory suitability;
- feature requests;
- unsupported historical snapshots;
- issues requiring an already fully compromised development machine.

## Sensitive and aerospace data

Do not submit proprietary aircraft telemetry, airline/customer information,
export-controlled material, credentials, or other confidential data. Use synthetic
or minimized reproduction data.

## Security advisories

Confirmed vulnerabilities may be handled through GitHub repository security
advisories so investigation and fixes can remain private until coordinated disclosure.

## No bug bounty

AeroPulse currently has no paid bug-bounty program. Responsible reports are still
appreciated and may be credited when desired and appropriate.
