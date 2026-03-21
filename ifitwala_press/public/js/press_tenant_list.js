frappe.listview_settings["Press Tenant"] = {
	add_fields: [
		"tenant_status",
		"subscription_tier",
		"subscription_status",
		"vip_flag",
		"active_environment",
		"contract_end_date",
		"sales_owner",
		"estimated_students",
	],
	get_indicator(doc) {
		if (doc.tenant_status === "Suspended" || doc.tenant_status === "Archived") {
			return [__(doc.tenant_status), "red", "tenant_status,=," + doc.tenant_status];
		}

		if (doc.vip_flag) {
			return [__("VIP"), "purple", "vip_flag,=,1"];
		}

		if (doc.subscription_status === "Trial" || doc.tenant_status === "Trial") {
			return [__("Trial"), "orange", "subscription_status,=,Trial"];
		}

		if (doc.subscription_status === "Pending Renewal") {
			return [__("Pending Renewal"), "yellow", "subscription_status,=,Pending Renewal"];
		}

		return [__(doc.tenant_status || "Lead"), "blue", "tenant_status,=," + (doc.tenant_status || "Lead")];
	},
};
