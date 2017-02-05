# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
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
    def product_id_change(
        self, product, uom_id, qty=0, name='', type='out_invoice',
        partner_id=False, fposition_id=False, price_unit=False,
        currency_id=False, company_id=None
    ):
        res = super(AccountInvoiceLine, self).product_id_change(
            product, uom_id, qty=qty, name=name, type=type,
            partner_id=partner_id, fposition_id=fposition_id,
            price_unit=price_unit, currency_id=currency_id, company_id=company_id
        )
        if res.get('value', False):
            if 'account_id' in res['value'] and 'invoice_line_tax_id' in res['value']:
                account = self.account_id.browse(res['value']['account_id'])
                taxes = self.invoice_line_tax_id.browse(res['value']['invoice_line_tax_id'])
                self._check_restricted_tax_ids(account, taxes)

        return res

    def _check_restricted_tax_ids(self, account, taxes):
        error = []
        if account.restricted_tax_ids:
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

    @api.multi
    def onchange_account_id(self, product_id, partner_id, inv_type, fposition_id, account_id):
        res = super(AccountInvoiceLine, self).onchange_account_id(product_id, partner_id, inv_type, fposition_id, account_id)

        if res.get('value', False):

            fpos = self.env['account.fiscal.position'].browse(fposition_id)
            account = self.account_id.browse(account_id)
            product = self.product_id.browse(product_id)
            if not res['value']['invoice_line_tax_id']:
                if inv_type in ('out_invoice', 'out_refund'):
                    default_taxes = product.taxes_id or account.tax_ids
                else:
                    default_taxes = product.supplier_taxes_id or account.tax_ids
                res['value']['invoice_line_tax_id'] = fpos.map_tax(default_taxes)
            tax_ids = res['value']['invoice_line_tax_id']
            taxes = self.invoice_line_tax_id.browse(tax_ids)

            self._check_restricted_tax_ids(account, taxes)

        return res
