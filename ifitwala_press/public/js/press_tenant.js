frappe.ui.form.on("Press Tenant", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		renderLinkedEnvironments(frm);
		renderBusinessSummary(frm);

		if (frm.doc.active_environment) {
			frm.add_custom_button(__("Open Active Environment"), () => {
				frappe.set_route("Form", "Tenant Environment", frm.doc.active_environment);
			});
		}

		if (hasSubscriptionRole()) {
			frm.add_custom_button(__("Record Subscription"), () => {
				frappe.prompt(
					[
						{ fieldname: "plan_name", fieldtype: "Data", label: __("Plan Name") },
						{
							fieldname: "subscription_tier",
							fieldtype: "Select",
							label: __("Subscription Tier"),
							options: "\nSandbox\nStandard\nPremium\nVIP",
							default: frm.doc.subscription_tier || "Sandbox",
						},
						{
							fieldname: "status",
							fieldtype: "Select",
							label: __("Status"),
							options: "\nTrial\nActive\nPending Renewal\nExpired\nSuspended\nCancelled",
							default: frm.doc.subscription_status || "Trial",
						},
						{ fieldname: "start_date", fieldtype: "Date", label: __("Start Date") },
						{ fieldname: "end_date", fieldtype: "Date", label: __("End Date") },
						{
							fieldname: "billing_cycle",
							fieldtype: "Select",
							label: __("Billing Cycle"),
							options: "\nMonthly\nQuarterly\nAnnual",
						},
						{ fieldname: "price", fieldtype: "Currency", label: __("Price") },
						{ fieldname: "currency", fieldtype: "Link", label: __("Currency"), options: "Currency" },
						{ fieldname: "notes", fieldtype: "Small Text", label: __("Notes") },
					],
					(values) => callBusinessMethod(frm, "record_tenant_subscription", { tenant: frm.doc.name, ...values }, __("Recording subscription")),
					__("Record Subscription"),
					__("Save")
				);
			}, __("Business"));
		}

		if (hasUsageSnapshotRole()) {
			frm.add_custom_button(__("Record Usage Snapshot"), () => {
				promptUsageSnapshot(frm, { tenant: frm.doc.name });
			}, __("Business"));
		}

		if (hasCostSnapshotRole()) {
			frm.add_custom_button(__("Record Cost Snapshot"), () => {
				promptCostSnapshot(frm, { tenant: frm.doc.name });
			}, __("Business"));
		}

		if (!hasLifecycleRole()) {
			return;
		}

		frm.add_custom_button(__("Create Sandbox"), () => {
			frappe.prompt(
				[
					{
						fieldname: "site_name",
						fieldtype: "Data",
						label: __("Site Name"),
						reqd: 1,
						default: frm.doc.tenant_slug ? `${frm.doc.tenant_slug}.sandbox` : "",
					},
					{
						fieldname: "environment_name",
						fieldtype: "Data",
						label: __("Environment Name"),
						default: frm.doc.tenant_name ? `${frm.doc.tenant_name} Sandbox` : "",
					},
					{
						fieldname: "policy",
						fieldtype: "Link",
						label: __("Policy"),
						options: "Tenant Policy",
						default: frm.doc.default_policy || "",
					},
					{
						fieldname: "expiry_date",
						fieldtype: "Date",
						label: __("Expiry Date"),
					},
					{
						fieldname: "demo_seed_mode",
						fieldtype: "Select",
						label: __("Demo Seed Mode"),
						options: "\nBlank Site\nRestore Demo Backup",
						default: "Blank Site",
					},
					{
						fieldname: "demo_seed_reference",
						fieldtype: "Data",
						label: __("Demo Seed Reference"),
					},
					{
						fieldname: "auto_provision_runtime",
						fieldtype: "Check",
						label: __("Provision Founder Demo Runtime"),
						default: 1,
					},
					{
						fieldname: "status_reason",
						fieldtype: "Small Text",
						label: __("Reason"),
					},
				],
				(values) => {
					frappe.call({
						method: "ifitwala_press.api.lifecycle.create_sandbox",
						args: {
							tenant: frm.doc.name,
							site_name: values.site_name,
							environment_name: values.environment_name,
							policy: values.policy,
							expiry_date: values.expiry_date,
							demo_seed_mode: values.demo_seed_mode,
							demo_seed_reference: values.demo_seed_reference,
							status_reason: values.status_reason,
						},
						freeze: true,
						freeze_message: __("Creating sandbox environment"),
						callback: ({ message }) => {
							if (!message) {
								return;
							}

							frappe.show_alert({
								message: __("Sandbox environment {0} created", [message.name]),
								indicator: "green",
							});
							frm.reload_doc();
							frappe.set_route("Form", "Tenant Environment", message.name);

							if (!values.auto_provision_runtime) {
								return;
							}

							frappe.call({
								method: "ifitwala_press.api.lifecycle.provision_founder_demo_runtime",
								args: {
									environment: message.name,
								},
								freeze: true,
								freeze_message: __("Provisioning founder demo runtime"),
								callback: () => {
									frappe.show_alert({
										message: __("Founder demo runtime provisioned"),
										indicator: "green",
									});
									if (
										window.cur_frm &&
										cur_frm.doctype === "Tenant Environment" &&
										cur_frm.doc.name === message.name
									) {
										cur_frm.reload_doc();
									}
								},
							});
						},
					});
				},
				__("Create Sandbox"),
				__("Create")
			);
		}, __("Actions"));
	},
});


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


