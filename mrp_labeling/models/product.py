# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_round
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp
import sys

import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ingredient_list = fields.Html(string='Ingredients List', related='product_variant_ids.ingredient_list', readonly=False)
    has_organic_farming = fields.Boolean(
        string='Organic Origin',
        help='Labelled Organic Farming Ingredients',
        related='product_variant_ids.has_organic_farming',
        readonly = False,
    )
    calculated_norm_weight = fields.Float(string='Berechnetes Gewicht pro ME (g)', related="product_variant_ids.calculated_norm_weight", store=True, readonly=False)
    norm_weight_diff = fields.Float(string='Abweichung (g)', related="product_variant_ids.norm_weight_diff", store=True, readonly=False)
    deviation = fields.Float(string='Abweichung (Prozent)', related="product_variant_ids.deviation", store=True, readonly=False)

    def _recursive_bom_ingredients_complete(self, qty=0, uom=0, level=0, ingredients=None):
        ingredients = ingredients or {}
        level += 1

        if not self.nutrition:
            raise ValidationError(_("Product %s is not activated for nutrition!") % self.display_name)

        if self.bom_ids:
            bom = self.bom_ids[0]
            bom_uom = bom.product_uom_id
            bom_qty = bom.product_qty
            if uom and uom != bom.product_uom_id:
                bom_qty = uom._compute_quantity(bom.product_qty, uom, round=False)
            multiplier = qty / bom_qty

            if len(self.bom_ids.ids) > 1:
                _logger.debug('\n--------- #%s Multiple BoMs (%s) ---------', level, self.display_name)
                _logger.debug('\n--------- Taking first BoM to calculate ---------', level, self.display_name)
                _logger.debug('\n Qty: %s %s | BoM Result Qty: %s %s | Multiplier: %s', qty, uom.name, bom_qty, bom_uom.name, multiplier)
                # Ask which one should be taken, for now we take the first bom
                for bom in [self.bom_ids[0]]:
                    for bom_line in bom.bom_line_ids.filtered(lambda bl: not bl.product_id.is_packaging):
                        partial_qty = bom_line.product_qty * multiplier
                        ingredients = bom_line.product_id.product_tmpl_id._recursive_bom_ingredients_complete(qty=partial_qty, uom=bom_line.product_uom_id, level=level, ingredients=ingredients)
            else:
                _logger.debug('\n--------- #%s Single BoM (%s) ---------', level, self.display_name)
                _logger.debug('\n Qty: %s %s | BoM Result Qty: %s %s | Multiplier: %s', qty, uom.name, bom_qty, bom_uom.name, multiplier)
                for bom_line in bom.bom_line_ids.filtered(lambda bl: not bl.product_id.is_packaging):
                    bom_line_qty = bom_line.product_qty
                    if bom_line.product_id.uom_id != bom_line.product_uom_id:
                        bom_line_qty = bom_line.product_uom_id._compute_quantity(bom_line.product_qty, bom_line.product_id.uom_id, round=False)
                    partial_qty = bom_line_qty * multiplier
                    ingredients = bom_line.product_id.product_tmpl_id._recursive_bom_ingredients_complete(qty=partial_qty, uom=bom_line.product_uom_id, level=level, ingredients=ingredients)
        else:
            _logger.debug('--------- #%s Product (%s) to List ---------', level, self.display_name)
            ingredients = self.add_to_ingridients_list_complete(ingredients, qty=qty, uom=uom)

        return ingredients

    @api.multi
    def add_to_ingridients_list_complete(self, ingredients, qty=0, uom=False):

        if self.norm_weight <= 0:
            raise ValidationError(_("Norm weight for product %s must be greater than 0!") % self.display_name)

        if uom and uom != self.uom_id:
            qty = uom._compute_quantity(qty, self.uom_id, round=False)

        multiplier = self.norm_weight * qty / 100
        _logger.debug("Facts: %s %s (%s kcal) of %s", qty, self.uom_id.name, self.energy_calories * multiplier, self.display_name)

        if self in ingredients:
            ingredients[self]['norm_weight'] += self.norm_weight * qty

            ingredients[self].update({
                'ingredient_name': (self.ingredient_name or self.name).strip(),
                'yeast_free': self.yeast_free,
                'organic_farming': self.organic_farming,
                'allergen_ids': self.allergen_ids,
            })
        else:
            ingredients[self] = {
                'norm_weight': self.norm_weight * qty,
                'ingredient_name': (self.ingredient_name or self.name).strip(),
                'yeast_free': self.yeast_free,
                'organic_farming': self.organic_farming,
                'allergen_ids': self.allergen_ids,
            }

        return ingredients

    @api.multi
    def write_nutrition_facts_complete(self, ingredients):
        tuple_list = []
        yeast_free = True
        organic_farming = False
        allergen_ids = self.env['product.food.allergen']
        total_norm_weight = 0
        for info in ingredients.values():
            total_norm_weight += info['norm_weight']
            tuple_list.append((info['ingredient_name'], info['norm_weight'], info['yeast_free'], info['allergen_ids'], info['organic_farming']))
            allergen_ids |= info['allergen_ids']
            if info['organic_farming']:
                organic_farming = True
            if not info['yeast_free']:
                yeast_free = False

        ingredient_list = sorted(tuple_list, key=lambda info: info[1], reverse=True)

        norm_weight_diff = total_norm_weight - self.norm_weight
        deviation = (total_norm_weight / self.norm_weight - 1) * 100
        show_percentage = True
        if abs(deviation) > 20:
            show_percentage = False

        ingredient_names = []
        for info in ingredient_list:
            ingredient_name = info[0]
            if info[3]:
                if len(ingredient_name.split('*')) > 1:
                    ingredient_name = ''
                    for part in info[0].split('*'):
                        if ',' in part or ' ' in part:
                            ingredient_name += part
                        else:
                            ingredient_name += '<strong>' + part + '</strong>'
                else:
                    if show_percentage and round(info[1] / total_norm_weight * 100) > 1:
                        ingredient_name = '<strong>%s (%s%%)</strong>' % (ingredient_name, int(round(info[1] / total_norm_weight * 100)))
                    else:
                        ingredient_name = '<strong>%s</strong>' % ingredient_name

            _logger.debug("%s g of %s", round(info[1], 2), ingredient_name)

            if info[4]:
                ingredient_name = '%s*' % ingredient_name
            ingredient_names.append(ingredient_name)

        _logger.debug("Abweichung: %s%%", round(deviation, 2))
        _logger.debug('Total Norm Weight: %s g', round(total_norm_weight, 2))

        self.write({
            'ingredient_list': ', '.join(ingredient_names) or self.ingredient_name or self.name,
            'has_organic_farming': organic_farming,
            'yeast_free': yeast_free,
            'calculated_norm_weight': total_norm_weight,
            'deviation': deviation,
            'norm_weight_diff': norm_weight_diff,
            'allergen_ids': [(6, 0, allergen_ids.ids)],
        })

    @api.multi
    def compute_labeling_facts(self):
        for template in self:
            qty = 1
            uom = template.uom_id
            ingredients = template._recursive_bom_ingredients_complete(qty=qty, uom=uom)
            template.write_nutrition_facts_complete(ingredients)

    @api.multi
    def batch_compute_labeling(self):
        for template in self:
            try:
                template.compute_labeling_facts()
            except ValidationError as e:
                if e[1]:
                    _logger.error('ValidationError: %s', e[1])
            except:
                e = sys.exc_info()
                _logger.error('%s: %s', e[0], e[1])

    @api.multi
    def batch_compute_all(self):
        self.mapped('product_variant_ids').batch_compute_price()
        super(ProductTemplate, self).batch_compute_all()
        for template in self:
            try:
                template.compute_labeling_facts()
            except ValidationError as e:
                if e[1]:
                    _logger.error('ValidationError: %s', e[1])
            except:
                e = sys.exc_info()
                _logger.error('%s: %s', e[0], e[1])


