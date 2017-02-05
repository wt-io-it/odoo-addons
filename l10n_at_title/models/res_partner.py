# -*- coding: utf-8 -*-

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    title = fields.Many2one(
        ondelete='restrict',
    )


class ResPartnerTitle(models.Model):
    _inherit = 'res.partner.title'

    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country'
    )
