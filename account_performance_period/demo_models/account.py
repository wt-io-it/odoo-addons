# -*- coding: utf-8 -*-
from odoo import models, api
from datetime import date
import threading


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model_create_multi
    def create(self, vals_list):
        if hasattr(threading.currentThread(), 'testing') and threading.currentThread().testing:
            # when we are in testing mode (inserting demo data into the db) we add dates for odoo core demo data
            for vals in vals_list:
                if not vals.get('date_start', None):
                    vals['date_start'] = date.today()
                if not vals.get('date_end', None):
                    vals['date_end'] = date.today()
        return super(AccountInvoiceLine, self).create(vals_list)

