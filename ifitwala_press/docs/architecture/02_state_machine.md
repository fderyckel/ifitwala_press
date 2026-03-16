# 02_state_machine.md

## Purpose

This document locks the environment lifecycle state machine for **Ifitwala_Press**.

The goal is to prevent lifecycle drift.

In a control plane, state is not decoration.
State determines what operators can do, what automation may do, what policies apply, and how the system explains reality.

This document defines:

- the canonical environment states
- the meaning of each state
- allowed transitions
- forbidden transitions
- actions expected per state
- failure handling rules
- audit logging expectations

This state machine applies primarily to **Tenant Environment**.

---

## Design principles

### 1. State must reflect operational truth
A state should correspond to a real operational condition, not just a vague label.

### 2. States must be few but meaningful
Too many states create noise.
Too few states create ambiguity.

### 3. Transitions must be governed
Operators must not freely jump between states unless explicitly allowed.

### 4. Failures must be visible
If something critical fails, it must appear in state and logs.

### 5. Sandbox and production are different journeys
The state machine must support both, without pretending they are the same process.

---

# 1. Canonical environment states

The current canonical environment states are:

1. Lead
2. Sandbox Provisioning
3. Sandbox Active
4. Sandbox Expired
5. Production Qualification
6. Production Provisioning
7. Live
8. Suspended
9. Archived
10. Provisioning Failed

This list is intentionally short.
Do not expand it casually.

---

# 2. State definitions

## 2.1 Lead

### Meaning
The tenant/environment relationship exists conceptually, but no usable environment is provisioned yet.

This is typically:
- a prospect tenant before sandbox creation
- an intended production environment record before actual provisioning starts

### Characteristics
- no working site yet
- no active domain expected yet
- no production guarantees
- mostly metadata and intent

### Typical operator questions
- Should we create a sandbox?
- Is this tenant qualified for any environment creation?
- What hosting/policy applies?

### Expected allowed actions
- Create Sandbox
- Prepare for Production Qualification
- Archive (if abandoned early)

---

## 2.2 Sandbox Provisioning

### Meaning
A sandbox environment is currently being created.

### Characteristics
- infra/site creation underway
- site may be partial or unusable
- demo data/template loading may be underway
- quotas and expiry should be assigned

### Typical operator questions
- Did site creation succeed?
- Did app install complete?
- Did demo data load?
- Did hostname setup complete?

### Expected allowed actions
- Retry provisioning if the platform supports it
- Cancel provisioning
- Mark failed if provisioning cannot complete

### Notes
Do not treat this as an active trial state.
It is a build state.

---

## 2.3 Sandbox Active

### Meaning
A sandbox environment exists and is usable.

### Characteristics
- accessible for trial/demo use
- disposable
- typically shared infra
- lower SLA expectations
- usually limited quotas
- often has an expiry date

### Typical operator questions
- Is the sandbox being used?
- Is it nearing expiry?
- Is the customer qualified for production?
- Does it need reset?

### Expected allowed actions
- Reset Sandbox
- Expire Sandbox
- Qualify for Production
- Suspend if absolutely needed
- Archive if abandoned

---

## 2.4 Sandbox Expired

### Meaning
The sandbox is no longer active for normal use.

### Characteristics
- access may be blocked or limited
- environment may still exist temporarily
- data may still be retained for a grace period
- still eligible for review, reactivation, or conversion depending on policy

### Typical operator questions
- Should we reactivate it?
- Should we convert the tenant to production?
- Should we archive/delete it?

### Expected allowed actions
- Reactivate Sandbox
- Qualify for Production
- Archive

---

## 2.5 Production Qualification

### Meaning
The tenant has moved beyond trial intent and is being qualified for real production provisioning.

### Characteristics
- commercial and operational decision point
- hosting tier should be clear
- database mode should be chosen
- conversion strategy should be clear
- production readiness should be reviewed

### Typical operator questions
- Standard or VIP?
- Shared DB or dedicated DB?
- Fresh production site or selective migration?
- Is the tenant operationally ready?

### Expected allowed actions
- Approve Production Provisioning
- Return to Sandbox Active only by explicit decision
- Archive if the deal dies

### Notes
This is a checkpoint state.
Do not skip it casually.

---

## 2.6 Production Provisioning

### Meaning
The production environment is currently being created or configured.

### Characteristics
- site creation underway
- DB placement selected
- policy applied
- routing/domain work may be underway
- backup/monitoring baseline should be prepared

### Typical operator questions
- Did production site creation succeed?
- Did migrations complete?
- Is the domain ready?
- Is the environment healthy enough to go live?

### Expected allowed actions
- Retry provisioning
- Mark failed
- Continue to Live once checks pass

### Notes
Do not use this state as a vague limbo.
Either provisioning is actively happening, or it failed, or it completed.

---

## 2.7 Live

### Meaning
The environment is actively serving as a real production environment.

### Characteristics
- production-grade
- intended for real school operations
- backed up
- monitored
- policy-bound
- billable or commercially relevant

### Typical operator questions
- Is it healthy?
- Is it saturated?
- Is it underpriced?
- Does it need upgrade or isolation change?
- Is the subscription healthy?

