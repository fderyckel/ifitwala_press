frappe.listview_settings["Tenant Environment"] = {
	add_fields: [
		"site_status",
		"environment_type",
		"hosting_tier",
		"database_mode",
		"primary_domain",
		"region",
		"health_score",
		"capacity_state",
		"estimated_monthly_cost",
		"last_health_check",
	],
	get_indicator(doc) {
		if (doc.site_status === "Provisioning Failed") {
			return [__("Provisioning Failed"), "red", "site_status,=,Provisioning Failed"];
		}

		if (doc.site_status === "Suspended") {
			return [__("Suspended"), "orange", "site_status,=,Suspended"];
		}

		if (doc.capacity_state === "Critical" || doc.capacity_state === "Saturated") {
			return [__(doc.capacity_state), "red", "capacity_state,=," + doc.capacity_state];
		}

		if (doc.site_status === "Live") {
			return [__("Live"), "green", "site_status,=,Live"];
		}

		if (doc.site_status === "Sandbox Active") {
			return [__("Sandbox Active"), "blue", "site_status,=,Sandbox Active"];
		}

		return [__(doc.site_status || "Lead"), "gray", "site_status,=," + (doc.site_status || "Lead")];
	},
};
