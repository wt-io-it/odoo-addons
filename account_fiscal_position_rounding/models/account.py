# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class account_tax(models.Model):
    _inherit = 'account.tax'

    reverse_charge = fields.Boolean(
        string="Reverse Charge"
    )

    @api.v7
    def compute_all(self, cr, uid, taxes, price_unit, quantity, product=None, partner=None, force_excluded=False, context=None):
        context = context or {}

        res = super(account_tax, self).compute_all(
            cr, uid, taxes, price_unit, quantity,
            product=product, partner=partner, force_excluded=force_excluded
        )
        return res

    @api.v8
    def compute_all(self, price_unit, quantity, product=None, partner=None, force_excluded=False):
        rounding_setting = self.env.user.company_id.tax_calculation_rounding_method
        _logger.debug('Rounding: %s', rounding_setting)
        if not self._context.get('b2c', True):
            self.env.user.company_id.tax_calculation_rounding_method = 'round_globally'
            force_excluded = True
            _logger.debug('B2B: Round globally')

        res = super(account_tax, self).compute_all(
            price_unit, quantity,
            product=product, partner=partner, force_excluded=force_excluded
        )
        self.env.user.company_id.tax_calculation_rounding_method = rounding_setting

        return res


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    def _get_b2c_context(self):
        if self.fiscal_position.b2c_fiscal_position:
            return True
        return False

    @api.multi
    def button_reset_taxes(self):
        account_invoice_tax = self.env['account.invoice.tax']
        ctx = dict(self._context)
        for invoice in self:
            self._cr.execute("DELETE FROM account_invoice_tax WHERE invoice_id=%s AND manual is False", (invoice.id,))
            self.invalidate_cache()
            partner = invoice.partner_id
            if partner.lang:
                ctx['lang'] = partner.lang
            ctx['b2c'] = invoice._get_b2c_context()
            for taxe in account_invoice_tax.with_context(ctx).compute(invoice).values():
                # We get the tax by reverse engineering the correct name
                name = taxe['name'].split(' - ')
                tax_retrieval = self.env['account.tax'].search(['|', ('description', 'ilike', name[0]), ('name', 'ilike', name[0])])
                for tax in tax_retrieval:
                    if tax.type == 'percent':
                        sum_child_ids = float(tax.amount)
                    if tax.reverse_charge:
                        sum_child_ids = 0
                    if tax.parent_id and tax in tax.parent_id.child_ids:
                        sum_child_ids = 0
                        for sub_tax in tax.parent_id.child_ids:
                            sum_child_ids += sub_tax.amount
                    taxe['name'] = 'USt. %i%%' % int(sum_child_ids * 100)
                account_invoice_tax.with_context(ctx).create(taxe)
        # dummy write on self to trigger recomputations
        return self.with_context(ctx).write({'invoice_line': []})


class account_invoice_tax(models.Model):
    _inherit = 'account.invoice.tax'

    def _get_b2c_context(self):
        if self.fiscal_position.b2c_fiscal_position:
            return True
        return False

    @api.v8
    def compute(self, invoice):
        tax_grouped = {}
        currency = invoice.currency_id.with_context(date=invoice.date_invoice or fields.Date.context_today(invoice))
        company_currency = invoice.company_id.currency_id
        for line in invoice.invoice_line:
            taxes = line.invoice_line_tax_id.with_context(b2c=invoice._get_b2c_context()).compute_all(
                (line.price_unit * (1 - (line.discount or 0.0) / 100.0)),
                line.quantity, line.product_id, invoice.partner_id)['taxes']
            for tax in taxes:
                val = {
                    'invoice_id': invoice.id,
                    'name': tax['name'],
                    'amount': tax['amount'],
                    'manual': False,
                    'sequence': tax['sequence'],
                    'base': currency.round(tax['price_unit'] * line['quantity']),
                }
                if invoice.type in ('out_invoice', 'in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = currency.compute(val['base'] * tax['base_sign'], company_currency, round=False)
                    val['tax_amount'] = currency.compute(val['amount'] * tax['tax_sign'], company_currency, round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_collected_id']
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = currency.compute(val['base'] * tax['ref_base_sign'], company_currency, round=False)
                    val['tax_amount'] = currency.compute(val['amount'] * tax['ref_tax_sign'], company_currency, round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_paid_id']

                # If the taxes generate moves on the same financial account as the invoice line
                # and no default analytic account is defined at the tax level, propagate the
                # analytic account from the invoice line to the tax line. This is necessary
                # in situations were (part of) the taxes cannot be reclaimed,
                # to ensure the tax move is allocated to the proper analytic account.
                if not val.get('account_analytic_id') and line.account_analytic_id and val['account_id'] == line.account_id.id:
                    val['account_analytic_id'] = line.account_analytic_id.id

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']

        for t in tax_grouped.values():
            t['base'] = currency.round(t['base'])
            t['amount'] = currency.round(t['amount'])
            t['base_amount'] = currency.round(t['base_amount'])
            t['tax_amount'] = currency.round(t['tax_amount'])

        return tax_grouped


class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    price_subtotal_custom = fields.Float(
        string='Amount',
        digits=dp.get_precision('Account'),
        compute='_compute_price'
    )

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_id', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id')
    def _compute_price(self):
        invoice = self.invoice_id
        b2c = invoice._get_b2c_context()
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = self.invoice_line_tax_id.with_context(b2c=b2c).compute_all(price, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_subtotal = taxes['total']
        if b2c:
            self.price_subtotal_custom = taxes['total_included']
        else:
            self.price_subtotal_custom = taxes['total']

        if invoice:
            self.price_subtotal = self.invoice_id.currency_id.round(self.price_subtotal)
            self.price_subtotal_custom = self.invoice_id.currency_id.round(self.price_subtotal_custom)

    @api.model
    def _default_price_unit(self):
        invoice = self.invoice_id
        return super(account_invoice_line, self).with_context(b2c=invoice._get_b2c_context())._default_price_unit()
