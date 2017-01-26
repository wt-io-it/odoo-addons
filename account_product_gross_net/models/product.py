# -*- coding: utf-8 -*-

from openerp import SUPERUSER_ID
from openerp import models, fields, api
from openerp.tools.float_utils import float_round
import openerp.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)


class product_category(models.Model):
    _inherit = "product.category"

    brut_net_factor = fields.Float(string='Gross/Net Ratio', default=1)


class product_template(models.Model):
    _inherit = 'product.template'

    list_price = fields.Float(
        compute='_compute_net_price',
    )
    lst_price_brut = fields.Float(
        string='Gross selling price',
        digits_compute=dp.get_precision('Product Price'),
    )

    brut_net_factor = fields.Float(string='Gross/Net Ratio', default=1)

    def get_list_price_factor(self, product, request):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        orm_user = registry.get('res.users')
        partner = orm_user.browse(cr, SUPERUSER_ID, request.uid, context).partner_id
        factor = 1
        if hasattr(partner.property_account_position, 'b2c_fiscal_position') and partner.property_account_position.b2c_fiscal_position:
            if product.brut_net_factor > 0:
                factor = product.brut_net_factor
        return factor

    @api.onchange('categ_id')
    def onchange_product_category(self):
        if self.categ_id.brut_net_factor > 0:
            self.brut_net_factor = self.categ_id.brut_net_factor

    @api.one
    @api.depends('lst_price_brut', 'brut_net_factor')
    def _compute_net_price(self):
        if self.brut_net_factor:
            self.list_price = self.lst_price_brut / self.brut_net_factor

        if 'request' not in self.env.context and 'uid' in self.env.context:
            variants_attribute_prices = self.env['product.attribute.price'].search(
                [('product_tmpl_id', '=', self.id)]
            )
            for attribute_price in variants_attribute_prices:
                value = attribute_price.value_id
                _logger.debug("Variant: %s", value.name)
                if value:
                    price_extra = value.with_context(active_id=self.id).price_extra
                    value.with_context(source='template').sudo().write({
                        'lst_price_brut': (
                            self.list_price + price_extra
                        ) * self.brut_net_factor
                    })


class product_product(models.Model):
    _inherit = 'product.product'

    @api.onchange('categ_id')
    def onchange_product_category(self):
        if self.categ_id.brut_net_factor > 0:
            self.product_tmpl_id.write({'brut_net_factor': self.categ_id.brut_net_factor})
            self.product_tmpl_id._compute_net_price()

            self.lst_price = self.lst_price_brut / self.categ_id.brut_net_factor


class product_attribute_value(models.Model):
    _inherit = "product.attribute.value"

    lst_price_brut = fields.Float(
        string='Gross selling price',
        digits_compute=dp.get_precision('Product Price'),
    )

    @api.multi
    def write(self, vals):
        if self.env.context.get('active_id', False):
            price_att = self.env['product.attribute.price'].search([('product_tmpl_id', '=', self.env.context['active_id']), ('value_id', '=', self.id)])
            if price_att:
                template = price_att.product_tmpl_id
                if 'price_extra' in vals:
                    vals['lst_price_brut'] = template.lst_price_brut + vals['price_extra'] * template.brut_net_factor
                elif 'lst_price_brut' in vals:
                    vals['price_extra'] = (vals['lst_price_brut'] - template.lst_price_brut) / template.brut_net_factor
        elif 'lst_price_brut' in vals:
            del vals['lst_price_brut']
        return super(product_attribute_value, self).write(vals)


class product_attribute_price(models.Model):
    _inherit = 'product.attribute.price'

    lst_price_brut = fields.Float(
        string='Gross selling price',
        related='value_id.lst_price_brut'
    )

    @api.model
    def create(self, vals):
        template = self.product_tmpl_id.browse(vals['product_tmpl_id'])
        vals['lst_price_brut'] = template.lst_price_brut + float(vals['price_extra']) * template.brut_net_factor
        return super(product_attribute_price, self).create(vals)
