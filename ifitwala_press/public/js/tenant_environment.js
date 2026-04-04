frappe.ui.form.on("Tenant Environment", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		setIngressFieldState(frm);
		renderTransitionHistory(frm);
		renderBusinessSummary(frm);

		if (hasUsageSnapshotRole()) {
			frm.add_custom_button(__("Record Usage Snapshot"), () => {
				promptUsageSnapshot(frm, { environment: frm.doc.name, tenant: frm.doc.tenant });
			}, __("Business"));
		}

		if (hasCostSnapshotRole()) {
			frm.add_custom_button(__("Record Cost Snapshot"), () => {
				promptCostSnapshot(frm, { environment: frm.doc.name, tenant: frm.doc.tenant });
			}, __("Business"));
		}

		if (!hasLifecycleRole()) {
			return;
		}

		addLifecycleButtons(frm);
	},
	ingress_access_mode(frm) {
		setIngressFieldState(frm);
	},
});


function addLifecycleButtons(frm) {
	const status = frm.doc.site_status;

	if (supportsEdgeRouteSync(frm)) {
		frm.add_custom_button(__("Sync Environment Edge Route"), () => {
			syncFounderEdgeRoute(frm);
		}, __("Actions"));
	}

	if (status === "Lead" || status === "Sandbox Active" || status === "Sandbox Expired") {
		frm.add_custom_button(__("Qualify for Production"), () => {
			frappe.prompt(
				[
					{
						fieldname: "hosting_tier",
						fieldtype: "Select",
						label: __("Hosting Tier"),
						reqd: 1,
						options: "\nStandard\nPremium\nVIP",
						default: frm.doc.hosting_tier === "Sandbox" ? "Standard" : frm.doc.hosting_tier,
					},
					{
						fieldname: "database_mode",
						fieldtype: "Select",
						label: __("Database Mode"),
						reqd: 1,
						options: "\nShared DB Fleet\nDedicated DB Instance",
						default: frm.doc.database_mode || "Shared DB Fleet",
					},
					{
						fieldname: "conversion_strategy",
						fieldtype: "Select",
						label: __("Conversion Strategy"),
						reqd: 1,
						options:
							"\nFresh Production Site\nCopy Config Only\nCopy Selected Data\nIn-place Upgrade",
					},
					{
						fieldname: "deployment_mode",
						fieldtype: "Select",
						label: __("Deployment Mode"),
						reqd: 1,
						options: "\nShared Runtime\nReserved Runtime\nDedicated Runtime",
						default: frm.doc.deployment_mode || "Shared Runtime",
					},
					{
						fieldname: "runtime_pool",
						fieldtype: "Link",
						label: __("Runtime Pool"),
						options: "Runtime Pool",
						default: frm.doc.runtime_pool || "",
					},
					{
						fieldname: "dedicated_runtime_target",
						fieldtype: "Data",
						label: __("Dedicated Runtime Target"),
						default: frm.doc.dedicated_runtime_target || "",
					},
					{
						fieldname: "policy",
						fieldtype: "Link",
						label: __("Policy"),
						options: "Tenant Policy",
						default: frm.doc.policy || "",
					},
						{
							fieldname: "region",
							fieldtype: "Data",
							label: __("Region"),
							default: frm.doc.region || "",
						},
						{
							fieldname: "primary_cloud_provider",
							fieldtype: "Select",
							label: __("Primary Cloud Provider"),
							options: "\nGoogle Cloud\nOVH\nOther",
							default: frm.doc.primary_cloud_provider || "Google Cloud",
						},
						{
							fieldname: "runtime_provider",
							fieldtype: "Select",
							label: __("Runtime Provider"),
							options: "\nGoogle Cloud\nOVH\nOther",
							default: frm.doc.runtime_provider || "Google Cloud",
						},
						{
							fieldname: "object_storage_provider",
							fieldtype: "Select",
							label: __("Object Storage Provider"),
							options: "\nGoogle Cloud\nOVH\nOther",
							default: frm.doc.object_storage_provider || "Google Cloud",
						},
						{
							fieldname: "dns_provider",
							fieldtype: "Select",
							label: __("DNS Provider"),
							options: "\nGoogle Cloud DNS\nOVH DNS\nOther",
							default: frm.doc.dns_provider || "Google Cloud DNS",
						},
						{
							fieldname: "status_reason",
							fieldtype: "Small Text",
							label: __("Reason"),
					},
				],
				(values) => callLifecycleMethod(frm, "qualify_for_production", values, __("Qualifying for production")),
				__("Qualify for Production"),
				__("Qualify")
			);
		}, __("Actions"));
	}

	if (status === "Sandbox Provisioning") {
		frm.add_custom_button(__("Provision Environment Runtime"), () => {
			callLifecycleMethod(
				frm,
				"provision_environment_runtime",
				{},
				__("Provisioning environment runtime")
			);
		}, __("Actions"));

		frm.add_custom_button(__("Complete Sandbox Provisioning"), () => {
			frappe.prompt(
				[
					{
						fieldname: "site_name",
						fieldtype: "Data",
						label: __("Site Name"),
						default: frm.doc.site_name,
					},
					{
						fieldname: "primary_domain",
						fieldtype: "Data",
						label: __("Primary Domain"),
						default: frm.doc.primary_domain || "",
					},
					{
						fieldname: "routing_mode",
						fieldtype: "Select",
						label: __("Routing Mode"),
						options: "\nInternal Only\nPublic\nPending",
						default: frm.doc.routing_mode || "Internal Only",
					},
					{
						fieldname: "dns_ready",
						fieldtype: "Check",
						label: __("DNS Ready"),
						default: frm.doc.dns_ready || 0,
					},
					{
						fieldname: "tls_ready",
						fieldtype: "Check",
						label: __("TLS Ready"),
						default: frm.doc.tls_ready || 0,
					},
					{
						fieldname: "host_header_value",
						fieldtype: "Data",
						label: __("Host Header Value"),
						default: frm.doc.host_header_value || "",
					},
					{
						fieldname: "db_name",
						fieldtype: "Data",
						label: __("DB Name"),
						default: frm.doc.db_name || "",
					},
					{
						fieldname: "db_user",
						fieldtype: "Data",
						label: __("DB User"),
						default: frm.doc.db_user || "",
					},
					{
						fieldname: "provisioning_job_id",
						fieldtype: "Data",
						label: __("Provisioning Job ID"),
						default: frm.doc.provisioning_job_id || "",
					},
					{
						fieldname: "last_provisioning_step",
						fieldtype: "Data",
						label: __("Last Provisioning Step"),
						default: frm.doc.last_provisioning_step || "",
					},
					{
						fieldname: "provisioning_message",
						fieldtype: "Small Text",
						label: __("Provisioning Message"),
						default: frm.doc.provisioning_message || "",
					},
						{
							fieldname: "runtime_reference",
							fieldtype: "Data",
							label: __("Runtime Reference"),
							default: frm.doc.runtime_reference || "",
						},
						{
							fieldname: "primary_cloud_provider",
							fieldtype: "Select",
							label: __("Primary Cloud Provider"),
							options: "\nGoogle Cloud\nOVH\nOther",
							default: frm.doc.primary_cloud_provider || "Google Cloud",
						},
						{
							fieldname: "runtime_provider",
							fieldtype: "Select",
							label: __("Runtime Provider"),
							options: "\nGoogle Cloud\nOVH\nOther",
							default: frm.doc.runtime_provider || "Google Cloud",
						},
						{
							fieldname: "object_storage_provider",
							fieldtype: "Select",
							label: __("Object Storage Provider"),
							options: "\nGoogle Cloud\nOVH\nOther",
							default: frm.doc.object_storage_provider || "Google Cloud",
						},
						{
							fieldname: "dns_provider",
							fieldtype: "Select",
							label: __("DNS Provider"),
							options: "\nGoogle Cloud DNS\nOVH DNS\nOther",
							default: frm.doc.dns_provider || "Google Cloud DNS",
						},
						{
							fieldname: "file_storage_provider",
							fieldtype: "Select",
							label: __("File Storage Provider"),
						options: "\nGCS\nLocal Temporary",
						default: frm.doc.file_storage_provider || "GCS",
					},
					{
						fieldname: "file_storage_class",
						fieldtype: "Select",
						label: __("File Storage Class"),
						options: "\nFrequent Access\nInfrequent Access",
						default: frm.doc.file_storage_class || "Frequent Access",
					},
					{
						fieldname: "backup_storage_provider",
						fieldtype: "Select",
						label: __("Backup Storage Provider"),
						options: "\nGCS\nLocal Temporary",
						default: frm.doc.backup_storage_provider || "GCS",
					},
					{
						fieldname: "backup_storage_class",
						fieldtype: "Select",
						label: __("Backup Storage Class"),
						options: "\nFrequent Access\nInfrequent Access",
						default: frm.doc.backup_storage_class || "Infrequent Access",
					},
					{
						fieldname: "backup_export_path",
						fieldtype: "Data",
						label: __("Backup Export Path"),
						default: frm.doc.backup_export_path || "",
					},
					{
						fieldname: "status_reason",
						fieldtype: "Small Text",
						label: __("Activation Note"),
					},
				],
				(values) =>
					callLifecycleMethod(
						frm,
						"complete_sandbox_provisioning",
						values,
						__("Completing sandbox provisioning")
					),
				__("Complete Sandbox Provisioning"),
				__("Complete")
			);
		}, __("Actions"));
	}

	if (status === "Production Qualification" || status === "Provisioning Failed") {
		frm.add_custom_button(__("Provision Production"), () => {
			frappe.prompt(
				[
					{
						fieldname: "site_name",
						fieldtype: "Data",
						label: __("Site Name"),
						default: frm.doc.site_name,
					},
					{
						fieldname: "primary_domain",
						fieldtype: "Data",
						label: __("Primary Domain"),
						default: frm.doc.primary_domain || "",
					},
					{
						fieldname: "provisioning_job_id",
						fieldtype: "Data",
						label: __("Provisioning Job ID"),
						default: frm.doc.provisioning_job_id || "",
					},
					{
						fieldname: "status_reason",
						fieldtype: "Small Text",
						label: __("Reason"),
					},
				],
				(values) => callLifecycleMethod(frm, "provision_production", values, __("Starting production provisioning")),
				__("Provision Production"),
				__("Start")
			);
		}, __("Actions"));
	}

	if (status === "Sandbox Provisioning" || status === "Production Provisioning") {
		frm.add_custom_button(__("Mark Provisioning Failed"), () => {
			frappe.prompt(
				[
					{
						fieldname: "last_provisioning_step",
						fieldtype: "Data",
						label: __("Last Provisioning Step"),
						default: frm.doc.last_provisioning_step || "",
					},
					{
						fieldname: "provisioning_job_id",
						fieldtype: "Data",
						label: __("Provisioning Job ID"),
						default: frm.doc.provisioning_job_id || "",
					},
					{
						fieldname: "provisioning_message",
						fieldtype: "Small Text",
						label: __("Provisioning Message"),
						default: frm.doc.provisioning_message || "",
					},
					{
						fieldname: "reason",
						fieldtype: "Small Text",
						label: __("Failure Reason"),
						reqd: 1,
					},
				],
				(values) =>
					callLifecycleMethod(
						frm,
						"mark_provisioning_failed",
						values,
						__("Marking provisioning as failed")
					),
				__("Mark Provisioning Failed"),
				__("Mark Failed")
			);
		}, __("Actions"));
	}

	if (status === "Production Provisioning") {
		frm.add_custom_button(__("Mark Live"), () => {
			frappe.prompt(
				[
					{
						fieldname: "status_reason",
						fieldtype: "Small Text",
						label: __("Go-live Note"),
					},
				],
				(values) => callLifecycleMethod(frm, "mark_live", values, __("Marking environment live")),
				__("Mark Live"),
				__("Mark Live")
			);
		}, __("Actions"));
	}

	if (status === "Live" || status === "Sandbox Active") {
		frm.add_custom_button(__("Suspend Environment"), () => {
			frappe.prompt(
				[
					{
						fieldname: "reason",
						fieldtype: "Small Text",
						label: __("Reason"),
						reqd: 1,
					},
				],
				(values) => callLifecycleMethod(frm, "suspend_environment", values, __("Suspending environment")),
				__("Suspend Environment"),
				__("Suspend")
			);
		}, __("Actions"));
	}

	if (status === "Sandbox Active") {
		frm.add_custom_button(__("Teardown Environment Runtime"), () => {
			frappe.prompt(
				[
					{
						fieldname: "reason",
						fieldtype: "Small Text",
						label: __("Teardown Reason"),
						reqd: 1,
					},
				],
				(values) =>
					callLifecycleMethod(
						frm,
						"teardown_environment_runtime",
						values,
						__("Tearing down environment runtime")
					),
				__("Teardown Environment Runtime"),
				__("Teardown")
			);
		}, __("Actions"));

		frm.add_custom_button(__("Expire Sandbox"), () => {
			frappe.prompt(
				[
					{
						fieldname: "runtime_reference",
						fieldtype: "Data",
						label: __("Runtime Reference"),
						default: frm.doc.runtime_reference || "",
					},
					{
						fieldname: "backup_export_path",
						fieldtype: "Data",
						label: __("Backup Export Path"),
						default: frm.doc.backup_export_path || "",
					},
					{
						fieldname: "last_provisioning_step",
						fieldtype: "Data",
						label: __("Last Runtime Step"),
						default: frm.doc.last_provisioning_step || "Runtime teardown",
					},
					{
						fieldname: "provisioning_message",
						fieldtype: "Small Text",
						label: __("Teardown Note"),
						default: frm.doc.provisioning_message || "",
					},
					{
						fieldname: "reason",
						fieldtype: "Small Text",
						label: __("Expiry Reason"),
						reqd: 1,
					},
				],
				(values) => callLifecycleMethod(frm, "expire_sandbox", values, __("Expiring sandbox")),
				__("Expire Sandbox"),
				__("Expire")
			);
		}, __("Actions"));
	}

	if (status === "Suspended") {
		frm.add_custom_button(__("Restore Environment"), () => {
			frappe.prompt(
				[
					{
						fieldname: "reason",
						fieldtype: "Small Text",
						label: __("Reason"),
						reqd: 1,
					},
				],
				(values) => callLifecycleMethod(frm, "restore_environment", values, __("Restoring environment")),
				__("Restore Environment"),
				__("Restore")
			);
		}, __("Actions"));
	}

	if (status !== "Archived") {
		frm.add_custom_button(__("Archive Environment"), () => {
			frappe.prompt(
				[
					{
						fieldname: "reason",
						fieldtype: "Small Text",
						label: __("Reason"),
						reqd: 1,
					},
				],
				(values) => callLifecycleMethod(frm, "archive_environment", values, __("Archiving environment")),
				__("Archive Environment"),
				__("Archive")
			);
		}, __("Actions"));
	}
}


