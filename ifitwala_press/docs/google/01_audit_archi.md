Ifitwala Press Architecture Feedback & Proposals (Updated)
2026-03-15

Status note added 2026-03-21:
Proposal 3 below is no longer aligned with the current repository posture.
Google Cloud SQL should not be treated as the current phase-1 DB plan, and "Cloud SQL for MariaDB" should not be treated as an active implementation target.

Design and Architecture Feedback
The architecture documentation for Ifitwala_Press describes an exceptionally rigorous and well-modeled internal control plane. By strictly defining the system as an internal tool and separating the commercial representation (Press Tenant) from the technical reality (Tenant Environment), you've avoided the most common pitfalls of PaaS design.

Strengths:

Domain Modeling: The "site-per-school" tenancy model using a shared runtime and isolated databases strikes a perfect balance between tenant security, blast radius control, and cost management.
State Machine Discipline: Emphasizing server-authoritative actions for lifecycle transitions (e.g., Qualify for Production, Mark Live) and maintaining an append-only Tenant Transition Log guarantees strong auditability.
Architectural Alignment: By stripping away Kubernetes complexity and aligning with the native Frappe Press architecture (Ansible + Docker on VMs), the platform will be much easier to operate and debug for a team already familiar with the Frappe ecosystem.
10 Proposals to Improve Design and Architecture (Agent/Ansible/Docker/MariaDB Model)
Ratings are on a scale of 0.0 - 1.0 based on the composite strength of the proposal across the 5 evaluation criteria: Optimization of Google Cloud infrastructure, Security, Frappe Framework engineering, Docker engineering, and DNS multi-tenant.

1. Managed Instance Groups (MIGs) for Worker Nodes
Rating: 0.95 Deploy the Docker host VMs (the worker nodes executing the Frappe apps) using Google Cloud Managed Instance Groups (MIGs) with Custom Custom VM images (Packer). Ansible can provision the base image, and the MIG ensures the baseline number of healthy VMs is always maintained.

Criteria Impact: High Google Cloud optimization and Docker engineering. Eliminates "pet" servers while keeping the simplicity of raw Docker hosts.
2. Cloud DNS Integration via Ifitwala_Press "Domain Hook"
Rating: 0.95 Since you are not using Kubernetes ExternalDNS, write a simple background hook in Ifitwala_Press that listens to Tenant Environment Domain record changes and directly calls the Google Cloud DNS API to create/delete A and CNAME records pointing to your Traefik Load Balancer IP.

Criteria Impact: Perfect fit for DNS multi-tenant automation. Makes the control plane the true single source of truth for routing without relying on external orchestration polling.
3. Managed DB later, self-managed MariaDB now
Rating: 0.60 Keep self-managed MariaDB 11.8 as the current founder-mode baseline. Revisit managed DB options only after the control-plane backbone and one manual lifecycle flow are proven. If a managed DB path is later adopted, it must be based on then-current provider support and an explicit compatibility decision.

Criteria Impact: Better alignment with current repository rollout policy. Avoids phase-1 drift and avoids planning around an unsupported or unproven managed DB assumption.
4. Direct Docker API via TLS or mTLS secure socket
Rating: 0.85 Instead of having Ansible run docker-compose up over SSH for every lifecycle event (which is slow), use Ansible to provision the VM and secure the Docker Daemon socket with mTLS. Have the Ifitwala_Press Agent communicate directly with the Docker API over this secure socket to spin containers up/down instantly.

Criteria Impact: Improves Docker engineering speed and Security. Faster sandbox spin-ups (seconds instead of minutes).
5. Centralized Traefik with Dynamic HTTP Provider
Rating: 0.85 Deploy Traefik on dedicated ingress VMs (or a small MIG behind a Google Cloud Load Balancer). Configure Traefik using its http provider feature, where Traefik queries a custom API endpoint exposed by Ifitwala_Press. Ifitwala_Press dynamically returns the routing JSON (Domain -> Internal IP:Port of the specific Docker container on the worker node).

Criteria Impact: Strong Frappe engineering and DNS multi-tenant routing. Decouples Traefik from Docker labels, allowing Traefik nodes to route traffic to any worker VM in the fleet seamlessly.
6. Ansible Pulled Configurations (Agent-driven)
Rating: 0.80 Instead of a central control node pushing Ansible playbooks over SSH to hundreds of worker nodes (which scales poorly), install ansible-pull on the worker VM images. The local agent on the VM pulls the desired configuration state from a secure internal git repo and applies it locally.

Criteria Impact: Highly scalable Google Cloud optimization and operational stability.
7. Google Cloud IAM Service Accounts per VM
Rating: 0.85 Do not distribute long-lived JSON keys to worker nodes to access Google Cloud Storage (GCS) for tenant file storage. Instead, assign a specific Google Cloud IAM Service Account to the underlying Compute Engine VM. The Frappe Docker containers can use the metadata server to inherit access to GCS.

Criteria Impact: Top-tier Security. No keys on disk means zero risk of credential leakage if a container escapes.
8. Externalize Redis to Memorystore (Split Cache vs Queue)
Rating: 0.80 Do not run Redis inside Docker on the worker nodes. Use Google Cloud Memorystore for Redis. Crucially, split the instances: one Memorystore instance for Cache/SocketIO (volatile) and a separate instance for Background Jobs / RQ (persistent).

Criteria Impact: High Frappe engineering resilience. Prevents cache evictions from dropping critical async background tasks.
9. Multi-stage Docker Image Construction
Rating: 0.80 Just because you aren't using Kubernetes doesn't mean images shouldn't be optimized. Build a multi-stage Dockerfile that compiles assets (Node/Yarn) in a builder stage and produces a lean, final Python runtime image containing ONLY the built app code.

Criteria Impact: Strong Docker engineering. Smaller images mean worker nodes pull updates faster during Ansible deployments, reducing deployment downtime for tenants.
10. Tenant-specific Docker Bridge Networks
Rating: 0.75 On the worker VMs, if running multiple tenant domains on the same host, isolate them using tenant-specific Docker bridge networks. The Traefik load balancer proxy is the only container attached to all bridge networks, preventing lateral movement between different tenant's Frappe containers on the same host.

Criteria Impact: High Security at the Docker engineering layer. Crucial for noisy-neighbor boundaries on standard production shared-runtimes.
