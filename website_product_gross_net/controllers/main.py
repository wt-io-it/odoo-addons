# -*- coding: utf-8 -*-
from openerp import http
from openerp.addons.website_sale_options.controllers.main import website_sale_options
from openerp.http import request
import logging

_logger = logging.getLogger(__name__)


class website_product_brut_net(website_sale_options):

    # Website Sale

    def get_attribute_value_ids(self, product):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        currency_obj = pool['res.currency']
        attribute_value_ids = []
        visible_attrs = set(l.attribute_id.id
                            for l in product.attribute_line_ids
                            if len(l.value_ids) > 1)
        if request.website.pricelist_id.id != context['pricelist']:
            website_currency_id = request.website.currency_id.id
            currency_id = self.get_pricelist().currency_id.id
            for p in product.product_variant_ids:
                price = currency_obj.compute(cr, uid, website_currency_id, currency_id, p.with_context(request=request).web_list_price)
                attribute_value_ids.append([p.id, [v.id for v in p.attribute_value_ids if v.attribute_id.id in visible_attrs], p.price, price])
        else:
            attribute_value_ids = [[p.id, [v.id for v in p.attribute_value_ids if v.attribute_id.id in visible_attrs], p.price, p.with_context(request=request).web_list_price]
                                   for p in product.product_variant_ids]

        return attribute_value_ids

    # Website Sale Options

    @http.route(['/shop/modal'], type='json', auth="public", methods=['POST'], website=True)
    def modal(self, product_id, **kw):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        pricelist = self.get_pricelist()
        if not context.get('pricelist'):
            context['pricelist'] = int(pricelist)

        website_context = kw.get('kwargs', {}).get('context', {})
        context = dict(context or {}, **website_context)
        from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
        to_currency = pricelist.currency_id
        compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)
        context['request'] = request
        product = pool['product.product'].browse(cr, uid, int(product_id), context=context)
        request.website = request.website.with_context(context)

        return request.website._render("website_sale_options.modal", {
            'product': product,
            'compute_currency': compute_currency,
            'get_attribute_value_ids': self.get_attribute_value_ids,
        })

    @http.route(['/shop/get_unit_price'], type='json', auth="public", methods=['POST'], website=True)
    def get_unit_price(self, product_ids, add_qty, use_order_pricelist=False, **kw):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        products = pool['product.product'].browse(cr, uid, product_ids, context=context)
        partner = pool['res.users'].browse(cr, uid, uid, context=context).partner_id
        if use_order_pricelist:
            pricelist_id = request.session.get('sale_order_code_pricelist_id') or partner.property_product_pricelist.id
        else:
            pricelist_id = partner.property_product_pricelist.id
        prices = pool['product.pricelist'].price_rule_get_multi(cr, uid, [], [(product, add_qty, partner) for product in products], context=context)
        return {product_id: prices[product_id][pricelist_id][0] for product_id in product_ids}
