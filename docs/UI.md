# Research workspace interface

The React app consumes `/catalog.json`, `/report.json`, and `/workspace.json`. All seven views run from static exports. The historical case catalogue remains a separate reading guide, never an empirical fallback.

## Views

- **Time machine:** switch between the eligible reviewed cohort and curated cases. Reviewed green cells come only from `reviewed.ledger.confirmed_year`; compound discovery milestones use their own gold marker in the case-study mode. Claims and identity priors both respect the displayed year. Uncertain identity contributions remain visible in the specimen pane.
- **Corpus & review:** source register, collection coverage, paginated exact-span proposals, plant-heading context, original table-row provenance, historical dates and edition dates kept separate. Search by source words or plant name and filter by source, category or review state.
- **Evidence ledger:** eligible species/indication outcomes, acquired study metadata, source links and review state. Original abstract text is served only by the local service. Offline cue suggestions remain visibly unreviewed. Copying suggested fields requires an explicit button and never changes the decision, personal attestation or saved review; abstaining suggestions cannot populate a verdict. Historical discovery stories sit in a separate collapsed section.
- **Backtest results:** freeze, outcome definition, category and novel-layer selectors; matched risk ratios and intervals, era ablation, temporal ranking benchmarks, reliability diagram and publication-bias scenario grids. No graph is created from null estimates.
- **Plant identities:** taxonomy candidates, expert prior drafts, reviewed distributions, availability dates and separate calibration status. Draft creation never claims expert review. Numeric name-match scores never become identity probabilities.
- **Research shortlist:** forward leads and hazard trails only when the exported model provides them. The prediction target is confirmation conditional on testing. Fit-ensemble spread is labelled as ensemble spread, not a confidence interval or an unconditional chance of success within twenty years.
- **The method:** estimand, matched comparisons, temporal windows, review boundaries, source rights and traditional-knowledge limitations.

## Local review and static operation

The app detects `/api/health` on local hosts. Local mode requires both `mode: "local"` and `review_enabled: true`; the API workspace must confirm local mode too. The hosted edition never pretends it can save a review.

A review requires an entered reviewer name, a decision, an evidence note and an explicit personal attestation. Claim reviews have separate historical-date and licence attestations plus a reviewed identity-group selector. Taxon reviews expose accepted name, family, backbone version, source, regional presence and hazard trail. Expert identity reviews expose candidate probabilities and the year when the prior could have been available. Acceptance and scientific eligibility remain distinct.

Reviews use `POST /api/reviews/{kind}/{record_id}` with an expected revision. Revision conflicts surface as errors. The hosted edition exports a JSON review batch with the same decision payload. An exported batch does not change any scientific state. Expert identity proposals use `POST /api/proposals/identity`; static mode exports the proposal instead. Unassigned draft probabilities stay null.

**Rebuild exports** starts `POST /api/rebuild`, polls the returned `/api/jobs/{id}` at most once per second and refreshes the workspace on completion. Rebuilds recompute eligibility and report state; they do not approve unresolved records. Collection and model-provider calls are not launched by this button.

## Validation

`node --test tests/frontend_model.mjs` checks the data boundary: unreviewed proposals cannot appear in the reviewed atlas, identity availability stays attached, discovery narratives cannot create green cells, missing analyses remain pending, and review payloads require explicit named attestation. `npm run build --prefix app/web` verifies the production application. Browser review is performed by the owning agent after the final export is generated.

The layout preserves the existing field/paper/forest/brass palette, botanical schematics and restrained mechanism. Tables scroll within their containers, the review queue is paginated, controls retain visible focus styles, navigation collapses on mobile, and dialogs constrain keyboard focus. Illustrations are schematic and cannot serve as botanical identification aids.