class ProductProduct(models.Model):
    _inherit = 'product.product'

    ingredient_list = fields.Html(string='Ingredients List')
    has_organic_farming = fields.Boolean(
        string='Organic Origin',
        help='Labelled Organic Farming Ingredients',
    )
    calculated_norm_weight = fields.Float(string='Berechnetes Gewicht pro ME (g)', digits=dp.get_precision('Stock Weight'), default=0)
    norm_weight_diff = fields.Float(string='Abweichung (g)', default=0)
    deviation = fields.Float(string='Abweichung (Prozent)', default=0)

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
                        message += message + u'%s hat einen Preis von EUR %s definiert, weshalb kein gültiger Preis für das Produkt %s ermittelt werden konnte!\n' % (sbom.product_id.name, price_product, product_name)

        if fail:
            raise ValidationError(message)

        price = super(ProductProduct, product)._calc_price(bom)
        if price > 0:
            return price

        return price

    @api.multi
    def compute_labeling_facts(self):
        for product in self:
            template = product.product_tmpl_id
            if template.product_variant_count <= 1:
                template.compute_labeling_facts()

    @api.multi
    def batch_compute_labeling(self):
        for product in self:
            try:
                product.compute_labeling_facts()
            except ValidationError as e:
                if e[1]:
                    _logger.error('ValidationError: %s', e[1])
            except:
                e = sys.exc_info()
                _logger.error('%s: %s', e[0], e[1])

    @api.multi
    def batch_compute_all(self):
        self.mapped('product_tmpl_id').batch_compute_all()
