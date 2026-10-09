# Accepted-calendar human collection V2

This additive workspace uses only the accepted Development subset from
`MNQ_GLOBEX_HISTORICAL_SESSION_CALENDAR_V1` /
`CME_GLOBEX_4H_SESSION_ANCHORED_V2`. The old labeler and all old labels remain
separate. No provider threshold, execution behavior or outcome engine changes.

## Start and label

Start the Lab with `./run_app.sh`, then open http://127.0.0.1:5173 and choose
**Zone Labeler → Accepted-calendar Ground Truth**. If an older backend is already
running, restart it before using the new API. Frozen identities and criteria are
expandable above the chart. Legacy labeling is explicitly separated below.

1. Open the frozen blind window. Only accepted complete full candles through the
   cutoff are delivered. Unknown sessions and shortened/incomplete candles are
   omitted, never synthesized. Gaps must not be interpreted as adjacent candles.
2. Label **all zones confirming at this cutoff**, not earlier zones visible in the
   context. Select VALID_SUPPLY, VALID_DEMAND or explicitly NOT_A_ZONE. There is no
   default human decision. Base selection starts unapproved and no rectangle is
   initially drawn. The last base candle must precede 1–3 adjacent departure bars.
   Human labels may disagree with V2's 1–3-base/1–2-departure thresholds.
3. Calculate and approve the human rectangle and confirm departure exclusion.
   Supply uses highest wick / lowest body; demand uses lowest wick / highest body.
   Uncheck “last zone” to record multiple zones, then finish the window. No-zone
   decisions require no invented base selection.
4. Review all 80 blind windows and all 24 near-miss windows. Near-miss reasons and
   candidate base selections are hidden. Near misses are a separate diagnostic
   sample, not ordinary blind observations or known human negatives.
5. Only then can Mode B expose the 50 provider proposals. Choose ACCEPT_EXACT,
   ACCEPT_ZONE_WRONG_BASE, ACCEPT_ZONE_WRONG_BOUNDARIES or REJECT_NOT_A_ZONE.
   Accepted corrections require an approved human base/rectangle. V2 is not altered.

Do not inspect private sampling CSVs/provider files while blind labeling. Local
trusted-user tooling cannot prevent deliberate inspection outside the UI. Prior
exposure to this research cannot be undone. “Blind” describes this collection UI,
not universal independence of the human observer.

## Frozen sample and coverage

Seed 20261008. Blind sampling is uniform without replacement over qualifying
accepted three-adjacent-full-bar cutoffs, 20 per year. It does not consult provider
hits. A chart shows up to 15 preceding inventory positions, retaining only accepted
candles. Some windows have fewer candles because unresolved intervals are omitted.
The incoming leg and eligible base/departure are judged at the displayed cutoff.
There is no retrospective extension of the chart to a later reaction.

Provider selection is deterministic round-robin across available year × side ×
base count × pattern strata, 25 proposals per side. Sparse strata are not invented.
There are four examples per near-miss category; no-overlap cases may have additional
violations. Three-departure cases test human disagreement with the frozen V2
confirmation limit; V2 still uses at most two departures.

All 104 unresolved **civil session labels** are excluded, including chart context.
These labels differ from the NY calendar date of an evening bar. The complete
exclusion list/hash, calendar hash, derived bar-contract hash, canonical bar hash,
dataset identity/hash and provider source/configuration hashes are frozen in
`work/zone-ground-truth-v2-calendar-accepted/frozen_sampling_protocol.json`.
Old candidate identities are never used by this workspace.

## Immutable labels and corrections

New records live under `storage/zone_ground_truth_v2_calendar_accepted/`, separate
from old annotations and the application database. Exclusive file creation, fsync
and a process lock serialize appends. Each annotation stores the human decision,
chart timestamps, selected base IDs, boundaries, notes, approval flags, identity,
protocol hash and UTC annotation time. Provider reviews additionally freeze the
exact original proposal. Corrections refer to an existing record, increment its
version, and leave all prior bytes intact. A correction cannot branch.

Once provider proposals are exposed, blind labels are frozen against further
editing to prevent retrospective contaminated corrections. A new independent
collection is needed for such changes. Snapshots are content-addressed and never
replace an older export. No automated browser test records are production labels.

## Matching, metrics and acceptance

Matching is one-to-one maximum-cardinality with stable ordering: same direction,
same confirmation opportunity, intersecting base intervals and same last base
candle (same departure sequence). Exact base, proximal, distal and availability
agreement remain separate. Different last-base dates can be concept misses even
when rectangles overlap; this strict rule is frozen, not chosen after labels.

Provider-review precision counts accepted concepts among all reviewed proposals.
Blind recall counts matched human zones among all human zones in completed blind
windows. Unmatched proposals within those windows are reported separately.
Near misses are excluded from both primary ratios. Base/boundary/time agreement
uses concept-matched rows from the two primary samples, with denominators and
mode-specific breakdowns reported. Overlapping observations are not independent
population estimates. Because cutoffs are fixed, availability agreement is a
conditional mechanical check, not population confirmation-time accuracy.

Before any human labels, thresholds are frozen:

| Tier | Precision / recall | Base / proximal / distal agreement | Availability |
|---|---:|---:|---:|
| ACCEPTED | ≥90% each | ≥90% each | ≥95% |
| ACCEPTED_WITH_LIMITATIONS | ≥80% each | ≥80% each | ≥90% |

Require all requested samples completed and at least ten valid human zones in
blind windows. Missing coverage or undefined metrics gives
`INSUFFICIENT_HUMAN_LABELS`; below the lower tier after adequate coverage gives
`HUMAN_GROUND_TRUTH_REJECTED`. These are disclosed engineering agreement criteria,
not statistical guarantees or permission to run forward-outcome research.

## Exports and preservation

Use Export immutable snapshot for JSON history/protocol/current comparison.
`scripts/zone_ground_truth_collection.py export` also writes CSVs and a reproducible
snapshot bundle. The initial requested deliverables explicitly show zero human
labels and null agreement metrics. They must not be mistaken for completed research.
No Validation/OOS outcomes, future reactions, paid downloads or provider tuning
are used. Database migrations are unnecessary. Existing studies and annotations
remain unchanged. Diagnostic draft sampling artifacts are archived locally and
are not the active frozen collection.
