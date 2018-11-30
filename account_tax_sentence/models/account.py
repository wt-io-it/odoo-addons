# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from odoo.addons import decimal_precision as dp

import logging

_logger = logging.getLogger(__name__)


class AccountTax(models.Model):
    _inherit = 'account.tax'

    apply_legal_tax_term = fields.Boolean(
        string="Apply Legal Tax Term"
    )
    legal_tax_sentence = fields.Char(
        string="Legal Tax Sentence",
        translate=True,
    )
