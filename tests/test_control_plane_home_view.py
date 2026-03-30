from __future__ import annotations

import importlib
import sys
from datetime import date
from types import ModuleType

import pytest


def _load_views_module(monkeypatch: pytest.MonkeyPatch):
	fake_frappe = ModuleType("frappe")
	fake_frappe.whitelist = lambda *args, **kwargs: (lambda fn: fn)  # type: ignore[attr-defined]
	fake_utils = ModuleType("frappe.utils")
	fake_utils.format_datetime = lambda value: str(value)  # type: ignore[attr-defined]

	monkeypatch.setitem(sys.modules, "frappe", fake_frappe)
	monkeypatch.setitem(sys.modules, "frappe.utils", fake_utils)
	sys.modules.pop("ifitwala_press.api.views", None)
	return importlib.import_module("ifitwala_press.api.views")


def test_build_control_plane_home_rolls_up_summary_and_attention(monkeypatch: pytest.MonkeyPatch) -> None:
	module = _load_views_module(monkeypatch)

	result = module._build_control_plane_home(
		tenants=[
			{
				"name": "TEN-001",
				"tenant_name": "Alpha School",
				"tenant_status": "Customer",
				"subscription_status": "Active",
				"contract_end_date": "2026-04-15",
				"vip_flag": 0,
			},
			{
				"name": "TEN-002",
				"tenant_name": "VIP Academy",
				"tenant_status": "Suspended",
				"subscription_status": "Active",
				"contract_end_date": "2026-05-30",
				"vip_flag": 1,
			},
		],
		environments=[
			{
				"name": "ENV-001",
				"tenant": "TEN-001",
				"environment_name": "Alpha Production",
				"environment_type": "Production",
				"site_name": "alpha",
				"site_status": "Live",
				"capacity_state": "Critical",
				"health_score": 42,
				"estimated_monthly_cost": 120.5,
				"expires_on": None,
			},
			{
				"name": "ENV-002",
				"tenant": "TEN-002",
				"environment_name": "VIP Sandbox",
				"environment_type": "Sandbox",
				"site_name": "vip-sandbox",
				"site_status": "Sandbox Active",
				"capacity_state": "Healthy",
				"health_score": 88,
				"estimated_monthly_cost": 55,
				"expires_on": "2026-04-02",
			},
			{
				"name": "ENV-003",
				"tenant": "TEN-001",
				"environment_name": "Broken Sandbox",
				"environment_type": "Sandbox",
				"site_name": "alpha-broken",
				"site_status": "Provisioning Failed",
				"capacity_state": "Warning",
				"health_score": None,
				"estimated_monthly_cost": 0,
				"expires_on": None,
			},
		],
		as_of=date(2026, 3, 30),
	)

	summary = {row["label"]: row["value"] for row in result["summary_cards"]}
	assert summary["Total Tenants"] == 2
	assert summary["Live Environments"] == 1
	assert summary["Sandbox Environments"] == 2
	assert summary["Capacity Alerts"] == 2
	assert summary["Provisioning Failures"] == 1
	assert summary["Renewals Due Soon"] == 1
	assert summary["Total Estimated Monthly Cost"] == 175.5

	lifecycle = {row["state"]: row["count"] for row in result["lifecycle_overview"]}
	assert lifecycle["Live"] == 1
	assert lifecycle["Sandbox Active"] == 1
	assert lifecycle["Provisioning Failed"] == 1

	attention_titles = [row["title"] for row in result["attention_queue"]]
	assert "Provisioning failed" in attention_titles
	assert "Critical capacity" in attention_titles
	assert "Low health score" in attention_titles
	assert "Sandbox expires soon" in attention_titles
	assert "Suspended VIP tenant" in attention_titles
	assert "Contract renewal due soon" in attention_titles

	assert result["top_cost_environments"][0]["environment_name"] == "Alpha Production"
	assert result["top_cost_environments"][0]["estimated_monthly_cost"] == 120.5
