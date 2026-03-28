# 19_hybrid_provider_placement_contract.md

## Purpose

This document locks the first provider-placement contract for **Ifitwala_Press** across a hybrid founder setup.

The near-term operating posture is:

- Google Cloud is the main production provider
- OVH may be used for low-cost sandbox and trial runtime placement
- Google Cloud Storage remains the only current object-storage provider
- Google Cloud DNS remains the default DNS authority
- the control plane remains provider-aware but provider-neutral in its lifecycle model

---

## 1. Core decision

Provider placement must be explicit on both policy and environment records.

The minimum governed fields are:

- `primary_cloud_provider`
- `runtime_provider`
- `object_storage_provider`
- `dns_provider`

These fields are not decorative.
They exist so the control plane can distinguish:

- where production is expected to live
- where cheap sandbox runtime may live
- which provider actually holds the object storage account
- which DNS authority is responsible for public routing

---

## 2. Current approved posture

For phase 1:

- Live production should remain on Google Cloud
- runtime placement on OVH is currently approved only for sandbox-style environments
- one DNS control plane is still preferred, with Google Cloud DNS remaining the default

This keeps the founder path pragmatic without blurring sandbox and production governance.

---

## 3. Why this matters

Without explicit provider placement:

- Google-vs-OVH deployment assumptions hide inside scripts
- sandbox exceptions drift into production logic
- storage and DNS responsibility become ambiguous
- operators lose fast visibility into where an environment actually runs

The control plane must own that intent explicitly.

---

## 4. Adapter implication

The founder runtime payload now needs to carry provider placement explicitly so adapters can branch safely.

That means the adapter can later make different choices for:

- Google production runtime
- OVH sandbox runtime
- Google Cloud DNS
- provider-specific storage credentials and endpoints

The lifecycle model stays the same even when the adapter implementation differs.
