# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from odoo.addons import decimal_precision as dp
from datetime import datetime

import pytz

import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    scheduled_date = fields.Date(
        string="Scheduled Date",
        related="picking_id.scheduled_date_only",
    )


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _order = "priority desc, scheduled_date_only asc, priority_scheduled desc, scheduled_date asc, id desc"

    priority_scheduled = fields.Selection(
        selection=PROCUREMENT_PRIORITIES,
        string='Day Priority',
        index=True, track_visibility='onchange',
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        default='1',
    )
    scheduled_date_only = fields.Date(
        string='Scheduled Date',
        compute='_compute_scheduled_date_only',
        index=True, store=True, readonly=True
    )

    @api.depends('scheduled_date')
    def _compute_scheduled_date_only(self):
        _logger.debug('Method _compute_scheduled_date_only (%s records)', len(self))
        tz_name = self.sudo().env.user.tz
        user_tz = tz_name and pytz.timezone(tz_name) or False
        utc = pytz.utc
        for picking in self:
            scheduled_date_only = False
            scheduled_date = picking.scheduled_date
            if scheduled_date:
                scheduled_date_dt = scheduled_date_tz = scheduled_date
                if user_tz:
                    scheduled_date_tz = utc.localize(scheduled_date_dt).astimezone(user_tz)
                scheduled_date_only = scheduled_date_tz.date()

            picking.scheduled_date_only = scheduled_date_only
