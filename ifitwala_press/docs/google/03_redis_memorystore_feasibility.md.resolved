# Feasibility Assessment: Splitting Redis via Google Cloud Memorystore

## 1. Feasibility & Rationale
**Yes, it is highly feasible and natively supported by the Frappe Framework.**

By default, an out-of-the-box Frappe installation (via `bench`) spins up three separate local Redis processes on three different ports (usually 13000, 11000, and 12000). 
- **Cache (`redis_cache`):** Used for speeding up UI loads, caching database queries, and session limits. Data here is *volatile* (temporary).
- **Queue (`redis_queue`):** Used by `RQ` (Redis Queue) to store background jobs (e.g., sending emails, generating massive reports, executing scheduled crons). Data here is *persistent and critical*.
- **SocketIO (`redis_socketio`):** Used as a Pub/Sub message broker to push real-time notifications to the browser UI.

### Why split them in the Cloud?
If you put your Cache and your Queue in the same Redis instance (or the same monolithic Docker container on your worker VM), and a school runs a massive report that consumes all available memory, Redis triggers an **Eviction Policy** (e.g., `allkeys-lru`) to prevent a crash.
- If it evicts a *cached user session*, the user just logs in again. No big deal.
- If it evicts a *background job from the queue*, **that job is silently destroyed and never executes**. Invoices don't send. Crons fail. Data integrity is damaged.

Splitting them into two differently-configured Google Cloud Memorystore instances guarantees that volatile cache spikes never destroy critical background jobs.

---

## 2. Implementation: Google Cloud Services Used

You will provision two separate **Google Cloud Memorystore for Redis** instances in your VPC (Private IPs only).

### Instance 1: The Volatile Cache (Cache + SocketIO)
- **Service:** Google Cloud Memorystore for Redis (Basic Tier)
- **Eviction Policy:** `allkeys-lru` (Least Recently Used). If memory fills up, it deletes the oldest cached data to make room.
- **Persistence:** Disabled (RDB/AOF off). If this instance restarts, cache is wiped clean. This is perfectly safe for Cache and SocketIO.
- **Cost/Size:** Start small (e.g., 2GB - 5GB depending on total tenants on that shared cluster).

### Instance 2: The Critical Queue (RQ)
- **Service:** Google Cloud Memorystore for Redis (Standard Tier / HA).
- **Eviction Policy:** `noeviction`. If memory fills up, Redis throws an Out Of Memory (OOM) error rather than silently deleting a scheduled job. (This alerts your monitoring to scale up, safely preserving jobs.)
- **Persistence:** Enabled (RDB snapshots) if you want an extra layer of safety, but standard HA failover usually suffices for Redis Queues.
- **Cost/Size:** Keep this dedicated. Background jobs are usually text payloads and don't take much memory. (e.g., 1GB - 2GB).

---

## 3. How to Configure Frappe (The Agent/Ansible Workflow)

Frappe defines where to find Redis in two places. 
1. `common_site_config.json` (Applies to all tenants on that "bench" / worker VM).
2. `site_config.json` (Specific to a single tenant).

Because these Memorystore instances will be shared by all tenants running on a specific Worker VM, you will have your Ansible script (or `Ifitwala_Press` Agent) inject these settings into the `common_site_config.json` when the Worker VM is provisioned.

**Example `frappe-bench/sites/common_site_config.json`:**
```json
{
  "redis_cache": "redis://10.X.X.5:6379",
  "redis_queue": "redis://10.X.X.6:6379",
  "redis_socketio": "redis://10.X.X.5:6379",
  "background_workers": 4
}
```
*(Notice how `redis_cache` and `redis_socketio` point to the same Memorystore IP (`10.X.X.5`), while `redis_queue` points to the dedicated HA Memorystore IP (`10.X.X.6`)).*

### Tuning Frappe for this Setup
Because you are using managed, network-attached Redis instead of local UNIX sockets or localhost, you must ensure your Docker containers are configured correctly:
1. **Network Latency:** Memorystore instances *must* be in the same Google Cloud Region and same VPC as your Compute Engine worker VMs to ensure sub-millisecond latency. Frappe makes thousands of Redis calls per page load; high latency will destroy TTFB (Time To First Byte).
2. **Workers:** Ensure your `supervisor.conf` (or Docker Compose equivalents) for the background workers (e.g., `frappe-worker-default`, `frappe-worker-short`) are pointing to the `common_site_config.json` so they actively poll `10.X.X.6` for jobs.

---

## 4. How it Optimizes Cost and Efficiency

### Efficiency (Reliability & Uptime)
- **Prevents Silent Job Failures:** As stated above, applying `noeviction` to the queue ensures that critical ERP operations (like billing runs) are never arbitrarily discarded due to volatile web cache filling up the RAM.
- **Independent Scaling:** If you onboard a massive school that heavily uses the UI (high cache demand) but runs few background jobs, you can vertical-scale the Cache Memorystore instance without paying to scale the Queue instance.

### Cost Optimization
If you did not use Google Cloud Memorystore, you would have to run Redis containers directly on your Google Compute Engine worker VMs.
- **The monolithic drawback:** Redis is single-threaded. To achieve high availability and failover (Redis Sentinel) across multiple worker VMs, you spend significant engineering time writing complex Ansible playbooks just to keep Redis stable. 
- **The Memorystore advantage:** By pushing Redis to a managed service, your worker VMs remain completely *stateless*. If a worker VM crashes, the MIG automatically spins up a new one. The new VM instantly connects to Memorystore, and **zero cached sessions or background jobs are lost.** You save massive amounts of DevOps labor cost and downtime penalties.
