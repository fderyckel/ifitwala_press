# 03_operator_surfaces.md

## Purpose

This document defines the first operator-facing surfaces for **Ifitwala_Press**.

Ifitwala_Press is an internal control plane.
That means its value does not come only from having correct DocTypes.
Its value comes from helping operators quickly understand:

- what exists
- what is healthy
- what is failing
- what is expensive
- what is about to expire
- what action is needed next

This document defines the first intended UI/operator surfaces so the data model and workflows remain practical.

It covers:

- dashboard intent
- list views
- environment detail surfaces
- tenant detail surfaces
- action surfaces
- operator priorities
- information hierarchy

This is not a pixel-perfect UI spec.
It is an operational UX design lock.

---

## 1. Design goals

### 1.1 Operator-first
The primary users are our own internal operators.

The UI must optimize for:
- fast scanning
- fast diagnosis
- low cognitive load
- safe actions
- clear escalation paths
- strong context around each tenant/environment

### 1.2 Clarity over decoration
This is not a marketing dashboard.
It is an operational console.

Visual design should help answer:
- what needs attention now?
- what changed?
- what is risky?
- what is costly?
- what state is this tenant actually in?

### 1.3 Actionable surfaces
Every major surface should make it obvious:
- what the current state is
- what the next valid actions are
- what information is missing
- what risk signals are present

### 1.4 Separate commercial and operational views, but connect them
Operators need both:
- technical state
- business state

The UI should not isolate those worlds too much.

Example:
A tenant may be healthy technically but underpriced commercially.
A tenant may be costly and also approaching renewal.
A tenant may be unhealthy and also VIP.

The operator surfaces must support this joined understanding.

---

# 2. Main operator home

The first major surface should be a **Control Plane Home** or **Press Home** page.

This is the command center.

## Purpose
To answer, in under 30 seconds:

- How many tenants do we have?
- How many environments are live?
- What is failing now?
- What sandboxes are expiring?
- Which customers are expensive?
- Which subscriptions need attention?
- What requires operator action today?

## Recommended sections

### 2.1 Top summary cards
These should be compact, not decorative.

Suggested cards:
- Total Tenants
- Live Environments
- Sandbox Environments
- Environments in Warning / Critical Capacity
- Provisioning Failures
- Renewals Due Soon
- Total Estimated Monthly Cost

### 2.2 Attention queue
This is the most important part of the home surface.

A single section showing urgent items such as:
- provisioning failed
- backup stale
- critical health score
- expiring sandboxs with active interest
- suspended VIP tenants
- subscriptions near expiry
- cost spikes

This should be short, prioritized, and action-oriented.

### 2.3 Lifecycle overview
A compact breakdown of environments by state:
- Lead
- Sandbox Provisioning
- Sandbox Active
- Sandbox Expired
- Production Qualification
- Production Provisioning
- Live
- Suspended
- Archived
- Provisioning Failed

This helps operators understand platform posture.

### 2.4 Cost overview
Simple at first:
- top 5 highest estimated monthly cost tenants
- highest month-over-month increase
- tenants whose estimated cost exceeds their current tier expectation

### 2.5 Subscription overview
Simple at first:
- trials ending soon
- pending renewals
- expired subscriptions still not archived
- VIP tenants requiring review

### 2.6 Health overview
Simple at first:
- unhealthy environments
- saturated environments
- stale health checks
- stale backup markers

---

# 3. Tenant list surface

The `Press Tenant` list should answer:
- who are our customers/prospects?
- what commercial state are they in?
- what tier are they on?
- who owns them internally?
- what active environment do they currently have?

## Recommended key columns
- Tenant Name
- Organization Type
- Tenant Status
- Subscription Tier
- Subscription Status
- VIP Flag
- Active Environment
- Estimated Students
- Contract End Date
- Sales Owner

## Recommended list indicators
Color indicators should help, not distract.

Examples:
- VIP = strong visual marker
- Trial = lighter state marker
- Expiring contract = warning marker
- Suspended = strong negative marker

## Recommended default filters
- Active Customers
- Trials
- VIP
- Renewals Due Soon
- Suspended
- No Active Environment

## Recommended quick actions
From the list or row actions:
- Open Tenant
- Create Sandbox
- Open Active Environment
- View Subscription
- Review Commercial State

---

# 4. Environment list surface

The `Tenant Environment` list is likely the single most important working list in the whole system.

It should answer:
- what environments exist?
- what state are they in?
- which are healthy or degraded?
- which are costly?
- which are live vs sandbox?
- which need intervention?

## Recommended key columns
- Tenant
- Environment Type
- Site Status
- Hosting Tier
- Database Mode
- Primary Domain
- Region
- Health Score
- Capacity State
- Estimated Monthly Cost
- Last Health Check

