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

    is_packaging = fields.Boolean(string="Packaging?", related="product_variant_ids.is_packaging", readonly=False)

    def _recursive_bom_ingredients(self, qty=0, uom=0, level=0, ingredients=None):
        ingredients = ingredients or {}
        level += 1

        if not self.nutrition:
            raise ValidationError(_("Product %s is not activated for nutrition!") % self.display_name)

        if self.bom_ids:
            if len(self.bom_ids.ids) > 1:
                _logger.debug('\n--------- #%s Multiple BoMs (%s) ---------', level, self.display_name)
                # Ask which one should be taken, for now we take the first bom
                for bom in [self.bom_ids[0]]:
                    bom_ingridients = {}
                    for bom_line in bom.bom_line_ids.filtered(lambda bl: not bl.product_id.is_packaging):
                        bom_ingridients = bom_line.product_id.product_tmpl_id._recursive_bom_ingredients(qty=bom_line.product_qty, uom=bom_line.product_uom_id, level=level, ingredients=bom_ingridients)
                self.write_nutrition_facts(bom_ingridients, qty=bom.product_qty, uom=bom.product_uom_id)
            else:
                bom = self.bom_ids
                _logger.debug('\n--------- #%s Single BoM (%s) ---------', level, self.display_name)
                bom_ingridients = {}
                for bom_line in bom.bom_line_ids.filtered(lambda bl: not bl.product_id.is_packaging):
                    bom_ingridients = bom_line.product_id.product_tmpl_id._recursive_bom_ingredients(qty=bom_line.product_qty, uom=bom_line.product_uom_id, level=level, ingredients=bom_ingridients)
                self.write_nutrition_facts(bom_ingridients, qty=bom.product_qty, uom=bom.product_uom_id)

        _logger.debug('--------- #%s Product (%s) to List ---------', level, self.display_name)

        ingredients = self.add_to_ingridients_list(ingredients, qty=qty, uom=uom)

        return ingredients

    @api.multi
    def add_to_ingridients_list(self, ingredients, qty=0, uom=False):

        if self.norm_weight <= 0:
            raise ValidationError(_("Norm weight for product %s must be greater than 0!") % self.display_name)

        if uom and uom != self.uom_id:
            qty = uom._compute_quantity(qty, self.uom_id)

        multiplier = self.norm_weight * qty / 100
        _logger.debug("Facts: %s %s (%s kcal) of %s", qty, self.uom_id.name, self.energy_calories * multiplier, self.display_name)

        if self in ingredients:
            ingredients[self]['norm_weight'] += self.norm_weight * qty
            ingredients[self]['energy_joule'] += self.energy_joule * multiplier
            ingredients[self]['energy_calories'] += self.energy_calories * multiplier
            ingredients[self]['fat_total'] += self.fat_total * multiplier
            ingredients[self]['fat_saturated'] += self.fat_saturated * multiplier
            ingredients[self]['carbohydrate'] += self.carbohydrate * multiplier
            ingredients[self]['carbo_sugars'] += self.carbo_sugars * multiplier
            ingredients[self]['roughage'] += self.roughage * multiplier
            ingredients[self]['protein'] += self.protein * multiplier
            ingredients[self]['sodium'] += self.sodium * multiplier
        else:
            ingredients[self] = {
                'norm_weight': self.norm_weight * qty,
                'energy_joule': self.energy_joule * multiplier,
                'energy_calories': self.energy_calories * multiplier,
                'fat_total': self.fat_total * multiplier,
                'fat_saturated': self.fat_saturated * multiplier,
                'carbohydrate': self.carbohydrate * multiplier,
                'carbo_sugars': self.carbo_sugars * multiplier,
                'roughage': self.roughage * multiplier,
                'protein': self.protein * multiplier,
                'sodium': self.sodium * multiplier,
            }

        return ingredients

    @api.multi
    def write_nutrition_facts(self, ingredients, qty=0, uom=False):

        energy_joule, energy_calories, fat_total, fat_saturated, carbohydrate, carbo_sugars, roughage, protein, sodium = [0, 0, 0, 0, 0, 0, 0, 0, 0]

        if uom and uom != self.uom_id:
            qty = uom._compute_quantity(qty, self.uom_id)

        for info in ingredients.values():
            energy_joule += info['energy_joule'] / qty * self.norm_factor
            energy_calories += info['energy_calories'] / qty * self.norm_factor
            fat_total += info['fat_total'] / qty * self.norm_factor
            fat_saturated += info['fat_saturated'] / qty * self.norm_factor
            carbohydrate += info['carbohydrate'] / qty * self.norm_factor
            carbo_sugars += info['carbo_sugars'] / qty * self.norm_factor
            roughage += info['roughage'] / qty * self.norm_factor
            protein += info['protein'] / qty * self.norm_factor
            sodium += info['sodium'] / qty * self.norm_factor

        self.write({
            'energy_joule': energy_joule,
            'energy_calories': energy_calories,
            'fat_total': fat_total,
            'fat_saturated': fat_saturated,
            'carbohydrate': carbohydrate,
            'carbo_sugars': carbo_sugars,
            'roughage': roughage,
            'protein': protein,
            'sodium': sodium
        })

        _logger.debug('--------- Kontrolle ---------')
        _logger.debug('Total: %s %s', qty, uom.name)
        _logger.debug('Brennwert: %s kJ / %s kcal', energy_joule, energy_calories)
        _logger.debug('Fett: %s kcal', fat_total)
        _logger.debug(u' - davon gesättigte Fettsäuren: %s kcal', fat_saturated)
        _logger.debug('Kohlenhydrate: %s', carbohydrate)
        _logger.debug(' - davon Zucker: %s', carbo_sugars)
        _logger.debug('Ballaststoffe: %s', roughage)
        _logger.debug(u'Eiweiß: %s', protein)
        _logger.debug('Salz: %s', sodium)

        return ingredients

    @api.multi
    def compute_nutrition_facts(self):
        self._recursive_bom_ingredients(qty=1, uom=self.uom_id)

    @api.multi
    def batch_compute_nutrition(self):
        for template in self:
            try:
                template.compute_nutrition_facts()
            except ValidationError as e:
                if e[1]:
                    _logger.error('ValidationError: %s', e[1])
            except:
                e = sys.exc_info()
                _logger.error('%s: %s', e[0], e[1])

    @api.multi
    def batch_compute_all(self):
        for template in self:
            try:
                template.compute_nutrition_facts()
            except ValidationError as e:
                if e[1]:
                    _logger.error('ValidationError: %s', e[1])
            except:
                e = sys.exc_info()
                _logger.error('%s: %s', e[0], e[1])


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_packaging = fields.Boolean(string="Packaging?")

    @api.multi
    def compute_nutrition_facts(self):
        if self.product_tmpl_id.product_variant_count <= 1:
            self.product_tmpl_id.compute_nutrition_facts()

    @api.multi
    def batch_compute_nutrition(self):
        for product in self:
            try:
                product.compute_nutrition_facts()
            except ValidationError as e:
                if e[1]:
                    _logger.error('ValidationError: %s', e[1])
            except:
                e = sys.exc_info()
                _logger.error('%s: %s', e[0], e[1])

    @api.multi
    def batch_compute_all(self):
        if self.product_tmpl_id.product_variant_count <= 1:
            self.product_tmpl_id.batch_compute_all()
