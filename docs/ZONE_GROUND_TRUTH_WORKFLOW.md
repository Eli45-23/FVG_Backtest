# Development Zone Ground Truth workflow

V2 remains **PROVISIONAL_PENDING_HUMAN_GROUND_TRUTH**. This workspace measures
human/provider definition agreement, not trading performance. The screenshots
are visual-semantic references; historical OHLC supplies numerical boundaries;
only decisions entered by the human labeler supply ground truth. Automated test
annotations are not human evidence.

## Open and label

Start the existing application with `./run_app.sh` and open **Zone Labeler**.
The only supported interval is [2020-01-01, 2024-01-01) New York. There is no
Validation/OOS selection, reveal endpoint or outcome request in this workspace.

1. Navigate next/previous, choose a saved random seed, or jump to a New York time.
   A seed deterministically selects the same opportunity from the fixed bar set.
   Opportunities include ordinary complete bars, not just provider detections.
2. Select first/last base candles and SUPPLY or DEMAND. The selected base must
   end immediately before one or two proposed departure candles. The backend
   rejects overlapping base/departure indices, broken adjacency, incomplete or
   shortened selected candles. Base length is deliberately not restricted to the
   provider's three-candle limit: human truth must be able to disagree with it.
3. Calculate the rectangle. Supply top = maximum base high, bottom = minimum
   base body edge. Demand bottom = minimum base low, top = maximum base body edge.
   Departure candles never enter those reducers.
4. Inspect the proposed departure and availability, body ratios, ATR ratios and
   boundaries. Explicitly confirm that the selected base excludes departure.
   The human must identify a visually misselected departure; the application
   cannot infer discretionary base membership without assuming the detector's
   own definition. It enforces disjoint intervals and asks for human confirmation.
5. Approve the rectangle for VALID_SUPPLY/VALID_DEMAND, or reject with NOT_A_ZONE.
   Save notes about definition only. No subsequent reaction should inform the label.
6. Export annotations, then freeze the label set and compare the provider.

Changing a selection clears approval and requires a new calculated preview.
Server-side re-computation and its hash prevent saving a stale/tampered preview.
The chart shows up to eight preceding context candles and ends at the proposed
confirmation candle. No candles after confirmation, forward outcomes, existing
provider predictions or future lifecycle information are returned in the preview.
The drawn base origin is unavailable until confirmation. The screen ends there,
so forward extension represents a rule, not a view of subsequent price behavior.
Navigation can expose adjacent periods over time; the software cannot erase prior
human market knowledge. Record that limitation when reviewing labels.

## Numerical foundation and limits

The labeler reuses the existing independently reduced four-hour engineering
artifact. Its SHA-256 must match the saved audit manifest. No source reconstruction
or detector tuning occurs on app startup. Identity includes dataset hashes, the
full saved session construction configuration, bar-file hash and provider config.

The candidate preset is `CME_GLOBEX_4H_SESSION_ANCHORED_V1`, anchored 18:00
America/New_York. Full starts: 18:00, 22:00, 02:00, 06:00, 10:00. The final 14:00
bar is shortened at close and is not selectable. DST uses timezone-aware NY.
Original Databento prices were aggregated as integers before division by 1e9;
MNQ quarter-point prices remain exact in the resulting floating-point OHLC.
ATR14 is SMA true range over eligible full bars, preserved across scheduled
closures and reset on missing coverage. Missing ATR is shown as unavailable.

**Historical calendar disagreements remain unresolved.** The workspace prominently
marks this construction provisional. Labels freeze that exact identity and cannot
be silently transferred to corrected bars. Missing/shortened context is not
synthesized. BOS/CHoCH are unavailable, not false. FVG is the strict three-candle
wick gap ending at the proposed confirmation. This workspace does not repair or
approve the blocked provider, and does not establish numerical equivalence with
TradingView's continuous-contract adjustment settings.

## Immutable persistence

No production database migration is needed. Artifacts live in
`$LAB_STORAGE/zone_ground_truth_v1/` (default `storage/zone_ground_truth_v1/`).
Atomic, exclusive content-addressed JSON files hold annotations, frozen snapshots
and comparison reports. Repeated identical saves are idempotent; there are no
update/delete endpoints. Every annotation includes recorded-at time, selected
bar timestamps, seed, decision, notes, approval, calculated preview and identities.
Snapshots embed their exact annotations; comparisons reference the snapshot and
provider source hash. Export uses complete JSON, without sampling.

One decision per last-base-candle/side opportunity is required in a snapshot.
Conflicting annotation revisions are preserved and block the current all-labels
freeze; selective adjudication/revision management is a future extension. Avoid
saving contradictory revisions in this first workflow.

## Agreement protocol (not an edge study)

Comparisons run only after freezing human labels. Replaying V2 uses Development
bars no later than the latest labeled confirmation. A prediction matches an
opportunity by **last base candle + side**, and must be available by that human
confirmation. Full base membership, boundaries and exact availability are scored
separately. Earlier availability is a timing disagreement; later availability is
a miss at the observed cutoff. Multiple predictions in one opportunity count as
one positive prediction, with count disclosed and deterministic matching preferring
exact base membership then zone ID.

- Positive human label + matched prediction: true positive.
- NOT_A_ZONE + matched prediction: false positive.
- Positive human label + no match: false negative.
- NOT_A_ZONE + no match: true negative.
- Precision = TP/(TP+FP); recall = TP/(TP+FN); undefined denominators return null.
- Base, exact-boundary and availability agreement are conditional on true positives.
- Reports include supply/demand and one/two/three (plus any longer) base groups.

These are **reviewed-opportunity** statistics, not exhaustive zone/population
precision and recall. Unreviewed predictions are not automatically false positives.
Unlabeled real zones cannot be counted as false negatives. Broader claims require
an independently specified exhaustive review coverage protocol. No threshold
optimization, predictive outcome interpretation or automatic provider acceptance
is performed. No trading edge may be inferred.

## API and verification

`/api/zone-labels/candidate`, `/preview`, `/annotations`, `/freeze`,
`/compare/{snapshot_id}`. Candidate navigation and preview are read-only. Saves,
freezes and comparisons create new immutable artifacts only.

Tests: `work/.venv/bin/python -m pytest backend/tests/test_zone_labels.py tests/test_zone_v2.py -q`
Frontend: `cd frontend && npm test && npm run build`.
Browser: run backend with a temporary LAB_STORAGE, Vite with LAB_TEST_API_PORT,
then `LAB_TEST_URL=http://127.0.0.1:5187 npx playwright test zone-labeler-e2e.spec.ts`.
Never point synthetic browser annotation tests at the user's label storage.
