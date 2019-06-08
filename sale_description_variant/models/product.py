# -*- coding: utf-8 -*-

from odoo import models, api, fields, _

import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    description_sale_variant = fields.Text(
        'Sale Variant Description', translate=True,
        help="A description of the Product that you want to communicate to your customers. "
             "This description will be copied to every Sales Order, Delivery Order and Customer Invoice/Credit Note")
