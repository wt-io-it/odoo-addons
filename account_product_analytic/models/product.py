# -*- coding: utf-8 -*-

from odoo import models, fields

import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Default Analytic Account',
        default=False,
    )

    analytic_tag_ids = fields.Many2many(
        comodel_name='account.analytic.tag',
        relation='product_template_analytic_tag_rel',
        column1='template_id',
        column2='tag_id',
        string='Default Analytic Tags',
    )
