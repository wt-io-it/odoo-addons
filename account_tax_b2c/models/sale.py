# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api

import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order']

    def _amount_all(self):
        if len(self) == 0:
            company_id = self.env.user.company_id
        else:
            company_id = self[0].company_id
        company = company_id.sudo()
        current_method = company.tax_calculation_rounding_method
        for order in self:
            if not order.fiscal_position_id.b2c_fiscal_position:
                company.tax_calculation_rounding_method = 'round_globally'
            else:
                company.tax_calculation_rounding_method = 'round_per_line'
            _logger.debug('Amount All: Tax Calculation Rounding Method: %s', company.tax_calculation_rounding_method)
            order.company_id.sudo().tax_calculation_rounding_method = company.tax_calculation_rounding_method
            super(SaleOrder, order)._amount_all()
        company.tax_calculation_rounding_method = current_method


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line']

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        if len(self) == 0:
            company_id = self.env.user.company_id
        else:
            company_id = self[0].company_id
        company = company_id.sudo()
        current_method = company.tax_calculation_rounding_method

        for line in self:
            fiscal_position = line.mapped('order_id').mapped('fiscal_position_id')
            if not fiscal_position.mapped('b2c_fiscal_position'):
                company.tax_calculation_rounding_method = 'round_globally'
            else:
                company.tax_calculation_rounding_method = 'round_per_line'
            self.mapped('company_id').sudo().tax_calculation_rounding_method = company.tax_calculation_rounding_method
            _logger.debug('Compute Amount: Tax Calculation Rounding Method: %s vs. %s', company_id.tax_calculation_rounding_method, company.tax_calculation_rounding_method)
            res = super(SaleOrderLine, line)._compute_amount()
            company.tax_calculation_rounding_method = current_method
        if res:
            _logger.warning('Result for _compute_amount: %s', res)
        return res
