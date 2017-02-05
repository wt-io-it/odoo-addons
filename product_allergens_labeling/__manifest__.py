# -*- coding: utf-8 -*-
{
    'name': 'Product Allergens Labeling',
    'summary': "Product Allergens Labeling (EU 1169/2011)",
    'category': 'Food',
    "version": "1.0",
    "sequence": 10,
    "author": "WT-IO-IT GmbH, Wolfgang Taferner",
    "website": "https://www.wt-io-it.at",
    "license": 'AGPL-3',
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',
        'data/product_food_allergen.xml',
        'views/product.xml',
        'views/product_food_allergen.xml'
    ],
    'installable': True,
    'auto_install': False,
}
