# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID
from odoo import http
from odoo.http import request
from odoo.tools.translate import _
import logging

_logger = logging.getLogger(__name__)


class publisher_warranty_transparency(http.Controller):

    @http.route(['/openerp-enterprise/ab/css/<string:dbuuid>.css'], type="http", auth="none")
    def dbuuid_pingback(self, dbuuid, **data):
        cr, uid, context, registry = request.cr, request.context.get('uid'), request.context, request.registry

        content = ''
        mimetype = 'text/css;charset=utf-8'

        name = False
        if SUPERUSER_ID != uid:
            name = 'Unauthenticated'

        if not uid:
            uid = SUPERUSER_ID
        user = registry['res.users'].browse(cr, SUPERUSER_ID, uid, context=context)

        if not name:
            name = user.name

        company = registry['res.company'].browse(cr, SUPERUSER_ID, user.company_id.id, context=context)
        company.write({'nbr_page_requests': company.nbr_page_requests + 1})
        _logger.debug("User: %s | Company: %s", name, company.name)
        return request.make_response(content, [('Content-Type', mimetype)])
