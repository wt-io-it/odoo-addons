# -*- coding: utf-8 -*-

{
    'name': 'Invoice Direction',
    'version': '1.0',
    'category': 'Accounting',
    'sequence': 14,
    'summary': 'Invoice Direction',
    "author": "WT-IO-IT GmbH, Wolfgang Taferner",
    "website": "https://www.wt-io-it.at",
    "license": 'AGPL-3',
    'images': [],
    'depends': [
        'account',
    ],
    'data': [
        'views/account_invoice.xml',
        'views/report_invoice.xml',

    ],
    'demo': [
    ],
    'test': [],
    'installable': True,
    'css': [],
    'auto_install': False,
    'application': False,
}