### Expected allowed actions
- Suspend
- Archive (rare, intentional)
- Refresh health / usage / cost
- Update routing/domain details
- Change hosting policy carefully through governed action

---

## 2.8 Suspended

### Meaning
The environment exists but is intentionally not in normal active use.

### Typical reasons
- billing issue
- contract issue
- operational hold
- security concern
- customer request
- end-of-term pause

### Characteristics
- data retained
- access restricted
- environment may still incur limited costs
- operational actions may still be allowed internally

### Typical operator questions
- Is this reversible?
- Why was it suspended?
- When should it be restored or archived?

### Expected allowed actions
- Restore to Live
- Archive
- Review costs/retention impact

---

## 2.9 Archived

### Meaning
The environment is no longer operationally active and is considered closed.

### Characteristics
- terminal or near-terminal state
- active use ended
- infra likely removed or frozen
- retention policy governs what remains
- should not serve live traffic

### Typical operator questions
- What remains retained?
- Is restore allowed?
- Is the archive policy complete?

### Expected allowed actions
- Very limited
- Potential restore only if explicitly supported by future policy
- Mostly read-only review

### Notes
Treat this as terminal in v1.

---

## 2.10 Provisioning Failed

### Meaning
A critical provisioning attempt failed.

This may apply to:
- sandbox provisioning
- production provisioning
- major environment rebuild

### Characteristics
- the environment is not in the intended usable state
- operator intervention or controlled retry is required
- failure details must be visible

### Typical operator questions
- What failed exactly?
- Was anything partially created?
- Can we retry safely?
- Should we abandon and archive?

### Expected allowed actions
- Retry provisioning
- Move back into the relevant provisioning state
- Archive
- Diagnose failure

### Notes
This state must not be silent, hidden, or reduced to a log detail only.

---

# 3. Allowed transitions

The following transitions are currently allowed.

## Lead
May transition to:
- Sandbox Provisioning
- Production Qualification
- Archived

## Sandbox Provisioning
May transition to:
- Sandbox Active
- Provisioning Failed
- Archived

## Sandbox Active
May transition to:
- Sandbox Expired
- Production Qualification
- Suspended
- Archived

## Sandbox Expired
May transition to:
- Sandbox Active
- Production Qualification
- Archived

## Production Qualification
May transition to:
- Production Provisioning
- Archived
- Sandbox Active (only by explicit operator override)

## Production Provisioning
May transition to:
- Live
- Provisioning Failed
- Archived

## Live
May transition to:
- Suspended
- Archived

## Suspended
May transition to:
- Live
- Archived

## Archived
May transition to:
- no normal transitions in v1

## Provisioning Failed
May transition to:
- Sandbox Provisioning
- Production Provisioning
- Archived

---

# 4. Forbidden transitions

The following should be forbidden unless the design is explicitly revised.

- Lead → Live
- Lead → Suspended
- Sandbox Provisioning → Live
- Sandbox Active → Live
- Sandbox Expired → Live
- Production Qualification → Live
- Live → Sandbox Active
- Live → Sandbox Expired
- Archived → Live
- Archived → Sandbox Active
- Archived → Production Provisioning
- Provisioning Failed → Live

These jumps destroy lifecycle clarity.

---

# 5. Transition table

| From | Allowed To | Reason |
|---|---|---|
| Lead | Sandbox Provisioning | Start trial provisioning |
| Lead | Production Qualification | Direct qualification path if no sandbox |
| Lead | Archived | Prospect abandoned |
| Sandbox Provisioning | Sandbox Active | Sandbox ready |
| Sandbox Provisioning | Provisioning Failed | Build failed |
| Sandbox Provisioning | Archived | Cancelled/abandoned |
| Sandbox Active | Sandbox Expired | Trial expired |
| Sandbox Active | Production Qualification | Qualified for live planning |
| Sandbox Active | Suspended | Exceptional internal hold |
| Sandbox Active | Archived | Trial abandoned/closed |
| Sandbox Expired | Sandbox Active | Reactivated |
| Sandbox Expired | Production Qualification | Late conversion path |
| Sandbox Expired | Archived | Ended |
| Production Qualification | Production Provisioning | Approved for build |
| Production Qualification | Archived | Deal died |
| Production Qualification | Sandbox Active | Explicit fallback |
| Production Provisioning | Live | Production ready |
| Production Provisioning | Provisioning Failed | Build failed |
| Production Provisioning | Archived | Cancelled |
| Live | Suspended | Hold state |
| Live | Archived | Ended/closed |
| Suspended | Live | Restored |
| Suspended | Archived | Closed permanently |
| Provisioning Failed | Sandbox Provisioning | Retry sandbox build |
| Provisioning Failed | Production Provisioning | Retry production build |
| Provisioning Failed | Archived | Abandoned |

---

# 6. State-specific action expectations

This section defines what kinds of actions should normally be available by state.

## Lead
Expected actions:
- Create Sandbox
- Mark Production Qualified
- Archive

Not expected:
- Reset Sandbox
- Suspend Live Environment
- Refresh Cost Snapshot

