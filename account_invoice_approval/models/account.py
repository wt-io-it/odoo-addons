# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp

import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    invoice_released = fields.Boolean(string='Released', copy=False)

    @api.multi
    def invoice_release_toggle(self):
        context = self.env.context.copy()
        context['release'] = not self.invoice_released
        self.env.context = context
        return self.invoice_release()

    @api.multi
    def invoice_release(self):
        _logger.debug("Un/Release Invoice: %s", self)
        text = _('unreleased')

        for invoice in self:
            if invoice.write({
                'invoice_released': self.env.context.get('release', False)
            }):
                if self.env.context.get('release', False):
                    text = _('released')
                invoice.message_post(body=_("""Invoice %s""") % (text))
                _logger.debug(
                    "Context (Release): %s | Invoice %s",
                    self.env.context.get('release'), text
                )

        return True
