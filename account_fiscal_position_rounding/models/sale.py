# -*- coding: utf-8 -*-

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)


class sale_order(models.Model):
    _inherit = 'sale.order'

    def _get_b2c_context(self):
        if self.fiscal_position.b2c_fiscal_position:
            return True
        return False


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    price_subtotal = fields.Float(
        string='Subtotal',
        compute='_amount_line',
        digits=dp.get_precision('Account')
    )

    @api.multi
    @api.onchange(
        'price_unit',
        'price_reduce',
        'product_uom_qty'
    )
    def _amount_line(self):
        for line in self:
            order = line.order_id

            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.with_context(
                b2c=order._get_b2c_context()
            ).compute_all(
                price, line.product_uom_qty,
                line.product_id, order.partner_id
            )

            line.price_subtotal = order.pricelist_id.currency_id.round(taxes['total'])
