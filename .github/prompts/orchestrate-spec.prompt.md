# Orchestrate one AeroPulse specification

Use the `Spec Delivery Orchestrator` custom agent to coordinate delivery of the approved
specification provided by the user.

Requirements:

- do not let the orchestrator edit files directly;
- perform the architecture/ADR gate before implementation;
- delegate implementation to the appropriate specialist;
- obtain an independent Test Engineer review;
- obtain a Security & Quality Reviewer pass;
- stop on unresolved BLOCKER/HIGH findings;
- consolidate acceptance-criteria traceability and actual validation evidence;
- leave merge/approval to the human reviewer.

The objective is not maximum agent activity. Use the minimum number of delegations needed to
deliver the specification safely and reviewably.
