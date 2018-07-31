# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from unittest import skip

class TestProductPriceConversion(TransactionCase):

    def setUp(self):
        super(TestProductPriceConversion, self).setUp()

        self.tax = self.env['account.tax'].create({
            'name': "20%",
            'amount_type': 'percent',
            'amount': 20,
            'sequence': 1,
            'company_id': self.env.user.company_id.id
        })

    def get_product_values(self):
        return {
            'name': 'Product for testing brut net prices',
            'taxes_id': [(6, 0, [self.tax.id])],
        }

    def _test_brut_net_price(self, price_vals, price_expected_vals):
        vals = self.get_product_values()
        vals.update(price_vals)
        product = self.env['product.product'].create(vals)
        self.assertEquals(price_expected_vals['lst_price'], product.lst_price)
        self.assertEquals(price_expected_vals['lst_price_net'], product.lst_price_net)
        self.assertEquals(price_expected_vals['lst_price_brut'], product.lst_price_brut)

    def test_price_net_given(self):
        self._test_brut_net_price({
                'lst_price_net': 100,
            },
            {
                'lst_price': 100,
                'lst_price_net': 100,
                'lst_price_brut': 120,
            })

    def test_price_brut_given(self):
        """
            if only brut is given it is overriden by the default value of
            list_price (1.0)
        """
        self._test_brut_net_price({
                'lst_price_brut': 200,
            },
            {
                'lst_price': 1,
                'lst_price_net': 1,
                'lst_price_brut': 1.2,
            })

    def test_list_price_and_price_brut_given(self):
        self._test_brut_net_price({
                'list_price': 200,
                'lst_price_brut': 240,
            },
            {
                'lst_price': 200,
                'lst_price_net': 200,
                'lst_price_brut': 240,
            })

    def test_list_price_given(self):
        self._test_brut_net_price({
                'list_price': 300,
            },
            {
                'lst_price': 300,
                'lst_price_net': 300,
                'lst_price_brut': 360,
            })

    def test_all_given_same(self):
        self._test_brut_net_price({
                'lst_price_net': 100,
                'list_price': 100,
                'lst_price_brut': 120,
            },
            {
                'lst_price': 100,
                'lst_price_net': 100,
                'lst_price_brut': 120,
            })

    def test_all_given_different(self):
        self._test_brut_net_price({
                'lst_price_net': 100,
                'list_price': 200,
                'lst_price_brut': 300,
            },
            {
                'lst_price': 100,
                'lst_price_net': 100,
                'lst_price_brut': 120,
            })