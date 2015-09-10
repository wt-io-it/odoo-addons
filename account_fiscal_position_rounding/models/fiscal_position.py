# -*- coding: utf-8 -*-

from openerp import models, fields
import logging

_logger = logging.getLogger(__name__)


class account_fiscal_position(models.Model):
    _inherit = 'account.fiscal.position'

    reverse_charge_sentence = fields.Char(
        string="Reverse Charge Sentence"
    )
    b2c_fiscal_position = fields.Boolean(string='B2C')