## Recommended list indicators
Examples:
- Live = green/steady
- Sandbox Active = soft neutral
- Provisioning Failed = strong red
- Suspended = amber/red
- Saturated = warning
- VIP = badge
- Dedicated DB = badge

## Recommended default filters
- Live
- Sandbox Active
- Provisioning Failed
- Suspended
- VIP
- Capacity Warning / Critical
- Shared DB
- Dedicated DB
- Missing Domain Readiness
- Stale Health Check

## Recommended quick actions
- Open Environment
- Run Health Check
- Qualify for Production
- Provision Production
- Suspend
- Restore
- Archive
- Refresh Usage Snapshot
- Refresh Cost Snapshot

---

# 5. Tenant detail page

The `Press Tenant` form/view should behave like a **customer command record**.

It should not just show fields.
It should give operators a structured understanding of the customer.

## Recommended layout sections

### 5.1 Header summary
Show at top:
- tenant name
- organization type
- tenant status
- subscription tier
- subscription status
- VIP flag
- active environment link

### 5.2 Commercial summary
Show:
- contract dates
- internal owners
- current plan
- renewal status
- notes on commercial posture

### 5.3 Size and risk summary
Show:
- estimated students
- estimated staff
- peak concurrency estimate
- sensitivity level
- residency requirement
- security notes

### 5.4 Environment panel
Show linked environments prominently:
- sandbox
- production
- staging if present

This must be visible without scrolling too far.

### 5.5 Cost / usage summary
Even if sourced from snapshots, show:
- latest estimated cost
- latest usage summary
- trend direction if available later

### 5.6 Operator actions
Likely actions:
- Create Sandbox Environment
- Mark Qualified
- Create Production Environment Record
- Open Active Environment
- View Subscription
- View Usage / Cost History

---

# 6. Environment detail page

The `Tenant Environment` form/view is the operational cockpit for one site.

This is where operators should spend most of their time when diagnosing or acting.

## Recommended layout sections

### 6.1 Header summary
At the top show clearly:
- tenant
- environment type
- site status
- hosting tier
- database mode
- primary domain
- health score
- capacity state

This must be scannable immediately.

### 6.2 Lifecycle panel
Show:
- current state
- last transition
- status reason
- expiry date if applicable
- linked recent transition logs

The operator should understand the environment’s journey immediately.

### 6.3 Routing panel
Show:
- primary domain
- alternate domains
- routing mode
- DNS readiness
- TLS readiness
- host header value
- future Traefik routing metadata

This section matters because routing issues are common and frustrating.

### 6.4 Deployment / placement panel
Show:
- region
- cluster
- namespace
- app image
- image tag
- deployment mode

### 6.5 Database panel
Show:
- DB mode
- DB instance
- DB name
- HA enabled
- last backup
- last restore test

This panel should make isolation level obvious.

### 6.6 Cache / queue / realtime panel
Show:
- redis endpoints or profile labels
- socketio enabled
- queue / worker profile

### 6.7 Health / capacity panel
Show:
- health score
- avg response time
- error rate
- slow query count
- queue backlog
- capacity state
- latest checks

This is one of the most important panels.

### 6.8 Cost / usage panel
Show latest snapshot summary:
- estimated monthly cost
- latest usage snapshot time
- storage used
- request volume
- concurrency estimate

### 6.9 Operator action bar
Available actions should depend on state.

Examples:
- Create Sandbox
- Reset Sandbox
- Expire Sandbox
- Qualify for Production
- Provision Production
- Run Health Check
- Refresh Usage Snapshot
- Refresh Cost Snapshot
- Suspend Environment
- Restore Environment
- Archive Environment

These should be server-authoritative actions, not direct status edits.

---

# 7. Transition history surface

Every environment should expose transition history clearly.

## Purpose
To answer:
- what happened?
- when did it happen?
- who triggered it?
- what failed?
- what is the most recent lifecycle movement?

## Recommended fields visible
- from state
- to state
- timestamp
- triggered by
- success/failure
- message
- related job id

## Recommended behavior
Recent transition logs should appear:
- in an embedded panel on the environment detail page
- as a dedicated list/report when needed

This is a trust surface.
If operators cannot read lifecycle history easily, the control plane is weak.

---

# 8. Usage and cost surfaces

These may not be fully built in phase 1, but the design intent should be clear now.

## 8.1 Usage view
Should help answer:
- which tenants are growing?
- who is consuming more storage?
- who has unusual request or concurrency patterns?
- who is underprovisioned relative to activity?

Recommended dimensions:
- by tenant
- by environment
- by time period