function supportsEdgeRouteSync(frm) {
	if (frm.doc.site_status === "Archived") {
		return false;
	}

	return (
		typeof frm.doc.runtime_reference === "string" &&
		(
			frm.doc.runtime_reference.startsWith("compose:") ||
			frm.doc.runtime_reference.startsWith("bench:")
		) &&
		Boolean(frm.doc.primary_domain)
	);
}


function setIngressFieldState(frm) {
	const showAllowlist = frm.doc.ingress_access_mode === "Allowlisted";
	frm.toggle_display("ingress_allowlist", showAllowlist);
	frm.set_df_property(
		"ingress_allowlist",
		"description",
		showAllowlist
			? __("CIDRs allowed through the shared founder edge proxy for this environment.")
			: __("Ingress allowlist is only used when Ingress Access Mode is Allowlisted.")
	);
}


function syncFounderEdgeRoute(frm) {
	const runSync = () =>
		frappe.call({
			method: "ifitwala_press.api.lifecycle.sync_environment_edge_route",
			args: {
				environment: frm.doc.name,
			},
			freeze: true,
			freeze_message: __("Syncing environment edge route"),
			callback: () => {
				frm.reload_doc();
			},
		});

	if (!frm.is_dirty()) {
		runSync();
		return;
	}

	frm.save().then(() => {
		runSync();
	});
}


