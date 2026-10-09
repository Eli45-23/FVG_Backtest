# Backend test storage isolation

`backend/tests/conftest.py` must set a fresh temporary LAB_STORAGE before pytest
imports any test module. Database engines are initialized on module import; setting
an environment variable later in test_api.py does not relocate an existing engine.
Do not override storage again during module collection.

An import-order incident during the accepted-calendar labeler task exposed this
problem. Two broad suite runs created test-only rows in normal storage. Those IDs
were identified by execution timestamps, test names and parent links, quarantined,
and removed without resetting the database. Original IDs/counts, immutable trigger
SQL, foreign keys, source files and historical artifact hashes were checked.

The broad suite includes real February 2024 legacy integrations and a synthetic
OOS-reveal state-machine test. A Development-only task must **not** run that entire
suite merely because storage is isolated: storage isolation and research-period
isolation are separate requirements. Use synthetic/Development-scoped tests only
unless reserved-period integration execution is explicitly authorized.

The local incident report is at
`work/zone-ground-truth-v2-calendar-accepted/isolation-incident/INCIDENT_REPORT.md`.
The original stored studies remained intact and no original sealed study was
revealed. The task cannot truthfully claim that no Validation rows were accessed
by the overbroad test invocation. These test results were not used for provider
selection, tuning or research interpretation.
