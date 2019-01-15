# -*- coding: utf-8 -*-
{
    'name': 'Product Cost Accuracy',
    'summary': "Product Cost Accuracy",
    'category': 'Product',
    "version": "1.0",
    "sequence": 10,
    "author": "WT-IO-IT GmbH, Wolfgang Taferner",
    "website": "https://www.wt-io-it.at",
    "license": 'AGPL-3',
    'depends': [
        'mrp_bom_cost',
        'stock_account',
    ],
    'data': [
        'data/ir_cron.xml',
        'data/decimal_precision.xml',
        'data/ir_actions_server.xml',
        'views/product.xml',
    ],
    'installable': True,
    'auto_install': False,
}
