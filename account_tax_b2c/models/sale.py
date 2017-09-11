# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models

import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order']

    def _amount_all(self):
        if len(self) == 0:
            company_id = self.env.user.company_id
        else:
            company_id = self[0].company_id
        company = company_id.sudo()
        current_method = company.tax_calculation_rounding_method
        if not self.fiscal_position_id.b2c_fiscal_position:
            company.tax_calculation_rounding_method = 'round_globally'
        else:
            company.tax_calculation_rounding_method = 'round_per_line'
        res = super(SaleOrder, self)._amount_all()
        company.tax_calculation_rounding_method = current_method
        return res
