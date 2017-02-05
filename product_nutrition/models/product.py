# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.float_utils import float_round
from openerp.exceptions import ValidationError
from openerp.addons import decimal_precision as dp

import logging

_logger = logging.getLogger(__name__)

JOULES_CALORIES_FACTOR = 4.2  # SI Value 4.1868


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    nutrition = fields.Boolean(string="Nutrition", related="product_variant_ids.nutrition")
    use_portions = fields.Boolean(string="Portions?", related="product_variant_ids.use_portions")
    portions = fields.Float(string="Portions per UoM", related="product_variant_ids.portions", default=1)
    portion_grams = fields.Float(string="Grams per Portion", related="product_variant_ids.portion_grams")
    norm_weight = fields.Float(string="Weight per UoM (g)", digits=dp.get_precision('Stock Weight'), help="Product UoM to be converted to 100g", related="product_variant_ids.norm_weight")
    norm_factor = fields.Float(string="UoM Factor", related="product_variant_ids.norm_factor")

    energy_joule = fields.Float(string="Energy (kJ)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.energy_joule")
    energy_calories = fields.Float(string="Energy (kcal)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.energy_calories")
    fat_total = fields.Float(string="Fat total (g)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.fat_total")
    fat_saturated = fields.Float(string="Fat saturated (g)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.fat_saturated")
    carbohydrate = fields.Float(string="Carbohydrate (g)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.carbohydrate")
    carbo_sugars = fields.Float(string="Sugars (g)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.carbo_sugars")
    roughage = fields.Float(string="Roughage (g)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.roughage")
    protein = fields.Float(string="Protein (g)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.protein")
    sodium = fields.Float(string="Sodium (g)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.sodium")

    energy_joule_uom = fields.Float(string="Energy per UoM (kJ)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    energy_calories_uom = fields.Float(string="Energy per UoM (kcal)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    fat_total_uom = fields.Float(string="Fat total per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    fat_saturated_uom = fields.Float(string="Fat saturated per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    carbohydrate_uom = fields.Float(string="Carbohydrate per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    carbo_sugars_uom = fields.Float(string="Sugars per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    roughage_uom = fields.Float(string="Roughage per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    protein_uom = fields.Float(string="Protein per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    sodium_uom = fields.Float(string="Sodium per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)

    energy_joule_portion = fields.Float(string="Energy per portion (kJ)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    energy_calories_portion = fields.Float(string="Energy per portion (kcal)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    fat_total_portion = fields.Float(string="Fat total per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    fat_saturated_portion = fields.Float(string="Fat saturated per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    carbohydrate_portion = fields.Float(string="Carbohydrate per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    carbo_sugars_portion = fields.Float(string="Sugars per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    roughage_portion = fields.Float(string="Roughage per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    protein_portion = fields.Float(string="Protein per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    sodium_portion = fields.Float(string="Sodium per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)

    @api.model
    def create(self, vals):
        product_tmpl = super(ProductTemplate, self).create(vals)
        product_tmpl.product_variant_ids.write(vals)
        return product_tmpl

    @api.multi
    def write(self, vals):
        nutrition = vals.get('nutrition', self.nutrition)
        norm_weight = vals.get('norm_weight', self.norm_weight)
        if nutrition and norm_weight == 0:
            raise ValidationError("Norm weight must be greater than 0")
        return super(ProductTemplate, self).write(vals)

    @api.multi
    @api.constrains('portions')
    def _contrains_portions(self):
        """
            Constraint for portion
        """
        for product in self:
            if product.portions <= 0:
                raise ValidationError("Portions must be greater than 0")
        return True

    @api.multi
    @api.onchange('norm_weight')
    def _compute_norm_factor(self):
        """
            Computes the norm factor based on the specific UoM weight in grams
        """
        for product in self:
            if product.norm_weight > 0:
                product.norm_factor = 100 / product.norm_weight
            elif product.nutrition:
                raise ValidationError("Norm weight must be greater than 0")

    @api.multi
    @api.onchange('portions', 'norm_factor', 'energy_joule', 'energy_calories', 'fat_total', 'fat_saturated', 'carbohydrate', 'carbo_sugars', 'roughage', 'protein', 'sodium')
    def _compute_facts_uom(self):
        """
            Computes the nutrition facts based on the normalization parameters
        """
        for product in self:
            if product.norm_factor > 0:
                product.energy_joule_uom = product.energy_joule / product.norm_factor
                product.energy_calories_uom = product.energy_calories / product.norm_factor
                product.fat_total_uom = product.fat_total / product.norm_factor
                product.fat_saturated_uom = product.fat_saturated / product.norm_factor
                product.carbohydrate_uom = product.carbohydrate / product.norm_factor
                product.carbo_sugars_uom = product.carbo_sugars / product.norm_factor
                product.roughage_uom = product.roughage / product.norm_factor
                product.protein_uom = product.protein / product.norm_factor
                product.sodium_uom = product.sodium / product.norm_factor
                if product._contrains_portions():
                    product.energy_joule_portion = product.energy_joule_uom / product.portions
                    product.energy_calories_portion = product.energy_calories_uom / product.portions
                    product.fat_total_portion = product.fat_total_uom / product.portions
                    product.fat_saturated_portion = product.fat_saturated_uom / product.portions
                    product.carbohydrate_portion = product.carbohydrate_uom / product.portions
                    product.carbo_sugars_portion = product.carbo_sugars_uom / product.portions
                    product.roughage_portion = product.roughage_uom / product.portions
                    product.protein_portion = product.protein_uom / product.portions
                    product.sodium_portion = product.sodium_uom / product.portions

    @api.multi
    @api.onchange('portions', 'norm_weight')
    def onchange_portions(self):
        """
            Converts Portions to Gram per portions
        """
        for product in self:
            if product.norm_weight > 0 and product.portions > 0:
                product.portion_grams = product.norm_weight / product.portions

    @api.multi
    @api.onchange('portion_grams')
    def onchange_portion_grams(self):
        """
            Converts Gram per portions to Portions
        """
        for product in self:
            if product.norm_weight > 0 and product.portion_grams > 0:
                product.portions = product.norm_weight / product.portion_grams

    @api.multi
    @api.onchange('energy_joule')
    def onchange_energy_joule(self):
        """
            Converts Joules to Calories
        """
        for product in self:
            if product.energy_joule > 0:
                product.energy_calories = product.energy_joule / JOULES_CALORIES_FACTOR

    @api.multi
    @api.onchange('energy_calories')
    def onchange_energy_calories(self):
        """
            Converts Calories to Joules
        """
        for product in self:
            if product.energy_calories > 0:
                product.energy_joule = product.energy_calories * JOULES_CALORIES_FACTOR


class ProductProduct(models.Model):
    _inherit = 'product.product'

    nutrition = fields.Boolean(string="Nutrition")
    use_portions = fields.Boolean(string="Portions?")
    portions = fields.Float(string="Portions per UoM", default=1)
    portion_grams = fields.Float(string="Grams per Portion")
    norm_weight = fields.Float(string="Weight per UoM (g)", digits=dp.get_precision('Stock Weight'), help="Product UoM to be converted to 100g", default=0)
    norm_factor = fields.Float(string="UoM Factor", compute='_compute_norm_factor', store=True, default=0)

    energy_joule = fields.Float(string="Energy (kJ)", digits=dp.get_precision('Stock Weight'))
    energy_calories = fields.Float(string="Energy (kcal)", digits=dp.get_precision('Stock Weight'))
    fat_total = fields.Float(string="Fat total (g)", digits=dp.get_precision('Stock Weight'))
    fat_saturated = fields.Float(string="Fat saturated (g)", digits=dp.get_precision('Stock Weight'))
    carbohydrate = fields.Float(string="Carbohydrate (g)", digits=dp.get_precision('Stock Weight'))
    carbo_sugars = fields.Float(string="Sugars (g)", digits=dp.get_precision('Stock Weight'))
    roughage = fields.Float(string="Roughage (g)", digits=dp.get_precision('Stock Weight'))
    protein = fields.Float(string="Protein (g)", digits=dp.get_precision('Stock Weight'))
    sodium = fields.Float(string="Sodium (g)", digits=dp.get_precision('Stock Weight'))

    energy_joule_uom = fields.Float(string="Energy per UoM (kJ)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    energy_calories_uom = fields.Float(string="Energy per UoM (kcal)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    fat_total_uom = fields.Float(string="Fat total per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    fat_saturated_uom = fields.Float(string="Fat saturated per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    carbohydrate_uom = fields.Float(string="Carbohydrate per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    carbo_sugars_uom = fields.Float(string="Sugars per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    roughage_uom = fields.Float(string="Roughage per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    protein_uom = fields.Float(string="Protein per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    sodium_uom = fields.Float(string="Sodium per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)

    energy_joule_portion = fields.Float(string="Energy per portion (kJ)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    energy_calories_portion = fields.Float(string="Energ per portiony (kcal)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    fat_total_portion = fields.Float(string="Fat total per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    fat_saturated_portion = fields.Float(string="Fat saturated per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    carbohydrate_portion = fields.Float(string="Carbohydrate per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    carbo_sugars_portion = fields.Float(string="Sugars per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    roughage_portion = fields.Float(string="Roughage per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    protein_portion = fields.Float(string="Protein per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    sodium_portion = fields.Float(string="Sodium per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)

    @api.model
    def create(self, vals):
        return super(ProductProduct, self).create(vals)

    @api.multi
    def write(self, vals):
        product = super(ProductProduct, self).write(vals)
        if vals.get('norm_weight') and self.norm_weight == 0:
            import pdb
            pdb.set_trace()
            raise ValidationError("Norm weight must be greater than 0")
        return product

    @api.multi
    @api.constrains('portions')
    def _contrains_portions(self):
        """
            Constraint for portion
        """
        for product in self:
            if product.portions <= 0:
                raise ValidationError("Portions must be greater than 0")
        return True

    @api.multi
    @api.depends('norm_weight')
    def _compute_norm_factor(self):
        """
            Computes the norm factor based on the specific UoM weight in grams
        """
        for product in self:
            if product.norm_weight > 0:
                product.norm_factor = 100 / product.norm_weight
            elif product.nutrition:
                raise ValidationError("Norm weight must be greater than 0")

    @api.multi
    @api.onchange('portions', 'norm_factor', 'energy_joule', 'energy_calories', 'fat_total', 'fat_saturated', 'carbohydrate', 'carbo_sugars', 'roughage', 'protein', 'sodium')
    def _compute_facts_uom(self):
        """
            Computes the nutrition facts based on the normalization parameters
        """
        for product in self:
            if product.norm_factor > 0:
                product.energy_joule_uom = product.energy_joule / product.norm_factor
                product.energy_calories_uom = product.energy_calories / product.norm_factor
                product.fat_total_uom = product.fat_total / product.norm_factor
                product.fat_saturated_uom = product.fat_saturated / product.norm_factor
                product.carbohydrate_uom = product.carbohydrate / product.norm_factor
                product.carbo_sugars_uom = product.carbo_sugars / product.norm_factor
                product.roughage_uom = product.roughage / product.norm_factor
                product.protein_uom = product.protein / product.norm_factor
                product.sodium_uom = product.sodium / product.norm_factor
                if product._contrains_portions():
                    product.energy_joule_portion = product.energy_joule_uom / product.portions
                    product.energy_calories_portion = product.energy_calories_uom / product.portions
                    product.fat_total_portion = product.fat_total_uom / product.portions
                    product.fat_saturated_portion = product.fat_saturated_uom / product.portions
                    product.carbohydrate_portion = product.carbohydrate_uom / product.portions
                    product.carbo_sugars_portion = product.carbo_sugars_uom / product.portions
                    product.roughage_portion = product.roughage_uom / product.portions
                    product.protein_portion = product.protein_uom / product.portions
                    product.sodium_portion = product.sodium_uom / product.portions

    @api.multi
    @api.onchange('portions', 'norm_weight')
    def onchange_portions(self):
        """
            Converts Portions to Gram per portions
        """
        for product in self:
            if product.norm_weight > 0 and product.portions > 0:
                product.portion_grams = product.norm_weight / product.portions

    @api.multi
    @api.onchange('portion_grams')
    def onchange_portion_grams(self):
        """
            Converts Gram per portions to Portions
        """
        for product in self:
            if product.norm_weight > 0 and product.portion_grams > 0:
                product.portions = product.norm_weight / product.portion_grams

    @api.multi
    @api.onchange('energy_joule')
    def onchange_energy_joule(self):
        """
            Converts Joules to Calories
        """
        for product in self:
            if product.energy_joule > 0:
                product.energy_calories = product.energy_joule / JOULES_CALORIES_FACTOR

    @api.multi
    @api.onchange('energy_calories')
    def onchange_energy_calories(self):
        """
            Converts Calories to Joules
        """
        for product in self:
            if product.energy_calories > 0:
                product.energy_joule = product.energy_calories * JOULES_CALORIES_FACTOR
