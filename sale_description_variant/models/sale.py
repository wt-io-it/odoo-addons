# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        result = super(SaleOrderLine, self).product_id_change()

        if self.product_id.description_sale_variant:
            self.name += '\n' + self.product_id.description_sale_variant

        return result
