# v0.7 follow-up verification

Applied the supplied v0.7 bug-hunt patch to repository baseline 74fbb78. The baseline passed 95 existing tests but failed added regression cases for policy validation, transition chronology, anonymous IDs, bridge errors, pending challenge handling, owner keys, TTL forwarding, CLI epoch zero, and canonical challenges.

Fixed a further evidence-collector bug: unittest reports subtest failures through addSubTest, which the collector did not implement. A deliberate failing subtest produced one failure and no recorded outcome. The collector now preserves assertion failures and exceptions, including their subcase details. Added positive and negative regression tests.

Added a behavioral browser regression that clicks twice after an oracle mismatch and verifies that score and round progression remain unchanged. Added real Chromium/Pyodide startup, all 22 engine probes, signed request, storage reload and JSON export/import coverage. CI runs these separately from the mock interpreter UI checks.

Current synthetic evidence counts are generated in docs/CURRENT-TEST-RESULTS.md. Five external calculator checks remain pending; Safari/iPad hardware is not verified. GitHub CI results are recorded in the pull request rather than claimed in advance.

Local verification: 117 unit tests, 22 probes, 60 game cases, 168 policy cases and 50 ingress cases passed (417 recorded passes, zero failures). Local Chromium exited with SIGTRAP before startup; browser verification runs in GitHub CI.