## 8.2 Cost view
Should help answer:
- what does each tenant approximately cost us?
- who is disproportionately expensive?
- who should move tiers?
- where is premium isolation justified?
- are sandboxes accumulating hidden cost?

Recommended dimensions:
- DB cost
- storage cost
- compute cost
- backup cost
- total estimated cost

## 8.3 Join usage and cost
A useful operator view later will be:
- tenant
- subscription tier
- estimated cost
- usage trend
- margin/risk signal

This is critical for internal platform discipline.

---

# 9. Subscription surface

This should remain simple early on, but it matters.

## Purpose
To help operators and commercial owners answer:
- who is trial vs paid?
- who is near renewal?
- who is overdue?
- which tenants should be upgraded?
- which tenants are mismatched to actual usage/cost?

## Recommended summary fields
- plan
- status
- start date
- end date
- billing cycle
- latest environment state
- latest estimated monthly cost

This should eventually support a practical renewal and pricing review workflow.

---

# 10. Alerts / incidents / attention surfaces

A good control plane needs a way to show problems without forcing operators to hunt through each environment.

## Recommended attention categories
- Provisioning Failure
- Health Degradation
- Capacity Warning
- Backup Warning
- Routing Failure
- Billing / Renewal Warning
- VIP Attention Required

## Recommended priorities
- Critical
- Warning
- Info

## Recommended behaviors
- appear on home dashboard
- appear on environment detail page
- eventually support owner / acknowledgment / resolution state

---

# 11. Operator workflows to support first

The UI should not be designed abstractly.
It should support real workflows.

## Workflow 1: Prospect to sandbox
Operator needs to:
- open tenant
- confirm commercial state
- create sandbox
- monitor provisioning
- hand it off to internal/commercial team

## Workflow 2: Sandbox to production qualification
Operator needs to:
- assess usage and seriousness
- choose tier
- choose DB mode
- decide fresh production vs selective copy
- move to production qualification

## Workflow 3: Production provisioning
Operator needs to:
- open qualified environment
- provision production
- confirm site/domain/policy details
- verify health
- mark live

## Workflow 4: Health diagnosis
Operator needs to:
- see warning or failure
- open environment
- inspect health/capacity/routing/DB panels
- run checks or take action

## Workflow 5: Cost review
Operator needs to:
- identify high-cost tenants
- compare with subscription tier
- decide if review/upgrade is needed

## Workflow 6: Renewal / commercial review
Operator needs to:
- identify renewals due
- see tenant usage and cost
- see environment importance and health
- prepare renewal or tiering decision

These workflows should shape the UI more than abstract completeness.

---

# 12. Information hierarchy

The operator should mentally move through the system in this order:

### Level 1: Platform overview
What needs attention overall?

### Level 2: Tenant view
What is the customer/commercial context?

### Level 3: Environment view
What is the operational reality?

### Level 4: Incident / transition / usage / cost detail
Why is this happening, and what action is justified?

This hierarchy should guide navigation.

---

# 13. Navigation recommendations

The left navigation or workspace entry points should stay tight.

Recommended main entries:
- Home / Dashboard
- Tenants
- Environments
- Subscriptions
- Usage
- Costs
- Health / Alerts
- Policies
- Transition Logs

Do not overload the UI with too many parallel entry points early.

---

# 14. What to avoid

Avoid these mistakes:

### 14.1 Raw admin clutter
Do not expose every field equally in the first UI.
Operators need hierarchy, not a field graveyard.

### 14.2 Status-only dashboards
A dashboard that only counts statuses but does not surface actions is weak.

### 14.3 Commercial/technical split that is too strong
If cost, usage, and health are separated too aggressively, operators lose context.

### 14.4 Overly fancy visuals
Use charts only if they clarify action.
This is an operations product, not a board deck.

### 14.5 Hidden critical actions
Important actions must be visible and understandable from the relevant record page.

---

# 15. Early implementation priority

The first useful operator surfaces should be:

## Phase 1
- Tenant list
- Environment list
- Tenant detail
- Environment detail
- Transition log panel
- top-level dashboard with attention queue

## Phase 1.5
- Subscription list/detail
- usage snapshot views
- cost snapshot views
- basic alerts surface

## Phase 2
- richer dashboards
- trend views
- tenant cohort analysis
- better cost/usage comparison tools

This ordering is enough to make the platform useful without overbuilding.

---

# 16. Final design position

Ifitwala_Press should feel like a serious internal operations console.

The operator should be able to answer quickly:

- what exists
- what matters
- what is failing
- what costs too much
- what is changing
- what action is valid next

That is the purpose of the operator surfaces.
