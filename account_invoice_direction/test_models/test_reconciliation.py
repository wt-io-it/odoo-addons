# -*- coding: utf-8 -*-

from odoo.addons.account.tests.test_reconciliation import TestReconciliation
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta

EARLIEST_DATE_USED_IN_TEST_RECONCILIATION = (datetime.today() - timedelta(days=60)).strftime(DEFAULT_SERVER_DATE_FORMAT)


def move_pre_existing_invoices_wrapper(method):
    """
    Because test_reconciliation creates invoices in the past we need to check if there are pre existing invoices that
    would prevent creating the tests invoices, we move those pre existing invoices far enough into the past for the
    test to not be bothered by them (and rollback at the end of the test takes care that everything seems the same
    after the test)
    :param method setUp method of the test that creates invoices in the past
    :returns wrapped method
    """
    def wrapped_method(self):
        method(self)
        for invoice in self.env['account.invoice'].search([
            ('state', 'not in', ['cancel', 'draft']),
            ('date_invoice', '>', EARLIEST_DATE_USED_IN_TEST_RECONCILIATION)
        ]):
            invoice.date_invoice = EARLIEST_DATE_USED_IN_TEST_RECONCILIATION

    return wrapped_method


TestReconciliation.setUp = move_pre_existing_invoices_wrapper(TestReconciliation.setUp)
