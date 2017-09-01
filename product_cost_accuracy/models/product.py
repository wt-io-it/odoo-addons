# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp

import logging

_logger = logging.getLogger(__name__)


class StockChangeStandardPrice(models.TransientModel):
    _inherit = "stock.change.standard.price"

    new_price = fields.Float(
        digits=dp.get_precision('Cost Price')
    )


class SuppliferInfo(models.Model):
    _inherit = "product.supplierinfo"

    price = fields.Float(
        digits=dp.get_precision('Cost Price')
    )


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    purchase_price = fields.Float(
        string="Purchase Price",
        compute='_compute_purchase_price',
    )
    standard_price = fields.Float(
        digits=dp.get_precision('Cost Price')
    )
    allow_standard_price_zero = fields.Boolean(string='No costs implied')

    @api.onchange('standard_price')
    def _compute_purchase_price(self):
        res = {}
        for product in self:
            factor = product.uom_po_id._compute_quantity(1, product.uom_id)
            product.purchase_price = product.standard_price * factor
        return res

    @api.multi
    def batch_compute_price(self):
        for template in self:
            for product in template.product_variant_ids:
                if product.standard_price == 0 and not product.allow_standard_price_zero:
                    product.standard_price = product.get_history_price(product.company_id.id)
                _logger.debug('Product: %s | Price: %s per %s', product.name, product.standard_price, product.uom_id.name)

            action = template.with_context(bulk_calc=True).compute_price()
            if not isinstance(action, bool):
                try:
                    price = action.get('context', {}).get('default_new_price', 0)
                    template.standard_price = price
                except:
                    _logger.error(u'Error in the calculation of the standard price for product %s', template.name)

    @api.multi
    def cron_batch_computation(self):
        self.search([]).batch_compute_price()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    standard_price = fields.Float(
        digits=dp.get_precision('Cost Price')
    )

    @api.onchange('standard_price')
    def _compute_purchase_price(self):
        res = {}
        for product in self:
            factor = product.uom_po_id._compute_quantity(1, product.uom_id)
            product.purchase_price = product.standard_price * factor
        return res

    @api.multi
    def write(self, vals):
        res = super(ProductProduct, self).write(vals)

        if vals.get('allow_standard_price_zero'):
            for product in self:
                if product.product_tmpl_id.product_variant_count == 1:
                    product.product_tmpl_id.allow_standard_price_zero = product.allow_standard_price_zero
        return res

    def _calc_price(self, bom):
        product = self
        if product.standard_price == 0 and not product.allow_standard_price_zero:
            product.standard_price = product.get_history_price(product.company_id.id)

        message = ''
        fail = False
        for sbom in bom.bom_line_ids:
            my_qty = sbom.product_qty
            if not sbom.attribute_value_ids:
                if sbom.product_id.standard_price <= 0:
                    sbom.product_id.batch_compute_price()
                price_product = sbom.product_id.uom_id._compute_price(sbom.product_id.standard_price, sbom.product_uom_id) * my_qty
                if price_product <= 0:
                    if not (sbom.product_id.allow_standard_price_zero and price_product == 0):
                        _logger.warning('Configuration missing: Product: %s | Quantity: %s | Costs: %s per %s', sbom.product_id.display_name, sbom.product_qty, sbom.product_id.standard_price, sbom.product_uom_id.name)
                        if not self._context.get('bulk_calc'):
                            fail = True
                        product_name = bom.product_id and bom.product_id.name or bom.product_tmpl_id and bom.product_tmpl_id.name
                        message += message + u'%s has a price of EUR %s defined, wheras no valid price for the product %s can be derived!\n' % (sbom.product_id.name, price_product, product_name)

        if fail:
            raise ValidationError(message)

        price = super(ProductProduct, product)._calc_price(bom)
        if price > 0:
            return price

        return price

    @api.multi
    def batch_compute_price(self):
        if self.product_tmpl_id.product_variant_count <= 1:
            self.product_tmpl_id.batch_compute_price()
