# Research campaign lifecycle — version 1

2026-10-28. State is persisted; displayed progress never represents invented percentages.

1. **DRAFT**: idempotent creation freezes objective, account/template, finite parameter domain,
   methodology, budgets and source. An actual-model draft may exist while its models are unavailable.
2. **AWAITING_APPROVAL**: REQUEST_APPROVAL → owner approves the exact campaign digest, research-only
   bounds and no-promotion statement. Server revalidates every allowed plan and reserves an active
   campaign slot atomically under a PostgreSQL advisory lock. Invalid prerequisites refuse approval.
3. **QUEUED → PLANNING**: fixed worker acquires a global worker slot, runtime row lock and expiring
   UUID lease. Fixture mode produces explicit SYNTHETIC_FIXTURE hypothesis/candidate; AI mode requires
   owner submission through Research role and explicit acceptance of validated structured output.
4. **AWAITING_APPROVAL / SUBMIT_EXPERIMENT**: the owner reviews the exact plan ID/hash and acknowledges
   it. Original Phase5 authorization, quotas, dataset/risk checks and idempotency execute in the same
   transaction as the immutable campaign/run link. No worker impersonates an owner.
5. **TESTING → EVALUATING**: only a genuinely successful existing ResearchJob advances. Complete
   hash-verified canonical MinIO evidence is required; sampled charts are never metric inputs.
6. **CRITIQUING**: fixture objections are deterministic, explicitly synthetic. Actual Critic uses a
   separate owner-reviewed Phase6 request and strict inert contract. Canonical evaluation is not
   replaced by a model claim. Feedback links the plan, evidence, decision and critique.
7. **READY_FOR_NEXT_ITERATION → PLANNING**: only justified training-only follow-up within every
   original bound; another exact owner handoff is required. Repeated training is labeled exposed.
8. **COMPLETED**: bounded research ended, including rejected hypotheses; not a profitability or
   trading eligibility signal. **STOPPED** includes insufficient evidence or acknowledged cancellation.
   **FAILED** records terminal child execution failure. **UNKNOWN** preserves uncertain outcomes.

## Controls and recovery

PAUSE blocks new coordinator work; already submitted children may finish. RESUME requires owner
MFA and valid original prerequisites; it cannot extend the deadline or budgets. CANCEL is a request,
not an acknowledgment. Existing child cancellation must reach terminal state before STOPPED is
acknowledged. An UNKNOWN AI child remains unresolved rather than being declared canceled.
A deadline or revoked source triggers fail-closed stopping, retaining the precise reason.

Leases expire after60 seconds. Restarted workers reconcile immutable experiment links and durable
ResearchJob state instead of issuing replacement backtests. Rolled-back metadata/storage failures
enter UNKNOWN with a bounded recovery marker; an already committed sequence is reconciled, not
replayed. Three abandoned/failing claims in an unresolved recovery sequence require owner review;
metadata recovery alone does not reset that counter; uncertain work continues
to occupy its concurrency slot. Waiting rows use a short scheduling lease to avoid starving peers.
No arbitrary test sleeps or increased browser timeouts establish correctness.

## API and inspection

GET list supports limit25 and offset; lineage limit100 and offset. All reads require full identity
and owner scope; mutation requires OWNER, CSRF and recent MFA. Create key/digest conflicts are409;
plan review mismatch is409; invalid typed input is422. Read-only reloading does not resubmit work.
Lineage contains Hypothesis → Candidate → Plan → Experiment → Evidence → Evaluation → Critique →
Feedback → next Hypothesis, plus immutable authorizations, controls and state transitions.