## Sandbox Provisioning
Expected actions:
- View provisioning progress
- Retry or fail provisioning
- Cancel/archive if needed

Not expected:
- Normal sandbox usage actions
- Production monitoring actions

## Sandbox Active
Expected actions:
- Reset Sandbox
- Expire Sandbox
- Qualify for Production
- Refresh usage snapshot

Not expected:
- Mark directly Live
- Use production-only billing logic

## Sandbox Expired
Expected actions:
- Reactivate Sandbox
- Qualify for Production
- Archive

Not expected:
- Treat as healthy active environment

## Production Qualification
Expected actions:
- choose hosting tier
- choose DB mode
- choose conversion strategy
- launch production provisioning

Not expected:
- mark directly Live without provisioning
- treat as active production

## Production Provisioning
Expected actions:
- track provisioning steps
- retry provisioning
- fail provisioning
- complete go-live checks

Not expected:
- full customer traffic
- subscription-driven live-state operations

## Live
Expected actions:
- suspend
- review health
- review usage
- review cost
- review subscription
- refresh checks

Not expected:
- sandbox reset
- demo-data actions

## Suspended
Expected actions:
- restore
- archive
- review retention/cost impact

Not expected:
- normal active production assumptions

## Archived
Expected actions:
- review only
- retention handling
- rare future restore only if explicitly designed later

Not expected:
- ordinary operational actions

## Provisioning Failed
Expected actions:
- diagnose
- retry provisioning
- archive

Not expected:
- pretend partial success is usable

---

# 7. Audit logging rules

Every state transition must create a `Tenant Transition Log` entry.

At minimum, each transition log should capture:

- tenant
- environment
- from_state
- to_state
- trigger_type
- triggered_by
- success/failure
- transition timestamp
- message / reason
- related job id if applicable

## Additional rule
If a transition fails, both of these should be true:

1. the failure should be visible in the environment record
2. the failure should be visible in transition logging

Do not rely on raw background job logs alone.

---

# 8. Failure handling rules

## 8.1 Provisioning failures
If sandbox or production provisioning fails:

- environment should move to `Provisioning Failed`
- `provisioning_message` or equivalent detail should be updated
- a transition log entry must be created
- partial resource creation should be tracked where feasible

## 8.2 Validation failures before transition
If an attempted transition is invalid:

- do not create the transition
- raise a clear server-side error
- do not silently “fix up” the state behind the scenes

## 8.3 Retry behavior
Retries should be explicit.

Do not auto-jump from `Provisioning Failed` to `Live`.
A retry must re-enter the appropriate provisioning state.

---

# 9. Operator override philosophy

This is an internal control plane, so some operator override ability is reasonable.

But override must not mean chaos.

## Allowed principle
An operator may be allowed to perform limited exceptional transitions, such as:
- Production Qualification → Sandbox Active

But such overrides must be:
- explicit
- logged
- justified
- rare

## Not allowed principle
Operators should not have a hidden “jump to anything” power in normal workflows.

That would destroy operational trust in the state machine.

---

# 10. State derivation vs stored state

The primary lifecycle state should be **stored explicitly** on `Tenant Environment`.

Do not try to infer the environment state from scattered fields like:
- `expires_on`
- `dns_ready`
- `db_host`
- `billing_status_snapshot`

Those fields can inform actions and validation, but the canonical lifecycle state must still be explicit.

Why:
- operators need one visible truth
- transitions need auditability
- history matters
- inferred state becomes brittle quickly

---

# 11. Relationship to health and incidents

Lifecycle state is not the same as health.

Examples:
- a `Live` environment may still be unhealthy
- a `Sandbox Active` environment may be degraded
- a `Suspended` environment may be healthy but intentionally inaccessible

Therefore:
- lifecycle state tracks **operational stage**
- health checks track **technical condition**
- incident/alert records track **events/problems**

Do not overload lifecycle state to mean everything.

---

# 12. Relationship to subscription status

Lifecycle state is not the same as subscription status.

Examples:
- tenant subscription may be `Pending Renewal` while environment is still `Live`
- billing issue may lead to `Suspended`, but the subscription and environment remain different concepts
- sandbox may be `Active` while subscription is still `Trial`

Therefore:
- lifecycle governs environment operations
- subscription status governs commercial status

Keep them separate.

---

# 13. Recommended implementation rules

When implementing this in Frappe:

### Rule 1
Do not expose raw status field editing as the normal UX.

### Rule 2
Use explicit server-side actions for transitions:
- create sandbox
- expire sandbox
- qualify for production
- provision production
- suspend environment
- restore environment
- archive environment

### Rule 3
Validate transition legality on the server.

### Rule 4
Write transition logs automatically from server-side actions.

### Rule 5
If transition side-effects fail, the system must not leave the environment in a misleading state.

---

# 14. Final locked position

The environment state machine for Ifitwala_Press is built around:

- explicit lifecycle states
- explicit allowed transitions
- explicit failure visibility
- explicit server-authoritative actions
- explicit audit logs

This is the current design lock.

Any later expansion must preserve clarity rather than add noise.
