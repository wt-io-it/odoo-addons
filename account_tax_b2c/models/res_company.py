# -*- coding: utf-8 -*-
# © 2015 WT-IO IT GmbH <https://www.wt-io-it.at>
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _set_rounding_method(self, method='round_globally'):
        '''
            We do set the tax_calculation method based on the situation and need to update the cache as most users are not allowed to write the settings
        '''
        self.sudo().tax_calculation_rounding_method = method

        # Cache Alignment
        self._cache['tax_calculation_rounding_method'] = method
        _logger.debug('User Company: %s | Root Company: %s', self.tax_calculation_rounding_method, self.sudo().tax_calculation_rounding_method)
