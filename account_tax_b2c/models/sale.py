# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api

import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order']

    def _amount_all(self):
        company = self.env.user.company_id
        for order in self:
            company = order.company_id
            current_method = company.tax_calculation_rounding_method
            if not order.fiscal_position_id.b2c_fiscal_position:
                method = 'round_globally'
            else:
                method = 'round_per_line'
            company._set_rounding_method(method=method)

            _logger.debug('Amount All: Tax Calculation Rounding Method: %s', company.tax_calculation_rounding_method)
            super(SaleOrder, order)._amount_all()
            _logger.debug('Total: %s | Tax: %s | Subtotal: %s | Rounding Method: %s', order.amount_total, order.amount_tax, order.amount_untaxed, company.tax_calculation_rounding_method)
            company._set_rounding_method(method=current_method)


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line']

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        company = self.env.user.company_id
        for line in self:
            company = line.company_id
            current_method = company.tax_calculation_rounding_method
            order = line.order_id
            fiscal_position = order.fiscal_position_id
            if not fiscal_position.b2c_fiscal_position:
                method = 'round_globally'
            else:
                method = 'round_per_line'
            company._set_rounding_method(method=method)
            res = super(SaleOrderLine, line)._compute_amount()
            _logger.debug('Total: %s | Tax: %s | Subtotal: %s | Rounding Method: %s', line.price_total, line.price_tax, line.price_subtotal, company.tax_calculation_rounding_method)
            company._set_rounding_method(method=current_method)
        return res
