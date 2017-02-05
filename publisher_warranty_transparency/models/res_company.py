# -*- coding: utf-8 -*-

from odoo import models, fields, api, release
import logging

_logger = logging.getLogger(__name__)


class res_company(models.Model):
    _inherit = "res.company"

    contract_reference = fields.Char(
        'Contract Reference',
        required=True
    )
    date_start = fields.Date(
        'Valid from',
        required=True
    )
    date_to = fields.Date(
        'Valid to',
        required=True,
    )

    nbr_page_requests = fields.Integer(
        'Active HTTP Page Requests',
    )

    nbr_users_contracted = fields.Integer(
        'Active Users allowed',
        required=True
    )

    nbr_apps_contracted = fields.Integer(
        'Apps allowed',
    )

    nbr_users = fields.Integer(
        'Total Users',
        compute='_get_warranty_info',
        readonly=True
    )
    nbr_active_users = fields.Integer(
        'Active Users',
        compute='_get_warranty_info',
        readonly=True
    )
    nbr_share_users = fields.Integer(
        'Share Users',
        compute='_get_warranty_info',
        readonly=True
    )

    nbr_active_share_users = fields.Integer(
        'Active Share Users',
        compute='_get_warranty_info',
        readonly=True
    )
    version = fields.Char(
        'Current Version',
        compute='_get_warranty_info',
    )
    apps = fields.Integer(
        'Installed Apps',
        compute='_get_warranty_info',
        readonly=True
    )

    def _get_warranty_info(self):
        msg = self.env['publisher_warranty.contract']._get_message()
        self.version = release.version
        self.nbr_users = msg['nbr_users']
        self.nbr_active_users = msg['nbr_active_users']
        self.nbr_share_users = msg['nbr_share_users']
        self.nbr_active_share_users = msg['nbr_active_share_users']
        self.apps = len(msg['apps'])
