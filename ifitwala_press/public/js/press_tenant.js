frappe.ui.form.on("Press Tenant", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		renderLinkedEnvironments(frm);

		if (frm.doc.active_environment) {
			frm.add_custom_button(__("Open Active Environment"), () => {
				frappe.set_route("Form", "Tenant Environment", frm.doc.active_environment);
			});
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
