# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase

class TestProductDemoListPrice(TransactionCase):

    def test_ensure_we_have_a_price_set_for_demo_products(self):
        apple_in_ear = self.env['product.template'].search([('name', '=', 'Apple In-Ear Headphones')])
        self.assertNotEqual(0, apple_in_ear.list_price, 'Expected apple in ear headphones to have a non zero list price')