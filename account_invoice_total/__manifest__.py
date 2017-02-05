# -*- coding: utf-8 -*-

{
    'name': 'Inbound Invoice Total',
    'version': '1.0',
    'category': 'Accounting',
    'sequence': 14,
    'summary': 'Inbound Invoice Total',
    "author": "WT-IO-IT GmbH, Wolfgang Taferner",
    "website": "https://www.wt-io-it.at",
    "license": 'AGPL-3',
    'images': [],
    'depends': [
        'account_invoice_direction',
    ],
    'data': [
        'views/account_invoice.xml',

    ],
    'demo': [
    ],
    'test': [],
    'installable': True,
    'css': [],
    'auto_install': False,
    'application': False,
}
