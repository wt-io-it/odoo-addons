# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    login_date = fields.Date(
        compute='_get_login_date',
        search='_search_login_date'
    )

    @api.v7
    def _get_login_date(self, cr, uid, ids, name, args, context=None):
        context = context or {}
        res = super(ResUsers, self)._get_login_date(cr, uid, ids, name, args, context=context)
        return res

    @api.v8
    def _get_login_date(self):
        res = self.pool.get('res.users')._get_login_date(self._cr, self._uid, self.ids, 'login_date', None, self._context)
        for user in self:
            user.login_date = res[user.id]

    @api.multi
    def _search_login_date(self, operator, value):
        users = self.env['res.users.login'].search([('login_dt', operator, value)])
        return [('id', 'in', users.ids)]
