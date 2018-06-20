# -*- coding: utf-8 -*-
{
    "sequence": 10,
    'name': 'Product Gross/Net Price',
    'summary': 'Product Gross/Net Price',
    'category': 'Accounting',
    'version': '1.0.1',
    'depends': [
        'product',
        'account',
    ],
    "author": "WT-IO-IT GmbH, Wolfgang Taferner",
    "website": "https://www.wt-io-it.at",
    "license": 'AGPL-3',
    'data': [
        'data/ir_actions_server.xml',
        'views/product.xml',
    ],
    'installable': True,
}
