# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.website_sale_stock.controllers.main import WebsiteSale
from odoo.tools.pycompat import izip
from odoo.http import request
from odoo.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class WebsiteSaleCustom(WebsiteSale):

    def get_attribute_value_ids(self, product):
        res = super(WebsiteSaleCustom, self).get_attribute_value_ids(product)
        variant_ids = [r[0] for r in res]

        new_res = []
        for record, variant in izip(res, request.env['product.product'].sudo().browse(variant_ids)):
            record[4].update({
                'description_sale_variant': variant.description_sale_variant,
            })
            new_res.append(record)

        return new_res
