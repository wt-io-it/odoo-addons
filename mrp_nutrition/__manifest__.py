# -*- coding: utf-8 -*-
{
    'name': 'Manufacturing Nutrition Facts',
    'summary': "Nutrition Facts via BoM",
    'category': 'Manufacturing',
    "version": "1.0",
    "sequence": 10,
    "author": "WT-IO-IT GmbH, Wolfgang Taferner",
    "website": "https://www.wt-io-it.at",
    "license": 'AGPL-3',
    'depends': ['mrp', 'product_extended', 'product_nutrition'],
    'data': [
        'data/ir_actions_server.xml',
        'views/product.xml',
    ],
    'installable': True,
    'auto_install': False,
}