function hasSubscriptionRole() {
	return (
		frappe.user.has_role("Ifitwala Press Admin") ||
		frappe.user.has_role("Ifitwala Press Sales") ||
		frappe.user.has_role("Ifitwala Press Finance")
	);
}


function hasCostSnapshotRole() {
	return hasUsageSnapshotRole() || frappe.user.has_role("Ifitwala Press Finance");
}


function renderLinkedEnvironments(frm) {
	frappe.call({
		method: "ifitwala_press.api.views.get_tenant_environment_panel",
		args: { tenant: frm.doc.name },
		callback: ({ message }) => {
			const environments = message?.environments || [];
			if (!environments.length) {
				frm.set_df_property(
					"linked_environments_html",
					"options",
					'<div class="text-muted">No linked environments yet.</div>'
				);
				frm.refresh_field("linked_environments_html");
				return;
			}

			const rows = environments
				.map((environment) => {
					const title = frappe.utils.escape_html(
						environment.environment_name || environment.site_name || environment.name
					);
					const state = frappe.utils.escape_html(environment.site_status || "Unknown");
					const kind = frappe.utils.escape_html(environment.environment_type || "Unknown");
					const tier = frappe.utils.escape_html(environment.hosting_tier || "Unassigned");
					const domain = environment.primary_domain
						? `<div class="text-muted small">${frappe.utils.escape_html(environment.primary_domain)}</div>`
						: "";

					return `
						<div class="ifitwala-panel-row">
							<div>
								<div><a href="/app/tenant-environment/${encodeURIComponent(environment.name)}">${title}</a></div>
								${domain}
							</div>
							<div class="text-muted small">${kind} | ${state} | ${tier}</div>
						</div>
					`;
				})
				.join("");

			frm.set_df_property(
				"linked_environments_html",
				"options",
				`<div class="ifitwala-panel">${rows}</div>`
			);
			frm.refresh_field("linked_environments_html");
		},
	});
}


function renderBusinessSummary(frm) {
	frappe.call({
		method: "ifitwala_press.api.business.get_tenant_business_summary",
		args: { tenant: frm.doc.name },
		callback: ({ message }) => {
			const subscription = message?.subscription;
			const usage = message?.usage_snapshot;
			const cost = message?.cost_snapshot;

			const sections = [
				renderSummaryBlock(
					__("Subscription"),
					subscription
						? [
							`${escape(subscription.plan_name || __("Unnamed Plan"))}`,
							`${escape(subscription.subscription_tier || "-")} | ${escape(subscription.status || "-")}`,
							`${escape(subscription.billing_cycle || "-")}${subscription.price ? ` | ${escape(subscription.price)} ${escape(subscription.currency || "")}` : ""}`,
						]
						: [__("No subscription recorded.")],
				),
				renderSummaryBlock(
					__("Latest Usage"),
					usage
						? [
							`${escape(usage.snapshot_on_display || "")}`,
							`${escape(String(usage.active_users_30d || 0))} active users | ${escape(String(usage.request_count || 0))} requests`,
							`${escape(String(usage.storage_used_gb || 0))} GB storage | peak concurrency ${escape(String(usage.peak_concurrency_estimate || 0))}`,
						]
						: [__("No usage snapshot recorded.")],
				),
				renderSummaryBlock(
					__("Latest Cost"),
					cost
						? [
							`${escape(cost.snapshot_on_display || "")}`,
							`${escape(String(cost.total_cost_estimate || 0))} ${escape(cost.currency || "")} total`,
							`DB ${escape(String(cost.db_cost_estimate || 0))} | Storage ${escape(String(cost.storage_cost_estimate || 0))} | Compute ${escape(String(cost.compute_cost_estimate || 0))}`,
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
