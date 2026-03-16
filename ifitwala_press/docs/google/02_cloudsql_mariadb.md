Feasibility Assessment: Google Cloud SQL (MariaDB) for Frappe v16
1. Feasibility: Can it be done?
Yes, absolutely. Running the Frappe Framework (version 16) against Google Cloud SQL for MariaDB is highly feasible and strongly recommended for production and control-plane deployments.

While Frappe's default installer (easy_install) assumes a local MariaDB database running on the same server, the framework itself communicates with the database layer purely over standard MySQL/MariaDB TCP/IP sockets. Decoupling the database is the standard enterprise practice to achieve high availability and simplify multi-tenancy.

2. Has it been done before?
Yes. Many large ERPNext instances split the architecture by relying on AWS RDS for MariaDB or Google Cloud SQL for MariaDB. bench (Frappe's CLI) has built-in flags exactly for this (--db-host and --db-port).

3. Constraints & Gotchas (Updated for Frappe v16)
Using Google Cloud SQL with Frappe v16 introduces a few specific constraints you must architect around:

A. MariaDB Version Requirements (v16 specific)
Requirement: Frappe Version 16 requires MariaDB 10.6.
Constraint: Do not assume that because Frappe v16 is newer, you should use the latest MariaDB (like 11.x). While Frappe Manager is experimenting with MariaDB 11 LTS support, MariaDB 10.6 remains the explicitly tested, stable, and recommended version across the community for v16. Using versions 10.11 or higher has historically caused ORM syntax errors or data corruption issues that are silently skipped. Google Cloud SQL offers MariaDB 10.6 as a standard option.
B. The "SUPER" Privilege Issue
When you run bench new-site <sitename>, Frappe attempts to connect using the MariaDB root user to execute CREATE DATABASE, CREATE USER, and GRANT ALL PRIVILEGES.

Constraint: Google Cloud SQL restricts true SUPER privileges. While the root equivalent user provided by Cloud SQL can create databases, Frappe's script sometimes attempts global configurations or specific GRANT statements that Cloud SQL blocks. Therefore, letting bench do the DB creation directly often fails in managed cloud environments.
C. Default Character Set and Collation
Frappe v16 strictly requires a 4-byte UTF-8 character set (utf8mb4) to support emojis and modern international text without truncating payloads.

Constraint: Google Cloud SQL defaults must be explicitly overridden via "Database Flags" upon creation.
D. Private Networking (VPC)
Your Frappe Docker containers running on Google Compute Engine VMs must be able to reach the Cloud SQL instance securely.

Constraint: You should never expose Cloud SQL to the public internet. You must configure Private Services Access (VPC Peering) so that the Cloud SQL instance gets a private IP address (e.g., 10.x.x.x) that your worker node VMs can route to internally without egressing to the public web.
4. How to Implement It (Specific Steps for Ifitwala Press)
For Ifitwala_Press (a control plane managing many tenants), you must implement a split-privilege architecture to guarantee security and bypass the SUPER privilege constraints.

When an operator clicks "Create Sandbox" or "Provision Production", Ifitwala_Press performs the following flow:

Phase 1: Infrastructure Setup (Google Cloud)
Provision the Instance: Create a Cloud SQL instance. Explicitly select MariaDB 10.6.
Network Type: Select Private IP and attach it to your default VPC.
Database Flags: Set the following flags in the Cloud SQL console:
character_set_server = utf8mb4
collation_server = utf8mb4_unicode_ci
Machine Type: Start with a minimum of 2 vCPU and 8GB RAM per shared instance. Adjust the buffer pool size flag (innodb_buffer_pool_size) to consume roughly 60-70% of available RAM.
Phase 2: Secure Tenant Creation Workflow (The Control Plane Logic)
Step 1. Control Plane Acts (via GCP API) Instead of letting the worker VM run a root bench command, Ifitwala_Press intercepts the process:

Ifitwala_Press uses its own GCP IAM Service Account to connect to the Cloud SQL Admin API over HTTPS.
It automatically creates a new logical database (e.g., tenant_foo_db).
It automatically creates a new database user (e.g., tenant_foo_user) and a secure random password (abcd123).
It applies the correct Cloud SQL user permissions to ensure that tenant_foo_user can only access tenant_foo_db.
Step 2. Hand-off to the Worker VM (Ansible/Agent)

Ifitwala_Press securely transmits the tenant's specific credentials (db_name, db_user, db_password, and the Cloud SQL Private IP db_host) to the Agent running on the target Google Compute Engine VM.
Step 3. Agent Installs the Frappe Site

The Agent generates the site directory (frappe-bench/sites/tenant_foo.yourdomain.com/).
The Agent manually writes the site_config.json file inside that folder containing the credentials generated in Step 1.
Because the database already exists and the user inherently has access to it, the Agent runs the specific command to install Frappe directly onto the provisioned destination, bypassing the "root" configuration sequence:
bash
bench --site tenant_foo.yourdomain.com install-app ifitwala_ed
Why this specific implementation?
Security: The underlying worker VMs running Frappe containers never hold the Cloud SQL root credentials. If a Docker container or worker VM is compromised, the blast radius is strictly limited to that VM's local tenants.
Bypasses Cloud SQL Limitations: By creating the database and user via Google Cloud APIs (Ifitwala_Press), bench never executes the global GRANT statements that typically fail on managed DBaaS solutions.
Frappe v16 Optimization: Deploying the exact version (10.6) and setting character encodings preemptively prevents cryptic ORM failures during major version upgrades later in Frappe 16's lifecycle.
