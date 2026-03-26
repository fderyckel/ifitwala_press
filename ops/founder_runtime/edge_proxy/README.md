# Founder Edge Proxy

This is the shared founder-mode edge proxy layer.

It exists so phase-1 DNS records can terminate on one host-level ingress point and then route by hostname to the correct per-environment loopback nginx port.

Current founder posture:

- nginx in Docker
- host network mode on the founder VM
- one route fragment per tenant environment
- route fragments written by the founder runtime adapter
- no automatic TLS yet

This is a founder-stage bridge.
It does not replace the later Traefik target.