function callLifecycleMethod(frm, methodName, values, freezeMessage) {
	frappe.call({
		method: `ifitwala_press.api.lifecycle.${methodName}`,
		args: {
			environment: frm.doc.name,
			...values,
		},
		freeze: true,
		freeze_message: freezeMessage,
		callback: () => {
			frm.reload_doc();
		},
	});
}


function hasLifecycleRole() {
	return (
		frappe.user.has_role("Ifitwala Press Admin") ||
		frappe.user.has_role("Ifitwala Press Ops")
	);
}


function hasUsageSnapshotRole() {
	return (
		hasLifecycleRole() ||
		frappe.user.has_role("Ifitwala Press Support")
	);
}


function hasCostSnapshotRole() {
	return hasUsageSnapshotRole() || frappe.user.has_role("Ifitwala Press Finance");
}


function renderTransitionHistory(frm) {
	frappe.call({
		method: "ifitwala_press.api.views.get_environment_transition_history",
		args: { environment: frm.doc.name, limit: 10 },
		callback: ({ message }) => {
			const transitionLogs = message?.transition_logs || [];
			if (!transitionLogs.length) {
				frm.set_df_property(
					"transition_history_html",
					"options",
					'<div class="text-muted">No transition history yet.</div>'
				);
				frm.refresh_field("transition_history_html");
				return;
			}

			const rows = transitionLogs
				.map((log) => {
					const fromState = frappe.utils.escape_html(log.from_state || "Unknown");
					const toState = frappe.utils.escape_html(log.to_state || "Unknown");
					const when = frappe.utils.escape_html(log.transition_on_display || "");
					const trigger = frappe.utils.escape_html(log.trigger_type || "Unknown");
					const actor = frappe.utils.escape_html(log.triggered_by || "System");
					const message = log.message
						? `<div class="text-muted small">${frappe.utils.escape_html(log.message)}</div>`
						: "";
					const statusBadge = log.success ? "green" : "red";

					return `
						<div class="ifitwala-panel-row">
							<div>
								<div><strong>${fromState}</strong> -> <strong>${toState}</strong></div>
								<div class="text-muted small">${when} | ${trigger} | ${actor}</div>
								${message}
							</div>
							<div class="indicator-pill ${statusBadge}">${log.success ? "Success" : "Failed"}</div>
						</div>
					`;
				})
				.join("");

			frm.set_df_property(
				"transition_history_html",
				"options",
				`<div class="ifitwala-panel">${rows}</div>`
			);
			frm.refresh_field("transition_history_html");
		},
	});
}


