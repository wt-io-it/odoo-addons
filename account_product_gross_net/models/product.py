# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.float_utils import float_round
from odoo.addons import decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    list_price = fields.Float(
        compute='_compute_net_price',
        # company_dependent=True,
        store=True,
    )
    lst_price_brut = fields.Float(
        string='Gross selling price',
        digits=dp.get_precision('Product Price'),
        # company_dependent=True,
    )
    lst_price_net = fields.Float(
        string='Net selling price',
        digits=dp.get_precision('Product Price'),
        # company_dependent=True,
    )

    brut_net_factor = fields.Float(
        string='Gross/Net Ratio',
        compute='_compute_net_price',
        store=True, readonly=True,
        default=1
    )

    def _get_brut_net_factor(self, price):
        product = self.product_variant_ids
        if len(self.product_variant_ids) > 1:
            product = self.product_variant_ids[0]
        company = self.env.user.company_id
        taxes = self.taxes_id.filtered(lambda x: x.company_id == company).with_context(round=False).compute_all(price, self.currency_id, 1, product=product, partner=self.env.user.company_id.partner_id)

        brut_net_factor = 1
        if taxes['total_excluded'] > 0:
            brut_net_factor = taxes['total_included'] / taxes['total_excluded']
            _logger.debug('%s / %s = %s', taxes['total_included'], taxes['total_excluded'], brut_net_factor)
        return brut_net_factor

    @api.model
    def create(self, vals):
        if 'lst_price_net' in vals:
            vals['list_price'] = vals.get('lst_price_net')
        template = super(ProductTemplate, self).create(vals)
        if 'lst_price_brut' in vals:
            vals['lst_price_net'] = template._get_net_price(vals.get('lst_price_brut'))
        if 'list_price' in vals:
            vals.update({
                'lst_price_brut': template._get_brut_price(vals.get('list_price')),
                'lst_price_net': vals.get('list_price')
            })
        template.write(vals)
        return template

    @api.multi
    def write(self, vals):
        if 'lst_price_net' in vals:
            vals['list_price'] = vals.get('lst_price_net')
        for template in self:
            if 'lst_price_brut' in vals:
                vals['lst_price_net'] = template._get_net_price(vals.get('lst_price_brut'))
            if 'list_price' in vals:
                vals.update({
                    'lst_price_brut': template._get_brut_price(vals.get('list_price')),
                    'lst_price_net': vals.get('list_price')
                })
            break
        return super(ProductTemplate, self).write(vals)

    def _get_brut_price(self, net_price):
        self.ensure_one()
        prec = self.env['decimal.precision'].precision_get('Product Price') + 1
        brut_net_factor = self._get_brut_net_factor(net_price)
        return float_round(net_price * brut_net_factor, prec)

    def _get_net_price(self, brut_price):
        self.ensure_one()
        prec = self.env['decimal.precision'].precision_get('Product Price') + 1
        brut_net_factor = self._get_brut_net_factor(brut_price)
        return float_round(brut_price / brut_net_factor, prec)

    @api.onchange('lst_price_net')
    def _compute_brut_price(self):
        for template in self:
            brut_net_factor = template._get_brut_net_factor(template.lst_price_net)

            prec = self.env['decimal.precision'].precision_get('Product Price') + 1
            template.update({
                'list_price': float_round(template.lst_price_net, prec),
                'brut_net_factor': brut_net_factor,
                'lst_price_brut': template._get_brut_price(self.lst_price_net)
            })

    @api.depends('lst_price_brut', 'taxes_id')
    def _compute_net_price(self):
        """
            The gross price will always have the last word, so even if you set a net price directly
            it might happen it will change to a calculated price based on gross price and the calculated ratio
        """
        for template in self:
            brut_net_factor = template._get_brut_net_factor(template.lst_price_brut)
            list_price = template._get_net_price(template.lst_price_brut)
            template.update({
                'list_price': list_price,
                'brut_net_factor': brut_net_factor,
                'lst_price_net': list_price
            })

    def _get_db_list_price(self):
        self.env.cr.execute("SELECT list_price FROM product_template WHERE id = %s", (self.id,))
        db_template = self.env.cr.dictfetchall()[0]
        return db_template['list_price']

    @api.multi
    def convert_list_brut_price(self):
        for template in self:
            if template.lst_price_brut == 0:
                template.lst_price_brut = template._get_db_list_price()
                template._compute_net_price()

    @api.multi
    def convert_list_net_price(self):
        for template in self:
            if template.lst_price_net == 0:
                template.lst_price_net = template._get_db_list_price()
                template._compute_brut_price()
