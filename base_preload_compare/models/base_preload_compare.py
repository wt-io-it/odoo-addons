# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class BasePreloadCompare(models.Model):
    _name = 'base.preload.compare'
    _description = 'Modules & Models to be preloaded when installing/updating them.'
    _order = 'id, name'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
    )
    module_id = fields.Many2one(
        'ir.module.module',
        string='Module',
        required=True,
    )
    model_ids = fields.Many2many(
        'ir.model',
        string='Models',
        required=True,
    )

    @api.multi
    def _compute_name(self):
        for bpc in self:
            bpc.name = '%s (%s)' % (bpc.module_id.display_name, ', '.join(bpc.model_ids.mapped('display_name')))
