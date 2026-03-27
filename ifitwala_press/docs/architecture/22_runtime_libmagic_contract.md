# 22_runtime_libmagic_contract.md

## Purpose

This document locks the `libmagic` runtime dependency for founder and later managed runtimes provisioned by **Ifitwala_Press**.

It exists because `ifitwala_drive` performs governed MIME validation during upload finalization and that validation is part of the fail-closed file governance contract, not an optional convenience.

---

## 1. Bottom line

Every runtime image that can execute `ifitwala_ed` + `ifitwala_drive` upload finalization must include:

- the native `libmagic` shared library
- the Python binding `python-magic`

This applies to:

- web containers
- worker containers
- scheduler images if they share the same immutable runtime image

If this dependency is missing, governed uploads must fail closed.

---

## 2. Why Press owns this

`ifitwala_drive` is intentionally strict here:

- it reads uploaded bytes from temporary storage
- it detects the actual MIME type using `python-magic`
- it rejects dangerous executable/script payloads
- it rejects payloads whose bytes do not match the claimed MIME type
- it refuses to finalize a governed file when MIME validation cannot be trusted

This is not an app-level tweak.
It is part of the runtime contract that **Ifitwala_Press** must enforce when it builds and ships the shared founder image.

Because Press owns the image and orchestrates deployment, Press must ensure the dependency is baked into the image instead of relying on one-off manual installs on hosts.

---

## 3. Why this matters for Ifitwala_Ed and Ifitwala_Drive

The file platform is governed from day 1.

That means a file must not become meaningful business state unless Drive can validate:

- what bytes were actually uploaded
- whether the payload is obviously dangerous
- whether the claimed file type matches the real content

Without `libmagic`, MIME detection becomes incomplete or unreliable.
That weakens:

- admissions document governance
- task submission validation
- organization and school media handling
- auditability of upload finalization decisions

For this reason, `libmagic` is a deployment requirement, not a local-dev extra.

---

## 4. Cost and concurrency posture

For a high-concurrency ERP runtime, the operational cost of `libmagic` is low.

The request-path work is:

- read only the first small prefix of the uploaded object
- run MIME detection on that prefix
- continue or reject

This does **not** materially change the concurrency posture compared with the larger costs already present in governed upload flows:

- request authentication
- DB reads/writes for upload sessions and governed file state
- object storage existence/finalize operations
- background processing for previews or derivatives

`libmagic` is therefore the correct trade:

- low runtime overhead
- materially better file-type trust
- cleaner fail-closed behavior

Press should treat it as a standard image dependency, not as a performance risk.

---

## 5. Deployment contract

The founder runtime image must bake in:

- OS package providing `libmagic`
- Python dependency `python-magic`

The host should not be the primary enforcement point.
The immutable image should carry the dependency so web and worker processes behave the same way everywhere.

At image build or bootstrap verification time, Press should validate that this command succeeds inside the runtime:

```bash
python -c "import magic; print(magic.from_buffer(b'%PDF-1.7', mime=True))"
```

Expected result:

```text
application/pdf
```

If it fails, the image is not valid for governed uploads.

---

## 6. Founder-mode implications

For founder mode this should be treated as mandatory now, not later.

The shared founder runtime image already carries:

- `frappe`
- `ifitwala_ed`
- `ifitwala_drive`

It must also carry the native upload-governance dependency required by that stack.

This keeps the product contract honest:

- Press provisions the runtime
- Drive enforces governed file finalization
- Ed consumes the governed file outcome

---

## 7. Non-goals

This does not mean:

- deep malware scanning must be synchronous
- full-file content inspection must happen on the request path
- file validation should move into Press

Press owns the runtime dependency.
Drive owns the governed MIME validation logic.

