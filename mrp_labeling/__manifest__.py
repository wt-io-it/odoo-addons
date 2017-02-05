# -*- coding: utf-8 -*-
{
    'name': 'Product Labeling',
    'summary': "Product Labeling",
    'category': 'Food',
    "version": "1.0",
    "sequence": 10,
    "author": "WT-IO-IT GmbH, Wolfgang Taferner",
    "website": "https://www.wt-io-it.at",
    "license": 'AGPL-3',
    'depends': ['product_allergens_labeling', 'mrp_nutrition', 'product_expiry'],
    'data': [
        'data/ir_actions_server.xml',
        'security/ir.model.access.csv',
        'views/product.xml',
        'views/mrp_production.xml',
    ],
    'installable': True,
    'auto_install': False,
}
