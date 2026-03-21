frappe.ui.form.on("Tenant Environment", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		renderTransitionHistory(frm);

		if (!hasLifecycleRole()) {
			return;
		}

		addLifecycleButtons(frm);
	},
});


function addLifecycleButtons(frm) {
	const status = frm.doc.site_status;

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
