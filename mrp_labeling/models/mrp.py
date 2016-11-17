# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta
from openerp.tools.float_utils import float_round
from openerp.exceptions import ValidationError
import addons.decimal_precision as dp

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

    @api.v7
    def product_id_change(self, cr, uid, ids, product_id, qty, context=None):
        context = context or {}
        res = super(MRPProduction, self).product_id_change(cr, uid, ids, product_id, qty, context=context)
        product = self.pool['product.product'].browse(cr, uid, product_id, context=context)
        res['value'].update({
            'life_date': _calc_date(product, 'life_time'),
            'use_date': _calc_date(product, 'use_time'),
            'removal_date': _calc_date(product, 'removal_time'),
            'alert_date': _calc_date(product, 'alert_time'),
        })
        return res

    @api.one
    @api.onchange('date_planned')
    def _get_date(self):
        """Compute the limit date for a given date"""
        product = self.product_id
        from_date = datetime.strptime(self.date_planned, '%Y-%m-%d %H:%M:%S')

        self.life_date = _calc_date(product, 'life_time', from_date=from_date)
        self.use_date = _calc_date(product, 'use_time', from_date=from_date)
        self.removal_date = _calc_date(product, 'removal_time', from_date=from_date)
        self.alert_date = _calc_date(product, 'alert_time', from_date=from_date)

    @api.multi
    def action_production_end(self):
        if super(MRPProduction, self).action_production_end():
            product = self.product_id
            from_date = datetime.strptime(self.date_finished, '%Y-%m-%d %H:%M:%S')
            if not _calc_date(product, 'use_time', from_date=from_date):
                raise ValidationError('Produkt hat kein Ablaufdatum konfiguriert! Auftrag kann nicht abgeschlossen werden.')
            res = self.write({
                'life_date': _calc_date(product, 'life_time', from_date=from_date),
                'use_date': _calc_date(product, 'use_time', from_date=from_date),
                'removal_date': _calc_date(product, 'removal_time', from_date=from_date),
                'alert_date': _calc_date(product, 'alert_time', from_date=from_date),
            })
            return res
        else:
            return False

    life_date = fields.Date(
        string='End of Life Date',
        help='This is the date on which the goods with this Serial Number may become dangerous and must not be consumed.',
        readonly=True, states={'draft': [('readonly', False)]}
    )
    use_date = fields.Date(
        string='Best before Date',
        help='This is the date on which the goods with this Serial Number start deteriorating, without being dangerous yet.',
        readonly=True, states={'draft': [('readonly', False)]}
    )
    removal_date = fields.Date(
        string='Removal Date',
        help='This is the date on which the goods with this Serial Number should be removed from the stock.',
        readonly=True, states={'draft': [('readonly', False)]}
    )
    alert_date = fields.Date(
        string='Alert Date',
        help="This is the date on which an alert should be notified about the goods with this Serial Number.",
        readonly=True, states={'draft': [('readonly', False)]}
    )
