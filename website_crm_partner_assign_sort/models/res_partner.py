# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    implemented_count_override = fields.Integer("Partner value override")

    @api.depends('implemented_count_override', 'implemented_partner_ids', 'implemented_partner_ids.website_published', 'implemented_partner_ids.active')
    def _compute_implemented_partner_count(self):
        has_override = self.filtered(lambda p: p.implemented_count_override)
        for partner in has_override:
            partner.implemented_count = partner.implemented_count_override

        no_override = self - has_override
        if no_override:
            super(ResPartner, no_override)._compute_implemented_partner_count()