function renderBusinessSummary(frm) {
	frappe.call({
		method: "ifitwala_press.api.business.get_environment_business_summary",
		args: { environment: frm.doc.name },
		callback: ({ message }) => {
			const usage = message?.usage_snapshot;
			const cost = message?.cost_snapshot;
			const sections = [
				renderSummaryBlock(
					__("Latest Usage"),
					usage
						? [
							`${escape(usage.snapshot_on_display || "")}`,
							`${escape(String(usage.active_users_30d || 0))} active users | ${escape(String(usage.request_count || 0))} requests`,
							`${escape(String(usage.storage_used_gb || 0))} GB storage | avg concurrency ${escape(String(usage.avg_concurrency_estimate || 0))}`,
							`Peak ${escape(String(usage.peak_concurrency_estimate || 0))} | queue jobs ${escape(String(usage.queue_jobs_processed || 0))}`,
						]
						: [__("No usage snapshot recorded.")],
				),
				renderSummaryBlock(
					__("Latest Cost"),
					cost
						? [
							`${escape(cost.snapshot_on_display || "")}`,
							`${escape(String(cost.total_cost_estimate || 0))} ${escape(cost.currency || "")} total`,
							`DB ${escape(String(cost.db_cost_estimate || 0))} | Storage ${escape(String(cost.storage_cost_estimate || 0))}`,
							`Compute ${escape(String(cost.compute_cost_estimate || 0))} | Backup ${escape(String(cost.backup_cost_estimate || 0))}`,
						]
						: [__("No cost snapshot recorded.")],
				),
			];

			frm.set_df_property("business_summary_html", "options", `<div class="ifitwala-summary-grid">${sections.join("")}</div>`);
			frm.refresh_field("business_summary_html");
		},
	});
}


