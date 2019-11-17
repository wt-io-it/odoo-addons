# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.tools.float_utils import float_round
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp

import logging

_logger = logging.getLogger(__name__)


def _calc_date(product, dtype, from_date=datetime.today()):
    duration = False
    if product:
        duration = getattr(product, dtype)

    # set date to False when no expiry time specified on the product
    date = duration and (from_date + timedelta(days=duration))
    return date and date.strftime('%Y-%m-%d') or False


class MRPProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model
    def create(self, vals):
        production = super(MRPProduction, self).create(vals)
        production.get_date()
        return production

    @api.multi
    def write(self, vals):
        res = super(MRPProduction, self).write(vals)
        return res

    def get_date(self):
        self._get_date()

    @api.onchange('date_planned_start', 'product_id')
    def _get_date(self):
        """Compute the limit date for a given date"""
        product = self.product_id
        date = self.date_planned_start
        if self.date_start:
            date = self.date_start
        if self.date_finished:
            date = self.date_finished
        from_date = date

        self.life_date = _calc_date(product, 'life_time', from_date=from_date)
        self.use_date = _calc_date(product, 'use_time', from_date=from_date)
        self.removal_date = _calc_date(product, 'removal_time', from_date=from_date)
        self.alert_date = _calc_date(product, 'alert_time', from_date=from_date)

        return {
            'date': from_date
        }

    life_date = fields.Date(
        string='End of Life Date',
        help='This is the date on which the goods with this Serial Number may become dangerous and must not be consumed.',
        readonly=True, states={'confirmed': [('readonly', False)]}
    )
    use_date = fields.Date(
        string='Best before Date',
        help='This is the date on which the goods with this Serial Number start deteriorating, without being dangerous yet.',
        readonly=True, states={'confirmed': [('readonly', False)]}
    )
    removal_date = fields.Date(
        string='Removal Date',
        help='This is the date on which the goods with this Serial Number should be removed from the stock.',
        readonly=True, states={'confirmed': [('readonly', False)]}
    )
    alert_date = fields.Date(
        string='Alert Date',
        help="This is the date on which an alert should be notified about the goods with this Serial Number.",
        readonly=True, states={'confirmed': [('readonly', False)]}
    )


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    def do_produce(self):
        res = super(MrpProductProduce, self).do_produce()
        production = self.production_id
        date = production._get_date().get('date')
        if date and not _calc_date(production.product_id, 'use_time', from_date=date):
            raise ValidationError('Produkt hat kein Ablaufdatum konfiguriert! Auftrag kann nicht abgeschlossen werden.')
        if not date:
            raise ValidationError('Es konnte kein Datum ermittelt werden, welches eigentlich nicht passieren darf. Bitte kontaktieren Sie Ihren Odoo Betreuer.')
        return res
