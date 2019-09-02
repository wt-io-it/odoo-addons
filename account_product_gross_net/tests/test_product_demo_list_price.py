# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase

class TestProductDemoListPrice(TransactionCase):

    def test_ensure_we_have_a_price_set_for_demo_products(self):
        customizable_desk = self.env['product.template'].search([('name', '=', 'Customizable Desk')])
        self.assertTrue(customizable_desk, 'Expected Customizable Desk to exist as a product for tests')
        self.assertNotEqual(0, customizable_desk.list_price, 'Expected Customizable Desk to have a non zero list price')
