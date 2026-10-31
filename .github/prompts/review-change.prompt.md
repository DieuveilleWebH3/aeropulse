# Review an AeroPulse change

Review the attached/current change against:

- ticket acceptance criteria;
- `.github/copilot-instructions.md`;
- `docs/architecture/repository-structure.md`;
- relevant ADRs;
- relevant path-specific instructions.

Review independently rather than assuming existing code is correct.

Consider:

- functional correctness;
- edge cases;
- data integrity;
- concurrency;
- idempotency;
- security;
- failure handling;
- API/contract compatibility;
- architecture boundaries;
- SOLID/KISS/DRY/YAGNI;
- test quality;
- observability;
- performance risks that are supported by evidence.

Classify findings as BLOCKER, HIGH, MEDIUM, LOW, or NIT.

For each material finding give:

- file/location;
- issue;
- impact;
- remediation;
- merge-blocking: yes/no.

Do not invent issues merely to produce findings.

End with:

- overall recommendation;
- residual risks;
- tests/checks that should be run.
