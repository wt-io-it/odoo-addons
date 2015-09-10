# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class product_template(models.Model):
    _inherit = 'product.template'

    web_list_price = fields.Float(
        compute='_compute_web_price',
    )

    def _compute_web_price(self):
        for template in self:
            factor = 1
            if 'request' in self.env.context:
                factor = template.get_list_price_factor(template, self.env.context['request'])
            template.web_list_price = template.lst_price * factor


class product_product(models.Model):
    _inherit = 'product.product'

    web_list_price = fields.Float(
        compute='_compute_web_price',
    )

    @api.multi
    def _compute_web_price(self):
        for product in self:
            factor = 1
            if 'request' in self.env.context:
                request = self.env.context['request']
                factor = product.product_tmpl_id.get_list_price_factor(product, request)
            if 'order' in self.env.context:
                order = self.env.context['order']
                if hasattr(order.fiscal_position, 'b2c_fiscal_position') and order.fiscal_position.b2c_fiscal_position:
                    if product.brut_net_factor > 0:
                        factor = product.brut_net_factor
            product.web_list_price = product.lst_price * factor
