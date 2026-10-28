"""Regression tests for ETA submission isolation and safe background jobs."""

from types import SimpleNamespace

import frappe
import pytest

from erpnext_egypt_compliance.erpnext_eta import main


def test_batch_submission_filters_by_company(monkeypatch):
    captured = {}

    connector = SimpleNamespace(submission_mode="Batch", eta_batch_size=10, delay_in_hours=0)
    monkeypatch.setattr(main, "get_company_eta_connector", lambda company: connector)

    def get_all(doctype, **kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(frappe, "get_all", get_all)
    main.get_batch_invoices("Company A")

    assert ["company", "=", "Company A"] in captured["filters"]
    assert ["docstatus", "=", 1] in captured["filters"]


def test_live_submission_skips_already_submitted(monkeypatch):
    invoice = SimpleNamespace(docstatus=1, company="Company A")
    invoice.get = lambda key: {"eta_submission_id": "submission-1", "eta_status": "", "eta_signature": "abc"}.get(key)

    monkeypatch.setattr(frappe, "get_doc", lambda doctype, name: invoice)
    monkeypatch.setattr(
        main, "submit_einvoice_background_logger",
        lambda *args, **kwargs: pytest.fail("Already submitted invoice must not be sent"),
    )

    main.autosubmit_eta_live_submission("INV-0001")
