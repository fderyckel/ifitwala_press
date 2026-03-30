# 16_founder_edge_proxy_contract.md

## Purpose

This document locks the shared founder-mode edge proxy contract for **Ifitwala_Press**.

It exists to turn phase-1 DNS records into real HTTP reachability without prematurely hardcoding the whole platform to Traefik.

---

## 1. Founder edge proxy decision

Phase 1 now uses:

- one shared nginx edge proxy on the founder runtime host
- Docker deployment for that shared edge proxy
- host network mode on the founder VM
- one generated route fragment per tenant environment
- Cloud DNS `A` records pointing to the founder runtime host IP

This is an MVP bridge.
It is not the later Traefik target.

---

## 2. Why this exists

Without a shared edge proxy:

- Cloud DNS records can be created
- per-environment runtime nginx instances can listen on loopback ports
- but hostname traffic still has nowhere authoritative to land on port 80

The shared founder edge proxy solves that gap.

---

## 3. Control-plane boundary

`Ifitwala_Press` owns:

- primary domain intent
- routing mode
- host header value
- DNS readiness
- TLS readiness

The founder runtime adapter owns:

- writing the route fragment for the environment
- reloading the shared founder proxy when route files change
- creating or updating the Cloud DNS record

The founder edge proxy does not own lifecycle state.

---

## 4. Founder routing flow

The intended founder routing flow is:

1. `Tenant Environment` defines or derives the primary domain
2. the runtime adapter provisions the environment stack on a loopback host port
3. the adapter writes a shared edge-proxy route for that hostname
4. the adapter reloads nginx
5. the adapter creates or updates the Cloud DNS `A` record with `gcloud dns ...`
6. `Ifitwala_Press` records routing metadata returned by the adapter

This gives us live HTTP reachability now while preserving the future Traefik migration path.

---

## 5. Explicit non-goals

Phase 1 does not require:

- automatic TLS issuance
- Traefik dynamic config
- Google load balancer integration
- multi-host edge routing

Those are later steps once the founder runtime flow is proven.
