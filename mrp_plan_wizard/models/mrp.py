# -*- coding: utf-8 -*-

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class MRPProduction(models.Model):
    _inherit = 'mrp.production'

    def _get_ingredients_recursive(self, ilist, properties=None, ingredients=None, production_list=None):
        ingredients = ingredients or {}
        production_list = production_list or {}
        for bom_line, line in ilist:
            product = bom_line.product_id or bom_line.product_id.search([('product_tmpl_id', '=', bom_line.product_id.product_tmpl_id.id)])
            bom = self.env['mrp.bom']._bom_find(product=product, company_id=product.company_id.id)
            qty = bom_line.product_uom_id._compute_quantity(line['qty'], product.uom_id)
            if bom:
                # There should only be a single BOM
                if len(bom.ids) > 1:
                    if product in ingredients:
                        ingredients[product] += qty
                    else:
                        ingredients[product] = qty
                    _logger.debug("More than one Bill of Material found, so we do not care about it by now and count it as a needed ingredient!")
                else:
                    if bom.type == 'normal':
                        if product in production_list:
                            production_list[product] += qty
                        else:
                            production_list[product] = qty

                    ilist = bom.explode(
                        product,
                        qty / bom.product_qty,
                    )
                    if ilist:
                        ingredients, production_list = self._get_ingredients_recursive(
                            ilist[1], ingredients=ingredients, production_list=production_list
                        )
                    else:
                        _logger.debug("No ingredients found!")
            else:
                if product in ingredients:
                    ingredients[product] += qty
                else:
                    ingredients[product] = qty
        return ingredients, production_list

    def get_mrp_planned_list(self, product, product_qty, product_uom_id, purchase_list=None, production_list=None):
        bom_obj = self.env['mrp.bom']
        prod_obj = self.env['mrp.production']
        purchase_list = purchase_list or {}
        production_list = production_list or {}

        bom = bom_obj.search([
            '|',
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('product_id', '=', product.id)
        ])
        qty = self.env['uom.uom'].browse(product_uom_id)._compute_quantity(product_qty, product.uom_id)

        if bom:
            # We assume that there should be only one BoM per product as we do not handle a choice of BoM during the calculation
            if len(bom.ids) > 1:
                if product in purchase_list:
                    purchase_list[product] += qty
                else:
                    purchase_list[product] = qty
                _logger.debug("More than one Bill of Material found, so we do not care about it by now and count it as a needed ingredient!")
            else:
                if bom.type == 'normal':
                    if product in production_list:
                        production_list[product] += qty
                    else:
                        production_list[product] = qty

                ilist = bom.explode(
                    product,
                    qty / bom.product_qty,
                )
                if ilist:
                    purchase_list, production_list = prod_obj._get_ingredients_recursive(
                        ilist[1], ingredients=purchase_list, production_list=production_list
                    )
                else:
                    _logger.debug("No ingredients found!")
        else:
            if product in purchase_list:
                purchase_list[product] += qty
            else:
                purchase_list[product] = qty

        return purchase_list, production_list
