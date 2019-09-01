# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    b2c_fiscal_position = fields.Boolean(
        string='B2C Fiscal Position',
        compute='_compute_b2c_fiscal_position',
        store=True, readonly=True,
    )

    @api.depends('property_account_position_id.b2c_fiscal_position')
    def _compute_b2c_fiscal_position(self):
        for partner in self:
            position = True
            if partner.property_account_position_id:
                position = partner.property_account_position_id.b2c_fiscal_position
            partner.b2c_fiscal_position = position
