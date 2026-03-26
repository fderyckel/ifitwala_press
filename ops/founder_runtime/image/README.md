# Founder Runtime Image

This directory holds the immutable phase-1 runtime image build context.

The runtime image contract is:

- start from a `frappe_docker`-style worker image
- bake `ifitwala_ed` and `ifitwala_drive` into that image
- keep site state and S3 credentials out of the image
- publish one pinned tag, then reference that tag from `IFITWALA_FOUNDER_RUNTIME_IMAGE`

## Files

- `Dockerfile`
  Founder runtime image build recipe
- `build-runtime-image.sh`
  Wrapper that builds and optionally pushes the image
- `build.env.example`
  Example build-time variables for the two app repositories and refs

## Build flow

1. Copy `build.env.example` to a private env file.
2. Pin `FRAPPE_BASE_IMAGE` to the worker image you have approved for founder mode.
3. Set `IFITWALA_ED_REPO`, `IFITWALA_ED_REF`, `IFITWALA_DRIVE_REPO`, and `IFITWALA_DRIVE_REF`.
4. Run `BUILD_ENV_FILE=/path/to/build.env ./build-runtime-image.sh`.
5. Update `IFITWALA_FOUNDER_RUNTIME_IMAGE` in the founder host adapter env once the tag is published.

This keeps the image immutable and keeps deployment-specific configuration in the adapter env and runtime payload.
