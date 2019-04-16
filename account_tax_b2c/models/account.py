# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from odoo.addons import decimal_precision as dp

import logging

_logger = logging.getLogger(__name__)


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    b2c_fiscal_position = fields.Boolean(string='B2C')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def get_taxes_values(self):
        if len(self) == 0:
            company = self.env.user.company_id
        else:
            company = self[0].company_id
        current_method = company.tax_calculation_rounding_method
        if not self.fiscal_position_id.b2c_fiscal_position:
            method = 'round_globally'
        else:
            method = 'round_per_line'
        company._set_rounding_method(method=method)
        _logger.debug('Taxes Computation: Tax Calculation Rounding Method: %s', company.tax_calculation_rounding_method)
        tax_grouped = super(AccountInvoice, self).get_taxes_values()
        company._set_rounding_method(method=current_method)
        return tax_grouped

    def _compute_residual(self):
        company = self.env.user.company_id
        for invoice in self:
            company = invoice.company_id
            current_method = company.tax_calculation_rounding_method
            if not invoice.fiscal_position_id.b2c_fiscal_position:
                method = 'round_globally'
            else:
                method = 'round_per_line'
            company._set_rounding_method(method=method)
            _logger.debug('Compute Residual: Tax Calculation Rounding Method: %s', company.tax_calculation_rounding_method)
            super(AccountInvoice, invoice)._compute_residual()
            company._set_rounding_method(method=current_method)
