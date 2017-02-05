# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.float_utils import float_round
from odoo.addons import decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)


class product_category(models.Model):
    _inherit = "product.category"

    brut_net_factor = fields.Float(string='Gross/Net Ratio', default=1)


class product_template(models.Model):
    _inherit = 'product.template'

    list_price = fields.Float(
        compute='_compute_net_price',
    )
    lst_price_brut = fields.Monetary(
        string='Gross selling price',
        digits=dp.get_precision('Product Price'),
    )

    brut_net_factor = fields.Float(string='Gross/Net Ratio', default=1)

    @api.onchange('categ_id')
    def onchange_product_category(self):
        if self.categ_id.brut_net_factor > 0:
            self.brut_net_factor = self.categ_id.brut_net_factor

    @api.depends('lst_price_brut', 'brut_net_factor')
    def _compute_net_price(self):
        for template in self:
            if template.brut_net_factor:
                template.list_price = template.lst_price_brut / template.brut_net_factor


class product_product(models.Model):
    _inherit = 'product.product'

    @api.onchange('categ_id')
    def onchange_product_category(self):
        if self.categ_id.brut_net_factor > 0:
            self.product_tmpl_id.write({'brut_net_factor': self.categ_id.brut_net_factor})
            self.product_tmpl_id._compute_net_price()

            self.lst_price = self.lst_price_brut / self.categ_id.brut_net_factor
