# -*- coding: utf-8 -*-
{
    'name': 'Product Account Analytic',
    'summary': "Default Analytic for products",
    'category': 'Accounting',
    "version": "1.0",
    "sequence": 10,
    "author": "WT-IO-IT GmbH, Wolfgang Taferner",
    "website": "https://www.wt-io-it.at",
    "license": 'AGPL-3',
    'depends': ['product', 'account'],
    'data': [
        'views/product.xml'
    ],
    'installable': True,
    'auto_install': False,
}
