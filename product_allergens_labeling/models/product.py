# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.float_utils import float_round
from openerp.exceptions import ValidationError
import openerp.addons.decimal_precision as dp

import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ingredients = fields.Boolean(
        string="Ingredients",
        related="product_variant_ids.ingredients"
    )
    ingredient_name = fields.Char(
        string="Name as ingredient",
        related="product_variant_ids.ingredient_name",
        help="Other name than the product name. In case there is an allergen inside it is possible to mark words manually with *word* to be printed bold."
    )
    gluten_free = fields.Boolean(
        string="Gluten-free",
        related='product_variant_ids.gluten_free'
    )
    yeast_free = fields.Boolean(
        string="Yeast-free",
        related='product_variant_ids.yeast_free'
    )
    lactose_free = fields.Boolean(
        string="Lactose-free",
        related='product_variant_ids.lactose_free'
    )
    allergen_ids = fields.Many2many(
        string='Food Allergens',
        related='product_variant_ids.allergen_ids'
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    ingredients = fields.Boolean(
        string="Ingredients",
        oldname='allergens_included'
    )
    gluten_free = fields.Boolean(
        string="Gluten-free",
        compute='_compute_allergen_label_free'
    )
    yeast_free = fields.Boolean(
        string="Yeast-free"
    )
    lactose_free = fields.Boolean(
        string="Lactose-free",
        compute='_compute_allergen_label_free'
    )
    ingredient_name = fields.Char(
        string="Name as ingredient",
        translate=True,
        default=lambda self: self.name,
        help="Other name than the product name. In case there is an allergen inside it is possible to mark words manually with *word* to be printed bold."
    )
    allergen_ids = fields.Many2many(
        'product.food.allergen',
        rel='product_product_food_allergen_rel',
        id1='product_id',
        id2='food_allergen_id',
        string='Food Allergens',
    )

    @api.onchange('allergen_ids')
    def _compute_allergen_label_free(self):
        for product in self:
            product.gluten_free = False
            product.lactose_free = False
            if product.env.ref('product_allergens_labeling.cereals_containing_gluten') not in product.allergen_ids:
                product.gluten_free = True
            if product.env.ref('product_allergens_labeling.milk_lactose') not in product.allergen_ids:
                product.lactose_free = True


class FoodAllergen(models.Model):
    _name = 'product.food.allergen'

    name = fields.Char(
        string="Allergen",
        required=True,
        translate=True
    )
    description = fields.Text(
        string="Description",
        translate=True
    )
    obligated_labeling = fields.Boolean(
        string="Labeling required"
    )