function promptUsageSnapshot(frm, defaults) {
	frappe.prompt(
		[
			{ fieldname: "snapshot_on", fieldtype: "Datetime", label: __("Snapshot On") },
			{ fieldname: "active_users_30d", fieldtype: "Int", label: __("Active Users 30d") },
			{ fieldname: "storage_used_gb", fieldtype: "Float", label: __("Storage Used (GB)") },
			{ fieldname: "file_count", fieldtype: "Int", label: __("File Count") },
			{ fieldname: "request_count", fieldtype: "Int", label: __("Request Count") },
			{ fieldname: "avg_concurrency_estimate", fieldtype: "Float", label: __("Avg Concurrency Estimate") },
			{ fieldname: "peak_concurrency_estimate", fieldtype: "Float", label: __("Peak Concurrency Estimate") },
			{ fieldname: "queue_jobs_processed", fieldtype: "Int", label: __("Queue Jobs Processed") },
			{ fieldname: "notes", fieldtype: "Small Text", label: __("Notes") },
		],
		(values) => callBusinessMethod(frm, "record_usage_snapshot", { ...defaults, ...values }, __("Recording usage snapshot")),
		__("Record Usage Snapshot"),
		__("Save")
	);
}


function promptCostSnapshot(frm, defaults) {
	frappe.prompt(
		[
			{ fieldname: "snapshot_on", fieldtype: "Datetime", label: __("Snapshot On") },
			{ fieldname: "db_cost_estimate", fieldtype: "Currency", label: __("DB Cost Estimate") },
			{ fieldname: "storage_cost_estimate", fieldtype: "Currency", label: __("Storage Cost Estimate") },
			{ fieldname: "compute_cost_estimate", fieldtype: "Currency", label: __("Compute Cost Estimate") },
			{ fieldname: "backup_cost_estimate", fieldtype: "Currency", label: __("Backup Cost Estimate") },
			{ fieldname: "total_cost_estimate", fieldtype: "Currency", label: __("Total Cost Estimate") },
			{ fieldname: "currency", fieldtype: "Link", label: __("Currency"), options: "Currency" },
			{ fieldname: "notes", fieldtype: "Small Text", label: __("Notes") },
		],
		(values) => callBusinessMethod(frm, "record_cost_snapshot", { ...defaults, ...values }, __("Recording cost snapshot")),
		__("Record Cost Snapshot"),
		__("Save")
	);
}


function callBusinessMethod(frm, methodName, args, freezeMessage) {
	frappe.call({
		method: `ifitwala_press.api.business.${methodName}`,
		args,
		freeze: true,
		freeze_message: freezeMessage,
		callback: () => frm.reload_doc(),
	});
}


function renderSummaryBlock(title, lines) {
	return `
		<div class="ifitwala-summary-block">
			<div class="ifitwala-summary-title">${escape(title)}</div>
			${lines.map((line) => `<div class="text-muted small">${line}</div>`).join("")}
		</div>
	`;
}


function escape(value) {
	return frappe.utils.escape_html(String(value ?? ""));
}
