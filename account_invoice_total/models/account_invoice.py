# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    check_total = fields.Monetary(
        string='Verification Total',
        readonly=True, states={'draft': [('readonly', False)]},
        default=0.0
    )

    @api.multi
    def _business_case_needs_check_total(self):
        business_type = 'sale'
        if self.type in ['in_invoice', 'in_refund']:
            business_type = 'purchase'

        if (
            business_type == 'purchase' and not self.invoice_direction_role or
            business_type == 'sale' and self.invoice_direction_role
        ):
            return True
        return False

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        values = super(AccountInvoice, self)._prepare_refund(invoice, date_invoice=date_invoice, date=date, description=description, journal_id=journal_id)
        if invoice._business_case_needs_check_total():
            values['check_total'] = invoice.check_total
        return values

    @api.onchange('invoice_direction_role')
    def onchange_direction(self):
        if not self._business_case_needs_check_total():
            self.check_total = 0.0

    @api.multi
    def invoice_validate(self):
        for invoice in self:
            if not self._context.get('install_mode') and not self._context.get('from_purchase_order_change')\
                    and not invoice._get_external_ids()[invoice.id]\
                    and (
                        float_compare(invoice.check_total, invoice.amount_total, precision_digits=2) != 0 and
                        invoice._business_case_needs_check_total()):
                raise UserError(
                    _('Please verify the total of the invoice!\nThe encoded total does not match the computed total.')
                )
        return super(AccountInvoice, self).invoice_validate()
