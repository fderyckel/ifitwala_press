frappe.pages["control-plane-home"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Control Plane Home"),
		single_column: true,
	});

	const home = new ControlPlaneHome(wrapper, page);
	wrapper.controlPlaneHome = home;
	home.renderSkeleton();
	home.refresh();
};


class ControlPlaneHome {
	constructor(wrapper, page) {
		this.wrapper = wrapper;
		this.page = page;
		this.body = $('<div class="ifitwala-home-page"></div>').appendTo(page.body);
		this.page.set_primary_action(__("Refresh"), () => this.refresh());
		this.page.set_secondary_action(__("Workspace"), () => frappe.set_route("Workspaces", "Ifitwala Press"));
		this.page.add_menu_item(__("Tenants"), () => frappe.set_route("List", "Press Tenant"));
		this.page.add_menu_item(__("Environments"), () => frappe.set_route("List", "Tenant Environment"));
	}

	renderSkeleton() {
		this.body.html(`
			<div class="ifitwala-home-section">
				<div class="ifitwala-home-heading">
					<div>
						<h3>${__("Operational Snapshot")}</h3>
						<p>${__("Control-plane posture for current tenants, environments, and commercial risk.")}</p>
					</div>
				</div>
				<div data-home-summary></div>
			</div>
			<div class="ifitwala-home-grid">
				<div class="ifitwala-home-section">
					<div class="ifitwala-home-heading">
						<div>
							<h3>${__("Attention Queue")}</h3>
							<p>${__("Short list of environments and tenants that need operator action next.")}</p>
						</div>
					</div>
					<div data-home-attention></div>
				</div>
				<div class="ifitwala-home-section">
					<div class="ifitwala-home-heading">
						<div>
							<h3>${__("Lifecycle Overview")}</h3>
							<p>${__("Environment count by lifecycle state.")}</p>
						</div>
					</div>
					<div data-home-lifecycle></div>
				</div>
			</div>
			<div class="ifitwala-home-section">
				<div class="ifitwala-home-heading">
					<div>
						<h3>${__("Cost Overview")}</h3>
						<p>${__("Highest estimated monthly cost environments from the current cached summaries.")}</p>
					</div>
				</div>
				<div data-home-cost></div>
			</div>
		`);
	}

	refresh() {
		frappe.call({
			method: "ifitwala_press.api.views.get_control_plane_home",
			freeze: false,
			callback: ({ message }) => {
				const payload = message || {};
				this.renderSummary(payload.summary_cards || []);
				this.renderAttention(payload.attention_queue || []);
				this.renderLifecycle(payload.lifecycle_overview || []);
				this.renderCost(payload.top_cost_environments || []);
			},
		});
	}

	renderSummary(cards) {
		const html = cards.length
			? `<div class="ifitwala-home-summary-grid">${cards.map((card) => renderMetricCard(card)).join("")}</div>`
			: renderEmptyState(__("No summary data yet."));
		this.body.find("[data-home-summary]").html(html);
	}

	renderAttention(items) {
		if (!items.length) {
			this.body.find("[data-home-attention]").html(renderEmptyState(__("Nothing urgent right now.")));
			return;
		}

		const rows = items
			.map((item) => {
				const route = JSON.stringify(item.route || []);
				return `
					<button class="ifitwala-home-row-button" data-route='${escapeAttr(route)}'>
						<div class="ifitwala-panel-row">
							<div>
								<div class="ifitwala-home-row-title">${escapeHtml(item.title)}</div>
								<div class="text-muted small">${escapeHtml(item.detail || "")}</div>
							</div>
							<span class="indicator-pill ${escapeClass(item.indicator || "blue")}">${escapeHtml(item.indicator || "info")}</span>
						</div>
					</button>
				`;
			})
			.join("");

		const panel = $(`<div class="ifitwala-panel">${rows}</div>`);
		panel.find("[data-route]").on("click", function () {
			const route = JSON.parse($(this).attr("data-route") || "[]");
			if (route.length) {
				frappe.set_route(...route);
			}
		});
		this.body.find("[data-home-attention]").empty().append(panel);
	}

	renderLifecycle(items) {
		const html = items.length
			? `<div class="ifitwala-home-summary-grid">${items
					.map((item) => renderMetricCard({ label: item.state, value: item.count, indicator: lifecycleIndicator(item.state) }))
					.join("")}</div>`
			: renderEmptyState(__("No lifecycle data yet."));
		this.body.find("[data-home-lifecycle]").html(html);
	}

	renderCost(items) {
		if (!items.length) {
			this.body.find("[data-home-cost]").html(renderEmptyState(__("No cost summaries recorded yet.")));
			return;
		}

		const rows = items
			.map((item) => `
				<div class="ifitwala-panel-row">
					<div>
						<div class="ifitwala-home-row-title">${escapeHtml(item.environment_name || item.name)}</div>
						<div class="text-muted small">${escapeHtml(item.site_status || "")}</div>
					</div>
					<div class="text-right">
						<div class="ifitwala-home-cost-value">${formatCurrency(item.estimated_monthly_cost)}</div>
						<div class="text-muted small">${escapeHtml(item.tenant || "")}</div>
					</div>
				</div>
			`)
			.join("");
		this.body.find("[data-home-cost]").html(`<div class="ifitwala-panel">${rows}</div>`);
	}
}


function renderMetricCard(card) {
	return `
		<div class="ifitwala-home-metric">
			<div class="ifitwala-home-metric-label">${escapeHtml(card.label)}</div>
			<div class="ifitwala-home-metric-value">${card.is_currency ? formatCurrency(card.value) : escapeHtml(String(card.value ?? 0))}</div>
			<div class="indicator-pill ${escapeClass(card.indicator || "blue")}">${escapeHtml(card.indicator || "info")}</div>
		</div>
	`;
}


function renderEmptyState(message) {
	return `<div class="ifitwala-summary-block text-muted">${escapeHtml(message)}</div>`;
}


function formatCurrency(value) {
	return format_number(value || 0, null, 2);
}


function lifecycleIndicator(state) {
	if (state === "Live") {
		return "green";
	}
	if (state === "Provisioning Failed") {
		return "red";
	}
	if (state === "Suspended" || state === "Sandbox Expired") {
		return "orange";
	}
	return "blue";
}


function escapeHtml(value) {
	return frappe.utils.escape_html(value == null ? "" : String(value));
}


function escapeAttr(value) {
	return escapeHtml(value).replace(/"/g, "&quot;");
}


function escapeClass(value) {
	return String(value || "")
		.toLowerCase()
		.replace(/[^a-z0-9-]/g, "");
}
