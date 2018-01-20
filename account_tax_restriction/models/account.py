# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, UserError
from odoo.addons import decimal_precision as dp

import logging

_logger = logging.getLogger(__name__)


class AccountAccount(models.Model):
    _inherit = 'account.account'

    restricted_tax_ids = fields.Many2many(
        'account.tax',
        rel='restrict_account_tax_item_rel',
        id1='account_id',
        id2='tax_id',
        string="Restricted Tax",
    )


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        for invoice in self:
            for line in invoice.invoice_line_ids:
                line._check_restricted_tax_ids(line.account_id, line.invoice_line_tax_ids)

        return super(AccountInvoice, self).invoice_validate()


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    @api.onchange('product_id', 'account_id', 'invoice_line_tax_ids')
    def onchange_check_restricted_tax(self):
        self._check_restricted_tax_ids(self.account_id, self.invoice_line_tax_ids, skip_empty=True)

    def _check_restricted_tax_ids(self, account, taxes, skip_empty=False):
        error = []
        if account.restricted_tax_ids:
            if not taxes and not skip_empty:
                raise UserError(
                    _('No taxes are coded for line %s, but it is required to have one of these taxes (%s) for account %s %s coded.') %
                    (self.name, ', '.join(account.restricted_tax_ids.mapped('name')), account.code, account.name)
                )
            for tax in taxes:
                if tax in account.restricted_tax_ids:
                    _logger.info("%s allowed", tax.name)
                else:
                    error.append(tax.name)
        if error:
            text = 'is'
            if len(error) > 1:
                text = 'are'
            raise except_orm(
                _('Error'),
                ', '.join(error) + _('\n\n%s not allowed on\n\n%s %s') % (text, account.code, account.name)
            )
        return True
