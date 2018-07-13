# -*- coding: utf-8 -*-

from odoo import models, api, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # in the tests we simulate that the user always entered this value correct
    check_total = fields.Monetary(
        compute='_compute_check_total',
    )

    @api.multi
    @api.depends('amount_total')
    def _compute_check_total(self):
        for invoice in self:
            invoice.check_total = invoice.amount_total

