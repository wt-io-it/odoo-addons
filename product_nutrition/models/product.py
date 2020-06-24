# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.float_utils import float_round
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp

import logging

_logger = logging.getLogger(__name__)

JOULES_CALORIES_FACTOR = 4.2  # SI Value 4.1868


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    nutrition = fields.Boolean(string="Nutrition", related="product_variant_ids.nutrition", readonly=False)
    use_portions = fields.Boolean(string="Portions?", related="product_variant_ids.use_portions", readonly=False)
    portions = fields.Float(string="Portions per UoM", related="product_variant_ids.portions", default=1, readonly=False)
    portion_grams = fields.Float(string="Grams per Portion", related="product_variant_ids.portion_grams", readonly=False)
    norm_weight = fields.Float(string="Weight per UoM (g)", digits=dp.get_precision('Stock Weight'), help="Product UoM to be converted to 100g", related="product_variant_ids.norm_weight", readonly=False)
    norm_factor = fields.Float(string="UoM Factor", related="product_variant_ids.norm_factor", readonly=False)
    carb_percentage = fields.Float(string="Carb Percentage", related="product_variant_ids.carb_percentage", digits=dp.get_precision('Stock Weight'), default=1)

    energy_joule = fields.Float(string="Energy (kJ)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.energy_joule", readonly=False)
    energy_calories = fields.Float(string="Energy (kcal)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.energy_calories", readonly=False)
    fat_total = fields.Float(string="Fat total (g)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.fat_total", readonly=False)
    fat_saturated = fields.Float(string="Fat saturated (g)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.fat_saturated", readonly=False)
    carbohydrate = fields.Float(string="Carbohydrate (g)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.carbohydrate", readonly=False)
    carbo_sugars = fields.Float(string="Sugars (g)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.carbo_sugars", readonly=False)
    roughage = fields.Float(string="Roughage (g)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.roughage", readonly=False)
    protein = fields.Float(string="Protein (g)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.protein", readonly=False)
    sodium = fields.Float(string="Sodium (g)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.sodium", readonly=False)
    bread_units = fields.Float(string="Bread Units (BU)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.bread_units", readonly=True)

    energy_joule_uom = fields.Float(string="Energy per UoM (kJ)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    energy_calories_uom = fields.Float(string="Energy per UoM (kcal)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    fat_total_uom = fields.Float(string="Fat total per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    fat_saturated_uom = fields.Float(string="Fat saturated per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    carbohydrate_uom = fields.Float(string="Carbohydrate per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    carbo_sugars_uom = fields.Float(string="Sugars per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    roughage_uom = fields.Float(string="Roughage per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    protein_uom = fields.Float(string="Protein per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    sodium_uom = fields.Float(string="Sodium per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    bread_units_uom = fields.Float(string="Bread Units per UoM (BU)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.bread_units_uom", default=0, readonly=True)

    energy_joule_portion = fields.Float(string="Energy per portion (kJ)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    energy_calories_portion = fields.Float(string="Energy per portion (kcal)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    fat_total_portion = fields.Float(string="Fat total per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    fat_saturated_portion = fields.Float(string="Fat saturated per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    carbohydrate_portion = fields.Float(string="Carbohydrate per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    carbo_sugars_portion = fields.Float(string="Sugars per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    roughage_portion = fields.Float(string="Roughage per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    protein_portion = fields.Float(string="Protein per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    sodium_portion = fields.Float(string="Sodium per portion (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    bread_units_portion = fields.Float(string="Bread Units per portion (BU)", digits=dp.get_precision('Stock Weight'), related="product_variant_ids.bread_units_portion", default=0, readonly=True)

    @api.model
    def create(self, vals):
        # As message_follower_ids and other magic values are injected during create
        local_vals = dict(vals)
        product_tmpl = super(ProductTemplate, self).create(vals)
        product_tmpl.product_variant_ids.write(local_vals)
        return product_tmpl

    @api.multi
    def write(self, vals):
        for template in self:
            nutrition = vals.get('nutrition', template.nutrition)
            norm_weight = vals.get('norm_weight', template.norm_weight)
            if nutrition and norm_weight == 0:
                raise ValidationError("Norm weight must be greater than 0")
        return super(ProductTemplate, self).write(vals)

    @api.multi
    @api.constrains('portions', 'use_portions')
    def _contrains_portions(self):
        """
            Constraint for portion
        """
        for template in self:
            if template.use_portions and template.portions <= 0:
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
    @api.depends('portions', 'norm_factor', 'energy_joule', 'energy_calories', 'fat_total', 'fat_saturated', 'carbohydrate', 'carbo_sugars', 'roughage', 'protein', 'sodium')
    def _compute_facts_uom(self):
        """
            Computes the nutrition facts based on the normalization parameters
        """
        for template in self:
            template.bread_units = template.carbohydrate / 12
            if template.norm_factor > 0:
                template.energy_joule_uom = template.energy_joule / template.norm_factor
                template.energy_calories_uom = template.energy_calories / template.norm_factor
                template.fat_total_uom = template.fat_total / template.norm_factor
                template.fat_saturated_uom = template.fat_saturated / template.norm_factor
                template.carbohydrate_uom = template.carbohydrate / template.norm_factor
                template.carbo_sugars_uom = template.carbo_sugars / template.norm_factor
                template.roughage_uom = template.roughage / template.norm_factor
                template.protein_uom = template.protein / template.norm_factor
                template.sodium_uom = template.sodium / template.norm_factor

                divisor = template.fat_total * 9.2 + template.carbohydrate * 4.2 + template.roughage * 2 + template.protein * 4.1
                if divisor:
                    template.carb_percentage = (
                        template.carbohydrate * 4.2 + template.roughage * 2
                    ) / divisor * 100

                if template.use_portions and template.portions != 0:
                    template.energy_joule_portion = template.energy_joule_uom / template.portions
                    template.energy_calories_portion = template.energy_calories_uom / template.portions
                    template.fat_total_portion = template.fat_total_uom / template.portions
                    template.fat_saturated_portion = template.fat_saturated_uom / template.portions
                    template.carbohydrate_portion = template.carbohydrate_uom / template.portions
                    template.carbo_sugars_portion = template.carbo_sugars_uom / template.portions
                    template.roughage_portion = template.roughage_uom / template.portions
                    template.protein_portion = template.protein_uom / template.portions
                    template.sodium_portion = template.sodium_uom / template.portions

                if template.use_portions and template.portions == 0:
                    _logger.info('The template %s is marked to use portions but the portions are zero', template.display_name)

    @api.multi
    @api.onchange('portions', 'norm_weight')
    def onchange_portions(self):
        """
            Converts Portions to Gram per portions
        """
        for template in self:
            if template.norm_weight > 0 and template.portions > 0:
                template.portion_grams = template.norm_weight / template.portions

    @api.multi
    @api.onchange('portion_grams')
    def onchange_portion_grams(self):
        """
            Converts Gram per portions to Portions
        """
        for template in self:
            if template.norm_weight > 0 and template.portion_grams > 0:
                template.portions = template.norm_weight / template.portion_grams

    @api.multi
    @api.onchange('energy_joule')
    def onchange_energy_joule(self):
        """
            Converts Joules to Calories
        """
        for template in self:
            if template.energy_joule > 0:
                template.energy_calories = template.energy_joule / JOULES_CALORIES_FACTOR

    @api.multi
    @api.onchange('energy_calories')
    def onchange_energy_calories(self):
        """
            Converts Calories to Joules
        """
        for template in self:
            if template.energy_calories > 0:
                template.energy_joule = template.energy_calories * JOULES_CALORIES_FACTOR


class ProductProduct(models.Model):
    _inherit = 'product.product'

    nutrition = fields.Boolean(string="Nutrition")
    use_portions = fields.Boolean(string="Portions?")
    portions = fields.Float(string="Portions per UoM", default=1)
    portion_grams = fields.Float(string="Grams per Portion")
    norm_weight = fields.Float(string="Weight per UoM (g)", digits=dp.get_precision('Stock Weight'), help="Product UoM to be converted to 100g", default=0)
    norm_factor = fields.Float(string="UoM Factor", compute='_compute_norm_factor', store=True, default=0)
    carb_percentage = fields.Float(string="Carb Percentage", compute='_compute_facts_uom', store=True, digits=dp.get_precision('Stock Weight'), default=1)

    energy_joule = fields.Float(string="Energy (kJ)", digits=dp.get_precision('Stock Weight'))
    energy_calories = fields.Float(string="Energy (kcal)", digits=dp.get_precision('Stock Weight'))
    bread_units = fields.Float(string="Bread Units (BU)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0, readonly=True)
    fat_total = fields.Float(string="Fat total (g)", digits=dp.get_precision('Stock Weight'))
    fat_saturated = fields.Float(string="Fat saturated (g)", digits=dp.get_precision('Stock Weight'))
    carbohydrate = fields.Float(string="Carbohydrate (g)", digits=dp.get_precision('Stock Weight'))
    carbo_sugars = fields.Float(string="Sugars (g)", digits=dp.get_precision('Stock Weight'))
    roughage = fields.Float(string="Roughage (g)", digits=dp.get_precision('Stock Weight'))
    protein = fields.Float(string="Protein (g)", digits=dp.get_precision('Stock Weight'))
    sodium = fields.Float(string="Sodium (g)", digits=dp.get_precision('Stock Weight'))

    energy_joule_uom = fields.Float(string="Energy per UoM (kJ)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    energy_calories_uom = fields.Float(string="Energy per UoM (kcal)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    bread_units_uom = fields.Float(string="Bread Units per UoM (BU)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0, readonly=True)
    fat_total_uom = fields.Float(string="Fat total per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    fat_saturated_uom = fields.Float(string="Fat saturated per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    carbohydrate_uom = fields.Float(string="Carbohydrate per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    carbo_sugars_uom = fields.Float(string="Sugars per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    roughage_uom = fields.Float(string="Roughage per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    protein_uom = fields.Float(string="Protein per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    sodium_uom = fields.Float(string="Sodium per UoM (g)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)

    energy_joule_portion = fields.Float(string="Energy per portion (kJ)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    energy_calories_portion = fields.Float(string="Energy per portion (kcal)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0)
    bread_units_portion = fields.Float(string="Bread Units per portion (BU)", compute='_compute_facts_uom', digits=dp.get_precision('Stock Weight'), default=0, readonly=True)
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
            raise ValidationError("Norm weight must be greater than 0")
        return product

    @api.multi
    @api.constrains('portions', 'use_portions')
    def _contrains_portions(self):
        """
            Constraint for portion
        """
        for product in self:
            if product.use_portions and product.portions <= 0:
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
    @api.depends('portions', 'norm_factor', 'energy_joule', 'energy_calories', 'fat_total', 'fat_saturated', 'carbohydrate', 'carbo_sugars', 'roughage', 'protein', 'sodium')
    def _compute_facts_uom(self):
        """
            Computes the nutrition facts based on the normalization parameters
        """
        for product in self:
            product.bread_units = product.carbohydrate / 12
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
                product.bread_units_uom = product.carbohydrate_uom / 12

                divisor = product.fat_total * 9.2 + product.carbohydrate * 4.2 + product.roughage * 2 + product.protein * 4.1
                if divisor:
                    product.carb_percentage = (
                        product.carbohydrate * 4.2 + product.roughage * 2
                    ) / divisor * 100

                if product.use_portions:
                    product.energy_joule_portion = product.energy_joule_uom / product.portions
                    product.energy_calories_portion = product.energy_calories_uom / product.portions
                    product.fat_total_portion = product.fat_total_uom / product.portions
                    product.fat_saturated_portion = product.fat_saturated_uom / product.portions
                    product.carbohydrate_portion = product.carbohydrate_uom / product.portions
                    product.carbo_sugars_portion = product.carbo_sugars_uom / product.portions
                    product.roughage_portion = product.roughage_uom / product.portions
                    product.protein_portion = product.protein_uom / product.portions
                    product.sodium_portion = product.sodium_uom / product.portions

                    product.bread_units_portion = product.carbohydrate_portion / 12

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
